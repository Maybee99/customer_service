from datetime import datetime

from ..models.database import SessionLocal
from ..models.conversation import Conversation
from ..models.message import Message
from ..utils.logger import logger


class ConversationService:
    """Handles conversation and message persistence in MySQL."""

    def get_or_create(self, session_id: str, user_id: str,
                      user_name: str = "", channel: str = "web") -> Conversation:
        """Find an existing conversation by session_id, or create a new one.

        Returns a Conversation where .id and .session_id are guaranteed to
        be loaded (even after session close).
        """
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(
                Conversation.session_id == session_id
            ).first()
            if not conv:
                conv = Conversation(
                    session_id=session_id,
                    user_id=user_id,
                    user_name=user_name,
                    channel=channel,
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)  # reload after commit so attrs stay live
                logger.info(f"[ConvService] Created conversation #{conv.id} "
                            f"for session={session_id}")
            else:
                # Touch updated_at so it sorts to the top
                conv.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(conv)  # reload after commit so attrs stay live
            # Read id/session_id NOW while session is still open so the
            # caller can safely access them after the session closes.
            _id = conv.id
            _sid = conv.session_id
            return conv
        finally:
            db.close()

    def save_message(self, conversation_id: int, role: str,
                     content: str) -> Message:
        """Persist a single message to the database."""
        db = SessionLocal()
        try:
            msg = Message(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )
            db.add(msg)
            db.commit()
            # Touch the conversation's updated_at
            db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).update({"updated_at": datetime.utcnow()})
            db.commit()
            return msg
        finally:
            db.close()

    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation and its messages (CASCADE)."""
        db = SessionLocal()
        try:
            conv = db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            if not conv:
                return False
            db.delete(conv)
            db.commit()
            logger.info(f"[ConvService] Deleted conversation #{conversation_id}")
            return True
        finally:
            db.close()

    def get_recent_messages(self, conversation_id: int,
                            limit: int = 20) -> list[dict]:
        """Fetch the most recent messages for a conversation.

        Returns list of {role, content} dicts in chronological order,
        limited to `limit` most recent messages.
        """
        db = SessionLocal()
        try:
            msgs = (
                db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
            # Reverse to chronological order (oldest first)
            return [{"role": m.role, "content": m.content} for m in reversed(msgs)]
        finally:
            db.close()
