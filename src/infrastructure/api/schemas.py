import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateItineraryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_name": "Juan Pérez",
                "origin_airport_id": 1,
                "destination_airport_id": 5,
                "departure_date": "2026-10-15T08:00:00Z",
                "duration_minutes": 55,
            }
        }
    )

    user_name: str = Field(
        ..., min_length=2, max_length=100, description="Nombre del pasajero"
    )
    origin_airport_id: int = Field(..., description="ID del aeropuerto de salida")
    destination_airport_id: int = Field(..., description="ID del aeropuerto de llegada")
    departure_date: datetime = Field(
        ..., description="Fecha y hora de salida programada"
    )
    duration_minutes: int = Field(
        ..., gt=0, le=1440, description="Duración estimada del vuelo en minutos"
    )


class ItineraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_name: str
    origin_airport_id: int
    destination_airport_id: int
    departure_date: datetime
    duration_minutes: int
    status: str
    created_at: datetime
    updated_at: datetime


class HealthCheckResponse(BaseModel):
    status: str
    service: str
    database_connected: bool
    outbox_worker_active: bool
