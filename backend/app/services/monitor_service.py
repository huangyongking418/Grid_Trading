"""Scheduled monitor service.

Polls market prices, compares them with pending grid layers, writes theoretical
operation logs, marks layers as triggered, creates in-app messages and pushes
configured channels (WeCom / DingTalk webhooks and SMTP email).
"""

import threading
from datetime import datetime
from typing import Dict, List, Tuple

import httpx

from app.core.database import SessionLocal
from app.models.all_models import (
    EmailConfig,
    GridLayer,
    InAppMessage,
    OperationLog,
    PriceSnapshot,
    PushConfig,
    Stock,
    StrategyInstance,
)
from app.services import email_service, market_data

_run_lock = threading.Lock()


def _is_triggered(direction: str, price: float, trigger_price: float) -> bool:
    if direction == "buy":
        return price <= trigger_price
    if direction == "sell":
        return price >= trigger_price
    return False


def _post_webhook(channel: str, webhook_url: str, content: str) -> Tuple[bool, str]:
    try:
        payload = {"msgtype": "text", "text": {"content": content}}
        resp = httpx.post(webhook_url, json=payload, timeout=8.0)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("errcode") not in (None, 0):
            return False, f"{channel}: {data.get('errmsg') or data}"
        return True, ""
    except Exception as exc:  # noqa: BLE001 - push failure must not break the run
        return False, f"{channel}: {exc}"


def push_to_user(db, user_id: int, content: str) -> List[Tuple[str, bool, str]]:
    configs = (
        db.query(PushConfig)
        .filter(PushConfig.user_id == user_id, PushConfig.enabled.is_(True))
        .all()
    )
    results = []
    for config in configs:
        if not config.webhook_url:
            continue
        ok, err = _post_webhook(config.channel, config.webhook_url, content)
        results.append((config.channel, ok, err))
    return results


def push_email_to_user(db, user_id: int, subject: str, content: str) -> Tuple[bool, str]:
    config = db.query(EmailConfig).filter(EmailConfig.user_id == user_id).first()
    if not config or not config.enabled or not config.to_email:
        return False, "email config disabled"
    smtp_cfg = email_service.load_smtp_config(db)
    return email_service.send_email(smtp_cfg, config.to_email, subject, content)


def _run(db) -> dict:
    now = datetime.now()
    instances = (
        db.query(StrategyInstance)
        .filter(
            StrategyInstance.status == "active",
            StrategyInstance.stock_id.isnot(None),
        )
        .all()
    )
    empty_result = {
        "checked_stocks": 0,
        "fetched_stocks": 0,
        "triggered_layers": 0,
        "messages": 0,
        "push_ok": 0,
        "push_failed": 0,
        "push_email_ok": 0,
        "push_email_failed": 0,
        "source": "none",
        "errors": [],
    }
    if not instances:
        return empty_result

    stock_ids = sorted({instance.stock_id for instance in instances})
    stocks = db.query(Stock).filter(Stock.id.in_(stock_ids)).all()
    stock_map = {stock.id: stock for stock in stocks}
    instance_map = {instance.id: instance for instance in instances}

    codes = [stock.code for stock in stocks]
    prices, source = market_data.fetch_prices(codes)
    errors = []
    if not prices:
        errors.append("both quote endpoints unavailable")
        return {**empty_result, "errors": errors}

    for stock in stocks:
        price = prices.get(stock.code)
        if price is None:
            errors.append(f"{stock.code}: no valid quote")
            continue
        stock.current_price = price
        db.add(PriceSnapshot(stock_id=stock.id, price=price, source=source, snapshot_time=now))

    layers = (
        db.query(GridLayer)
        .filter(
            GridLayer.instance_id.in_(list(instance_map)),
            GridLayer.status == "pending",
            GridLayer.layer_type == "grid",
        )
        .all()
    )

    triggered_items: List[Tuple[OperationLog, str]] = []
    triggered_count = 0
    for layer in layers:
        instance = instance_map.get(layer.instance_id)
        if not instance:
            continue
        stock = stock_map.get(instance.stock_id)
        if not stock:
            continue
        price = prices.get(stock.code)
        if price is None:
            continue
        if not _is_triggered(layer.direction, price, layer.trigger_price):
            continue

        layer.status = "triggered"
        op = OperationLog(
            user_id=instance.user_id,
            instance_id=instance.id,
            stock_id=stock.id,
            layer_id=layer.id,
            trigger_price=layer.trigger_price,
            quantity=layer.quantity,
            direction=layer.direction,
            log_type="theoretical",
            operate_time=now,
            note=f"market price {price}",
            push_status=[],
        )
        db.add(op)

        msg_type = "buy_trigger" if layer.direction == "buy" else "sell_trigger"
        title = "买入触发提醒" if layer.direction == "buy" else "卖出触发提醒"
        content = (
            f"{stock.name} {stock.code} 现价 {price}，"
            f"{'买入' if layer.direction == 'buy' else '卖出'}触发价 {layer.trigger_price}，"
            f"建议数量 {layer.quantity}"
        )
        push_content = f"{title}\n{content}"
        db.add(
            InAppMessage(
                user_id=instance.user_id,
                title=title,
                content=content,
                message_type=msg_type,
                related_stock_id=stock.id,
                related_instance_id=instance.id,
            )
        )
        triggered_items.append((op, push_content))
        triggered_count += 1

    db.commit()

    push_ok = 0
    push_failed = 0
    push_email_ok = 0
    push_email_failed = 0
    for op, push_content in triggered_items:
        sent_channels = []
        for channel, ok, err in push_to_user(db, op.user_id, push_content):
            if ok:
                push_ok += 1
                sent_channels.append(channel)
            else:
                push_failed += 1
                errors.append(err)
        ok, err = push_email_to_user(db, op.user_id, "网格交易触发提醒", push_content)
        if ok:
            push_ok += 1
            push_email_ok += 1
            sent_channels.append("email")
        else:
            push_failed += 1
            push_email_failed += 1
            if "email config disabled" not in str(err):
                errors.append(f"email: {err}")
        op.push_status = sent_channels
    db.commit()

    fetched_stocks = sum(1 for stock in stocks if prices.get(stock.code) is not None)
    return {
        "checked_stocks": len(stocks),
        "fetched_stocks": fetched_stocks,
        "triggered_layers": triggered_count,
        "messages": triggered_count,
        "push_ok": push_ok,
        "push_failed": push_failed,
        "push_email_ok": push_email_ok,
        "push_email_failed": push_email_failed,
        "source": source,
        "errors": errors,
    }


def run_monitor_once() -> dict:
    """Run one monitor pass. Returns immediately if another pass is running."""
    if not _run_lock.acquire(blocking=False):
        return {"skipped": True, "reason": "monitor already running"}
    db = SessionLocal()
    try:
        return _run(db)
    finally:
        db.close()
        _run_lock.release()
