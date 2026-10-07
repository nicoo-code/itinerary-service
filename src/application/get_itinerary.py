import uuid

from src.domain.models.itinerary import Itinerary
from src.domain.ports.itinerary_repository_port import ItineraryRepositoryPort


class GetItineraryUseCase:
    """Caso de uso para consultar un itinerario por su identificador único."""

    def __init__(self, itinerary_repo: ItineraryRepositoryPort):
        self._itinerary_repo = itinerary_repo

    async def execute(self, itinerary_id: uuid.UUID) -> Itinerary | None:
        return await self._itinerary_repo.find_by_id(itinerary_id)


class ListItinerariesUseCase:
    """Caso de uso para listar todos los itinerarios almacenados."""

    def __init__(self, itinerary_repo: ItineraryRepositoryPort):
        self._itinerary_repo = itinerary_repo

    async def execute(self) -> list[Itinerary]:
        return await self._itinerary_repo.list_all()


class DeleteItineraryUseCase:
    """Caso de uso para eliminar un itinerario por su ID."""

    def __init__(self, itinerary_repo: ItineraryRepositoryPort):
        self._itinerary_repo = itinerary_repo

    async def execute(self, itinerary_id: uuid.UUID) -> bool:
        return await self._itinerary_repo.delete(itinerary_id)
