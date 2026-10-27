"""历史行情获取与缓存：akshare 主源 + 东方财富备用域名 + 腾讯 + 新浪降级。

优先使用 akshare 东方财富 60 分钟前复权接口；若主域名不可达，
依次尝试东方财富备用域名（同源前复权）、新浪 60 分钟接口
（约 1 年、未复权）与腾讯 60 分钟接口（约 10 个月、未复权），
并把实际数据源与口径写回回测会话。
"""

import json
import logging
import time
from datetime import date, datetime, time as dtime
from typing import Any, Dict, List, Tuple

import httpx
from sqlalchemy.orm import Session

from app.models.backtest_models import BacktestKline


logger = logging.getLogger(__name__)


_COLUMN_MAP = {
    "时间": "trade_time",
    "开盘": "open",
    "收盘": "close",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
}

_EASTMONEY_HOSTS = [
    "1.push2his.eastmoney.com",
    "5.push2his.eastmoney.com",
    "10.push2his.eastmoney.com",
    "20.push2his.eastmoney.com",
    "30.push2his.eastmoney.com",
]

# 腾讯行情历史 K 线接口，优先保留可用的公开域名。
_TENCENT_URLS = [
    "https://web.ifzq.gtimg.cn/appstock/app/kline/mkline",
    "https://web3.ifzq.gtimg.cn/appstock/app/kline/mkline",
    "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/kline/mkline",
]

_HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Referer": "https://quote.eastmoney.com/",
}


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, dtime(0, 0))
    if isinstance(value, str) and len(value) == 12 and value.isdigit():
        # 腾讯分钟 K 线时间格式，如 202608071400
        return datetime.strptime(value, "%Y%m%d%H%M")
    return datetime.fromisoformat(str(value).replace("/", "-"))


def _normalize_rows(df: Any, stock_type: str) -> List[Dict[str, Any]]:
    """把 akshare 分钟K线 DataFrame 转成统一字段的 dict 列表。"""
    rows: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        item: Dict[str, Any] = {}
        for col in df.columns:
            key = _COLUMN_MAP.get(str(col))
            if key:
                item[key] = row[col]
        if "trade_time" not in item:
            raise ValueError("行情数据缺少时间列")
        try:
            item["trade_time"] = _parse_datetime(item["trade_time"])
            item["open"] = float(item.get("open") or 0)
            item["high"] = float(item.get("high") or 0)
            item["low"] = float(item.get("low") or 0)
            item["close"] = float(item.get("close") or 0)
            item["volume"] = float(item.get("volume") or 0)
            item["amount"] = float(item.get("amount") or 0)
        except (TypeError, ValueError):
            continue
        if item["close"] > 0:
            item["stock_type"] = stock_type
            rows.append(item)
    return rows


def _fetch_akshare(
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
    adjust: str = "qfq",
) -> List[Dict[str, Any]]:
    import akshare as ak  # 延迟导入，避免后端启动变慢

    symbol = str(stock_code).strip()
    start_text = f"{start_date.isoformat()} 09:30:00"
    end_text = f"{end_date.isoformat()} 15:00:00"
    if stock_type == "etf":
        df = ak.fund_etf_hist_min_em(
            symbol=symbol,
            period=period,
            adjust=adjust,
            start_date=start_text,
            end_date=end_text,
        )
    else:
        df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            adjust=adjust,
            start_date=start_text,
            end_date=end_text,
        )
    rows = _normalize_rows(df, stock_type)
    if not rows:
        raise ValueError("akshare 返回空数据")
    return rows


def _secid(stock_code: str, stock_type: str) -> str:
    code = str(stock_code).strip()
    market = "1" if code.startswith(("6", "5", "9")) else "0"
    return f"{market}.{code}"


def _fetch_eastmoney_direct(
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
    adjust: str = "qfq",
) -> List[Dict[str, Any]]:
    """东方财富备用域名直连：与 akshare 同源，支持 60 分钟前复权历史区间。"""
    klt = {"15": "15", "30": "30", "60": "60"}.get(str(period), "60")
    fqt = "1" if adjust == "qfq" else "0"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57",
        "klt": klt,
        "fqt": fqt,
        "secid": _secid(stock_code, stock_type),
        "beg": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "lmt": 100000,
    }
    errors = []
    for host in _EASTMONEY_HOSTS[:3]:
        try:
            resp = httpx.get(
                f"https://{host}/api/qt/stock/kline/get",
                params=params,
                timeout=6,
                headers=_HTTP_HEADERS,
            )
            resp.raise_for_status()
            data = (resp.json().get("data") or {})
            klines = data.get("klines") or []
            rows: List[Dict[str, Any]] = []
            for line in klines:
                parts = str(line).split(",")
                if len(parts) < 7:
                    continue
                rows.append(
                    {
                        "trade_time": _parse_datetime(parts[0]),
                        "open": float(parts[1]),
                        "close": float(parts[2]),
                        "high": float(parts[3]),
                        "low": float(parts[4]),
                        "volume": float(parts[5] or 0),
                        "amount": float(parts[6] or 0),
                        "stock_type": stock_type,
                    }
                )
            rows = [
                r
                for r in rows
                if datetime.combine(start_date, dtime(0, 0))
                <= r["trade_time"]
                <= datetime.combine(end_date, dtime(23, 59, 59))
            ]
            if rows:
                return rows
            errors.append(f"{host}: no data")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{host}: {exc}")
        time.sleep(1)
    raise ValueError("东方财富备用域名获取失败：" + " | ".join(errors))


