"""add independent backtest tables

Revision ID: 005_backtest_tables
Revises: 004_email_smtp_split
Create Date: 2026-08-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_backtest_tables"
down_revision: Union[str, None] = "004_email_smtp_split"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "backtest_strategy",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(64), nullable=True),
        sa.Column("template_id", sa.Integer(), nullable=True),
        sa.Column("stock_code", sa.String(16), nullable=False),
        sa.Column("stock_name", sa.String(64), nullable=False),
        sa.Column("stock_type", sa.String(16), nullable=False),
        sa.Column("grid_spacing", sa.Float(), nullable=False),
        sa.Column("grid_layers", sa.Integer(), nullable=False),
        sa.Column("asymmetry_ratio", sa.Float(), nullable=False),
        sa.Column("base_price", sa.Float(), nullable=False),
        sa.Column("stop_loss_strategy", sa.String(32), nullable=True),
        sa.Column("fund_allocation", sa.String(32), nullable=False),
        sa.Column("total_funds", sa.Float(), nullable=False),
        sa.Column("grid_funds", sa.Float(), nullable=False),
        sa.Column("position_funds", sa.Float(), nullable=False),
        sa.Column("split_mode", sa.String(16), nullable=False),
        sa.Column("layer_shares", sa.JSON(), nullable=True),
        sa.Column("reset_cycle_days", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.Column("update_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_strategy_user_id", "backtest_strategy", ["user_id"])

    op.create_table(
        "backtest_session",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("strategy_id", sa.Integer(), nullable=False),
        sa.Column("strategy_snapshot", sa.JSON(), nullable=True),
        sa.Column("stock_code", sa.String(16), nullable=False),
        sa.Column("stock_name", sa.String(64), nullable=False),
        sa.Column("stock_type", sa.String(16), nullable=False),
        sa.Column("period", sa.String(8), nullable=False),
        sa.Column("adjust", sa.String(8), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("initial_cash", sa.Float(), nullable=True),
        sa.Column("fee_config", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("kline_count", sa.Integer(), nullable=False),
        sa.Column("trade_count", sa.Integer(), nullable=False),
        sa.Column("run_start_time", sa.DateTime(), nullable=True),
        sa.Column("run_end_time", sa.DateTime(), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["strategy_id"], ["backtest_strategy.id"]),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_session_user_id", "backtest_session", ["user_id"])
    op.create_index("ix_backtest_session_strategy_id", "backtest_session", ["strategy_id"])

    op.create_table(
        "backtest_kline",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("stock_code", sa.String(16), nullable=False),
        sa.Column("stock_type", sa.String(16), nullable=False),
        sa.Column("period", sa.String(8), nullable=False),
        sa.Column("adjust", sa.String(8), nullable=False),
        sa.Column("trade_time", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("source", sa.String(32), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "stock_code", "period", "adjust", "trade_time",
            name="uq_backtest_kline_symbol_period_adjust_time",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_kline_stock_code", "backtest_kline", ["stock_code"])
    op.create_index("ix_backtest_kline_trade_time", "backtest_kline", ["trade_time"])

    op.create_table(
        "backtest_grid_layer",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("layer_index", sa.Integer(), nullable=False),
        sa.Column("layer_type", sa.String(16), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("trigger_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["backtest_session.id"]),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_grid_layer_session_id", "backtest_grid_layer", ["session_id"])

    op.create_table(
        "backtest_trade",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("layer_index", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(8), nullable=False),
        sa.Column("trade_time", sa.DateTime(), nullable=False),
        sa.Column("trigger_price", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False),
        sa.Column("cash_after", sa.Float(), nullable=True),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["backtest_session.id"]),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_trade_user_id", "backtest_trade", ["user_id"])
    op.create_index("ix_backtest_trade_session_id", "backtest_trade", ["session_id"])

    op.create_table(
        "backtest_metric",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("total_return_rate", sa.Float(), nullable=True),
        sa.Column("annual_return_rate", sa.Float(), nullable=True),
        sa.Column("max_drawdown", sa.Float(), nullable=True),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("win_rate", sa.Float(), nullable=True),
        sa.Column("profit_loss_ratio", sa.Float(), nullable=True),
        sa.Column("total_trade_count", sa.Integer(), nullable=False),
        sa.Column("buy_count", sa.Integer(), nullable=False),
        sa.Column("sell_count", sa.Integer(), nullable=False),
        sa.Column("total_fee", sa.Float(), nullable=False),
        sa.Column("final_asset", sa.Float(), nullable=True),
        sa.Column("benchmark_return_rate", sa.Float(), nullable=True),
        sa.Column("excess_return", sa.Float(), nullable=True),
        sa.Column("equity_curve", sa.JSON(), nullable=True),
        sa.Column("drawdown_curve", sa.JSON(), nullable=True),
        sa.Column("create_time", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["session_id"], ["backtest_session.id"]),
        sa.UniqueConstraint("session_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
    )
    op.create_index("ix_backtest_metric_session_id", "backtest_metric", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_backtest_metric_session_id", "backtest_metric")
    op.drop_table("backtest_metric")
    op.drop_index("ix_backtest_trade_session_id", "backtest_trade")
    op.drop_index("ix_backtest_trade_user_id", "backtest_trade")
    op.drop_table("backtest_trade")
    op.drop_index("ix_backtest_grid_layer_session_id", "backtest_grid_layer")
    op.drop_table("backtest_grid_layer")
    op.drop_index("ix_backtest_kline_trade_time", "backtest_kline")
    op.drop_index("ix_backtest_kline_stock_code", "backtest_kline")
    op.drop_table("backtest_kline")
    op.drop_index("ix_backtest_session_strategy_id", "backtest_session")
    op.drop_index("ix_backtest_session_user_id", "backtest_session")
    op.drop_table("backtest_session")
    op.drop_index("ix_backtest_strategy_user_id", "backtest_strategy")
    op.drop_table("backtest_strategy")
