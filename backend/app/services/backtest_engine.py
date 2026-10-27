"""回测撮合与绩效计算：纯逻辑模块，可独立单元测试。"""

import math
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List

from app.models.all_models import StrategyInstance
from app.services.grid_engine import calculate_layers


DEFAULT_FEE_CONFIG: Dict[str, float] = {
    "commission_rate": 0.00025,   # 佣金万 2.5
    "min_commission": 5.0,        # 最低 5 元
    "stamp_tax_rate": 0.001,      # 卖出印花税千 1（ETF 免征）
    "transfer_fee_rate": 0.00001, # 过户费万 0.1
    "slippage": 0.0,              # 滑点，默认 0
}

_ANNUAL_FACTOR = 240 * 4  # A股约 240 个交易日/年，每交易日 4 根 60 分钟K线


def strategy_to_snapshot(strategy) -> Dict[str, Any]:
    """把模拟策略 ORM 对象转成回测参数快照（供会话快照与网格生成共用）。"""
    return {
        "stock_code": strategy.stock_code,
        "stock_name": strategy.stock_name,
        "stock_type": strategy.stock_type,
        "grid_spacing": strategy.grid_spacing,
        "grid_layers": strategy.grid_layers,
        "asymmetry_ratio": strategy.asymmetry_ratio,
        "base_price": strategy.base_price,
        "stop_loss_strategy": strategy.stop_loss_strategy,
        "fund_allocation": strategy.fund_allocation,
        "total_funds": strategy.total_funds,
        "grid_funds": strategy.grid_funds,
        "position_funds": strategy.position_funds,
        "split_mode": strategy.split_mode,
        "layer_shares": strategy.layer_shares,
        "reset_cycle_days": strategy.reset_cycle_days,
    }


def calc_fee(
    amount: float,
    direction: str,
    stock_type: str,
    fee_config: Dict[str, float] | None = None,
) -> float:
    """按费用配置计算单笔手续费（佣金 + 过户费，卖出另加印花税）。"""
    cfg = {**DEFAULT_FEE_CONFIG, **(fee_config or {})}
    commission = max(amount * cfg["commission_rate"], cfg["min_commission"])
    transfer = amount * cfg["transfer_fee_rate"]
    stamp = 0.0
    if direction == "sell" and stock_type != "etf":
        stamp = amount * cfg["stamp_tax_rate"]
    return round(commission + transfer + stamp, 2)