def _fetch_tencent_fallback(
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
    adjust: str = "qfq",
) -> List[Dict[str, Any]]:
    """腾讯 60 分钟历史行情：约 10 个月、未复权，作为最后兜底。"""
    scale = {"15": "15", "30": "30", "60": "60"}.get(str(period), "60")
    symbol = _sina_symbol(stock_code)
    param = f"{symbol},m{scale},,800"
    start_dt = datetime.combine(start_date, dtime(0, 0))
    end_dt = datetime.combine(end_date, dtime(23, 59, 59))
    errors: List[str] = []
    for url in _TENCENT_URLS:
        try:
            resp = httpx.get(
                url,
                params={"param": param},
                timeout=8,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://gu.qq.com/",
                },
            )
            resp.raise_for_status()
            node = (resp.json().get("data") or {}).get(symbol) or {}
            klines = node.get(f"m{scale}") or []
            if not klines:
                errors.append(f"{url}: empty")
                continue
            rows: List[Dict[str, Any]] = []
            for parts in klines:
                if not isinstance(parts, list) or len(parts) < 6:
                    continue
                try:
                    trade_time = _parse_datetime(parts[0])
                    open_price = float(parts[1])
                    close = float(parts[2])
                    high = float(parts[3])
                    low = float(parts[4])
                    volume = float(parts[5] or 0)
                except (TypeError, ValueError):
                    continue
                if trade_time < start_dt or trade_time > end_dt or close <= 0:
                    continue
                rows.append(
                    {
                        "trade_time": trade_time,
                        "open": open_price,
                        "high": high,
                        "low": low,
                        "close": close,
                        # 腾讯成交量为手，成交额按 手 * 100 * 收盘价 换算为元。
                        "volume": volume,
                        "amount": round(volume * 100 * close, 2),
                        "stock_type": stock_type,
                    }
                )
            if rows:
                return sorted(rows, key=lambda r: r["trade_time"])
            errors.append(f"{url}: no data in range")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{url}: {exc}")
    raise ValueError("腾讯分钟行情获取失败：" + " | ".join(errors))


def _sina_symbol(stock_code: str) -> str:
    code = str(stock_code).strip()
    if code.startswith(("6", "5", "9")):
        return f"sh{code}"
    return f"sz{code}"


def _fetch_sina_fallback(
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
) -> List[Dict[str, Any]]:
    """新浪 60 分钟接口：约 1 年、未前复权，作为东财之后的优先降级源。"""
    scale = {"15": "15", "30": "30", "60": "60"}.get(str(period), "60")
    url = (
        "https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20_=/CN_MarketDataService.getKLineData"
        f"?symbol={_sina_symbol(stock_code)}&scale={scale}&ma=no&datalen=1023"
    )
    resp = httpx.get(
        url,
        timeout=12,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"},
    )
    resp.raise_for_status()
    text = resp.text
    start = text.find("[")
    end = text.rfind("]")
    if start < 0 or end <= start:
        raise ValueError("新浪行情接口返回格式异常")
    items = json.loads(text[start : end + 1])
    rows: List[Dict[str, Any]] = []
    start_dt = datetime.combine(start_date, dtime(0, 0))
    end_dt = datetime.combine(end_date, dtime(23, 59, 59))
    for item in items:
        trade_time = _parse_datetime(item.get("day"))
        if trade_time < start_dt or trade_time > end_dt:
            continue
        try:
            close = float(item.get("close") or 0)
            rows.append(
                {
                    "trade_time": trade_time,
                    "open": float(item.get("open") or 0),
                    "high": float(item.get("high") or 0),
                    "low": float(item.get("low") or 0),
                    "close": close,
                    "volume": float(item.get("volume") or 0),
                    "amount": float(item.get("amount") or 0),
                    "stock_type": stock_type,
                }
            )
        except (TypeError, ValueError):
            continue
    if not rows:
        raise ValueError(
            "新浪降级数据未覆盖所选区间（仅约最近 1 年），请调整回测日期或恢复东方财富接口"
        )
    return sorted(rows, key=lambda r: r["trade_time"])


