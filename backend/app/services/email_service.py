"""Email notification service via SMTP.

The SMTP sender is a system-level configuration stored in SystemParam;
recipients are per-user values stored in EmailConfig.
"""

import smtplib
import socket
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Dict, Optional, Tuple

from app.models.all_models import SystemParam

SMTP_KEYS = {
    "host": "email_smtp_host",
    "port": "email_smtp_port",
    "user": "email_smtp_user",
    "password": "email_smtp_password",
    "from_email": "email_from_email",
    "enabled": "email_enabled",
}


def load_smtp_config(db) -> Dict[str, str]:
    """Load the system-level SMTP sender configuration."""
    params = {p.param_key: p.param_value for p in db.query(SystemParam).all()}
    return {
        "host": (params.get(SMTP_KEYS["host"], "") or "").strip(),
        "port": params.get(SMTP_KEYS["port"], "465"),
        "user": (params.get(SMTP_KEYS["user"], "") or "").strip(),
        "password": params.get(SMTP_KEYS["password"], "") or "",
        "from_email": (params.get(SMTP_KEYS["from_email"], "") or "").strip(),
        "enabled": str(params.get(SMTP_KEYS["enabled"], "0")).lower()
        in ("1", "true", "yes", "on"),
    }


def save_smtp_config(db, config: Dict) -> None:
    """Persist the system-level SMTP sender configuration."""
    values = {
        "host": (config.get("smtp_host", "") or "").strip(),
        "port": str(config.get("smtp_port", 465)),
        "user": (config.get("smtp_user", "") or "").strip(),
        "password": config.get("smtp_password", "") or "",
        "from_email": (config.get("from_email", "") or "").strip(),
        "enabled": "1" if config.get("enabled") else "0",
    }
    for key, value in values.items():
        param_key = SMTP_KEYS[key]
        row = db.query(SystemParam).filter(SystemParam.param_key == param_key).first()
        if row:
            row.param_value = value
        else:
            db.add(
                SystemParam(
                    param_key=param_key,
                    param_value=value,
                    description="email smtp setting",
                )
            )


def _open_connection(cfg: Dict[str, str]):
    port = int(cfg.get("port") or 465)
    if port == 465:
        return smtplib.SMTP_SSL(cfg["host"], port, timeout=15)
    connection = smtplib.SMTP(cfg["host"], port, timeout=15)
    connection.ehlo()
    if port == 587:
        connection.starttls()
        connection.ehlo()
    return connection


def _friendly_error(exc: Exception) -> str:
    """Translate common SMTP errors into readable Chinese messages."""
    message = str(exc)
    lowered = message.lower()
    if isinstance(exc, socket.gaierror) or "getaddrinfo failed" in lowered:
        return "无法解析 SMTP 服务器地址，请检查服务器地址"
    if isinstance(exc, TimeoutError) or "timed out" in lowered:
        return "连接 SMTP 服务器超时，请检查网络或服务器"
    if isinstance(exc, ConnectionRefusedError) or "connection refused" in lowered:
        return "无法连接 SMTP 服务器，请检查地址和端口"
    if isinstance(exc, smtplib.SMTPAuthenticationError):
        return "SMTP 登录失败，请检查账号和授权码"
    if isinstance(exc, smtplib.SMTPConnectError):
        return "SMTP 连接失败，请检查服务器和端口"
    if isinstance(exc, smtplib.SMTPException):
        return f"SMTP 发送失败：{message}"
    return message


def send_email(
    cfg: Dict[str, str],
    to_email: str,
    subject: str,
    content: str,
    require_enabled: bool = True,
) -> Tuple[bool, Optional[str]]:
    """Send one plain-text email. Returns (ok, error_message)."""
    if not cfg:
        return False, "未配置邮箱发件服务器"
    if require_enabled and not cfg.get("enabled"):
        return False, "发件服务器未启用"
    if not cfg.get("host") or not cfg.get("user") or not cfg.get("password"):
        return False, "SMTP 配置不完整"
    if not to_email:
        return False, "收件人邮箱为空"

    try:
        msg = MIMEText(content, "plain", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        sender = cfg.get("from_email") or cfg["user"]
        msg["From"] = formataddr((str(Header(sender, "utf-8")), sender))
        recipients = [item.strip() for item in to_email.split(",") if item.strip()]
        msg["To"] = ", ".join(recipients)

        connection = _open_connection(cfg)
        try:
            connection.login(cfg["user"], cfg["password"])
            connection.sendmail(sender, recipients, msg.as_string())
        finally:
            try:
                connection.quit()
            except Exception:
                pass
        return True, None
    except Exception as exc:  # noqa: BLE001 - report the SMTP error to the caller
        return False, _friendly_error(exc)
