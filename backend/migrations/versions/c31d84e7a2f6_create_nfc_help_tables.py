"""create NFC help tables"""

import sqlalchemy as sa
from alembic import op

revision = "c31d84e7a2f6"
down_revision = "f9c37a20d1e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nfc_tags",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("person_id", sa.BigInteger(), nullable=False),
        sa.Column("public_token_hash", sa.String(64), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("guardian_name", sa.String(100), nullable=False),
        sa.Column("guardian_phone", sa.String(30), nullable=False),
        sa.Column("contact_reveal_enabled", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nfc_tags_person_id", "nfc_tags", ["person_id"])
    op.create_index("ix_nfc_tags_public_token_hash", "nfc_tags", ["public_token_hash"], unique=True)
    op.create_table(
        "nfc_help_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("nfc_tag_id", sa.BigInteger(), nullable=False),
        sa.Column("alert_id", sa.BigInteger(), nullable=False),
        sa.Column("finder_token_hash", sa.String(64), nullable=False),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("contact_revealed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["nfc_tag_id"], ["nfc_tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_nfc_help_events_nfc_tag_id", "nfc_help_events", ["nfc_tag_id"])
    op.create_index("ix_nfc_help_events_alert_id", "nfc_help_events", ["alert_id"])


def downgrade() -> None:
    op.drop_table("nfc_help_events")
    op.drop_table("nfc_tags")
