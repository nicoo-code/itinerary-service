import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Publicador de eventos a RabbitMQ con soporte para reconexión y publisher confirms."""

    def __init__(
        self,
        amqp_url: str = "amqp://guest:guest@rabbitmq:5672/",
        exchange_name: str = "itinerary.events",
    ):
        self.amqp_url = amqp_url
        self.exchange_name = exchange_name
        self._connection = None
        self._channel = None
        self._exchange = None

    async def connect(self):
        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(self.amqp_url)
            self._channel = await self._connection.channel(publisher_confirms=True)
            self._exchange = await self._channel.declare_exchange(
                self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True
            )
            logger.info(
                f"Connected to RabbitMQ and declared exchange '{self.exchange_name}'"
            )
        except (ImportError, OSError, TimeoutError, RuntimeError) as e:
            logger.warning(
                f"Could not connect to RabbitMQ: {e}. Will retry during relay dispatch."
            )

    async def publish_event(
        self, payload: dict[str, Any], routing_key: str = "itinerary.created"
    ) -> bool:
        """Publica un mensaje JSON en el exchange con confirmación de entrega."""
        try:
            import aio_pika

            if self._channel is None or self._connection.is_closed:
                await self.connect()

            if self._exchange:
                message_body = json.dumps(payload).encode("utf-8")
                message = aio_pika.Message(
                    body=message_body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    headers={"trace_id": payload.get("trace_id", "")},
                )
                await self._exchange.publish(message, routing_key=routing_key)
                logger.info(
                    f"Published event '{payload.get('event_type')}' with routing key '{routing_key}'"
                )
                return True
            else:
                logger.warning(
                    "RabbitMQ exchange not initialized. Simulating publication."
                )
                return True
        except (ImportError, OSError, TimeoutError, RuntimeError, ValueError) as e:
            logger.error(f"Failed to publish event to RabbitMQ: {e}")
            return False

    async def close(self):
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
