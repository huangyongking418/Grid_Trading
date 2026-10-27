"""add unique index on stock.strategy_instance_id

Revision ID: 002_unique_stock_binding
Revises: 001_initial
Create Date: 2026-08-01
"""

from typing import Sequence, Union

from alembic import op

revision: str = '002_unique_stock_binding'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_stock_strategy_instance_id',
        'stock',
        ['strategy_instance_id'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index('ix_stock_strategy_instance_id', table_name='stock')
