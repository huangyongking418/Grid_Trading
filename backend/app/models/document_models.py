from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.core.database import Base


class SystemDocument(Base):
    """操作手册等文档表：存储元数据与本地文件路径。"""

    __tablename__ = "system_document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, default=1, index=True, comment="上传人ID")
    title = Column(String(128), nullable=False, comment="文档标题")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_path = Column(String(512), nullable=False, comment="本地存储路径")
    file_ext = Column(String(16), nullable=False, comment="扩展名")
    file_size = Column(Integer, nullable=False, default=0, comment="文件大小（字节）")
    category = Column(String(32), default="操作手册", nullable=False, comment="分类：操作手册/说明文档/其他")
    description = Column(String(500), nullable=True, comment="文档说明")
    status = Column(String(16), default="enabled", nullable=False, comment="enabled/disabled")
    create_time = Column(DateTime, default=datetime.now, nullable=False)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
