"""APScheduler lifecycle and status management for the market monitor job."""

import threading
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.database import SessionLocal
from app.models.all_models import SystemParam
from app.services import market_data, monitor_service, reset_service

JOB_ID = "market_monitor"
PARAM_ENABLED = "scheduler_enabled"
PARAM_INTERVAL = "scheduler_interval_minutes"
DEFAULT_ENABLED = True
DEFAULT_INTERVAL_MINUTES = 15

_scheduler = BackgroundScheduler()
_config_lock = threading.Lock()
_state = {
    "enabled": DEFAULT_ENABLED,
    "interval_minutes": DEFAULT_INTERVAL_MINUTES,
    "started_at": None,
    "last_run_at": None,
    "last_result": None,
    "last_error": None,
    "running_now": False,
}


def _iso(value) -> str:
    return value.isoformat(timespec="seconds") if value else None


def _read_param(db, key: str, default: str) -> str:
    row = db.query(SystemParam).filter(SystemParam.param_key == key).first()
    return row.param_value if row else default


def _write_param(db, key: str, value: str) -> None:
    row = db.query(SystemParam).filter(SystemParam.param_key == key).first()
    if row:
        row.param_value = value
    else:
        db.add(SystemParam(param_key=key, param_value=value, description="scheduler setting"))


def _load_config(db) -> None:
    enabled_raw = _read_param(db, PARAM_ENABLED, "1")
    interval_raw = _read_param(db, PARAM_INTERVAL, str(DEFAULT_INTERVAL_MINUTES))
    _state["enabled"] = str(enabled_raw).strip().lower() in ("1", "true", "yes", "on")
    try:
        _state["interval_minutes"] = max(1, int(float(interval_raw)))
    except (TypeError, ValueError):
        _state["interval_minutes"] = DEFAULT_INTERVAL_MINUTES


def _run_all() -> dict:
    """执行行情监控与基准价重置检查，返回合并后的执行结果。"""
    result = monitor_service.run_monitor_once()
    reset_result = {}
    db = SessionLocal()
    try:
        reset_result = reset_service.check_all_expired(db)
    finally:
        db.close()
    if isinstance(result, dict):
        return {**result, "reset_count": reset_result.get("reset_count", 0)}
    return result


def _tick() -> None:
    _state["running_now"] = True
    try:
        result = _run_all()
        _state["last_run_at"] = datetime.now()
        _state["last_result"] = result
        _state["last_error"] = None
    except Exception as exc:  # noqa: BLE001 - keep scheduler alive
        _state["last_error"] = str(exc)
    finally:
        _state["running_now"] = False


def _schedule_job() -> None:
    interval = _state["interval_minutes"]
    job = _scheduler.get_job(JOB_ID)
    if job:
        _scheduler.reschedule_job(JOB_ID, trigger="interval", minutes=interval)
    else:
        _scheduler.add_job(
            _tick,
            "interval",
            minutes=interval,
            id=JOB_ID,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60,
        )


def start(db) -> None:
    """Load persisted settings, schedule the job and start the scheduler."""
    with _config_lock:
        _load_config(db)
        if _state["enabled"]:
            _schedule_job()
        if not _scheduler.running:
            _scheduler.start()
        _state["started_at"] = datetime.now()


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


def get_status() -> dict:
    job = _scheduler.get_job(JOB_ID)
    return {
        "running": _scheduler.running,
        "enabled": _state["enabled"],
        "interval_minutes": _state["interval_minutes"],
        "next_run_time": _iso(job.next_run_time) if job and job.next_run_time else None,
        "last_run_at": _iso(_state["last_run_at"]),
        "last_result": _state["last_result"],
        "last_error": _state["last_error"],
        "running_now": _state["running_now"],
        "started_at": _iso(_state["started_at"]),
        "market_source": market_data.get_state(),
    }


def update_config(db, enabled: bool, interval_minutes: int) -> dict:
    """Persist scheduler settings and apply them to the running scheduler."""
    with _config_lock:
        _state["enabled"] = bool(enabled)
        _state["interval_minutes"] = max(1, int(interval_minutes))
        _write_param(db, PARAM_ENABLED, "1" if _state["enabled"] else "0")
        _write_param(db, PARAM_INTERVAL, str(_state["interval_minutes"]))
        db.commit()
        if not _scheduler.running:
            _scheduler.start()
        job = _scheduler.get_job(JOB_ID)
        if _state["enabled"]:
            _schedule_job()
        elif job:
            _scheduler.remove_job(JOB_ID)
    return get_status()


def run_now() -> dict:
    """Trigger one monitor pass immediately and update the status state."""
    _state["running_now"] = True
    try:
        result = _run_all()
        _state["last_run_at"] = datetime.now()
        _state["last_result"] = result
        _state["last_error"] = None
        return result
    except Exception as exc:  # noqa: BLE001
        _state["last_error"] = str(exc)
        return {"error": str(exc)}
    finally:
        _state["running_now"] = False
