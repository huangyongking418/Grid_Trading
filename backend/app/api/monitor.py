from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user, can_view_all
from app.models.all_models import PushConfig, OperationLog, EmailConfig
from app.api.users import require_admin
from app.services import email_service
from pydantic import BaseModel
from datetime import datetime


class PushConfigOut(BaseModel):
    id: int
    channel: str
    webhook_url: Optional[str] = None
    enabled: bool
    create_time: datetime
    update_time: datetime
    model_config = {"from_attributes": True}


class PushConfigUpdate(BaseModel):
    webhook_url: Optional[str] = None
    enabled: Optional[bool] = None


class MonitorLogOut(BaseModel):
    id: int
    stock_id: Optional[int] = None
    stock_code: Optional[str] = None
    stock_name: Optional[str] = None
    push_status: Optional[List[str]] = None
    trigger_price: float
    direction: str
    log_type: str
    create_time: datetime
    model_config = {"from_attributes": True}


class EmailConfigOut(BaseModel):
    id: Optional[int] = None
    to_email: str = ""
    enabled: bool = False


class EmailConfigIn(BaseModel):
    to_email: str = ""
    enabled: bool = False


class SmtpConfigOut(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    has_password: bool = False
    from_email: str = ""
    enabled: bool = False


class SmtpConfigIn(BaseModel):
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    enabled: bool = False


class EmailTestIn(BaseModel):
    to_email: Optional[str] = None


def _email_config_out(config: Optional[EmailConfig]) -> EmailConfigOut:
    if not config:
        return EmailConfigOut()
    return EmailConfigOut(
        id=config.id,
        to_email=config.to_email,
        enabled=config.enabled,
    )


def _smtp_config_out(cfg: dict) -> SmtpConfigOut:
    return SmtpConfigOut(
        smtp_host=cfg.get("host", ""),
        smtp_port=int(cfg.get("port") or 465),
        smtp_user=cfg.get("user", ""),
        has_password=bool(cfg.get("password")),
        from_email=cfg.get("from_email", ""),
        enabled=bool(cfg.get("enabled")),
    )


router = APIRouter(prefix="/api/monitor", tags=["??"])


@router.get("/push-config", response_model=List[PushConfigOut])
def list_push_configs(db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(PushConfig)
    if not can_view_all(current):
        q = q.filter(PushConfig.user_id == current.id)
    return q.all()


@router.put("/push-config/{channel}", response_model=PushConfigOut)
def update_push_config(channel: str, data: PushConfigUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    config = db.query(PushConfig).filter(PushConfig.channel == channel, PushConfig.user_id == current.id).first()
    if not config:
        config = PushConfig(channel=channel, enabled=False, user_id=current.id)
        db.add(config)
    if data.webhook_url is not None:
        config.webhook_url = data.webhook_url
    if data.enabled is not None:
        config.enabled = data.enabled
    db.commit()
    db.refresh(config)
    return config


@router.get("/smtp-config", response_model=SmtpConfigOut)
def get_smtp_config(db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    return _smtp_config_out(email_service.load_smtp_config(db))


@router.put("/smtp-config", response_model=SmtpConfigOut)
def update_smtp_config(
    data: SmtpConfigIn,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    require_admin(current)
    cfg = email_service.load_smtp_config(db)
    if not data.smtp_password:
        data.smtp_password = cfg.get("password", "")
    email_service.save_smtp_config(db, data.model_dump())
    db.commit()
    return _smtp_config_out(email_service.load_smtp_config(db))


@router.get("/email-config", response_model=EmailConfigOut)
def get_email_config(db: Session = Depends(get_db), current=Depends(get_current_user)):
    config = db.query(EmailConfig).filter(EmailConfig.user_id == current.id).first()
    return _email_config_out(config)


@router.put("/email-config", response_model=EmailConfigOut)
def update_email_config(
    data: EmailConfigIn,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    config = db.query(EmailConfig).filter(EmailConfig.user_id == current.id).first()
    if not config:
        config = EmailConfig(user_id=current.id)
        db.add(config)
    config.to_email = data.to_email
    config.enabled = data.enabled
    db.commit()
    db.refresh(config)
    return _email_config_out(config)


@router.post("/email-test")
def test_email_config(
    data: Optional[EmailTestIn] = None,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    config = db.query(EmailConfig).filter(EmailConfig.user_id == current.id).first()
    to_email = ""
    if data and data.to_email:
        to_email = data.to_email
    elif config:
        to_email = config.to_email
    if not to_email:
        return {"ok": False, "error": "请先填写测试收件人或配置收件人邮箱"}
    smtp_cfg = email_service.load_smtp_config(db)
    ok, err = email_service.send_email(
        smtp_cfg,
        to_email,
        "网格交易系统测试邮件",
        "这是一封测试邮件，邮箱配置正常。",
        require_enabled=False,
    )
    return {"ok": ok, "error": err}


@router.get("/logs", response_model=List[MonitorLogOut])
def list_monitor_logs(db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(OperationLog).filter(OperationLog.log_type == 'theoretical')
    if not can_view_all(current):
        q = q.filter(OperationLog.user_id == current.id)
    logs = q.order_by(OperationLog.create_time.desc()).limit(50).all()
    result = []
    for log in logs:
        result.append(
            MonitorLogOut(
                id=log.id,
                stock_id=log.stock_id,
                stock_code=log.stock.code if log.stock else None,
                stock_name=log.stock.name if log.stock else None,
                push_status=log.push_status or [],
                trigger_price=log.trigger_price,
                direction=log.direction,
                log_type=log.log_type,
                create_time=log.create_time,
            )
        )
    return result
