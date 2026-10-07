import uuid
from abc import ABC, abstractmethod

from src.domain.models.itinerary import OutboxEvent


class OutboxRepositoryPort(ABC):
    """Puerto para la gestión y sondeo de eventos en el buzón transaccional (Transactional Outbox)."""

    @abstractmethod
    async def get_pending_events(self, limit: int = 20) -> list[OutboxEvent]:
        """Obtiene un lote de eventos en estado PENDING ordenados cronológicamente."""

    @abstractmethod
    async def mark_as_published(self, event_id: uuid.UUID) -> None:
        """Actualiza el estado del evento a PUBLISHED con fecha de procesamiento."""

    @abstractmethod
    async def mark_as_failed(
        self, event_id: uuid.UUID, retry_increment: bool = True
    ) -> None:
        """Registra un fallo en la publicación e incrementa el contador de reintentos."""