def build_grid_layers(strategy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """复用正式策略的网格计算规则，生成回测网格层（不落正式库）。"""
    instance = StrategyInstance(
        grid_spacing=strategy["grid_spacing"],
        grid_layers=strategy["grid_layers"],
        asymmetry_ratio=strategy.get("asymmetry_ratio") or 1.0,
        base_price=strategy["base_price"],
        stop_loss_strategy=strategy.get("stop_loss_strategy") or "none",
        fund_allocation=strategy.get("fund_allocation") or "equal",
        total_funds=strategy.get("total_funds") or 0,
        grid_funds=(
            strategy.get("grid_funds")
            if strategy.get("grid_funds") is not None
            else strategy.get("total_funds") or 0
        ),
        position_funds=strategy.get("position_funds") or 0,
        split_mode=strategy.get("split_mode") or "amount",
        layer_shares=strategy.get("layer_shares"),
    )
    return calculate_layers(instance)


def _exec_price(trigger_price: float, direction: str, slippage: float) -> float:
    if direction == "buy":
        return trigger_price * (1 + slippage)
    return trigger_price * (1 - slippage)


def run_backtest(
    strategy: Dict[str, Any],
    klines: List[Dict[str, Any]],
    fee_config: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """按 60 分钟K线逐根撮合，返回成交记录、网格状态、资产曲线与绩效指标。"""
    if not klines:
        raise ValueError("没有可用的历史K线，无法执行回测")

    cfg = {**DEFAULT_FEE_CONFIG, **(fee_config or {})}
    slippage = float(cfg.get("slippage") or 0)
    stock_type = strategy.get("stock_type") or "stock"
    layers = build_grid_layers(strategy)

    position_qty = 0
    position_amount = 0.0
    grid_buy_layers: Dict[int, Dict[str, Any]] = {}
    grid_sell_layers: Dict[int, Dict[str, Any]] = {}
    for layer in layers:
        if layer["layer_type"] == "position":
            position_qty = int(layer["quantity"] or 0)
            position_amount = float(layer["amount"] or 0)
        elif layer["direction"] == "buy":
            grid_buy_layers[int(layer["layer_index"])] = layer
        else:
            grid_sell_layers[int(layer["layer_index"])] = layer

    position_fee = calc_fee(position_amount, "buy", stock_type, cfg) if position_amount > 0 else 0.0
    cash = float(strategy.get("grid_funds") or 0) + max(0.0, float(strategy.get("position_funds") or 0) - position_amount) - position_fee
    initial_asset = cash + position_qty * float(strategy["base_price"])

    grid_holdings: Dict[int, int] = {}
    trades: List[Dict[str, Any]] = []
    equity_points: List[Dict[str, Any]] = []
    completed_pairs: List[Dict[str, float]] = []
    total_fee = position_fee
    buy_count = 0
    sell_count = 0
    skip_count = 0

    first_open = float(klines[0]["open"])
    benchmark_qty = float(strategy.get("total_funds") or 0) / first_open if first_open > 0 else 0.0

    def snapshot_asset(close_price: float) -> float:
        grid_qty = sum(grid_holdings.values())
        return cash + (position_qty + grid_qty) * close_price

    for kline in klines:
        trade_time = kline["trade_time"]
        low = float(kline["low"])
        high = float(kline["high"])
        close = float(kline["close"])

        # 先评估买入（先低后高）
        for idx in sorted(grid_buy_layers):
            layer = grid_buy_layers[idx]
            if layer["status"] != "pending" or low > layer["trigger_price"]:
                continue
            buy_price = _exec_price(layer["trigger_price"], "buy", slippage)
            amount = round(layer["quantity"] * buy_price, 2)
            fee = calc_fee(amount, "buy", stock_type, cfg)
            if cash >= amount + fee:
                cash -= amount + fee
                grid_holdings[idx] = grid_holdings.get(idx, 0) + layer["quantity"]
                layer["status"] = "bought"
                layer["_fee"] = fee
                total_fee += fee
                buy_count += 1
                trades.append(
                    {
                        "layer_index": idx,
                        "direction": "buy",
                        "trade_time": trade_time,
                        "trigger_price": round(buy_price, 4),
                        "quantity": layer["quantity"],
                        "amount": amount,
                        "fee": fee,
                        "cash_after": round(cash, 2),
                        "note": "",
                    }
                )
            else:
                skip_count += 1
                trades.append(
                    {
                        "layer_index": idx,
                        "direction": "buy",
                        "trade_time": trade_time,
                        "trigger_price": round(buy_price, 4),
                        "quantity": 0,
                        "amount": 0,
                        "fee": 0,
                        "cash_after": round(cash, 2),
                        "note": "现金不足，跳过买入",
                    }
                )

        # 再评估卖出
        for idx in sorted(grid_buy_layers):
            buy_layer = grid_buy_layers[idx]
            if buy_layer["status"] != "bought":
                continue
            sell_layer = grid_sell_layers.get(idx)
            if not sell_layer or high < sell_layer["trigger_price"]:
                continue
            sell_price = _exec_price(sell_layer["trigger_price"], "sell", slippage)
            qty = buy_layer["quantity"]
            amount = round(qty * sell_price, 2)
            fee = calc_fee(amount, "sell", stock_type, cfg)
            cash += amount - fee
            grid_holdings[idx] -= qty
            buy_layer["status"] = "sold"
            sell_layer["status"] = "sold"
            total_fee += fee
            sell_count += 1
            trades.append(
                {
                    "layer_index": idx,
                    "direction": "sell",
                    "trade_time": trade_time,
                    "trigger_price": round(sell_price, 4),
                    "quantity": qty,
                    "amount": amount,
                    "fee": fee,
                    "cash_after": round(cash, 2),
                    "note": "",
                }
            )
            completed_pairs.append(
                {
                    "buy_amount": buy_layer["amount"],
                    "buy_fee": buy_layer["_fee"],
                    "sell_amount": amount,
                    "sell_fee": fee,
                }
            )

        equity_points.append(
            {
                "time": trade_time.isoformat(timespec="minutes"),
                "asset": round(snapshot_asset(close), 2),
                "benchmark_asset": round(benchmark_qty * close, 2),
            }
        )

    final_asset = equity_points[-1]["asset"]
    total_return = (final_asset / initial_asset - 1) * 100 if initial_asset > 0 else 0.0
    benchmark_return = (
        (benchmark_qty * klines[-1]["close"] / (strategy.get("total_funds") or 1) - 1) * 100
        if benchmark_qty and (strategy.get("total_funds") or 0) > 0
        else 0.0
    )

    metrics = compute_metrics(
        equity_points=equity_points,
        completed_pairs=completed_pairs,
        total_return=total_return,
        benchmark_return=benchmark_return,
        total_fee=total_fee,
        buy_count=buy_count,
        sell_count=sell_count,
        skip_count=skip_count,
        final_asset=final_asset,
    )

    return {
        "layers": layers,
        "trades": trades,
        "equity_points": equity_points,
        "drawdown_points": metrics["drawdown_points"],
        "metrics": metrics,
        "initial_asset": round(initial_asset, 2),
        "final_asset": round(final_asset, 2),
        "total_fee": round(total_fee, 2),
        "skip_count": skip_count,
    }


def compute_metrics(
    equity_points: List[Dict[str, Any]],
    completed_pairs: List[Dict[str, float]],
    total_return: float,
    benchmark_return: float,
    total_fee: float,
    buy_count: int,
    sell_count: int,
    skip_count: int,
    final_asset: float,
) -> Dict[str, Any]:
    """计算绩效指标；收益率/回撤/胜率以百分比存储，夏普不带单位。"""
    assets = [p["asset"] for p in equity_points]
    initial_asset = assets[0] if assets else 0

    # 最大回撤与回撤曲线
    peak = -math.inf
    max_drawdown = 0.0
    drawdown_points: List[Dict[str, Any]] = []
    for p in equity_points:
        peak = max(peak, p["asset"])
        dd = (p["asset"] - peak) / peak if peak > 0 else 0.0
        drawdown_points.append({"time": p["time"], "drawdown": round(dd * 100, 2)})
        max_drawdown = min(max_drawdown, dd)

    # 年化：按自然日
    annual_return = 0.0
    if len(equity_points) >= 2:
        try:
            t0 = datetime.fromisoformat(equity_points[0]["time"])
            t1 = datetime.fromisoformat(equity_points[-1]["time"])
            days = max((t1 - t0).total_seconds() / 86400, 1)
            if total_return > -100:
                annual_return = ((1 + total_return / 100) ** (365 / days) - 1) * 100
        except ValueError:
            annual_return = 0.0

    # 夏普：按K线收益率年化
    sharpe = 0.0
    returns = [
        (assets[i] / assets[i - 1] - 1)
        for i in range(1, len(assets))
        if assets[i - 1] > 0
    ]
    if len(returns) >= 2:
        mu = mean(returns)
        sigma = math.sqrt(sum((r - mu) ** 2 for r in returns) / (len(returns) - 1))
        if sigma > 0:
            sharpe = round(mu / sigma * math.sqrt(_ANNUAL_FACTOR), 2)

    # 胜率与盈亏比：按完成买卖配对
    pair_profits = []
    for pair in completed_pairs:
        profit = (
            pair["sell_amount"]
            - pair["buy_amount"]
            - pair["buy_fee"]
            - pair["sell_fee"]
        )
        pair_profits.append(profit)
    wins = [p for p in pair_profits if p > 0]
    losses = [p for p in pair_profits if p <= 0]
    win_rate = len(wins) / len(pair_profits) * 100 if pair_profits else 0.0
    profit_loss_ratio = 0.0
    if wins and losses:
        avg_win = sum(wins) / len(wins)
        avg_loss = abs(sum(losses) / len(losses))
        profit_loss_ratio = round(avg_win / avg_loss, 2) if avg_loss > 0 else 0.0

    return {
        "total_return_rate": round(total_return, 2),
        "annual_return_rate": round(annual_return, 2),
        "max_drawdown": round(abs(max_drawdown) * 100, 2),
        "sharpe_ratio": sharpe,
        "win_rate": round(win_rate, 2),
        "profit_loss_ratio": profit_loss_ratio,
        "total_trade_count": buy_count + sell_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "skip_count": skip_count,
        "total_fee": round(total_fee, 2),
        "final_asset": round(final_asset, 2),
        "benchmark_return_rate": round(benchmark_return, 2),
        "excess_return": round(total_return - benchmark_return, 2),
        "drawdown_points": drawdown_points,
    }
