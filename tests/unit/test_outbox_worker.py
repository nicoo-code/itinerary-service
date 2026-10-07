import asyncio
import uuid
from unittest.mock import AsyncMock

import pytest
from src.domain.models.itinerary import OutboxEvent
from src.infrastructure.messaging.outbox_relay_worker import OutboxRelayWorker


@pytest.mark.asyncio
async def test_outbox_worker_publishes_and_marks_published():
    mock_outbox_repo = AsyncMock()
    mock_publisher = AsyncMock()

    event_id = uuid.uuid4()
    dummy_event = OutboxEvent(
        id=event_id,
        aggregate_type="ITINERARY",
        aggregate_id=uuid.uuid4(),
        event_type="ItineraryCreatedEvent",
        payload={"event_id": str(event_id), "data": {"user_name": "Test User"}},
        status="PENDING",
    )

    first_call = True

    async def fake_get_pending(limit=10):
        nonlocal first_call
        if first_call:
            first_call = False
            return [dummy_event]
        return []

    mock_outbox_repo.get_pending_events.side_effect = fake_get_pending
    mock_publisher.publish_event.return_value = True

    worker = OutboxRelayWorker(
        outbox_repo=mock_outbox_repo,
        publisher=mock_publisher,
        poll_interval_seconds=0.01,
    )

    task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.05)
    worker.stop()
    await task

    mock_publisher.publish_event.assert_called_once_with(
        payload=dummy_event.payload, routing_key="itinerary.created"
    )
    mock_outbox_repo.mark_as_published.assert_called_once_with(event_id)


@pytest.mark.asyncio
async def test_outbox_worker_marks_failed_on_publish_error():
    mock_outbox_repo = AsyncMock()
    mock_publisher = AsyncMock()

    event_id = uuid.uuid4()
    dummy_event = OutboxEvent(
        id=event_id,
        aggregate_type="ITINERARY",
        aggregate_id=uuid.uuid4(),
        event_type="ItineraryCreatedEvent",
        payload={"event_id": str(event_id)},
        status="PENDING",
    )

    first_call = True

    async def fake_get_pending(limit=10):
        nonlocal first_call
        if first_call:
            first_call = False
            return [dummy_event]
        return []

    mock_outbox_repo.get_pending_events.side_effect = fake_get_pending
    mock_publisher.publish_event.return_value = False

    worker = OutboxRelayWorker(
        outbox_repo=mock_outbox_repo,
        publisher=mock_publisher,
        poll_interval_seconds=0.01,
    )

    task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.05)
    worker.stop()
    await task

    mock_publisher.publish_event.assert_called_once()
    mock_outbox_repo.mark_as_failed.assert_called_once_with(event_id)
    mock_outbox_repo.mark_as_published.assert_not_called()
