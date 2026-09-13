"""create person status events

Revision ID: 21e99e55ce0e
Revises: d28e31f6b4c2
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "21e99e55ce0e"
down_revision: str | Sequence[str] | None = "d28e31f6b4c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "person_status_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("external_event_id", sa.String(length=100), nullable=True),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("sensor_id", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("judged_at", sa.DateTime(), nullable=False),
        sa.Column("detected_value", sa.String(length=255), nullable=True),
        sa.Column(
            "received_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False
        ),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_person_status_events_external_event_id",
        "person_status_events",
        ["external_event_id"],
        unique=True,
    )
    op.create_index("ix_person_status_events_judged_at", "person_status_events", ["judged_at"])
    op.create_index("ix_person_status_events_person_id", "person_status_events", ["person_id"])
    op.create_index("ix_person_status_events_sensor_id", "person_status_events", ["sensor_id"])


def downgrade() -> None:
    op.drop_table("person_status_events")
