import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.auth import get_current_user, has_permission
from app.core.database import get_db
from app.models.all_models import User
from app.models.document_models import SystemDocument
from app.api.users import require_admin


router = APIRouter(prefix="/api/documents", tags=["文档管理"])

DOC_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "documents"
ALLOWED_DOC_EXTS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".jpg", ".jpeg", ".png", ".webp",
}
MAX_DOC_SIZE = 20 * 1024 * 1024


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


def _doc_out(doc: SystemDocument, uploader: Optional[str] = None) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "file_name": doc.file_name,
        "file_ext": doc.file_ext,
        "file_size": doc.file_size,
        "category": doc.category,
        "description": doc.description,
        "status": doc.status,
        "uploader": uploader,
        "create_time": doc.create_time,
        "update_time": doc.update_time,
    }


@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    category: str = Form("操作手册"),
    description: str = Form(""),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """管理员上传操作手册等文档。"""
    require_admin(current)
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_DOC_EXTS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    data = await file.read()
    if len(data) > MAX_DOC_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")
    final_title = title.strip() or (file.filename or "未命名文档")
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    (DOC_DIR / stored_name).write_bytes(data)
    doc = SystemDocument(
        user_id=current.id,
        title=final_title[:128],
        file_name=file.filename or stored_name,
        file_path=str(DOC_DIR / stored_name),
        file_ext=ext.lstrip(".").lower(),
        file_size=len(data),
        category=category.strip() or "操作手册",
        description=description.strip(),
        status="enabled",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _doc_out(doc, current.username)


@router.get("")
def list_documents(
    enabled_only: bool = Query(False),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """管理员查看全部；普通用户仅查看启用文档；enabled_only=true 时只返回启用文档。"""
    is_admin = has_permission(current, "system_manage")
    if not is_admin and not has_permission(current, "document_view"):
        raise HTTPException(status_code=403, detail="无权限访问操作手册")
    q = db.query(SystemDocument)
    if enabled_only or not is_admin:
        q = q.filter(SystemDocument.status == "enabled")
    docs = q.order_by(SystemDocument.create_time.desc()).all()
    user_map = {u.id: u.username for u in db.query(User).all()}
    return [_doc_out(d, user_map.get(d.user_id)) for d in docs]


@router.put("/{doc_id}")
def update_document(
    doc_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """管理员编辑文档标题/分类/说明/状态。"""
    require_admin(current)
    doc = db.query(SystemDocument).filter(SystemDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    for key, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(doc, key, value)
    db.commit()
    db.refresh(doc)
    return _doc_out(doc)


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """管理员删除文档记录与物理文件。"""
    require_admin(current)
    doc = db.query(SystemDocument).filter(SystemDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    path = Path(doc.file_path)
    if path.exists() and path.is_file():
        path.unlink()
    db.delete(doc)
    db.commit()
    return None


@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """登录用户鉴权下载；普通用户仅可下载启用文档。"""
    is_admin = has_permission(current, "system_manage")
    if not is_admin and not has_permission(current, "document_view"):
        raise HTTPException(status_code=403, detail="无权限访问操作手册")
    doc = db.query(SystemDocument).filter(SystemDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if not is_admin and doc.status != "enabled":
        raise HTTPException(status_code=404, detail="文档不存在")
    path = Path(doc.file_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="文档文件不存在")
    return FileResponse(
        path,
        filename=doc.file_name,
        media_type="application/octet-stream",
    )
