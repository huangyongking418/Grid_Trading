from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import (
    hash_password, verify_password, create_token,
    get_current_user, has_permission,
)
from app.models.all_models import User, Role, SystemParam
from app.schemas.auth import RegisterIn, LoginIn, LoginOut, UserOut, ChangePasswordIn


router = APIRouter(prefix="/api/auth", tags=["认证"])


def user_to_out(user: User) -> UserOut:
    """将 User 模型转换为 UserOut，填充角色名称"""
    out = UserOut.model_validate(user)
    out.role_name = user.role.name if user.role else None
    return out


@router.post("/register", response_model=LoginOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    """注册：默认普通用户，有效期按系统参数"""
    # 校验用户名和手机号唯一
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="账号已存在")
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="手机号已注册")

    # 获取普通用户角色
    user_role = db.query(Role).filter(Role.name == "普通用户").first()
    if not user_role:
        raise HTTPException(status_code=500, detail="系统未初始化普通用户角色")

    # 获取账号有效期参数
    param = db.query(SystemParam).filter(SystemParam.param_key == "account_expire_days").first()
    expire_days = int(param.param_value) if param else 5

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        phone=data.phone,
        role_id=user_role.id,
        status="active",
        expire_date=datetime.now() + timedelta(days=expire_days),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.username)
    return LoginOut(token=token, user=user_to_out(user))


@router.post("/login", response_model=LoginOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    """登录并返回 Token"""
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已停用")
    if user.expire_date and user.expire_date.timestamp() < datetime.now().timestamp():
        raise HTTPException(status_code=403, detail="账号已过期")

    token = create_token(user.id, user.username)
    return LoginOut(token=token, user=user_to_out(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return user_to_out(current_user)


@router.post("/change-password")
def change_password(
    data: ChangePasswordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改当前登录用户密码：校验原密码，更新哈希，提示重新登录。"""
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于 6 位")
    if data.new_password == data.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "密码修改成功，请重新登录"}