def fetch_minute_kline_with_fallback(
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
    adjust: str = "qfq",
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """按 akshare、东财备用域名、新浪、腾讯的顺序获取，返回 (rows, 数据源说明)。"""
    try:
        rows = _fetch_akshare(stock_code, stock_type, start_date, end_date, period, adjust)
        return rows, {"source": "akshare", "adjust": adjust, "note": ""}
    except Exception as ak_exc:  # noqa: BLE001
        logger.warning("akshare 历史行情获取失败: %s", ak_exc)

    try:
        rows = _fetch_eastmoney_direct(stock_code, stock_type, start_date, end_date, period, adjust)
        return rows, {
            "source": "eastmoney_direct",
            "adjust": adjust,
            "note": "akshare 主域名不可达，已切换东方财富备用域名（同源，前复权）",
        }
    except Exception as em_exc:  # noqa: BLE001
        logger.warning("东方财富备用域名历史行情获取失败: %s", em_exc)

    try:
        rows = _fetch_sina_fallback(stock_code, stock_type, start_date, end_date, period)
        return rows, {
            "source": "sina_m60_fallback",
            "adjust": "none",
            "note": "东方财富历史行情接口不可达，已降级为新浪 60 分钟数据（未前复权，仅约 1 年）",
        }
    except Exception as sx_exc:  # noqa: BLE001
        logger.warning("新浪历史行情获取失败: %s", sx_exc)

    try:
        rows = _fetch_tencent_fallback(stock_code, stock_type, start_date, end_date, period, adjust)
        return rows, {
            "source": "tencent_m60_fallback",
            "adjust": "none",
            "note": "akshare、东方财富与新浪历史行情不可达，已切换腾讯 60 分钟数据（未复权，约 10 个月）",
        }
    except Exception as tx_exc:  # noqa: BLE001
        logger.warning("腾讯历史行情获取失败: %s", tx_exc)
        raise ValueError(
            "历史行情获取失败：akshare 东方财富接口不可达，东财备用域名、新浪与腾讯降级均失败："
            f"{tx_exc}"
        ) from tx_exc


def get_kline_with_meta(
    db: Session,
    stock_code: str,
    stock_type: str,
    start_date: date,
    end_date: date,
    period: str = "60",
    adjust: str = "qfq",
) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    """优先读取缓存，缓存缺失时按降级顺序拉取并保存到 backtest_kline。"""
    start_dt = datetime.combine(start_date, dtime(0, 0))
    end_dt = datetime.combine(end_date, dtime(23, 59, 59))

    cached = (
        db.query(BacktestKline)
        .filter(
            BacktestKline.stock_code == stock_code,
            BacktestKline.period == period,
            BacktestKline.adjust == adjust,
            BacktestKline.trade_time >= start_dt,
            BacktestKline.trade_time <= end_dt,
        )
        .order_by(BacktestKline.trade_time.asc())
        .all()
    )
    if cached:
        source = cached[0].source or "cache"
        note = ""
        if source != "akshare":
            note = f"行情来源：{source}；复权口径：{cached[0].adjust}"
        return (
            [
                {
                    "trade_time": k.trade_time,
                    "open": k.open,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                    "amount": k.amount,
                    "stock_type": k.stock_type,
                }
                for k in cached
            ],
            {"source": source, "adjust": cached[0].adjust, "note": note},
        )

    rows, meta = fetch_minute_kline_with_fallback(
        stock_code, stock_type, start_date, end_date, period, adjust
    )
    existing = {
        k.trade_time
        for k in db.query(BacktestKline.trade_time).filter(
            BacktestKline.stock_code == stock_code,
            BacktestKline.period == period,
            BacktestKline.adjust == meta["adjust"],
        ).all()
    }
    for row in rows:
        if row["trade_time"] in existing:
            continue
        db.add(
            BacktestKline(
                stock_code=stock_code,
                stock_type=stock_type,
                period=period,
                adjust=meta["adjust"],
                trade_time=row["trade_time"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row.get("volume"),
                amount=row.get("amount"),
                source=meta["source"],
            )
        )
    db.commit()
    return rows, meta


def clear_kline_cache(
    db: Session,
    stock_code: str,
    period: str = "60",
    adjust: str = "qfq",
) -> int:
    """删除指定标的的行情缓存，用于手动刷新。返回删除条数。"""
    deleted = (
        db.query(BacktestKline)
        .filter(
            BacktestKline.stock_code == stock_code,
            BacktestKline.period == period,
            BacktestKline.adjust == adjust,
        )
        .delete()
    )
    db.commit()
    return deleted
