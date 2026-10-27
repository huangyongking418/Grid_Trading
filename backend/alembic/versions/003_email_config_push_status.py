"""add email_config and operation_log push_status

Revision ID: 003_email_config_push_status
Revises: 002_unique_stock_binding
Create Date: 2026-08-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_email_config_push_status"
down_revision: Union[str, None] = "002_unique_stock_binding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "email_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("smtp_host", sa.String(128), nullable=False),
        sa.Column("smtp_port", sa.Integer(), nullable=False),
        sa.Column("smtp_user", sa.String(128), nullable=False),
        sa.Column("smtp_password", sa.String(255), nullable=False),
        sa.Column("from_email", sa.String(128), nullable=False),
        sa.Column("to_email", sa.String(255), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_email_config_user_id", "email_config", ["user_id"])
    op.add_column("operation_log", sa.Column("push_status", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("operation_log", "push_status")
    op.drop_index("ix_email_config_user_id", table_name="email_config")
    op.drop_table("email_config")
