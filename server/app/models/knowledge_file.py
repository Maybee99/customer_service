 from sqlalchemy import Column, BigInteger, String, Text, Enum, Integer, TIMESTAMP
 from sqlalchemy.sql import func
 from app.models.database import Base
 class KnowledgeFile(Base):
     __tablename__ = "knowledge_files"
     id = Column(BigInteger, primary_key=True, autoincrement=True)
     original_filename = Column(String(500), nullable=False)
     file_type = Column(String(20), nullable=False)
     file_hash = Column(String(64), nullable=False, unique=True)
     file_size = Column(BigInteger, nullable=False)
     parse_mode = Column(Enum("chunk", "qa"), nullable=False)
     chunk_count = Column(Integer, default=0)
     image_count = Column(Integer, default=0)
     status = Column(Enum("uploading", "processing", "ready", "failed"), default="uploading")
     error_message = Column(Text, nullable=True)
     created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
     updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
