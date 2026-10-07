from abc import ABC, abstractmethod


class AirportValidatorPort(ABC):
    """Puerto para validar la existencia de aeropuertos contra el servicio canónico."""

    @abstractmethod
    async def validate_airport_exists(self, airport_id: int) -> bool:
        """Verifica síncronamente si el aeropuerto con el ID indicado existe y está activo."""
