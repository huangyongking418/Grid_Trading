"""基准价周期重置检查与提醒服务。"""

from datetime import datetime, timedelta
from typing import List, Optional

from app.models.all_models import InAppMessage, ResetLog, StrategyInstance
from app.services.monitor_service import push_email_to_user, push_to_user


def check_expired_instances(
    db,
    instances: List[StrategyInstance],
    now: Optional[datetime] = None,
) -> List[dict]:
    """检查策略是否到达重置周期；到期则重置基准价、写日志、发站内消息并推送。"""
    now = now or datetime.now()
    results = []
    for inst in instances:
        if inst.last_reset_time:
            next_reset = inst.last_reset_time + timedelta(days=inst.reset_cycle_days)
        else:
            next_reset = inst.create_time + timedelta(days=inst.reset_cycle_days)
        if now < next_reset:
            continue

        old_price = inst.base_price
        inst.last_reset_time = now
        db.add(
            ResetLog(
                instance_id=inst.id,
                old_base_price=old_price,
                new_base_price=inst.base_price,
                reset_reason="periodic_reset",
            )
        )

        content = f"策略 {inst.name or inst.id} 基准价已从 {old_price} 重置为 {inst.base_price}"
        db.add(
            InAppMessage(
                user_id=inst.user_id,
                title="基准价重置提醒",
                content=content,
                message_type="reset_expiry",
                related_instance_id=inst.id,
            )
        )

        push_content = f"基准价重置提醒\n{content}"
        sent_channels = []
        for channel, ok, _err in push_to_user(db, inst.user_id, push_content):
            if ok:
                sent_channels.append(channel)
        ok, _err = push_email_to_user(db, inst.user_id, "网格交易基准价重置提醒", push_content)
        if ok:
            sent_channels.append("email")

        results.append(
            {
                "instance_id": inst.id,
                "old_base_price": old_price,
                "new_base_price": inst.base_price,
                "status": "reset",
                "push_channels": sent_channels,
            }
        )
    db.commit()
    return results


def check_all_expired(db, now: Optional[datetime] = None) -> dict:
    """定时任务使用：检查所有启用且配置了重置周期的策略。"""
    instances = (
        db.query(StrategyInstance)
        .filter(
            StrategyInstance.status == "active",
            StrategyInstance.reset_cycle_days > 0,
        )
        .all()
    )
    results = check_expired_instances(db, instances, now=now)
    return {"reset_count": len(results), "results": results}
