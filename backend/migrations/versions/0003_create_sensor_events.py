"""create sensor events table

Revision ID: 0003_create_sensor_events
Revises: 0002_create_people
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_create_sensor_events"
down_revision: str | None = "0002_create_people"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sensor_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("sensor_id", sa.BigInteger(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("detected_value", sa.String(length=255), nullable=False),
        sa.Column("sensor_status", sa.String(length=30), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sensor_events_person_id", "sensor_events", ["person_id"])
    op.create_index("ix_sensor_events_sensor_id", "sensor_events", ["sensor_id"])
    op.create_index("ix_sensor_events_detected_at", "sensor_events", ["detected_at"])


def downgrade() -> None:
    op.drop_index("ix_sensor_events_detected_at", table_name="sensor_events")
    op.drop_index("ix_sensor_events_sensor_id", table_name="sensor_events")
    op.drop_index("ix_sensor_events_person_id", table_name="sensor_events")
    op.drop_table("sensor_events")
