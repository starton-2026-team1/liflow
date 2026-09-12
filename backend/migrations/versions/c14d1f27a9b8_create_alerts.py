"""create alerts and inactivity settings

Revision ID: c14d1f27a9b8
Revises: 179f9f3bf4dd
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c14d1f27a9b8"
down_revision: str | Sequence[str] | None = "179f9f3bf4dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "people",
        sa.Column("inactivity_threshold_minutes", sa.Integer(), nullable=False, server_default="30"),
    )
    op.create_table(
        "alerts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("sensor_id", sa.BigInteger(), nullable=True),
        sa.Column("cause", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=30), nullable=False),
        sa.Column("dedup_key", sa.String(length=160), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("safety_confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_person_id", "alerts", ["person_id"])
    op.create_index("ix_alerts_sensor_id", "alerts", ["sensor_id"])
    op.create_index("ix_alerts_cause", "alerts", ["cause"])
    op.create_index("ix_alerts_occurred_at", "alerts", ["occurred_at"])
    op.create_index("ix_alerts_dedup_key", "alerts", ["dedup_key"], unique=True)


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_column("people", "inactivity_threshold_minutes")
