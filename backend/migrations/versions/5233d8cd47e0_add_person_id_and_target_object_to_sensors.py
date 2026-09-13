"""add person_id and target_object to sensors

Revision ID: 5233d8cd47e0
Revises: 0001_create_sensors
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5233d8cd47e0"
down_revision: str | None = "0001_create_sensors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sensors", sa.Column("person_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "sensors", sa.Column("target_object", sa.String(length=100), nullable=True)
    )
    op.execute("UPDATE sensors SET person_id = 0 WHERE person_id IS NULL")
    op.execute("UPDATE sensors SET target_object = 'UNKNOWN' WHERE target_object IS NULL")
    op.alter_column(
        "sensors", "person_id", existing_type=sa.BigInteger(), nullable=False
    )
    op.alter_column(
        "sensors",
        "target_object",
        existing_type=sa.String(length=100),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("sensors", "target_object")
    op.drop_column("sensors", "person_id")
