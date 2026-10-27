from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, has_permission, hash_password
from app.models.all_models import User, Role, SystemParam


router = APIRouter(prefix="/api/users", tags=["用户管理"])


class UserCreate(BaseModel):
    username: str
    password: str
    phone: str
    role_id: int
    expire_days: Optional[int] = None


class UserUpdate(BaseModel):
    phone: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[str] = None
    expire_days: Optional[int] = None


def require_admin(user: User):
    if not has_permission(user, "system_manage"):
        raise HTTPException(status_code=403, detail="无权限访问系统管理")


@router.get("")
def list_users(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    require_admin(current)
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "phone": u.phone,
            "role_id": u.role_id,
            "role_name": u.role.name if u.role else None,
            "status": u.status,
            "expire_date": u.expire_date,
            "create_time": u.create_time,
        }
        for u in users
    ]


@router.post("", status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    require_admin(current)
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="账号已存在")
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    param = db.query(SystemParam).filter(SystemParam.param_key == "account_expire_days").first()
    expire_days = data.expire_days if data.expire_days else (int(param.param_value) if param else 5)
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        phone=data.phone,
        role_id=data.role_id,
        status="active",
        expire_date=datetime.now() + timedelta(days=expire_days),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "message": "创建成功"}


@router.put("/{user_id}")
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    require_admin(current)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if data.phone is not None:
        user.phone = data.phone
    if data.role_id is not None:
        user.role_id = data.role_id
    if data.status is not None:
        user.status = data.status
    if data.expire_days is not None:
        user.expire_date = datetime.now() + timedelta(days=data.expire_days)
    db.commit()
    return {"id": user.id, "message": "更新成功"}
