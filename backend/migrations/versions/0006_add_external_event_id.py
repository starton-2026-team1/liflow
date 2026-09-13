"""add external event id

Revision ID: 0006_add_external_event_id
Revises: 0005_add_user_id_to_people
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_add_external_event_id"
down_revision: str | None = "0005_add_user_id_to_people"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sensor_events",
        sa.Column("external_event_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        "ix_sensor_events_external_event_id",
        "sensor_events",
        ["external_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_sensor_events_external_event_id", table_name="sensor_events")
    op.drop_column("sensor_events", "external_event_id")
