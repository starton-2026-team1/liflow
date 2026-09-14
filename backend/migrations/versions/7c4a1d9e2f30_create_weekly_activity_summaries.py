"""create weekly activity summaries

Revision ID: 7c4a1d9e2f30
Revises: b4d2c9e7f1a3
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "7c4a1d9e2f30"
down_revision: str | Sequence[str] | None = "b4d2c9e7f1a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "weekly_activity_summaries",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("latest_event_at", sa.DateTime(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("person_id", "period_start", "period_end", name="uq_weekly_activity_summary_period"),
    )
    op.create_index("ix_weekly_activity_summaries_person_id", "weekly_activity_summaries", ["person_id"])


def downgrade() -> None:
    op.drop_table("weekly_activity_summaries")
