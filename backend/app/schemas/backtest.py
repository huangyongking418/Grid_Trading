from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class BacktestStrategyCreate(BaseModel):
    name: Optional[str] = None
    template_id: Optional[int] = None
    stock_code: str
    stock_name: str
    stock_type: str = "stock"  # stock / etf
    grid_spacing: float
    grid_layers: int = Field(ge=1, le=50)
    asymmetry_ratio: float = 1.0
    base_price: float
    stop_loss_strategy: Optional[str] = "none"
    fund_allocation: str = "equal"
    total_funds: float = 0
    grid_funds: Optional[float] = None
    position_funds: Optional[float] = None
    split_mode: str = "amount"
    layer_shares: Optional[dict] = None
    reset_cycle_days: int = 0

    @model_validator(mode="after")
    def check_funds(self):
        if self.stock_type not in ("stock", "etf"):
            raise ValueError("回测标的仅支持 A股个股(stock) 与 ETF(etf)")
        if self.split_mode not in ("amount", "shares"):
            raise ValueError("切分方式仅支持 amount / shares")
        total = self.total_funds if self.total_funds is not None else 0
        grid = self.grid_funds if self.grid_funds is not None else total
        pos = self.position_funds if self.position_funds is not None else (total - grid)
        if grid < 0 or pos < 0:
            raise ValueError("网格资金与底仓资金不能为负数")
        if abs(total - (grid + pos)) > 0.01:
            raise ValueError("总资金必须等于网格资金 + 底仓资金")
        self.grid_funds = round(grid, 2)
        self.position_funds = round(pos, 2)
        return self


class BacktestStrategyUpdate(BaseModel):
    name: Optional[str] = None
    template_id: Optional[int] = None
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    stock_type: Optional[str] = None
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
        if "stock_type" in vals and vals["stock_type"] not in ("stock", "etf"):
            raise ValueError("回测标的仅支持 stock / etf")
        if "split_mode" in vals and vals["split_mode"] not in ("amount", "shares"):
            raise ValueError("切分方式仅支持 amount / shares")
        funds_keys = [k for k in ("total_funds", "grid_funds", "position_funds") if k in vals]
        if len(funds_keys) == 3:
            t, g, p = vals["total_funds"], vals["grid_funds"], vals["position_funds"]
            if abs(t - (g + p)) > 0.01:
                raise ValueError("总资金必须等于网格资金 + 底仓资金")
        return self


class BacktestStrategyOut(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    template_id: Optional[int] = None
    stock_code: str
    stock_name: str
    stock_type: str
    grid_spacing: float
    grid_layers: int
    asymmetry_ratio: float
    base_price: float
    stop_loss_strategy: Optional[str] = None
    fund_allocation: str
    total_funds: float
    grid_funds: float
    position_funds: float
    split_mode: str
    layer_shares: Optional[dict] = None
    reset_cycle_days: int
    status: str
    create_time: datetime
    update_time: datetime

    model_config = {"from_attributes": True}


class BacktestSessionCreate(BaseModel):
    strategy_id: int
    start_date: date
    end_date: date
    fee_config: Optional[Dict[str, float]] = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        if (self.end_date - self.start_date).days > 3650:
            raise ValueError("回测区间不能超过 10 年")
        return self


class BacktestMetricOut(BaseModel):
    total_return_rate: Optional[float] = None
    annual_return_rate: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    total_trade_count: int = 0
    buy_count: int = 0
    sell_count: int = 0
    total_fee: float = 0
    final_asset: Optional[float] = None
    benchmark_return_rate: Optional[float] = None
    excess_return: Optional[float] = None

    model_config = {"from_attributes": True}


class BacktestSessionOut(BaseModel):
    id: int
    user_id: int
    strategy_id: int
    strategy_name: Optional[str] = None
    stock_code: str
    stock_name: str
    stock_type: str
    period: str
    adjust: str
    start_date: date
    end_date: date
    initial_cash: Optional[float] = None
    fee_config: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    data_source: Optional[str] = None
    data_note: Optional[str] = None
    kline_count: int = 0
    trade_count: int = 0
    run_start_time: Optional[datetime] = None
    run_end_time: Optional[datetime] = None
    create_time: datetime
    metric: Optional[BacktestMetricOut] = None

    model_config = {"from_attributes": True}


class BacktestTradeOut(BaseModel):
    id: int
    session_id: int
    layer_index: int
    direction: str
    trade_time: datetime
    trigger_price: float
    quantity: int
    amount: float
    fee: float
    cash_after: Optional[float] = None
    note: Optional[str] = None
    create_time: datetime

    model_config = {"from_attributes": True}


class BacktestGridLayerOut(BaseModel):
    id: int
    session_id: int
    layer_index: int
    layer_type: str
    direction: str
    trigger_price: float
    quantity: int
    amount: float
    status: str
    create_time: datetime

    model_config = {"from_attributes": True}


class BacktestKlineOut(BaseModel):
    trade_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float] = None
    amount: Optional[float] = None

    model_config = {"from_attributes": True}


class BacktestMetricDetailOut(BaseModel):
    total_return_rate: Optional[float] = None
    annual_return_rate: Optional[float] = None
    max_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None
    total_trade_count: int = 0
    buy_count: int = 0
    sell_count: int = 0
    total_fee: float = 0
    final_asset: Optional[float] = None
    benchmark_return_rate: Optional[float] = None
    excess_return: Optional[float] = None
    equity_curve: Optional[List[Dict[str, Any]]] = None
    drawdown_curve: Optional[List[Dict[str, Any]]] = None

    model_config = {"from_attributes": True}
