# Itinerary Service - Microservicio de Gestión de Itinerarios Personales

[![CI Pipeline](https://github.com/nicoo-code/itinerary-service/actions/workflows/ci.yml/badge.svg)](https://github.com/nicoo-code/itinerary-service/actions)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-red.svg)](https://alembic.sqlalchemy.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-AMQP%200--9--1-orange.svg)](https://www.rabbitmq.com/)
[![Pattern](https://img.shields.io/badge/Pattern-Transactional%20Outbox-brightgreen.svg)]()

Microservicio desacoplado responsable del ciclo de vida de los itinerarios de viaje (CRUD), aplicando **Arquitectura Hexagonal**, **Arquitectura Basada en Eventos (EDA)** y el patrón **Transactional Outbox** para garantizar consistencia distribuida entre la base de datos relacional y el broker **RabbitMQ**.

---

## 1. Arquitectura Hexagonal y Estructura

El microservicio aísla estrictamente el modelo de dominio y las reglas de negocio de los detalles de infraestructura:

```
src/
├── domain/                         # Capa de Dominio (Pura e independiente)
│   ├── models/                     # Entidades (Itinerary, OutboxEvent)
│   ├── events/                     # Eventos de integración (ItineraryCreatedEvent)
│   ├── ports/                      # Contratos de interfaces abstractas
│   │   ├── itinerary_repository_port.py
│   │   ├── outbox_repository_port.py
│   │   └── airport_validator_port.py
│   └── exceptions.py               # Excepciones de negocio
├── application/                    # Capa de Aplicación (Casos de uso)
│   ├── create_itinerary.py         # Orquesta validación síncrona y outbox atómico
│   └── get_itinerary.py            # Consulta, listado y eliminación
└── infrastructure/                 # Capa de Infraestructura (Implementaciones)
    ├── persistence/                # Base de datos relacional
    │   ├── models.py               # Mapeo SQLAlchemy (itineraries, outbox_events)
    │   ├── sqlalchemy_itinerary_repo.py
    │   └── alembic/                # Migraciones versionadas (env.py, versions/)
    ├── clients/
    │   └── airport_http_validator.py # Cliente HTTP resiliente hacia Airport Service
    ├── messaging/                  # Integración con el Broker RabbitMQ
    │   ├── rabbitmq_publisher.py   # Publicador AMQP con Publisher Confirms
    │   └── outbox_relay_worker.py  # Worker de sondeo y relé transaccional
    ├── api/                        # Controladores FastAPI y Esquemas Pydantic
    │   ├── router.py
    │   └── schemas.py
    ├── config.py                   # Configuración y variables de entorno
    └── main.py                     # Ciclo de vida (lifespan) de la app
```

---

## 2. Patrón Transactional Outbox y Double Write Problem

### El Problema de Doble Escritura (Double Write Problem)
En arquitecturas distribuidas, una operación de negocio típica requiere guardar un registro en la base de datos relacional y emitir un mensaje a un broker. Si se ejecutan como dos operaciones separadas:
1. Si falla la base de datos tras publicar el mensaje, el broker emite un evento de datos inexistentes.
2. Si la base de datos guarda exitosamente pero el broker o la red fallan antes de publicar, el evento se pierde irremediablemente.

### La Solución Implementada: Transactional Outbox
1. **Transacción Atómica ACID:** `CreateItineraryUseCase` persiste en una **única transacción** la entidad `Itinerary` en la tabla `itineraries` y el evento `ItineraryCreatedEvent` en la tabla `outbox_events` con estado `PENDING`.
2. **Worker Asíncrono de Relé:** `OutboxRelayWorker` se ejecuta en segundo plano sondeando eventos `PENDING` en lotes.
3. **Publicación Confiable:** Despacha el mensaje hacia RabbitMQ esperando la confirmación (`Publisher Confirms`).
4. **Actualización de Estado:** Al confirmar la entrega, actualiza el registro en `outbox_events` a `PUBLISHED` con su marca de tiempo. Si falla, incrementa `retry_count` para reintentar sin pérdida de información (entrega *at-least-once*).

---

## 3. Contrato de Mensajería AsyncAPI 2.6.0

La especificación formal del evento `ItineraryCreatedEvent` se encuentra en [`docs/asyncapi.yaml`](docs/asyncapi.yaml):
- **Exchange:** `itinerary.events` (Topic)
- **Routing Key:** `itinerary.created`
- **Garantía:** Idempotencia asegurada mediante el identificador `event_id` (UUIDv4).

---

## 4. Migraciones de Base de Datos con Alembic

Las migraciones del esquema relacional están completamente versionadas:

```bash
# Aplicar migraciones hasta la última versión
alembic upgrade head

# Crear una nueva migración tras cambios en modelos
alembic revision --autogenerate -m "descripcion_del_cambio"

# Revertir última migración
alembic downgrade -1
```

---

## 5. Endpoints REST (Swagger / OpenAPI)

Swagger UI interactivo disponible en `/docs` y ReDoc en `/redoc`:

| Método | Endpoint | Código | Descripción |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/itineraries` | `201 Created` | Valida aeropuertos vía HTTP y crea itinerario con outbox atómico. |
| `GET` | `/api/v1/itineraries` | `200 OK` | Lista todos los itinerarios persistidos. |
| `GET` | `/api/v1/itineraries/{id}` | `200 OK` | Consulta detalle de un itinerario por UUID. |
| `DELETE`| `/api/v1/itineraries/{id}` | `204 No Content` | Elimina un itinerario por UUID. |
| `GET` | `/health` | `200 OK` | Estado de conexión a base de datos y worker outbox. |

---

## 6. Ejecución Local y Docker

### Con Python local:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8002 --reload
```

### Con Docker Compose autónomo:
```bash
docker compose up --build
```

---

## 7. Pruebas Automatizadas

```bash
pytest tests/ -v --cov=src --cov-report=term --cov-report=xml:coverage.xml
```

---

## 8. Variables de Entorno

| Variable | Valor por Defecto | Descripción |
| :--- | :--- | :--- |
| `PORT` | `8002` | Puerto HTTP del servicio |
| `DATABASE_URL` | `postgresql://itinerary_user:itinerary_pass@postgres-itinerary:5432/itinerary_db` | URL de conexión SQL |
| `AIRPORT_SERVICE_URL` | `http://airport-service:8001` | URL para validación síncrona HTTP de aeropuertos |
| `RABBITMQ_URL` | `amqp://guest:guest@rabbitmq:5672/` | Conexión AMQP al broker RabbitMQ |
| `LOG_LEVEL` | `INFO` | Nivel de logging estructurado JSON |
