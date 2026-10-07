from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from src.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["service"] == "itinerary-service"
        assert "database_connected" in data


@pytest.mark.asyncio
async def test_create_and_get_itinerary_flow(monkeypatch):
    # Simular que el cliente HTTP de validación de aeropuertos responde True
    from src.main import airport_validator

    monkeypatch.setattr(
        airport_validator, "validate_airport_exists", AsyncMock(return_value=True)
    )

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # 1. Crear itinerario
        payload = {
            "user_name": "Valeria Morales",
            "origin_airport_id": 1,
            "destination_airport_id": 12,
            "departure_date": datetime.now(UTC).isoformat(),
            "duration_minutes": 75,
        }
        res_create = await client.post("/api/v1/itineraries", json=payload)
        assert res_create.status_code == 201
        created = res_create.json()
        itinerary_id = created["id"]
        assert created["user_name"] == "Valeria Morales"
        assert created["status"] == "CREATED"

        # 2. Consultar por ID
        res_get = await client.get(f"/api/v1/itineraries/{itinerary_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == itinerary_id

        # 3. Listar todos
        res_list = await client.get("/api/v1/itineraries")
        assert res_list.status_code == 200
        assert any(item["id"] == itinerary_id for item in res_list.json())

        # 4. Eliminar
        res_del = await client.delete(f"/api/v1/itineraries/{itinerary_id}")
        assert res_del.status_code == 204

        # 5. Verificar 404 tras eliminación
        res_not_found = await client.get(f"/api/v1/itineraries/{itinerary_id}")
        assert res_not_found.status_code == 404


@pytest.mark.asyncio
async def test_create_itinerary_same_airports_returns_422():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        payload = {
            "user_name": "Error User",
            "origin_airport_id": 1,
            "destination_airport_id": 1,
            "departure_date": datetime.now(UTC).isoformat(),
            "duration_minutes": 30,
        }
        res = await client.post("/api/v1/itineraries", json=payload)
        assert res.status_code == 422
        assert "no pueden ser el mismo" in res.json()["detail"]
