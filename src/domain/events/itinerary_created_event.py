import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


def _get_utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True)
class ItineraryCreatedData:
    """Datos de negocio transportados por el evento de creación de itinerario."""

    itinerary_id: str
    user_name: str
    origin_airport_id: int
    destination_airport_id: int
    departure_date: str
    duration_minutes: int
    status: str = "CREATED"


@dataclass(frozen=True)
class ItineraryCreatedEvent:
    """
    Evento de Integración formal emitido cuando un itinerario ha sido confirmado y persistido.
    Cumple con el contrato AsyncAPI 2.6.0 definido para la arquitectura Event-Driven.
    """

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "ItineraryCreatedEvent"
    timestamp: str = field(default_factory=lambda: _get_utc_now().isoformat() + "Z")
    trace_id: str = "00000000000000000000000000000000"
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        itinerary_id: uuid.UUID,
        user_name: str,
        origin_airport_id: int,
        destination_airport_id: int,
        departure_date: datetime,
        duration_minutes: int,
        trace_id: str = "00000000000000000000000000000000",
    ) -> "ItineraryCreatedEvent":
        data = ItineraryCreatedData(
            itinerary_id=str(itinerary_id),
            user_name=user_name,
            origin_airport_id=origin_airport_id,
            destination_airport_id=destination_airport_id,
            departure_date=departure_date.isoformat() + "Z",
            duration_minutes=duration_minutes,
            status="CREATED",
        )
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="ItineraryCreatedEvent",
            timestamp=_get_utc_now().isoformat() + "Z",
            trace_id=trace_id,
            data=asdict(data),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
