import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def _get_utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass
class Itinerary:
    """Entidad pura del dominio para representar un itinerario de viaje personal."""

    id: uuid.UUID
    user_name: str
    origin_airport_id: int
    destination_airport_id: int
    departure_date: datetime
    duration_minutes: int
    status: str = "CREATED"
    created_at: datetime = field(default_factory=_get_utc_now)
    updated_at: datetime = field(default_factory=_get_utc_now)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = str(self.id)
        data["departure_date"] = self.departure_date.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class OutboxEvent:
    """Entidad del patrón Transactional Outbox para garantizar entrega confiable de eventos."""

    id: uuid.UUID
    aggregate_type: str
    aggregate_id: uuid.UUID
    event_type: str
    payload: dict[str, Any]
    status: str = "PENDING"  # PENDING, PUBLISHED, FAILED
    retry_count: int = 0
    created_at: datetime = field(default_factory=_get_utc_now)
    processed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = str(self.id)
        data["aggregate_id"] = str(self.aggregate_id)
        data["created_at"] = self.created_at.isoformat()
        if self.processed_at:
            data["processed_at"] = self.processed_at.isoformat()
        return data
