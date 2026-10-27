from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.all_models import StrategyInstance, GridLayer
from app.services.grid_engine import generate_and_save_layers, calculate_layers
from app.schemas.strategy import StrategyInstanceCreate


router = APIRouter(prefix="/api/strategies", tags=["????"])


class GridLayerOut:
    pass


from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GridLayerOutSchema(BaseModel):
    id: int
    instance_id: int
    layer_index: int
    layer_type: str = "grid"
    direction: str
    trigger_price: float
    quantity: int
    amount: float
    status: str
    create_time: datetime

    model_config = {"from_attributes": True}


class PreviewLayerOut(BaseModel):
    layer_index: int
    layer_type: str = "grid"
    direction: str
    trigger_price: float
    quantity: int
    amount: float
    status: str


@router.get("/instances/{instance_id}/layers", response_model=List[GridLayerOutSchema])
def get_layers(instance_id: int, db: Session = Depends(get_db)):
    # 排序：卖出组在前、买入组在后，各组内按层号升序（底仓 layer_index=0 位于买入组最前）
    layers = db.query(GridLayer).filter(
        GridLayer.instance_id == instance_id
    ).order_by(GridLayer.direction.desc(), GridLayer.layer_index.asc()).all()
    return layers


@router.post("/preview", response_model=List[PreviewLayerOut])
def preview_layers(data: StrategyInstanceCreate):
    """策略预览：根据当前表单参数计算操作明细（不落库）"""
    instance = StrategyInstance(
        grid_spacing=data.grid_spacing,
        grid_layers=data.grid_layers,
        asymmetry_ratio=data.asymmetry_ratio,
        base_price=data.base_price,
        stop_loss_strategy=data.stop_loss_strategy,
        fund_allocation=data.fund_allocation,
        total_funds=data.total_funds or 0,
        grid_funds=data.grid_funds if data.grid_funds is not None else data.total_funds,
        position_funds=data.position_funds if data.position_funds is not None else 0,
        split_mode=data.split_mode,
        layer_shares=data.layer_shares,
    )
    return calculate_layers(instance)


@router.post("/instances/{instance_id}/layers/generate", response_model=List[GridLayerOutSchema])
def generate_layers(instance_id: int, db: Session = Depends(get_db)):
    instance = db.query(StrategyInstance).filter(StrategyInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="???????")
    layers = generate_and_save_layers(instance, db)
    return layers
