from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import can_view_all, get_current_user
from app.core.database import get_db
from app.models.all_models import ResetLog, StrategyInstance
from app.services.reset_service import check_expired_instances


class ResetLogOut(BaseModel):
    id: int
    instance_id: int
    old_base_price: float
    new_base_price: float
    reset_reason: Optional[str] = None
    create_time: datetime
    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api/reset", tags=["????"])


@router.get("/logs", response_model=List[ResetLogOut])
def list_reset_logs(db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(ResetLog).join(StrategyInstance)
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    return q.order_by(ResetLog.create_time.desc()).limit(50).all()


@router.post("/check")
def check_and_reset(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """检查当前用户可见策略的基准价重置周期，到期则重置并发送提醒。"""
    q = db.query(StrategyInstance).filter(
        StrategyInstance.status == 'active',
        StrategyInstance.reset_cycle_days > 0,
    )
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    results = check_expired_instances(db, q.all(), now=datetime.now())
    return {'reset_count': len(results), 'results': results}
