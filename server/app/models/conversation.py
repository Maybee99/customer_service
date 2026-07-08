from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..models.database import Base
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    user_name = Column(String(255), nullable=True)
    channel = Column(String(50), default="web")
    status = Column(Enum("active", "closed"), default="active", index=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    def to_dict(self, with_messages=False):
        first_msg = self.messages[0].content if self.messages else ""
        last_msg = self.messages[-1].content if self.messages else ""
        d = {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "title": (first_msg[:30] + "...") if len(first_msg) > 30 else first_msg or "新对话",
            "preview": (last_msg[:60] + "...") if len(last_msg) > 60 else last_msg or "",
            "message_count": len(self.messages) if self.messages else 0,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else "",
            "updated_at": str(self.updated_at) if self.updated_at else "",
        }
        if with_messages:
            d["messages"] = [m.to_dict() for m in self.messages]
        return d
