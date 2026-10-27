import unittest
from datetime import date
from unittest import mock

import httpx

from app.services.backtest_data import _fetch_tencent_fallback


class TencentFallbackTest(unittest.TestCase):
    def _sample_payload(self):
        return {
            "code": 0,
            "msg": "",
            "data": {
                "sh600519": {
                    "m60": [
                        ["202608061400", "1308.78", "1307.34", "1311.76", "1305.26", "3906.25", {}, "3.1248"],
                        ["202608061500", "1307.42", "1308.55", "1314.00", "1307.07", "5430.40", {}, "4.3440"],
                        ["202608071030", "1308.66", "1303.49", "1315.19", "1301.00", "10138.79", {}, "8.1105"],
                    ]
                }
            },
        }

    def test_parse_rows_and_filter_by_date(self):
        request = httpx.Request("GET", "https://example.com/kline")
        response = httpx.Response(200, json=self._sample_payload(), request=request)
        with mock.patch("app.services.backtest_data.httpx.get", return_value=response) as mocked:
            rows = _fetch_tencent_fallback(
                "600519",
                "stock",
                date(2026, 8, 6),
                date(2026, 8, 6),
                period="60",
            )
        mocked.assert_called_once()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["trade_time"].isoformat(), "2026-08-06T14:00:00")
        self.assertEqual(rows[1]["close"], 1308.55)
        # 腾讯成交量为手，成交额按 手 * 100 * 收盘价 换算为元。
        self.assertEqual(rows[0]["amount"], round(3906.25 * 100 * 1307.34, 2))


if __name__ == "__main__":
    unittest.main()
