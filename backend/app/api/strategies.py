from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user, can_view_all
from app.models.all_models import (
    InAppMessage,
    OperationLog,
    ResetLog,
    StrategyTemplate,
    StrategyInstance,
    Stock,
)
from app.services.bind_service import bind_instance_to_stock, unbind_instance
from app.services.grid_engine import generate_and_save_layers
from app.schemas.strategy import (
    StrategyTemplateOut,
    StrategyInstanceCreate,
    StrategyInstanceUpdate,
    StrategyInstanceOut,
)

router = APIRouter(prefix="/api/strategies", tags=["策略管理"])


# ========== 策略模板 ==========

@router.get("/templates", response_model=List[StrategyTemplateOut])
def list_templates(db: Session = Depends(get_db)):
    """获取所有策略模板"""
    return db.query(StrategyTemplate).all()


# ========== 策略实例 ==========

@router.get("/instances", response_model=List[StrategyInstanceOut])
def list_instances(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """获取所有策略实例"""
    q = db.query(StrategyInstance)
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    return q.order_by(StrategyInstance.create_time.desc()).all()


@router.get("/instances/{instance_id}", response_model=StrategyInstanceOut)
def get_instance(instance_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """获取单个策略实例详情"""
    q = db.query(StrategyInstance).filter(StrategyInstance.id == instance_id)
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    instance = q.first()
    if not instance:
        raise HTTPException(status_code=404, detail="策略实例不存在")
    return instance


@router.post("/instances", response_model=StrategyInstanceOut, status_code=201)
def create_instance(data: StrategyInstanceCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """创建策略实例"""
    # 校验模板是否存在
    if data.template_id:
        template = db.query(StrategyTemplate).filter(StrategyTemplate.id == data.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="策略模板不存在")
    
    stock_id = data.stock_id
    payload = data.model_dump()
    payload.pop("stock_id", None)
    instance = StrategyInstance(**payload, user_id=current.id)
    db.add(instance)
    db.flush()
    if stock_id:
        stock = db.query(Stock).filter(Stock.id == stock_id, Stock.user_id == current.id).first()
        if not stock:
            db.rollback()
            raise HTTPException(status_code=404, detail="标的不存在")
        bind_instance_to_stock(db, instance, stock)
    db.commit()
    db.refresh(instance)
    try:
        generate_and_save_layers(instance, db)
    except Exception:
        pass  # 明细生成失败不影响策略保存
    return instance


@router.put("/instances/{instance_id}", response_model=StrategyInstanceOut)
def update_instance(instance_id: int, data: StrategyInstanceUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """更新策略实例"""
    q = db.query(StrategyInstance).filter(StrategyInstance.id == instance_id)
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    instance = q.first()
    if not instance:
        raise HTTPException(status_code=404, detail="策略实例不存在")
    
    update_data = data.model_dump(exclude_unset=True)
    if "stock_id" in update_data:
        stock_id = update_data.pop("stock_id")
        if stock_id is None:
            unbind_instance(db, instance)
        else:
            stock = db.query(Stock).filter(Stock.id == stock_id, Stock.user_id == current.id).first()
            if not stock:
                raise HTTPException(status_code=404, detail="标的不存在")
            bind_instance_to_stock(db, instance, stock)
    for key, value in update_data.items():
        setattr(instance, key, value)

    # 资金约束校验：若同时提供三项，需满足 总资金 = 网格资金 + 底仓资金
    if all(k in update_data for k in ("total_funds", "grid_funds", "position_funds")):
        t, g, p = update_data["total_funds"], update_data["grid_funds"], update_data["position_funds"]
        if abs(t - (g + p)) > 0.01:
            raise HTTPException(status_code=400, detail="总资金必须等于网格资金 + 底仓资金")

    db.commit()
    db.refresh(instance)
    try:
        generate_and_save_layers(instance, db)
    except Exception:
        pass  # 明细生成失败不影响策略保存
    return instance


@router.delete("/instances/{instance_id}", status_code=204)
def delete_instance(instance_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    """删除策略实例"""
    q = db.query(StrategyInstance).filter(StrategyInstance.id == instance_id)
    if not can_view_all(current):
        q = q.filter(StrategyInstance.user_id == current.id)
    instance = q.first()
    if not instance:
        raise HTTPException(status_code=404, detail="策略实例不存在")

    unbind_instance(db, instance)
    # 清理引用该策略的外键数据，避免数据库外键约束导致删除失败
    db.query(OperationLog).filter(OperationLog.instance_id == instance.id).delete(
        synchronize_session=False
    )
    db.query(ResetLog).filter(ResetLog.instance_id == instance.id).delete(
        synchronize_session=False
    )
    db.query(InAppMessage).filter(InAppMessage.related_instance_id == instance.id).update(
        {"related_instance_id": None}, synchronize_session=False
    )
    db.delete(instance)
    db.commit()
    return None
