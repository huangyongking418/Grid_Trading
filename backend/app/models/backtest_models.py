from datetime import datetime

from sqlalchemy import (
    Column, Integer, Float, String, DateTime, ForeignKey, JSON, Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class BacktestStrategy(Base):
    """模拟策略表：参数与正式策略一致，数据完全独立。"""

    __tablename__ = "backtest_strategy"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    name = Column(String(64), nullable=True, comment="模拟策略名称")
    template_id = Column(Integer, nullable=True, comment="来源模板ID（仅记录，不关联正式表）")
    stock_code = Column(String(16), nullable=False, comment="标的代码快照")
    stock_name = Column(String(64), nullable=False, comment="标的名称快照")
    stock_type = Column(String(16), nullable=False, comment="stock / etf")

    grid_spacing = Column(Float, nullable=False, comment="网格间距（百分比）")
    grid_layers = Column(Integer, nullable=False, comment="网格层数（单侧）")
    asymmetry_ratio = Column(Float, default=1.0, nullable=False, comment="不对称比")
    base_price = Column(Float, nullable=False, comment="网格基准价")
    stop_loss_strategy = Column(String(32), default="none", nullable=True, comment="none / stop_layer / full_stop")
    fund_allocation = Column(String(32), default="equal", nullable=False, comment="equal / pyramid")
    total_funds = Column(Float, default=0, nullable=False, comment="总资金")
    grid_funds = Column(Float, default=0, nullable=False, comment="网格资金")
    position_funds = Column(Float, default=0, nullable=False, comment="底仓资金")
    split_mode = Column(String(16), default="amount", nullable=False, comment="amount / shares")
    layer_shares = Column(JSON, nullable=True, comment="份额切分配置")
    reset_cycle_days = Column(Integer, default=0, nullable=False, comment="基准重置周期天数")
    status = Column(String(16), default="active", nullable=False, comment="active / inactive")

    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    sessions = relationship("BacktestSession", back_populates="strategy", cascade="all, delete-orphan")


class BacktestSession(Base):
    """回测会话表：一次回测的周期、状态、费用配置与策略参数快照。"""

    __tablename__ = "backtest_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    strategy_id = Column(Integer, ForeignKey("backtest_strategy.id"), nullable=False, index=True)
    strategy_snapshot = Column(JSON, nullable=True, comment="执行时的策略参数快照")
    stock_code = Column(String(16), nullable=False, comment="标的代码快照")
    stock_name = Column(String(64), nullable=False, comment="标的名称快照")
    stock_type = Column(String(16), nullable=False, comment="stock / etf")
    period = Column(String(8), default="60", nullable=False, comment="K线周期（分钟）")
    adjust = Column(String(8), default="qfq", nullable=False, comment="复权方式 qfq")
    start_date = Column(Date, nullable=False, comment="回测开始日期")
    end_date = Column(Date, nullable=False, comment="回测结束日期")
    initial_cash = Column(Float, nullable=True, comment="初始资金")
    fee_config = Column(JSON, nullable=True, comment="费用与滑点配置")
    status = Column(String(16), default="pending", nullable=False, comment="pending/running/success/failed")
    error_message = Column(String(500), nullable=True, comment="失败原因")
    data_source = Column(
        String(32),
        nullable=True,
        comment="实际行情来源: akshare/eastmoney_direct/tencent_m60_fallback/sina_m60_fallback",
    )
    data_note = Column(String(500), nullable=True, comment="数据源降级与复权口径说明")
    kline_count = Column(Integer, default=0, nullable=False, comment="K线数量")
    trade_count = Column(Integer, default=0, nullable=False, comment="成交笔数")
    run_start_time = Column(DateTime, nullable=True, comment="回测开始执行时间")
    run_end_time = Column(DateTime, nullable=True, comment="回测结束执行时间")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    strategy = relationship("BacktestStrategy", back_populates="sessions")
    layers = relationship("BacktestGridLayer", back_populates="session", cascade="all, delete-orphan")
    trades = relationship("BacktestTrade", back_populates="session", cascade="all, delete-orphan")
    metric = relationship("BacktestMetric", back_populates="session", cascade="all, delete-orphan", uselist=False)

    @property
    def strategy_name(self):
        return self.strategy.name if self.strategy else None


class BacktestKline(Base):
    """历史K线缓存表：同一标的+周期+复权+时间唯一存储。"""

    __tablename__ = "backtest_kline"
    __table_args__ = (
        UniqueConstraint(
            "stock_code", "period", "adjust", "trade_time",
            name="uq_backtest_kline_symbol_period_adjust_time",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(16), nullable=False, index=True)
    stock_type = Column(String(16), nullable=False)
    period = Column(String(8), default="60", nullable=False)
    adjust = Column(String(8), default="qfq", nullable=False)
    trade_time = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    amount = Column(Float, nullable=True)
    source = Column(String(32), default="akshare", nullable=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)


class BacktestGridLayer(Base):
    """回测网格层快照：每次回测保存当时的网格价位与最终状态。"""

    __tablename__ = "backtest_grid_layer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("backtest_session.id"), nullable=False, index=True)
    layer_index = Column(Integer, nullable=False, comment="层号，0 为底仓")
    layer_type = Column(String(16), default="grid", nullable=False, comment="grid / position")
    direction = Column(String(8), nullable=False, comment="buy / sell")
    trigger_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(16), default="pending", nullable=False, comment="pending/bought/sold/holding/invalid")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    session = relationship("BacktestSession", back_populates="layers")


class BacktestTrade(Base):
    """回测成交记录表：保存全部模拟成交。"""

    __tablename__ = "backtest_trade"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    session_id = Column(Integer, ForeignKey("backtest_session.id"), nullable=False, index=True)
    layer_index = Column(Integer, nullable=False)
    direction = Column(String(8), nullable=False, comment="buy / sell")
    trade_time = Column(DateTime, nullable=False, comment="成交对应的K线时间")
    trigger_price = Column(Float, nullable=False, comment="成交价（触发价）")
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False, comment="成交金额")
    fee = Column(Float, default=0, nullable=False, comment="手续费")
    cash_after = Column(Float, nullable=True, comment="成交后剩余现金")
    note = Column(String(255), nullable=True)
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    session = relationship("BacktestSession", back_populates="trades")


class BacktestMetric(Base):
    """回测绩效指标表：指标与资产/回撤曲线。"""

    __tablename__ = "backtest_metric"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("backtest_session.id"), nullable=False, unique=True, index=True)
    total_return_rate = Column(Float, nullable=True)
    annual_return_rate = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_loss_ratio = Column(Float, nullable=True)
    total_trade_count = Column(Integer, default=0, nullable=False)
    buy_count = Column(Integer, default=0, nullable=False)
    sell_count = Column(Integer, default=0, nullable=False)
    total_fee = Column(Float, default=0, nullable=False)
    final_asset = Column(Float, nullable=True)
    benchmark_return_rate = Column(Float, nullable=True)
    excess_return = Column(Float, nullable=True)
    equity_curve = Column(JSON, nullable=True, comment="[{time, asset, benchmark_asset}]")
    drawdown_curve = Column(JSON, nullable=True, comment="[{time, drawdown}]")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    session = relationship("BacktestSession", back_populates="metric")
