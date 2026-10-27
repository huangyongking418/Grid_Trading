from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class StockCreate(BaseModel):
    code: str
    name: str
    type: str  # stock / etf / fund
    exchange: Optional[str] = None
    current_price: Optional[float] = None


class StockOut(BaseModel):
    id: int
    code: str
    name: str
    type: str
    exchange: Optional[str] = None
    current_price: Optional[float] = None
    strategy_instance_id: Optional[int] = None
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class StockBind(BaseModel):
    instance_id: int

class StockSearchOut(BaseModel):
    code: str
    name: str
    type: str
    stock_id: Optional[int] = None
