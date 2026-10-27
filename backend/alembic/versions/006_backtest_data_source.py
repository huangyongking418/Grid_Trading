"""add data_source and data_note to backtest_session

Revision ID: 006_backtest_data_source
Revises: 005_backtest_tables
Create Date: 2026-08-04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006_backtest_data_source"
down_revision: Union[str, None] = "005_backtest_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "backtest_session",
        sa.Column("data_source", sa.String(32), nullable=True, comment="实际行情来源"),
    )
    op.add_column(
        "backtest_session",
        sa.Column("data_note", sa.String(500), nullable=True, comment="数据源降级与复权口径说明"),
    )


def downgrade() -> None:
    op.drop_column("backtest_session", "data_note")
    op.drop_column("backtest_session", "data_source")
