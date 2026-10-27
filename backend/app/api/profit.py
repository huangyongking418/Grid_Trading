from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user, can_view_all
from app.models.all_models import OperationLog, StrategyInstance, GridLayer, InAppMessage
from pydantic import BaseModel


class OperationCreate(BaseModel):
    instance_id: int
    stock_id: Optional[int] = None
    trigger_price: float
    quantity: Optional[int] = None
    direction: str
    fee: Optional[float] = 0
    note: Optional[str] = None
    operate_time: Optional[datetime] = None


class OperationOut(BaseModel):
    id: int
    instance_id: Optional[int] = None
    stock_id: Optional[int] = None
    trigger_price: float
    quantity: Optional[int] = None
    direction: str
    log_type: str
    fee: Optional[float] = None
    note: Optional[str] = None
    operate_time: Optional[datetime] = None
    create_time: datetime
    model_config = {"from_attributes": True}


class YieldPoint(BaseModel):
    date: str
    theoretical_yield: float = 0
    actual_yield: float = 0


router = APIRouter(prefix="/api/profit", tags=["????"])


@router.get("/operations", response_model=List[OperationOut])
def list_operations(stock_id: Optional[int] = None, log_type: Optional[str] = None, db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(OperationLog)
    if not can_view_all(current):
        q = q.filter(OperationLog.user_id == current.id)
    if stock_id:
        q = q.filter(OperationLog.stock_id == stock_id)
    if log_type:
        q = q.filter(OperationLog.log_type == log_type)
    return q.order_by(OperationLog.create_time.desc()).limit(100).all()


@router.post("/operations", response_model=OperationOut, status_code=201)
def create_operation(data: OperationCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    op = OperationLog(**data.model_dump(), log_type='actual', user_id=current.id)
    db.add(op)
    db.commit()
    db.refresh(op)

    msg_type = 'buy_trigger' if data.direction == 'buy' else 'sell_trigger'
    msg_title = '买入触发提醒' if data.direction == 'buy' else '卖出触发提醒'
    msg = InAppMessage(
        title=msg_title,
        content=f'价格 {data.trigger_price} 触发{data.direction}信号，数量 {data.quantity}',
        message_type=msg_type,
        related_stock_id=data.stock_id,
        related_instance_id=data.instance_id,
    )
    db.add(msg)
    db.commit()

    return op


@router.delete("/operations/{op_id}", status_code=204)
def delete_operation(op_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    op = db.query(OperationLog).filter(OperationLog.id == op_id, OperationLog.user_id == current.id).first()
    if not op:
        raise HTTPException(status_code=404, detail="?????")
    db.delete(op)
    db.commit()
    return None


@router.get("/theoretical/{instance_id}")
def get_theoretical_yield(instance_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    layers = db.query(GridLayer).filter(GridLayer.instance_id == instance_id).all()
    ops = db.query(OperationLog).filter(
        OperationLog.instance_id == instance_id,
        OperationLog.log_type == 'theoretical',
    ).all()
    total_investment = sum(l.amount for l in layers if l.direction == 'buy')
    total_return = sum(o.trigger_price * (o.quantity or 0) for o in ops if o.direction == 'sell')
    total_cost = sum(o.trigger_price * (o.quantity or 0) for o in ops if o.direction == 'buy')
    yield_rate = ((total_return - total_cost) / (total_investment or 1)) * 100
    return {
        "total_investment": round(total_investment, 2),
        "total_return": round(total_return, 2),
        "total_cost": round(total_cost, 2),
        "yield_rate": round(yield_rate, 2),
    }


@router.get("/actual")
def get_actual_yield(stock_id: Optional[int] = None, db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(OperationLog).filter(OperationLog.log_type == 'actual')
    if not can_view_all(current):
        q = q.filter(OperationLog.user_id == current.id)
    if stock_id:
        q = q.filter(OperationLog.stock_id == stock_id)
    ops = q.order_by(OperationLog.create_time).all()
    total_buy = sum(o.trigger_price * (o.quantity or 0) + (o.fee or 0) for o in ops if o.direction == 'buy')
    total_sell = sum(o.trigger_price * (o.quantity or 0) - (o.fee or 0) for o in ops if o.direction == 'sell')
    yield_rate = 0
    if total_buy > 0:
        yield_rate = round(((total_sell - total_buy) / total_buy) * 100, 2)
    return {
        "total_buy": round(total_buy, 2),
        "total_sell": round(total_sell, 2),
        "yield_rate": yield_rate,
        "operation_count": len(ops),
    }
