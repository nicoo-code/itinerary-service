import uuid
from abc import ABC, abstractmethod

from src.domain.models.itinerary import Itinerary, OutboxEvent


class ItineraryRepositoryPort(ABC):
    """Puerto de persistencia transaccional para itinerarios y eventos outbox."""

    @abstractmethod
    async def save_with_outbox(
        self, itinerary: Itinerary, outbox_event: OutboxEvent
    ) -> Itinerary:
        """Persiste atómicamente el itinerario y el evento outbox en la misma transacción ACID."""

    @abstractmethod
    async def find_by_id(self, itinerary_id: uuid.UUID) -> Itinerary | None:
        """Busca un itinerario por su identificador único."""

    @abstractmethod
    async def list_all(self) -> list[Itinerary]:
        """Obtiene la lista completa de itinerarios registrados."""

    @abstractmethod
    async def delete(self, itinerary_id: uuid.UUID) -> bool:
        """Elimina un itinerario por su identificador único."""
