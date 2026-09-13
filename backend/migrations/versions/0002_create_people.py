"""create people table

Revision ID: 0002_create_people
Revises: 5233d8cd47e0
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_create_people"
down_revision: str | None = "5233d8cd47e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "people",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("age_group", sa.String(length=30), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("living_space", sa.String(length=100), nullable=False),
        sa.Column("health_notes", sa.Text(), nullable=True),
        sa.Column("monitoring_status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("people")
