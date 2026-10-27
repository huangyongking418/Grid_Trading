"""initial: create all 9 tables

Revision ID: 001_initial
Revises:
Create Date: 2026-07-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. strategy_template
    op.create_table(
        'strategy_template',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(64), nullable=False, comment='??????'),
        sa.Column('description', sa.String(255), nullable=True, comment='????'),
        sa.Column('direction_type', sa.String(32), nullable=False, comment='??????'),
        sa.Column('default_params', sa.JSON(), nullable=True, comment='??????'),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 2. stock
    op.create_table(
        'stock',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(16), nullable=False, comment='????'),
        sa.Column('name', sa.String(64), nullable=False, comment='????'),
        sa.Column('type', sa.String(16), nullable=False, comment='????: stock/etf/fund'),
        sa.Column('exchange', sa.String(8), nullable=True, comment='???: SH/SZ'),
        sa.Column('current_price', sa.Float(), nullable=True, comment='????'),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )
    op.create_index('ix_stock_code', 'stock', ['code'])

    # 3. strategy_instance
    op.create_table(
        'strategy_instance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(64), nullable=True, comment='???????'),
        sa.Column('stock_id', sa.Integer(), nullable=True),
        sa.Column('grid_spacing', sa.Float(), nullable=False),
        sa.Column('grid_layers', sa.Integer(), nullable=False),
        sa.Column('asymmetry_ratio', sa.Float(), nullable=False),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('stop_loss_strategy', sa.String(32), nullable=True),
        sa.Column('fund_allocation', sa.String(32), nullable=False),
        sa.Column('total_funds', sa.Float(), nullable=False),
        sa.Column('reset_cycle_days', sa.Integer(), nullable=False),
        sa.Column('last_reset_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['template_id'], ['strategy_template.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stock.id'], ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 4. push_config
    op.create_table(
        'push_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('channel', sa.String(32), nullable=False),
        sa.Column('webhook_url', sa.String(512), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.Column('update_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('channel'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 5. trade_session
    op.create_table(
        'trade_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('market', sa.String(16), nullable=False),
        sa.Column('open_time', sa.String(8), nullable=False),
        sa.Column('close_time', sa.String(8), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 6. grid_layer
    op.create_table(
        'grid_layer',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('layer_index', sa.Integer(), nullable=False),
        sa.Column('direction', sa.String(8), nullable=False),
        sa.Column('trigger_price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instance.id'], ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 7. price_snapshot
    op.create_table(
        'price_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('source', sa.String(32), nullable=True),
        sa.Column('snapshot_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['stock_id'], ['stock.id'], ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 8. operation_log
    op.create_table(
        'operation_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=True),
        sa.Column('stock_id', sa.Integer(), nullable=True),
        sa.Column('layer_id', sa.Integer(), nullable=True),
        sa.Column('trigger_price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=True),
        sa.Column('direction', sa.String(8), nullable=False),
        sa.Column('log_type', sa.String(16), nullable=False),
        sa.Column('fee', sa.Float(), nullable=True),
        sa.Column('note', sa.String(255), nullable=True),
        sa.Column('operate_time', sa.DateTime(), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instance.id'], ),
        sa.ForeignKeyConstraint(['stock_id'], ['stock.id'], ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )

    # 9. reset_log
    op.create_table(
        'reset_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('old_base_price', sa.Float(), nullable=False),
        sa.Column('new_base_price', sa.Float(), nullable=False),
        sa.Column('reset_reason', sa.String(128), nullable=True),
        sa.Column('create_time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['instance_id'], ['strategy_instance.id'], ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
    )


def downgrade() -> None:
    op.drop_table('reset_log')
    op.drop_table('operation_log')
    op.drop_table('price_snapshot')
    op.drop_table('grid_layer')
    op.drop_table('trade_session')
    op.drop_table('push_config')
    op.drop_table('strategy_instance')
    op.drop_table('stock')
    op.drop_index('ix_stock_code', 'stock')
    op.drop_table('strategy_template')
