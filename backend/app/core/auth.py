import hashlib
import hmac
import base64
import json
import time
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.all_models import User


SECRET_KEY = settings.jwt_secret or secrets.token_urlsafe(48)
TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7天
PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 260_000
LEGACY_PASSWORD_SALT = b"gts_salt"
LEGACY_PASSWORD_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PASSWORD_ITERATIONS,
    ).hex()
    return f"{PASSWORD_SCHEME}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(f"{PASSWORD_SCHEME}$"):
        try:
            _, iterations_text, salt, expected = password_hash.split("$", 3)
            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode(),
                salt.encode(),
                int(iterations_text),
            ).hex()
            return hmac.compare_digest(digest, expected)
        except (TypeError, ValueError):
            return False

    # 兼容旧版本固定盐值的密码哈希；用户下次修改密码后会自动升级。
    legacy_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        LEGACY_PASSWORD_SALT,
        LEGACY_PASSWORD_ITERATIONS,
    ).hex()
    return hmac.compare_digest(legacy_digest, password_hash)


def create_token(user_id: int, username: str) -> str:
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(time.time()) + TOKEN_EXPIRE_SECONDS,
    }
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    signing_input = f"{header}.{body}"
    signature = base64.urlsafe_b64encode(
        hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    ).rstrip(b"=").decode()
    return f"{signing_input}.{signature}"


def decode_token(token: str) -> Optional[dict]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header, body, signature = parts
        signing_input = f"{header}.{body}"
        expected = base64.urlsafe_b64encode(
            hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        ).rstrip(b"=").decode()
        if not hmac.compare_digest(expected, signature):
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """从 Authorization Bearer token 解析当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已停用")
    if user.expire_date and user.expire_date.timestamp() < time.time():
        raise HTTPException(status_code=403, detail="账号已过期")
    return user


def has_permission(user: User, function_code: str) -> bool:
    """检查用户角色是否拥有功能权限"""
    if not user.role:
        return False
    return any(
        p.function_code == function_code
        for p in user.role.permissions
    )


def can_view_all(user: User) -> bool:
    """检查用户数据权限是否为全部"""
    if not user.role:
        return False
    return any(p.data_scope == "all" for p in user.role.permissions)
