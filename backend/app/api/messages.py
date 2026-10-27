from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, can_view_all
from app.models.all_models import InAppMessage


router = APIRouter(prefix="/api/messages", tags=["站内消息"])


class MessageCreate(BaseModel):
    title: str
    content: Optional[str] = None
    message_type: str
    related_stock_id: Optional[int] = None
    related_instance_id: Optional[int] = None


class MessageOut(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    message_type: str
    related_stock_id: Optional[int] = None
    related_instance_id: Optional[int] = None
    is_read: bool
    create_time: datetime
    model_config = {"from_attributes": True}


@router.get("", response_model=List[MessageOut])
def list_messages(db: Session = Depends(get_db), current=Depends(get_current_user)):
    q = db.query(InAppMessage)
    if not can_view_all(current):
        q = q.filter(InAppMessage.user_id == current.id)
    return q.order_by(InAppMessage.create_time.desc()).all()


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db), current=Depends(get_current_user)):
    count = db.query(InAppMessage).filter(InAppMessage.is_read == False, InAppMessage.user_id == current.id).count()
    return {"count": count}


@router.put("/{message_id}/read", response_model=MessageOut)
def mark_read(message_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    msg = db.query(InAppMessage).filter(InAppMessage.id == message_id, InAppMessage.user_id == current.id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    msg.is_read = True
    db.commit()
    db.refresh(msg)
    return msg


@router.put("/read-all")
def mark_all_read(db: Session = Depends(get_db), current=Depends(get_current_user)):
    db.query(InAppMessage).filter(InAppMessage.is_read == False, InAppMessage.user_id == current.id).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.post("", response_model=MessageOut, status_code=201)
def create_message(data: MessageCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    msg = InAppMessage(**data.model_dump(), user_id=current.id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
