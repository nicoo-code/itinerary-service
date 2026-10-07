import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from src.application.create_itinerary import (
    AirportNotFoundException,
    CreateItineraryUseCase,
    InvalidItineraryException,
)
from src.application.get_itinerary import (
    DeleteItineraryUseCase,
    GetItineraryUseCase,
    ListItinerariesUseCase,
)
from src.domain.models.itinerary import Itinerary, OutboxEvent


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.save_with_outbox.side_effect = lambda itin, outbox: itin
    return repo


@pytest.fixture
def mock_validator():
    validator = AsyncMock()
    validator.validate_airport_exists.return_value = True
    return validator


@pytest.mark.asyncio
async def test_create_itinerary_success(mock_repo, mock_validator):
    use_case = CreateItineraryUseCase(mock_repo, mock_validator)

    departure = datetime.now(UTC)
    itinerary = await use_case.execute(
        user_name="Carlos Gomez",
        origin_airport_id=1,
        destination_airport_id=5,
        departure_date=departure,
        duration_minutes=60,
        trace_id="test-trace-12345",
    )

    assert itinerary is not None
    assert itinerary.user_name == "Carlos Gomez"
    assert itinerary.origin_airport_id == 1
    assert itinerary.destination_airport_id == 5
    assert itinerary.status == "CREATED"

    # Verificar que el validador consultó ambos aeropuertos
    assert mock_validator.validate_airport_exists.call_count == 2

    # Verificar llamada atómica a save_with_outbox
    mock_repo.save_with_outbox.assert_called_once()
    args = mock_repo.save_with_outbox.call_args[0]
    passed_itin, passed_outbox = args[0], args[1]

    assert isinstance(passed_itin, Itinerary)
    assert isinstance(passed_outbox, OutboxEvent)
    assert passed_outbox.event_type == "ItineraryCreatedEvent"
    assert passed_outbox.status == "PENDING"
    assert passed_outbox.payload["data"]["user_name"] == "Carlos Gomez"


@pytest.mark.asyncio
async def test_create_itinerary_fails_same_airports(mock_repo, mock_validator):
    use_case = CreateItineraryUseCase(mock_repo, mock_validator)

    with pytest.raises(InvalidItineraryException):
        await use_case.execute(
            user_name="Ana Lopez",
            origin_airport_id=1,
            destination_airport_id=1,
            departure_date=datetime.now(UTC),
            duration_minutes=45,
        )

    mock_repo.save_with_outbox.assert_not_called()


@pytest.mark.asyncio
async def test_create_itinerary_fails_origin_not_found(mock_repo, mock_validator):
    mock_validator.validate_airport_exists.side_effect = lambda aid: aid != 999
    use_case = CreateItineraryUseCase(mock_repo, mock_validator)

    with pytest.raises(AirportNotFoundException) as excinfo:
        await use_case.execute(
            user_name="Pedro Pascal",
            origin_airport_id=999,
            destination_airport_id=5,
            departure_date=datetime.now(UTC),
            duration_minutes=50,
        )

    assert "999" in str(excinfo.value)
    mock_repo.save_with_outbox.assert_not_called()


@pytest.mark.asyncio
async def test_get_and_list_itineraries(mock_repo):
    test_id = uuid.uuid4()
    dummy_itin = Itinerary(
        id=test_id,
        user_name="Luis",
        origin_airport_id=1,
        destination_airport_id=9,
        departure_date=datetime.now(UTC),
        duration_minutes=40,
    )
    mock_repo.find_by_id.return_value = dummy_itin
    mock_repo.list_all.return_value = [dummy_itin]
    mock_repo.delete.return_value = True

    get_uc = GetItineraryUseCase(mock_repo)
    list_uc = ListItinerariesUseCase(mock_repo)
    del_uc = DeleteItineraryUseCase(mock_repo)

    found = await get_uc.execute(test_id)
    assert found.id == test_id

    all_items = await list_uc.execute()
    assert len(all_items) == 1

    deleted = await del_uc.execute(test_id)
    assert deleted is True
