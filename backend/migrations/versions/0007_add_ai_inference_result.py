"""add ai inference result columns to sensor_events

Revision ID: 0007_add_ai_inference_result
Revises: 21e99e55ce0e
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_add_ai_inference_result"
down_revision: str | None = "21e99e55ce0e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sensor_events",
        sa.Column("ai_label", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "sensor_events",
        sa.Column("ai_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "sensor_events",
        sa.Column("ai_is_anomaly", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sensor_events", "ai_is_anomaly")
    op.drop_column("sensor_events", "ai_score")
    op.drop_column("sensor_events", "ai_label")
