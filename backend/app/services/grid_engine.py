"""
???????
????????????????????????????
?????????????????????
"""

from typing import List, Tuple
from app.models.all_models import StrategyInstance, GridLayer


def calculate_layers(
    instance: StrategyInstance,
    total_funds: float = None,
) -> List[dict]:
    """
    根据策略参数生成网格层与底仓记录

    支持两种切分方式：
      - amount（基于金额切分）：网格资金按资金分配规则切分到各层，再换算成份额
      - shares（基于份额切分）：直接按每层份额计算各层金额

    返回：
        [{ layer_index, layer_type, direction, trigger_price, quantity, amount, status }]
    """
    funds = total_funds or instance.total_funds or 0
    grid_funds = getattr(instance, 'grid_funds', None)
    if grid_funds is None:
        grid_funds = funds  # 兼容存量：未设置网格资金时默认等于总资金
    grid_funds = grid_funds or 0
    position_funds = getattr(instance, 'position_funds', None) or 0
    split_mode = getattr(instance, 'split_mode', None) or 'amount'
    layer_shares = getattr(instance, 'layer_shares', None) or {}

    base = instance.base_price
    spacing = instance.grid_spacing
    layers = instance.grid_layers
    ratio = instance.asymmetry_ratio or 1.0
    allocation = instance.fund_allocation or 'equal'
    lot = 100  # 最小交易单位：A股 100 股/手（ETF 100 份/手）

    results = []

    # ===== 底仓记录（不参与网格触发与重置） =====
    if position_funds > 0 and base > 0:
        pos_qty = int(position_funds / base / lot) * lot
        pos_amount = round(pos_qty * base, 2)
        results.append({
            'layer_index': 0,
            'layer_type': 'position',
            'direction': 'buy',
            'trigger_price': base,
            'quantity': pos_qty,
            'amount': pos_amount,
            'status': 'holding',
        })

    # ===== 网格层 =====
    if split_mode == 'shares':
        # 基于份额切分：每层份额由用户指定
        buy_share = int(layer_shares.get('buy') or 0)
        sell_share = int(layer_shares.get('sell') or 0)
    else:
        # 基于金额切分：按资金分配规则切分网格资金
        if allocation == 'equal':
            per_layer_funds = grid_funds / (layers * 2)
        elif allocation == 'pyramid':
            total_weight = sum(layers + 1 - i for i in range(layers))
            per_layer_funds = [grid_funds * (layers - i) / (total_weight * 2) for i in range(layers)]
        else:
            per_layer_funds = grid_funds / (layers * 2)

    for i in range(1, layers + 1):
        # 买入层
        buy_price = round(base * (1 - i * spacing / 100), 4)
        if buy_price <= 0:
            continue

        if split_mode == 'shares':
            buy_qty = buy_share
        elif allocation == 'pyramid':
            buy_funds = per_layer_funds[i - 1]
            buy_qty = int(buy_funds / buy_price / lot) * lot
        else:
            buy_qty = int(per_layer_funds / buy_price / lot) * lot
        buy_amount = round(buy_qty * buy_price, 2)

        results.append({
            'layer_index': i,
            'layer_type': 'grid',
            'direction': 'buy',
            'trigger_price': buy_price,
            'quantity': buy_qty,
            'amount': buy_amount,
            'status': 'pending',
        })

        # 卖出层（间距按不对称比缩放）
        sell_spacing = spacing * ratio
        sell_price = round(base * (1 + i * sell_spacing / 100), 4)

        if split_mode == 'shares':
            sell_qty = sell_share
        else:
            # 金额切分：卖出层与同层买入份额配对（低买高卖同份额），
            # 避免因卖出价更高导致折算份额不足一手而取整为 0
            sell_qty = buy_qty
        sell_amount = round(sell_qty * sell_price, 2)

        results.append({
            'layer_index': i,
            'layer_type': 'grid',
            'direction': 'sell',
            'trigger_price': sell_price,
            'quantity': sell_qty,
            'amount': sell_amount,
            'status': 'pending',
        })

    return results


def generate_and_save_layers(instance: StrategyInstance, db_session) -> List[GridLayer]:
    """
    ????????????
    """
    # ????
    db_session.query(GridLayer).filter(
        GridLayer.instance_id == instance.id
    ).delete()

    layer_data = calculate_layers(instance)
    layers = []
    for data in layer_data:
        layer = GridLayer(
            instance_id=instance.id,
            **data
        )
        db_session.add(layer)
        layers.append(layer)

    db_session.commit()
    for layer in layers:
        db_session.refresh(layer)
    return layers
