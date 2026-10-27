"""统一的策略实例 <-> 标的 绑定/解绑逻辑（1:1）。"""

from sqlalchemy.orm import Session

from app.models.all_models import Stock, StrategyInstance


def unbind_instance(db: Session, instance: StrategyInstance) -> None:
    """解除策略实例与标的的绑定，双向字段同步清空。"""
    if instance.stock_id:
        stock = db.query(Stock).filter(Stock.id == instance.stock_id).first()
        if stock and stock.strategy_instance_id == instance.id:
            stock.strategy_instance_id = None
        instance.stock_id = None


def bind_instance_to_stock(db: Session, instance: StrategyInstance, stock: Stock) -> None:
    """将策略实例绑定到标的（1:1），自动解除双方原有的旧绑定。"""
    # 该策略若已绑定其他标的，先解除
    if instance.stock_id and instance.stock_id != stock.id:
        old_stock = db.query(Stock).filter(Stock.id == instance.stock_id).first()
        if old_stock:
            old_stock.strategy_instance_id = None
    # 该标的若已绑定其他策略，先解除
    if stock.strategy_instance_id and stock.strategy_instance_id != instance.id:
        old_instance = db.query(StrategyInstance).filter(
            StrategyInstance.id == stock.strategy_instance_id
        ).first()
        if old_instance:
            old_instance.stock_id = None

    stock.strategy_instance_id = instance.id
    instance.stock_id = stock.id
