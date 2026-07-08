 from app.models.database import SessionLocal
 from app.models.conversation import Conversation
 from app.models.message import Message
 from app.utils.logger import logger
 class ConversationService:
     def get_or_create(self, session_id, user_id, channel="web"):
         db = SessionLocal()
         try:
             conv = db.query(Conversation).filter(Conversation.session_id == session_id).first()
             if not conv:
                 conv = Conversation(session_id=session_id, user_id=user_id, channel=channel)
                 db.add(conv)
                 db.commit()
                 db.refresh(conv)
             return conv
         finally:
             db.close()
     def save_message(self, conversation_id, role, content):
         db = SessionLocal()
         try:
             msg = Message(conversation_id=conversation_id, role=role, content=content)
             db.add(msg)
             db.commit()
             return msg
         finally:
             db.close()
