import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.all_models import Announcement
from app.api.users import require_admin


router = APIRouter(prefix="/api/announcements", tags=["公告"])

ANNOUNCEMENT_IMG_DIR = (
    Path(__file__).resolve().parent.parent.parent / "uploads" / "announcements"
)
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


class AnnouncementCreate(BaseModel):
    title: str
    content: Optional[str] = None
    image_url: Optional[str] = None
    image_name: Optional[str] = None


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None
    image_name: Optional[str] = None


@router.get("")
def list_announcements(db: Session = Depends(get_db), current=Depends(get_current_user)):
    """所有登录用户可查看启用的公告"""
    if hasattr(current, "role") and current.role and any(
        p.function_code == "system_manage" for p in current.role.permissions
    ):
        items = db.query(Announcement).order_by(Announcement.create_time.desc()).all()
    else:
        items = db.query(Announcement).filter(
            Announcement.status == "enabled"
        ).order_by(Announcement.create_time.desc()).all()
    return [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "image_url": a.image_url,
            "image_name": a.image_name,
            "status": a.status,
            "create_time": a.create_time,
        }
        for a in items
    ]


@router.post("", status_code=201)
def create_announcement(data: AnnouncementCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    a = Announcement(
        title=data.title,
        content=data.content,
        image_url=data.image_url,
        image_name=data.image_name,
        status="enabled",
    )
    db.add(a)
    db.commit()
    return {"id": a.id, "message": "公告已发布"}


@router.put("/{ann_id}")
def update_announcement(ann_id: int, data: AnnouncementUpdate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    require_admin(current)
    a = db.query(Announcement).filter(Announcement.id == ann_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="公告不存在")
    if data.title is not None:
        a.title = data.title
    if data.content is not None:
        a.content = data.content
    if data.status is not None:
        a.status = data.status
    if data.image_url is not None:
        a.image_url = data.image_url
    if data.image_name is not None:
        a.image_name = data.image_name
    db.commit()
    return {"id": a.id, "message": "公告已更新"}


@router.post("/upload-image", status_code=201)
async def upload_announcement_image(
    file: UploadFile = File(...),
    current=Depends(get_current_user),
):
    """管理员上传公告图片，保存到 uploads/announcements，返回访问 URL。"""
    require_admin(current)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="仅支持 JPG / PNG / WebP 图片")
    data = await file.read()
    if len(data) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 5MB")
    ANNOUNCEMENT_IMG_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (ANNOUNCEMENT_IMG_DIR / filename).write_bytes(data)
    return {"url": f"/uploads/announcements/{filename}"}
