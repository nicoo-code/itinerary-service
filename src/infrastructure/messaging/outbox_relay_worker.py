import asyncio
import logging

from src.domain.ports.outbox_repository_port import OutboxRepositoryPort
from src.infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher

logger = logging.getLogger(__name__)


class OutboxRelayWorker:
    """
    Worker en segundo plano para el patrón Transactional Outbox.
    Sondea eventos PENDING en la base de datos relacional y los despacha a RabbitMQ.
    Garantiza consistencia eventual y entrega at-least-once.
    """

    def __init__(
        self,
        outbox_repo: OutboxRepositoryPort,
        publisher: RabbitMQPublisher,
        poll_interval_seconds: float = 1.0,
    ):
        self.outbox_repo = outbox_repo
        self.publisher = publisher
        self.poll_interval_seconds = poll_interval_seconds
        self._is_running = False

    async def start(self):
        """Inicia el ciclo continuo de sondeo y relé."""
        self._is_running = True
        logger.info("Starting OutboxRelayWorker background process...")

        while self._is_running:
            try:
                # 1. Obtener lote de eventos pendientes
                pending_events = await self.outbox_repo.get_pending_events(limit=10)

                for event in pending_events:
                    # 2. Publicar en RabbitMQ
                    success = await self.publisher.publish_event(
                        payload=event.payload, routing_key="itinerary.created"
                    )

                    # 3. Actualizar estado en la base de datos
                    if success:
                        await self.outbox_repo.mark_as_published(event.id)
                        logger.info(f"Outbox event {event.id} marked as PUBLISHED.")
                    else:
                        await self.outbox_repo.mark_as_failed(event.id)
                        logger.warning(
                            f"Outbox event {event.id} failed to publish, marked for retry."
                        )

            except (RuntimeError, OSError, ValueError, KeyError, TypeError) as e:
                logger.error(f"Error in OutboxRelayWorker execution loop: {e}")

            # Esperar antes del siguiente sondeo
            await asyncio.sleep(self.poll_interval_seconds)

    def stop(self):
        self._is_running = False
        logger.info("Stopping OutboxRelayWorker...")
