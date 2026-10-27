from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.database import get_db
from app.api.users import require_admin
from app.services import scheduler_manager

router = APIRouter(prefix="/api/scheduler", tags=["定时任务"])


class SchedulerConfigIn(BaseModel):
    enabled: bool
    interval_minutes: int


@router.get("/status")
def get_scheduler_status(current=Depends(get_current_user)):
    require_admin(current)
    return scheduler_manager.get_status()


@router.put("/config")
def update_scheduler_config(
    data: SchedulerConfigIn,
    db=Depends(get_db),
    current=Depends(get_current_user),
):
    require_admin(current)
    return scheduler_manager.update_config(db, data.enabled, data.interval_minutes)


@router.post("/run")
def run_scheduler_now(current=Depends(get_current_user)):
    require_admin(current)
    result = scheduler_manager.run_now()
    return {"result": result, "status": scheduler_manager.get_status()}
