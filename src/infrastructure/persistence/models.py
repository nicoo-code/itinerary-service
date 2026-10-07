import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _get_utc_now():
    return datetime.now(UTC)


class ItineraryModel(Base):
    """Modelo ORM para la tabla de itinerarios."""

    __tablename__ = "itineraries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_name = Column(String(100), nullable=False)
    origin_airport_id = Column(Integer, nullable=False)
    destination_airport_id = Column(Integer, nullable=False)
    departure_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="CREATED")
    created_at = Column(DateTime, nullable=False, default=_get_utc_now)
    updated_at = Column(
        DateTime, nullable=False, default=_get_utc_now, onupdate=_get_utc_now
    )


class OutboxEventModel(Base):
    """Modelo ORM para la tabla de eventos de integración del Transactional Outbox."""

    __tablename__ = "outbox_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type = Column(String(50), nullable=False, default="ITINERARY")
    aggregate_id = Column(String(36), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, PUBLISHED, FAILED
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=_get_utc_now)
    processed_at = Column(DateTime, nullable=True)
