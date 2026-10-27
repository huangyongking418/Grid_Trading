from datetime import datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import can_view_all, get_current_user, has_permission
from app.core.database import get_db
from app.models.all_models import User
from app.models.backtest_models import (
    BacktestGridLayer,
    BacktestKline,
    BacktestMetric,
    BacktestSession,
    BacktestStrategy,
    BacktestTrade,
)
from app.schemas.backtest import (
    BacktestGridLayerOut,
    BacktestKlineOut,
    BacktestMetricDetailOut,
    BacktestSessionCreate,
    BacktestSessionOut,
    BacktestStrategyCreate,
    BacktestStrategyOut,
    BacktestStrategyUpdate,
    BacktestTradeOut,
)
from app.services.backtest_data import clear_kline_cache
from app.services.backtest_engine import (
    DEFAULT_FEE_CONFIG,
    build_grid_layers,
    strategy_to_snapshot,
)
from app.services.backtest_runner import start_backtest

router = APIRouter(prefix="/api/backtest", tags=["模拟回测"])


def _require_backtest(current: User) -> None:
    if not has_permission(current, "backtest_manage"):
        raise HTTPException(status_code=403, detail="无权限访问模拟回测")


def _get_owned_strategy(db: Session, strategy_id: int, current: User) -> BacktestStrategy:
    q = db.query(BacktestStrategy).filter(BacktestStrategy.id == strategy_id)
    if not can_view_all(current):
        q = q.filter(BacktestStrategy.user_id == current.id)
    strategy = q.first()
    if not strategy:
        raise HTTPException(status_code=404, detail="模拟策略不存在")
    return strategy


def _get_owned_session(db: Session, session_id: int, current: User) -> BacktestSession:
    q = db.query(BacktestSession).filter(BacktestSession.id == session_id)
    if not can_view_all(current):
        q = q.filter(BacktestSession.user_id == current.id)
    session = q.first()
    if not session:
        raise HTTPException(status_code=404, detail="回测会话不存在")
    return session


# ========== 模拟策略 CRUD ==========

@router.get("/strategies", response_model=List[BacktestStrategyOut])
def list_strategies(db: Session = Depends(get_db), current=Depends(get_current_user)):
    _require_backtest(current)
    q = db.query(BacktestStrategy)
    if not can_view_all(current):
        q = q.filter(BacktestStrategy.user_id == current.id)
    return q.order_by(BacktestStrategy.create_time.desc()).all()


@router.post("/strategies", response_model=BacktestStrategyOut, status_code=201)
def create_strategy(
    data: BacktestStrategyCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    strategy = BacktestStrategy(**data.model_dump(), user_id=current.id)
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.get("/strategies/{strategy_id}", response_model=BacktestStrategyOut)
def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    return _get_owned_strategy(db, strategy_id, current)


@router.put("/strategies/{strategy_id}", response_model=BacktestStrategyOut)
def update_strategy(
    strategy_id: int,
    data: BacktestStrategyUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    strategy = _get_owned_strategy(db, strategy_id, current)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(strategy, key, value)
    db.commit()
    db.refresh(strategy)
    return strategy


@router.delete("/strategies/{strategy_id}", status_code=204)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    strategy = _get_owned_strategy(db, strategy_id, current)
    db.delete(strategy)
    db.commit()
    return None


@router.post("/strategies/{strategy_id}/preview-layers")
def preview_layers(
    strategy_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """根据模拟策略生成网格价位预览（不落库）。"""
    _require_backtest(current)
    strategy = _get_owned_strategy(db, strategy_id, current)
    return build_grid_layers(strategy_to_snapshot(strategy))


# ========== 回测会话 ==========

@router.get("/sessions", response_model=List[BacktestSessionOut])
def list_sessions(db: Session = Depends(get_db), current=Depends(get_current_user)):
    _require_backtest(current)
    q = db.query(BacktestSession)
    if not can_view_all(current):
        q = q.filter(BacktestSession.user_id == current.id)
    return q.order_by(BacktestSession.create_time.desc()).all()


@router.post("/sessions", response_model=BacktestSessionOut, status_code=201)
def create_session(
    data: BacktestSessionCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    strategy = _get_owned_strategy(db, data.strategy_id, current)
    fee_config = {**DEFAULT_FEE_CONFIG, **(data.fee_config or {})}
    session = BacktestSession(
        user_id=current.id,
        strategy_id=strategy.id,
        strategy_snapshot=strategy_to_snapshot(strategy),
        stock_code=strategy.stock_code,
        stock_name=strategy.stock_name,
        stock_type=strategy.stock_type,
        period="60",
        adjust="qfq",
        start_date=data.start_date,
        end_date=data.end_date,
        initial_cash=strategy.total_funds,
        fee_config=fee_config,
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    start_backtest(session.id)
    return session


@router.get("/sessions/{session_id}", response_model=BacktestSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    return _get_owned_session(db, session_id, current)


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    session = _get_owned_session(db, session_id, current)
    db.delete(session)
    db.commit()
    return None


@router.get("/sessions/{session_id}/trades", response_model=List[BacktestTradeOut])
def list_trades(
    session_id: int,
    limit: int = Query(200, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    _get_owned_session(db, session_id, current)
    return (
        db.query(BacktestTrade)
        .filter(BacktestTrade.session_id == session_id)
        .order_by(BacktestTrade.trade_time.asc(), BacktestTrade.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/sessions/{session_id}/layers", response_model=List[BacktestGridLayerOut])
def list_session_layers(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """读取该次回测保存的网格价位快照（用于K线图叠加与复盘）。"""
    _require_backtest(current)
    _get_owned_session(db, session_id, current)
    return (
        db.query(BacktestGridLayer)
        .filter(BacktestGridLayer.session_id == session_id)
        .order_by(BacktestGridLayer.direction.desc(), BacktestGridLayer.layer_index.asc())
        .all()
    )


@router.get("/sessions/{session_id}/metrics", response_model=BacktestMetricDetailOut)
def get_metrics(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    _get_owned_session(db, session_id, current)
    metric = db.query(BacktestMetric).filter(BacktestMetric.session_id == session_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="回测尚未完成，暂无绩效指标")
    return metric


@router.get("/sessions/{session_id}/equity-curve")
def get_equity_curve(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    _get_owned_session(db, session_id, current)
    metric = db.query(BacktestMetric).filter(BacktestMetric.session_id == session_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="回测尚未完成，暂无资产曲线")
    return {"points": metric.equity_curve or []}


@router.get("/sessions/{session_id}/kline", response_model=List[BacktestKlineOut])
def get_session_kline(
    session_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    _require_backtest(current)
    session = _get_owned_session(db, session_id, current)
    start_dt = datetime.combine(session.start_date, time(0, 0))
    end_dt = datetime.combine(session.end_date, time(23, 59, 59))
    return (
        db.query(BacktestKline)
        .filter(
            BacktestKline.stock_code == session.stock_code,
            BacktestKline.period == session.period,
            BacktestKline.adjust == session.adjust,
            BacktestKline.trade_time >= start_dt,
            BacktestKline.trade_time <= end_dt,
        )
        .order_by(BacktestKline.trade_time.asc())
        .all()
    )


class KlineRefreshIn(BaseModel):
    stock_code: str


@router.post("/kline/refresh")
def refresh_kline(
    data: KlineRefreshIn,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """手动清空指定标的的行情缓存，下次回测重新拉取。"""
    _require_backtest(current)
    deleted = clear_kline_cache(db, data.stock_code)
    return {"deleted": deleted}
