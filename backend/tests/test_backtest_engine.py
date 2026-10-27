import unittest
from datetime import datetime

from app.services.backtest_engine import calc_fee, run_backtest


def make_strategy(**overrides):
    base = {
        "stock_type": "stock",
        "grid_spacing": 1.0,
        "grid_layers": 2,
        "asymmetry_ratio": 1.0,
        "base_price": 10.0,
        "stop_loss_strategy": "none",
        "fund_allocation": "equal",
        "total_funds": 20000.0,
        "grid_funds": 20000.0,
        "position_funds": 0.0,
        "split_mode": "amount",
        "layer_shares": None,
        "reset_cycle_days": 0,
    }
    base.update(overrides)
    return base


def kline(time_str, open_, high, low, close):
    return {
        "trade_time": datetime.fromisoformat(time_str),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
    }


class FeeTest(unittest.TestCase):
    def test_stock_buy_sell_fee(self):
        buy_fee = calc_fee(10000, "buy", "stock")
        sell_fee = calc_fee(10000, "sell", "stock")
        self.assertEqual(buy_fee, 5.1)   # 佣金最低5 + 过户费0.1
        self.assertEqual(sell_fee, 15.1)  # 加印花税10

    def test_etf_no_stamp_tax(self):
        self.assertEqual(calc_fee(10000, "sell", "etf"), 5.1)


class MatchingTest(unittest.TestCase):
    def test_buy_sell_pairs_completed(self):
        klines = [
            kline("2026-07-01T10:30", 10.0, 10.1, 9.8, 10.0),
            kline("2026-07-01T11:30", 10.0, 10.3, 9.9, 10.2),
        ]
        result = run_backtest(make_strategy(), klines)
        metrics = result["metrics"]
        self.assertEqual(metrics["buy_count"], 2)
        self.assertEqual(metrics["sell_count"], 2)
        self.assertEqual(metrics["total_trade_count"], 4)
        self.assertEqual(metrics["win_rate"], 100.0)
        self.assertGreater(result["final_asset"], result["initial_asset"])

    def test_cash_insufficient_skip(self):
        strategy = make_strategy(
            split_mode="shares",
            layer_shares={"buy": 10000, "sell": 10000},
            grid_funds=110000.0,
            total_funds=110000.0,
            grid_layers=2,
        )
        klines = [kline("2026-07-01T10:30", 10.0, 9.9, 9.5, 9.6)]
        result = run_backtest(strategy, klines)
        skip_trades = [t for t in result["trades"] if t["quantity"] == 0]
        self.assertEqual(len(skip_trades), 1)
        self.assertIn("现金不足", skip_trades[0]["note"])
        self.assertEqual(result["metrics"]["skip_count"], 1)

    def test_end_position_valued_at_last_close(self):
        strategy = make_strategy(grid_layers=1, grid_funds=20000.0, total_funds=20000.0)
        klines = [
            kline("2026-07-01T10:30", 10.0, 9.9, 9.9, 9.5),
            kline("2026-07-01T11:30", 9.6, 9.6, 9.4, 9.7),
        ]
        result = run_backtest(strategy, klines)
        trades = [t for t in result["trades"] if t["direction"] == "buy" and t["quantity"] > 0]
        self.assertEqual(len(trades), 1)
        qty = trades[0]["quantity"]
        cash_after = trades[0]["cash_after"]
        expected = round(cash_after + qty * 9.7, 2)
        self.assertEqual(result["final_asset"], expected)


if __name__ == "__main__":
    unittest.main()
