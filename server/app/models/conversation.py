 from sqlalchemy import Column, Integer, String, Enum, TIMESTAMP
 from sqlalchemy.sql import func
 from sqlalchemy.orm import relationship
 from app.models.database import Base
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
         d = {"id": self.id, "session_id": self.session_id, "user_id": self.user_id}
         if with_messages:
             d["messages"] = [m.to_dict() for m in self.messages]
         return d
