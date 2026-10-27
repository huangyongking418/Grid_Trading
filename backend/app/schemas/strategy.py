from pydantic import BaseModel, Field, model_validator
from typing import Optional, Any
from datetime import datetime


# === 策略模板 ===

class StrategyTemplateOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    direction_type: str
    default_params: Optional[Any] = None
    create_time: datetime

    model_config = {"from_attributes": True}


# === 策略实例 ===

class StrategyInstanceCreate(BaseModel):
    template_id: Optional[int] = None
    name: Optional[str] = None
    stock_id: Optional[int] = None
    grid_spacing: float
    grid_layers: int = Field(ge=1, le=50)
    asymmetry_ratio: float = 1.0
    base_price: float
    stop_loss_strategy: Optional[str] = "none"
    fund_allocation: str = "equal"
    total_funds: float = 0
    grid_funds: Optional[float] = None
    position_funds: Optional[float] = None
    split_mode: str = "amount"  # amount 金额切分 / shares 份额切分
    layer_shares: Optional[dict] = None  # 份额切分: {"buy": 每层买入份额, "sell": 每层卖出份额}
    reset_cycle_days: int = 0

    @model_validator(mode="after")
    def check_funds(self):
        total = self.total_funds if self.total_funds is not None else 0
        grid = self.grid_funds if self.grid_funds is not None else total
        pos = self.position_funds if self.position_funds is not None else (total - grid)
        if grid < 0 or pos < 0:
            raise ValueError("网格资金与底仓资金不能为负数")
        if abs(total - (grid + pos)) > 0.01:
            raise ValueError("总资金必须等于网格资金 + 底仓资金")
        if self.split_mode not in ("amount", "shares"):
            raise ValueError("切分方式仅支持 amount(金额切分) / shares(份额切分)")
        self.grid_funds = round(grid, 2)
        self.position_funds = round(pos, 2)
        return self


class StrategyInstanceUpdate(BaseModel):
    name: Optional[str] = None
    stock_id: Optional[int] = None
    grid_spacing: Optional[float] = None
    grid_layers: Optional[int] = None
    asymmetry_ratio: Optional[float] = None
    base_price: Optional[float] = None
    stop_loss_strategy: Optional[str] = None
    fund_allocation: Optional[str] = None
    total_funds: Optional[float] = None
    grid_funds: Optional[float] = None
    position_funds: Optional[float] = None
    split_mode: Optional[str] = None
    layer_shares: Optional[dict] = None
    reset_cycle_days: Optional[int] = None
    status: Optional[str] = None

    @model_validator(mode="after")
    def check_funds_update(self):
        vals = self.model_dump(exclude_unset=True)
        if "split_mode" in vals and vals["split_mode"] not in ("amount", "shares"):
            raise ValueError("切分方式仅支持 amount(金额切分) / shares(份额切分)")
        funds_keys = [k for k in ("total_funds", "grid_funds", "position_funds") if k in vals]
        if len(funds_keys) == 3:
            t, g, p = vals["total_funds"], vals["grid_funds"], vals["position_funds"]
            if abs(t - (g + p)) > 0.01:
                raise ValueError("总资金必须等于网格资金 + 底仓资金")
        return self


class StrategyInstanceOut(BaseModel):
    id: int
    user_id: int
    template_id: Optional[int] = None
    name: Optional[str] = None
    stock_id: Optional[int] = None
    grid_spacing: float
    grid_layers: int
    asymmetry_ratio: float
    base_price: float
    stop_loss_strategy: Optional[str] = None
    fund_allocation: str
    total_funds: float
    grid_funds: float = 0
    position_funds: float = 0
    split_mode: str = "amount"
    layer_shares: Optional[dict] = None
    reset_cycle_days: int
    last_reset_time: Optional[datetime] = None
    status: str
    create_time: datetime
    update_time: datetime
    template: Optional[StrategyTemplateOut] = None

    model_config = {"from_attributes": True}
