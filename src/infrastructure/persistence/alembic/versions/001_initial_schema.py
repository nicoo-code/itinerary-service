"""001_initial_schema

Revision ID: 001_initial
Revises:
Create Date: 2026-09-20 22:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Crear tabla itineraries
    op.create_table(
        "itineraries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_name", sa.String(length=100), nullable=False),
        sa.Column("origin_airport_id", sa.Integer(), nullable=False),
        sa.Column("destination_airport_id", sa.Integer(), nullable=False),
        sa.Column("departure_date", sa.DateTime(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="CREATED"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )

    # 2. Crear tabla outbox_events
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "aggregate_type",
            sa.String(length=50),
            nullable=False,
            server_default="ITINERARY",
        ),
        sa.Column("aggregate_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="PENDING"
        ),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("outbox_events")
    op.drop_table("itineraries")
