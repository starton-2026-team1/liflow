"""add user ownership to people

Revision ID: 0005_add_user_id_to_people
Revises: 0004_create_users
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_add_user_id_to_people"
down_revision: str | None = "0004_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 기존 MVP 데이터는 소유자를 확인할 수 없으므로 미귀속 상태로 보존한다.
    # 애플리케이션에서 새로 생성되는 대상자는 항상 user_id를 저장한다.
    op.add_column("people", sa.Column("user_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_people_user_id", "people", ["user_id"])
    op.create_foreign_key(
        "fk_people_user_id_users",
        "people",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_sensors_person_id", "sensors", ["person_id"])
    op.create_foreign_key(
        "fk_sensors_person_id_people",
        "sensors",
        "people",
        ["person_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_sensors_person_id_people", "sensors", type_="foreignkey")
    op.drop_index("ix_sensors_person_id", table_name="sensors")
    op.drop_constraint("fk_people_user_id_users", "people", type_="foreignkey")
    op.drop_index("ix_people_user_id", table_name="people")
    op.drop_column("people", "user_id")
