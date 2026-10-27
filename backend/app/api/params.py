from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.all_models import SystemParam
from app.api.users import require_admin


router = APIRouter(prefix="/api/params", tags=["系统参数"])


class ParamCreate(BaseModel):
    param_key: str
    param_value: str
    description: Optional[str] = None


class ParamUpdate(BaseModel):
    param_value: str
    description: Optional[str] = None


@router.get("")
def list_params(db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    params = db.query(SystemParam).all()
    return [
        {
            "id": p.id,
            "param_key": p.param_key,
            "param_value": p.param_value,
            "description": p.description,
        }
        for p in params
    ]


@router.post("", status_code=201)
def create_param(data: ParamCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    if db.query(SystemParam).filter(SystemParam.param_key == data.param_key).first():
        raise HTTPException(status_code=400, detail="参数已存在")
    p = SystemParam(param_key=data.param_key, param_value=data.param_value, description=data.description)
    db.add(p)
    db.commit()
    return {"id": p.id, "message": "参数创建成功"}


@router.put("/{param_id}")
def update_param(param_id: int, data: ParamUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    p = db.query(SystemParam).filter(SystemParam.id == param_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="参数不存在")
    p.param_value = data.param_value
    if data.description is not None:
        p.description = data.description
    db.commit()
    return {"id": p.id, "message": "参数已更新"}
