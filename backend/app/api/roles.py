from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, has_permission
from app.models.all_models import Role, RolePermission
from app.api.users import require_admin


router = APIRouter(prefix="/api/roles", tags=["角色管理"])


class PermissionIn(BaseModel):
    function_code: str
    data_scope: str = "self"


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[PermissionIn] = []


class RoleUpdate(BaseModel):
    description: Optional[str] = None
    permissions: List[PermissionIn] = []


@router.get("")
def list_roles(db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    roles = db.query(Role).all()
    result = []
    for r in roles:
        result.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_preset": r.is_preset,
            "permissions": [
                {"function_code": p.function_code, "data_scope": p.data_scope}
                for p in r.permissions
            ],
        })
    return result


@router.post("", status_code=201)
def create_role(data: RoleCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    if db.query(Role).filter(Role.name == data.name).first():
        raise HTTPException(status_code=400, detail="角色已存在")
    role = Role(name=data.name, description=data.description, is_preset=False)
    db.add(role)
    db.flush()
    for p in data.permissions:
        db.add(RolePermission(role_id=role.id, function_code=p.function_code, data_scope=p.data_scope))
    db.commit()
    return {"id": role.id, "message": "角色创建成功"}


@router.put("/{role_id}/permissions")
def update_permissions(
    role_id: int, data: RoleUpdate,
    db: Session = Depends(get_db), current=Depends(get_current_user),
):
    require_admin(current)
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    if data.description is not None:
        role.description = data.description
    permissions = data.permissions
    # 管理员角色的系统管理权限不可移除，始终保留
    if role.is_preset and role.name == "管理员":
        permissions = [p for p in permissions if p.function_code != "system_manage"]
        permissions.append(PermissionIn(function_code="system_manage", data_scope="all"))
    # 删除旧权限，写入新权限
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    for p in permissions:
        db.add(RolePermission(role_id=role_id, function_code=p.function_code, data_scope=p.data_scope))
    db.commit()
    return {"message": "角色已更新"}
