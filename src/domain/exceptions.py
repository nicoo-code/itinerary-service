"""
Excepciones del Dominio para Itinerary Service.
Representan violaciones a las reglas de negocio o inconsistencias del modelo de dominio.
"""


class ItineraryDomainException(Exception):
    """Excepción base del dominio de itinerarios."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AirportNotFoundException(ItineraryDomainException):
    """Lanzada cuando un aeropuerto referenciado no existe en el catálogo externo."""

    def __init__(self, airport_id_or_msg):
        if isinstance(airport_id_or_msg, int):
            message = f"El aeropuerto con ID {airport_id_or_msg} no existe en el catálogo canónico."
        else:
            message = str(airport_id_or_msg)
        super().__init__(message)


class InvalidItineraryException(ItineraryDomainException):
    """Lanzada cuando las reglas de negocio del itinerario son violadas (ej. origen == destino)."""

    def __init__(self, message: str):
        super().__init__(message)


class ItineraryNotFoundException(ItineraryDomainException):
    """Lanzada cuando no se encuentra un itinerario solicitado por ID."""

    def __init__(self, itinerary_id: str):
        super().__init__(f"Itinerario con ID {itinerary_id} no encontrado.")
        self.itinerary_id = itinerary_id
