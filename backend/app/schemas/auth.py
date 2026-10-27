from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RegisterIn(BaseModel):
    username: str
    password: str
    phone: str


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str


class UserOut(BaseModel):
    id: int
    username: str
    phone: str
    role_id: int
    status: str
    expire_date: datetime
    create_time: datetime
    role_name: Optional[str] = None

    model_config = {"from_attributes": True}


class LoginOut(BaseModel):
    token: str
    user: UserOut
