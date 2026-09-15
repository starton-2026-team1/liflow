"""create FCM device tokens

Revision ID: f9c37a20d1e4
Revises: 7c4a1d9e2f30
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "f9c37a20d1e4"
down_revision: str | Sequence[str] | None = "7c4a1d9e2f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fcm_device_tokens",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fcm_device_tokens_user_id", "fcm_device_tokens", ["user_id"])
    op.create_index("ix_fcm_device_tokens_token", "fcm_device_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_fcm_device_tokens_token", table_name="fcm_device_tokens")
    op.drop_index("ix_fcm_device_tokens_user_id", table_name="fcm_device_tokens")
    op.drop_table("fcm_device_tokens")
