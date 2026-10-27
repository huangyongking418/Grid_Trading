from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.all_models import SystemParam


router = APIRouter(prefix="/api/config", tags=["系统配置"])


FOOTER_DEFAULTS = [
    ("footer_copyright", "版权信息", "Copyright © 2026 网格交易系统"),
    ("footer_icp", "备案号", ""),
    ("footer_support", "技术支持", ""),
    ("footer_version", "版本信息", "v2.12"),
]


@router.get("/footer")
def get_footer_config(db: Session = Depends(get_db)):
    """登录页页脚配置：读取 footer_ 开头的系统参数，缺失时写入默认值。"""
    existing = {
        p.param_key: p
        for p in db.query(SystemParam)
        .filter(SystemParam.param_key.like("footer_%"))
        .all()
    }

    # 兼容旧键 footer_text：迁移为 footer_copyright，保留已维护的值
    legacy = existing.pop("footer_text", None)
    if legacy and "footer_copyright" not in existing:
        migrated = SystemParam(
            param_key="footer_copyright",
            param_value=legacy.param_value,
            description="版权信息",
        )
        db.add(migrated)
        db.delete(legacy)
        db.commit()
        db.refresh(migrated)
        existing["footer_copyright"] = migrated

    for key, label, default in FOOTER_DEFAULTS:
        if key not in existing:
            param = SystemParam(param_key=key, param_value=default, description=label)
            db.add(param)
            db.commit()
            db.refresh(param)
            existing[key] = param

    items = []
    for key, label, _ in FOOTER_DEFAULTS:
        param = existing[key]
        value = (param.param_value or "").strip()
        if not value:
            continue
        items.append({"key": key, "label": label, "value": value})
    return {"items": items}
