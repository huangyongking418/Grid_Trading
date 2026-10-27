"""补齐业务表缺失的 user_id 索引

Revision ID: 010_user_id_indexes
Revises: 009_system_document
Create Date: 2026-08-05
"""

from typing import Sequence, Union

from alembic import op


revision: str = "010_user_id_indexes"
down_revision: Union[str, None] = "009_system_document"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_stock_user_id", "stock", ["user_id"])
    op.create_index("ix_operation_log_user_id", "operation_log", ["user_id"])
    op.create_index("ix_push_config_user_id", "push_config", ["user_id"])
    op.create_index("ix_in_app_message_user_id", "in_app_message", ["user_id"])
    op.create_index(
        "ix_strategy_instance_user_id_create_time",
        "strategy_instance",
        ["user_id", "create_time"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_strategy_instance_user_id_create_time",
        table_name="strategy_instance",
    )
    op.drop_index("ix_in_app_message_user_id", table_name="in_app_message")
    op.drop_index("ix_push_config_user_id", table_name="push_config")
    op.drop_index("ix_operation_log_user_id", table_name="operation_log")
    op.drop_index("ix_stock_user_id", table_name="stock")
