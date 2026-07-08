from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..models.database import Base
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(Enum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    conversation = relationship("Conversation", back_populates="messages")
    def to_dict(self):
        return {"id": self.id, "role": self.role, "content": self.content}
