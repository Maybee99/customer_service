"""
Knowledge image metadata — stores per-page image info for image-heavy PDFs.
One row per rendered page image, linked to its source KnowledgeFile.
"""

from sqlalchemy import Column, BigInteger, String, Integer, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from ..models.database import Base


class KnowledgeImage(Base):
    __tablename__ = "knowledge_images"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(
        BigInteger,
        ForeignKey("knowledge_files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_hash = Column(String(64), nullable=False, index=True)
    page_num = Column(Integer, nullable=False)
    image_path = Column(String(500), nullable=False)     # full URL
    image_filename = Column(String(255), nullable=False)  # bare filename for serving
    step_label = Column(String(255), nullable=True)       # e.g. "第一步：登录系统"
    description = Column(Text, nullable=True)             # Qwen-VL raw description
    created_at = Column(TIMESTAMP, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "file_hash": self.file_hash,
            "page_num": self.page_num,
            "image_path": self.image_path,
            "image_filename": self.image_filename,
            "step_label": self.step_label,
            "description": self.description,
        }
