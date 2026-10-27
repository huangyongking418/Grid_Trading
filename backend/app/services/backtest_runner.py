"""模拟回测异步执行：后台线程独立会话运行，不影响正式监控调度。"""

import threading
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.backtest_models import (
    BacktestGridLayer,
    BacktestMetric,
    BacktestSession,
    BacktestStrategy,
    BacktestTrade,
)
from app.services.backtest_data import get_kline_with_meta
from app.services.backtest_engine import run_backtest, strategy_to_snapshot


def start_backtest(session_id: int) -> None:
    """创建后台线程执行回测，立即返回。"""
    thread = threading.Thread(target=_run_worker, args=(session_id,), daemon=True)
    thread.start()


def _run_worker(session_id: int) -> None:
    db: Session = SessionLocal()
    try:
        session = (
            db.query(BacktestSession)
            .filter(BacktestSession.id == session_id)
            .first()
        )
        if not session:
            return
        strategy = (
            db.query(BacktestStrategy)
            .filter(BacktestStrategy.id == session.strategy_id)
            .first()
        )
        if not strategy:
            raise ValueError("模拟策略不存在")

        session.status = "running"
        session.run_start_time = datetime.now()
        session.error_message = None
        db.commit()

        strategy_snapshot = session.strategy_snapshot or strategy_to_snapshot(strategy)
        strategy_snapshot["stock_type"] = session.stock_type
        klines, data_meta = get_kline_with_meta(
            db,
            stock_code=session.stock_code,
            stock_type=session.stock_type,
            start_date=session.start_date,
            end_date=session.end_date,
            period=session.period,
            adjust=session.adjust,
        )
        result = run_backtest(strategy_snapshot, klines, session.fee_config)
        session.data_source = data_meta["source"]
        session.data_note = data_meta["note"]
        session.adjust = data_meta["adjust"]

        db.query(BacktestGridLayer).filter(BacktestGridLayer.session_id == session.id).delete()
        db.query(BacktestTrade).filter(BacktestTrade.session_id == session.id).delete()
        db.query(BacktestMetric).filter(BacktestMetric.session_id == session.id).delete()

        for layer in result["layers"]:
            db.add(
                BacktestGridLayer(
                    session_id=session.id,
                    layer_index=layer["layer_index"],
                    layer_type=layer["layer_type"],
                    direction=layer["direction"],
                    trigger_price=layer["trigger_price"],
                    quantity=layer["quantity"],
                    amount=layer["amount"],
                    status=layer["status"],
                )
            )

        for trade in result["trades"]:
            db.add(
                BacktestTrade(
                    user_id=session.user_id,
                    session_id=session.id,
                    layer_index=trade["layer_index"],
                    direction=trade["direction"],
                    trade_time=trade["trade_time"],
                    trigger_price=trade["trigger_price"],
                    quantity=trade["quantity"],
                    amount=trade["amount"],
                    fee=trade["fee"],
                    cash_after=trade["cash_after"],
                    note=trade["note"],
                )
            )

        metrics = result["metrics"]
        db.add(
            BacktestMetric(
                session_id=session.id,
                total_return_rate=metrics["total_return_rate"],
                annual_return_rate=metrics["annual_return_rate"],
                max_drawdown=metrics["max_drawdown"],
                sharpe_ratio=metrics["sharpe_ratio"],
                win_rate=metrics["win_rate"],
                profit_loss_ratio=metrics["profit_loss_ratio"],
                total_trade_count=metrics["total_trade_count"],
                buy_count=metrics["buy_count"],
                sell_count=metrics["sell_count"],
                total_fee=metrics["total_fee"],
                final_asset=metrics["final_asset"],
                benchmark_return_rate=metrics["benchmark_return_rate"],
                excess_return=metrics["excess_return"],
                equity_curve=result["equity_points"],
                drawdown_curve=result["drawdown_points"],
            )
        )

        session.kline_count = len(klines)
        session.trade_count = metrics["total_trade_count"]
        session.status = "success"
        session.run_end_time = datetime.now()
        db.commit()
    except Exception as exc:  # noqa: BLE001 - 失败原因写入会话
        db.rollback()
        session = (
            db.query(BacktestSession)
            .filter(BacktestSession.id == session_id)
            .first()
        )
        if session:
            session.status = "failed"
            session.error_message = str(exc)[:500]
            session.run_end_time = datetime.now()
            db.commit()
    finally:
        db.close()
