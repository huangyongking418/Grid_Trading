from app.core.database import Base
"""
?????? ? ??? ORM ????
? 9 ???strategy_template, strategy_instance, stock,
          grid_layer, operation_log, price_snapshot,
          push_config, trade_session, reset_log
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Text, DateTime, ForeignKey,
    Enum, JSON, Boolean, DECIMAL, Index
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# ========== ?????? ==========

class TimestampMixin:
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


# ========== 1. ????? ==========

class StrategyTemplate(Base):
    __tablename__ = "strategy_template"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, comment="??????")
    description = Column(String(255), nullable=True, comment="????")
    # ????: oscillation_up / oscillation / oscillation_down
    direction_type = Column(String(32), nullable=False, comment="??????")
    default_params = Column(JSON, nullable=True, comment="??????")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    instances = relationship("StrategyInstance", back_populates="template")

    def __repr__(self):
        return f"<StrategyTemplate {self.name}>"


# ========== 2. ????? ==========

class StrategyInstance(Base, TimestampMixin):
    __tablename__ = "strategy_instance"
    __table_args__ = (
        Index("ix_strategy_instance_user_id_create_time", "user_id", "create_time"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # ???????? user_id = 1
    user_id = Column(Integer, default=1, nullable=False)
    template_id = Column(Integer, ForeignKey("strategy_template.id"), nullable=True, comment="???????")
    name = Column(String(64), nullable=True, comment="???????")
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=True, comment="?????ID")

    # ????
    grid_spacing = Column(Float, nullable=False, comment="网格间距（百分比），如 1.0 表示 1%")
    grid_layers = Column(Integer, nullable=False, comment="????????")
    asymmetry_ratio = Column(Float, default=1.0, nullable=False, comment="??????????/??????")
    base_price = Column(Float, nullable=False, comment="?????")
    stop_loss_strategy = Column(String(32), default="none", nullable=True, comment="????: none / stop_layer / full_stop")
    fund_allocation = Column(String(32), default="equal", nullable=False, comment="????: equal / pyramid / custom")
    total_funds = Column(Float, default=0, nullable=False, comment="?????")
    # 资金拆分：总资金 = 网格资金 + 底仓资金
    grid_funds = Column(Float, default=0, nullable=False, comment="网格资金（用于网格层切分）")
    position_funds = Column(Float, default=0, nullable=False, comment="底仓资金（长期持有，不参与网格）")
    split_mode = Column(String(16), default="amount", nullable=False, comment="切分方式: amount 金额切分 / shares 份额切分")
    layer_shares = Column(JSON, nullable=True, comment="份额切分配置: {buy: 每层买入份额, sell: 每层卖出份额}")

    # ????
    reset_cycle_days = Column(Integer, default=0, nullable=False, comment="??????????0=???")
    last_reset_time = Column(DateTime, nullable=True, comment="??????")

    status = Column(String(16), default="active", nullable=False, comment="????: active / inactive")

    # ??
    template = relationship("StrategyTemplate", back_populates="instances")
    stock = relationship("Stock", back_populates="strategy_instance")
    layers = relationship("GridLayer", back_populates="instance", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="instance")
    reset_log_list = relationship("ResetLog", back_populates="instance")

    def __repr__(self):
        return f"<StrategyInstance {self.id}: {self.name or 'Unnamed'}>"


# ========== 3. ????? ==========

class Stock(Base, TimestampMixin):
    __tablename__ = "stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    code = Column(String(16), nullable=False, unique=True, index=True, comment="?????? 600519?")
    name = Column(String(64), nullable=False, comment="????")
    # ????: stock / etf / fund
    type = Column(String(16), nullable=False, comment="????")
    exchange = Column(String(8), nullable=True, comment="???: SH / SZ")
    strategy_instance_id = Column(Integer, nullable=True, comment="???ID")
    current_price = Column(Float, nullable=True, comment="????/??")

    # ??
    strategy_instance = relationship("StrategyInstance", back_populates="stock", uselist=False)
    price_snapshots = relationship("PriceSnapshot", back_populates="stock", cascade="all, delete-orphan")
    operation_logs = relationship("OperationLog", back_populates="stock")

    def __repr__(self):
        return f"<Stock {self.code} {self.name}>"


# ========== 4. ?????? ==========

class GridLayer(Base):
    __tablename__ = "grid_layer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("strategy_instance.id"), nullable=False, comment="??????")
    layer_type = Column(String(16), default="grid", nullable=False, comment="层类型: grid 网格层 / position 底仓")
    layer_index = Column(Integer, nullable=False, comment="????0?????")
    direction = Column(String(8), nullable=False, comment="??: buy / sell")
    trigger_price = Column(Float, nullable=False, comment="????")
    quantity = Column(Integer, nullable=False, comment="????/??")
    amount = Column(Float, nullable=False, comment="??")
    status = Column(String(16), default="pending", nullable=False, comment="??: pending / triggered / invalid")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    instance = relationship("StrategyInstance", back_populates="layers")

    def __repr__(self):
        return f"<GridLayer {self.instance_id}-{self.layer_index} {self.direction} @ {self.trigger_price}>"


# ========== 5. ????? ==========

class OperationLog(Base):
    __tablename__ = "operation_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    instance_id = Column(Integer, ForeignKey("strategy_instance.id"), nullable=True, comment="??????")
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=True, comment="????")
    layer_id = Column(Integer, nullable=True, comment="?????ID?????")
    trigger_price = Column(Float, nullable=False, comment="????")
    quantity = Column(Integer, nullable=True, comment="??")
    direction = Column(String(8), nullable=False, comment="??: buy / sell")
    # ????: theoretical??????/ actual??????
    log_type = Column(String(16), default="theoretical", nullable=False, comment="????")
    fee = Column(Float, default=0, nullable=True, comment="???")
    note = Column(String(255), nullable=True, comment="??")
    push_status = Column(JSON, nullable=True, comment="??")
    operate_time = Column(DateTime, nullable=True, comment="????????????")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    instance = relationship("StrategyInstance", back_populates="operation_logs")
    stock = relationship("Stock", back_populates="operation_logs")

    def __repr__(self):
        return f"<OperationLog {self.id} {self.direction} @ {self.trigger_price}>"


# ========== 6. ????? ==========

class PriceSnapshot(Base):
    __tablename__ = "price_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey("stock.id"), nullable=False, comment="??ID")
    price = Column(Float, nullable=False, comment="??")
    source = Column(String(32), default="akshare", nullable=True, comment="????")
    snapshot_time = Column(DateTime, default=datetime.now, nullable=False, comment="????")

    stock = relationship("Stock", back_populates="price_snapshots")

    def __repr__(self):
        return f"<PriceSnapshot {self.stock_id} @ {self.price}>"


# ========== 7. ????? ==========

class PushConfig(Base):
    __tablename__ = "push_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    channel = Column(String(32), nullable=False, unique=True, comment="??: wechat / dingtalk")
    webhook_url = Column(String(512), nullable=True, comment="Webhook ??")
    enabled = Column(Boolean, default=False, nullable=False, comment="????")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<PushConfig {self.channel}: {'ON' if self.enabled else 'OFF'}>"


# ========== 7.1 邮箱推送配置 ==========

class EmailConfig(Base):
    __tablename__ = "email_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    to_email = Column(String(255), nullable=False, default="", comment="")
    enabled = Column(Boolean, default=False, nullable=False, comment="")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<EmailConfig {self.user_id}: {'ON' if self.enabled else 'OFF'}>"


# ========== 8. ????? ==========

class TradeSession(Base):
    __tablename__ = "trade_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    market = Column(String(16), nullable=False, comment="??: A_stock / fund")
    open_time = Column(String(8), nullable=False, comment="???? HH:mm")
    close_time = Column(String(8), nullable=False, comment="???? HH:mm")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<TradeSession {self.market}: {self.open_time}-{self.close_time}>"


# ========== 9. ???????? ==========

class ResetLog(Base):
    __tablename__ = "reset_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_id = Column(Integer, ForeignKey("strategy_instance.id"), nullable=False, comment="????ID")
    old_base_price = Column(Float, nullable=False, comment="????")
    new_base_price = Column(Float, nullable=False, comment="????")
    reset_reason = Column(String(128), default="periodic_reset", nullable=True, comment="????")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    instance = relationship("StrategyInstance", back_populates="reset_log_list")


class InAppMessage(Base):
    __tablename__ = "in_app_message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True)
    title = Column(String(128), nullable=False, comment="????")
    content = Column(String(500), nullable=True, comment="????")
    message_type = Column(String(32), nullable=False, comment="????: reset_expiry / buy_trigger / sell_trigger")
    related_stock_id = Column(Integer, ForeignKey("stock.id"), nullable=True, comment="????ID")
    related_instance_id = Column(Integer, ForeignKey("strategy_instance.id"), nullable=True, comment="??????ID")
    is_read = Column(Boolean, default=False, nullable=False, comment="????")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<InAppMessage {self.id}: {self.title}>"


# ========== 10. 用户表 ==========

class User(Base, TimestampMixin):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False, unique=True, index=True, comment="登录账号")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    phone = Column(String(20), nullable=False, unique=True, comment="手机号")
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False, comment="角色ID")
    status = Column(String(16), default="active", nullable=False, comment="状态: active/disabled")
    expire_date = Column(DateTime, nullable=False, comment="账号有效期")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    role = relationship("Role", back_populates="users")

    def __repr__(self):
        return f"<User {self.username}>"


# ========== 11. 角色表 ==========

class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, comment="角色名称")
    description = Column(String(255), nullable=True, comment="角色描述")
    is_preset = Column(Boolean, default=False, nullable=False, comment="是否预置角色")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name}>"


# ========== 12. 角色权限表 ==========

class RolePermission(Base):
    __tablename__ = "role_permission"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False, comment="角色ID")
    function_code = Column(String(64), nullable=False, comment="功能权限代码")
    data_scope = Column(String(16), default="self", nullable=False, comment="数据权限: self/all")
    create_time = Column(DateTime, default=datetime.now, nullable=False)

    role = relationship("Role", back_populates="permissions")

    def __repr__(self):
        return f"<RolePermission {self.function_code}: {self.data_scope}>"


# ========== 13. 系统参数表 ==========

class SystemParam(Base):
    __tablename__ = "system_param"

    id = Column(Integer, primary_key=True, autoincrement=True)
    param_key = Column(String(64), nullable=False, unique=True, comment="参数键")
    param_value = Column(String(255), nullable=False, comment="参数值")
    description = Column(String(255), nullable=True, comment="参数说明")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<SystemParam {self.param_key}={self.param_value}>"


# ========== 14. 公告表 ==========

class Announcement(Base):
    __tablename__ = "announcement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False, comment="公告标题")
    content = Column(Text, nullable=True, comment="公告内容")
    image_url = Column(String(255), nullable=True, comment="公告图片URL")
    image_name = Column(String(128), nullable=True, comment="公告图片名称")
    status = Column(String(16), default="enabled", nullable=False, comment="状态: enabled/disabled")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Announcement {self.title}>"


    def __repr__(self):
        return f"<ResetLog {self.instance_id}: {self.old_base_price} -> {self.new_base_price}>"


# ========== 15. 模拟回测独立模型（不修改现有表结构） ==========
from app.models.backtest_models import (  # noqa: E402,F401
    BacktestStrategy,
    BacktestSession,
    BacktestKline,
    BacktestGridLayer,
    BacktestTrade,
    BacktestMetric,
)


# ========== 16. 文档管理独立模型 ==========
from app.models.document_models import SystemDocument  # noqa: E402,F401
