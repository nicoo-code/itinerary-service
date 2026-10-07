import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, sessionmaker
from src.domain.models.itinerary import Itinerary, OutboxEvent
from src.domain.ports.itinerary_repository_port import ItineraryRepositoryPort
from src.domain.ports.outbox_repository_port import OutboxRepositoryPort
from src.infrastructure.persistence.models import ItineraryModel, OutboxEventModel

logger = logging.getLogger(__name__)


class SqlAlchemyItineraryRepository(ItineraryRepositoryPort, OutboxRepositoryPort):
    """
    Repositorio que implementa la persistencia de itinerarios y eventos Transactional Outbox.
    Garantiza atomicidad transaccional ACID para evitar el Double Write Problem.
    """

    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def _to_domain_itinerary(self, model: ItineraryModel) -> Itinerary:
        return Itinerary(
            id=uuid.UUID(model.id),
            user_name=model.user_name,
            origin_airport_id=model.origin_airport_id,
            destination_airport_id=model.destination_airport_id,
            departure_date=model.departure_date,
            duration_minutes=model.duration_minutes,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_domain_outbox(self, model: OutboxEventModel) -> OutboxEvent:
        return OutboxEvent(
            id=uuid.UUID(model.id),
            aggregate_type=model.aggregate_type,
            aggregate_id=uuid.UUID(model.aggregate_id),
            event_type=model.event_type,
            payload=model.payload,
            status=model.status,
            retry_count=model.retry_count,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )

    async def save_with_outbox(
        self, itinerary: Itinerary, outbox_event: OutboxEvent
    ) -> Itinerary:
        session: Session = self.session_factory()
        try:
            # 1. Crear modelo Itinerary
            itin_model = ItineraryModel(
                id=str(itinerary.id),
                user_name=itinerary.user_name,
                origin_airport_id=itinerary.origin_airport_id,
                destination_airport_id=itinerary.destination_airport_id,
                departure_date=itinerary.departure_date,
                duration_minutes=itinerary.duration_minutes,
                status=itinerary.status,
                created_at=itinerary.created_at,
                updated_at=itinerary.updated_at,
            )

            # 2. Crear modelo OutboxEvent
            outbox_model = OutboxEventModel(
                id=str(outbox_event.id),
                aggregate_type=outbox_event.aggregate_type,
                aggregate_id=str(outbox_event.aggregate_id),
                event_type=outbox_event.event_type,
                payload=outbox_event.payload,
                status=outbox_event.status,
                retry_count=outbox_event.retry_count,
                created_at=outbox_event.created_at,
                processed_at=outbox_event.processed_at,
            )

            # Transacción atómica ACID
            session.add(itin_model)
            session.add(outbox_model)
            session.commit()
            session.refresh(itin_model)

            return self._to_domain_itinerary(itin_model)

        except Exception as e:
            session.rollback()
            logger.error(f"Atomic transaction rollback in save_with_outbox: {e}")
            raise
        finally:
            session.close()

    async def find_by_id(self, itinerary_id: uuid.UUID) -> Itinerary | None:
        session: Session = self.session_factory()
        try:
            model = (
                session.query(ItineraryModel)
                .filter(ItineraryModel.id == str(itinerary_id))
                .first()
            )
            if model:
                return self._to_domain_itinerary(model)
            return None
        finally:
            session.close()

    async def list_all(self) -> list[Itinerary]:
        session: Session = self.session_factory()
        try:
            models = (
                session.query(ItineraryModel)
                .order_by(ItineraryModel.created_at.desc())
                .all()
            )
            return [self._to_domain_itinerary(m) for m in models]
        finally:
            session.close()

    async def delete(self, itinerary_id: uuid.UUID) -> bool:
        session: Session = self.session_factory()
        try:
            model = (
                session.query(ItineraryModel)
                .filter(ItineraryModel.id == str(itinerary_id))
                .first()
            )
            if model:
                session.delete(model)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_pending_events(self, limit: int = 20) -> list[OutboxEvent]:
        session: Session = self.session_factory()
        try:
            models = (
                session.query(OutboxEventModel)
                .filter(OutboxEventModel.status == "PENDING")
                .order_by(OutboxEventModel.created_at.asc())
                .limit(limit)
                .all()
            )
            return [self._to_domain_outbox(m) for m in models]
        finally:
            session.close()

    async def mark_as_published(self, event_id: uuid.UUID) -> None:
        session: Session = self.session_factory()
        try:
            model = (
                session.query(OutboxEventModel)
                .filter(OutboxEventModel.id == str(event_id))
                .first()
            )
            if model:
                model.status = "PUBLISHED"
                model.processed_at = datetime.now(UTC)
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def mark_as_failed(
        self, event_id: uuid.UUID, retry_increment: bool = True
    ) -> None:
        session: Session = self.session_factory()
        try:
            model = (
                session.query(OutboxEventModel)
                .filter(OutboxEventModel.id == str(event_id))
                .first()
            )
            if model:
                if retry_increment:
                    model.retry_count += 1
                if model.retry_count >= 5:
                    model.status = "FAILED"
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
