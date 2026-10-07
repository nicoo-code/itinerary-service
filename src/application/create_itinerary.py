import logging
import uuid
from datetime import datetime

from src.domain.events.itinerary_created_event import ItineraryCreatedEvent
from src.domain.exceptions import (
    AirportNotFoundException,
    InvalidItineraryException,
)
from src.domain.models.itinerary import Itinerary, OutboxEvent
from src.domain.ports.airport_validator_port import AirportValidatorPort
from src.domain.ports.itinerary_repository_port import ItineraryRepositoryPort

logger = logging.getLogger(__name__)

# Re-exportar excepciones para mantener compatibilidad hacia atrás
__all__ = [
    "CreateItineraryUseCase",
    "AirportNotFoundException",
    "InvalidItineraryException",
]


class CreateItineraryUseCase:
    """Caso de uso para crear itinerarios validando aeropuertos y aplicando Transactional Outbox."""

    def __init__(
        self,
        itinerary_repo: ItineraryRepositoryPort,
        airport_validator: AirportValidatorPort,
    ):
        self._itinerary_repo = itinerary_repo
        self._airport_validator = airport_validator

    async def execute(
        self,
        user_name: str,
        origin_airport_id: int,
        destination_airport_id: int,
        departure_date: datetime,
        duration_minutes: int,
        trace_id: str = "00000000000000000000000000000000",
    ) -> Itinerary:
        # 1. Regla de Negocio: Origen y destino no pueden ser idénticos
        if origin_airport_id == destination_airport_id:
            raise InvalidItineraryException(
                "El aeropuerto de salida y de llegada no pueden ser el mismo."
            )

        # 2. Validación síncrona HTTP de aeropuerto de origen
        origin_exists = await self._airport_validator.validate_airport_exists(
            origin_airport_id
        )
        if not origin_exists:
            logger.error(
                f"Validation failed: Origin airport ID {origin_airport_id} does not exist."
            )
            raise AirportNotFoundException(
                f"El aeropuerto de salida con ID {origin_airport_id} no existe."
            )

        # 3. Validación síncrona HTTP de aeropuerto de destino
        destination_exists = await self._airport_validator.validate_airport_exists(
            destination_airport_id
        )
        if not destination_exists:
            logger.error(
                f"Validation failed: Destination airport ID {destination_airport_id} does not exist."
            )
            raise AirportNotFoundException(
                f"El aeropuerto de llegada con ID {destination_airport_id} no existe."
            )

        # 4. Construcción de entidad de dominio Itinerary
        itinerary_id = uuid.uuid4()
        itinerary = Itinerary(
            id=itinerary_id,
            user_name=user_name,
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            departure_date=departure_date,
            duration_minutes=duration_minutes,
            status="CREATED",
        )

        # 5. Construcción del Evento de Integración para el Buzón Transaccional
        integration_event = ItineraryCreatedEvent.create(
            itinerary_id=itinerary_id,
            user_name=user_name,
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            departure_date=departure_date,
            duration_minutes=duration_minutes,
            trace_id=trace_id,
        )

        outbox_event = OutboxEvent(
            id=uuid.UUID(integration_event.event_id),
            aggregate_type="ITINERARY",
            aggregate_id=itinerary_id,
            event_type=integration_event.event_type,
            payload=integration_event.to_dict(),
            status="PENDING",
        )

        # 6. Persistencia atómica ACID (Transactional Outbox)
        saved_itinerary = await self._itinerary_repo.save_with_outbox(
            itinerary, outbox_event
        )
        logger.info(
            f"Itinerary {itinerary_id} and OutboxEvent {integration_event.event_id} persisted atomically.",
            extra={"trace_id": trace_id},
        )
        return saved_itinerary
