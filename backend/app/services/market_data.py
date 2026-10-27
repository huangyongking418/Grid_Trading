"""Market data service with a primary and a backup free quote source.

Primary: Tencent (qt.gtimg.cn)
Backup:  Sina (hq.sinajs.cn)

Both endpoints are free HTTP interfaces. The caller first tries the primary
source and automatically falls back to the backup source on failure.
"""

import re
import threading
from datetime import datetime
from typing import Dict, List, Tuple

import httpx

TENCENT_URL = "https://qt.gtimg.cn/q="
SINA_URL = "https://hq.sinajs.cn/list="
TIMEOUT_SECONDS = 8.0
USER_AGENT = "Mozilla/5.0"

_SINA_HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": "https://finance.sina.com.cn",
}

_state_lock = threading.Lock()
_state = {
    "active_source": "tencent",
    "last_error": None,
    "last_switch_at": None,
    "last_success_at": None,
}


def get_state() -> dict:
    """Return a copy of the current source state for status display."""
    with _state_lock:
        return dict(_state)


def _exchange_prefix(code: str) -> str:
    code = str(code).strip()
    if code.startswith(("6", "5", "9")):
        return "sh"
    if code.startswith(("0", "1", "2", "3")):
        return "sz"
    if code.startswith(("4", "8")):
        return "bj"
    return ""


def _symbols(codes: List[str]) -> List[str]:
    return [f"{_exchange_prefix(code)}{code}" for code in codes if _exchange_prefix(code)]


def _parse_tencent(text: str, wanted: set) -> Dict[str, float]:
    prices = {}
    for match in re.finditer(r'v_(\w+)="([^"]*)"', text):
        symbol = match.group(1)
        parts = match.group(2).split("~")
        if len(parts) < 4:
            continue
        code = symbol[2:]
        if code not in wanted:
            continue
        try:
            price = float(parts[3])
        except (TypeError, ValueError):
            continue
        if price > 0:
            prices[code] = price
    return prices


def _parse_sina(text: str, wanted: set) -> Dict[str, float]:
    prices = {}
    for match in re.finditer(r'hq_str_(\w+)="([^"]*)"', text):
        symbol = match.group(1)
        parts = match.group(2).split(",")
        if len(parts) < 4:
            continue
        code = symbol[2:]
        if code not in wanted:
            continue
        try:
            price = float(parts[3])
        except (TypeError, ValueError):
            continue
        if price > 0:
            prices[code] = price
    return prices


def _fetch_tencent(codes: List[str]) -> Dict[str, float]:
    symbols = ",".join(_symbols(codes))
    if not symbols:
        return {}
    resp = httpx.get(
        TENCENT_URL + symbols,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    )
    resp.raise_for_status()
    text = resp.content.decode("gbk", errors="ignore")
    return _parse_tencent(text, set(codes))


def _fetch_sina(codes: List[str]) -> Dict[str, float]:
    symbols = ",".join(_symbols(codes))
    if not symbols:
        return {}
    resp = httpx.get(SINA_URL + symbols, timeout=TIMEOUT_SECONDS, headers=_SINA_HEADERS)
    resp.raise_for_status()
    text = resp.content.decode("gbk", errors="ignore")
    return _parse_sina(text, set(codes))


def _mark_success(source: str) -> None:
    with _state_lock:
        _state["active_source"] = source
        _state["last_error"] = None
        _state["last_success_at"] = datetime.now().isoformat(timespec="seconds")


def fetch_prices(codes: List[str]) -> Tuple[Dict[str, float], str]:
    """Fetch prices for A-share / ETF codes.

    Returns (prices, source). source is "tencent", "sina" or "none". Unknown or
    suspended codes are simply skipped; a zero price is treated as invalid.
    """
    codes = [str(code).strip() for code in codes if str(code).strip()]
    if not codes:
        return {}, "none"

    errors = []
    try:
        prices = _fetch_tencent(codes)
        if prices:
            _mark_success("tencent")
            return prices, "tencent"
        errors.append("tencent: no valid quote")
    except Exception as exc:  # noqa: BLE001 - fall back to backup source
        errors.append(f"tencent: {exc}")

    try:
        prices = _fetch_sina(codes)
        if prices:
            with _state_lock:
                previous = _state["active_source"]
                if previous != "sina":
                    _state["last_switch_at"] = datetime.now().isoformat(timespec="seconds")
            _mark_success("sina")
            return prices, "sina"
        errors.append("sina: no valid quote")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"sina: {exc}")

    with _state_lock:
        _state["last_error"] = " | ".join(errors)
    return {}, "none"
