"""merge AI inference and push subscription heads

Revision ID: b4d2c9e7f1a3
Revises: 0007_add_ai_inference_result, a71f2c80e6b9
"""
from collections.abc import Sequence

revision: str = "b4d2c9e7f1a3"
down_revision: str | Sequence[str] | None = (
    "0007_add_ai_inference_result",
    "a71f2c80e6b9",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
