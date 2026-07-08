 from fastapi import APIRouter, Depends, HTTPException, Query
 from sqlalchemy.orm import Session
 from app.models.database import get_db
 from app.models.conversation import Conversation
 from app.models.message import Message
 from app.utils.logger import logger
 from typing import Optional

 router = APIRouter()


 @router.get("/conversations")
 async def list_conversations(
     user_id: Optional[str] = Query(None),
     limit: int = Query(50),
     page: int = Query(1),
     db: Session = Depends(get_db),
 ):
     try:
         query = db.query(Conversation).order_by(Conversation.updated_at.desc())
         if user_id:
             query = query.filter(Conversation.user_id == user_id)
         total = query.count()
         conversations = query.offset((page - 1) * limit).limit(limit).all()
         return {
             "conversations": [c.to_dict() for c in conversations],
             "total": total,
             "page": page,
             "limit": limit,
         }
     except Exception as e:
         logger.error(f"Failed to list conversations: {e}")
         raise HTTPException(status_code=500, detail=str(e))


 @router.get("/conversations/{conversation_id}")
 async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
     conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
     if not conv:
         raise HTTPException(status_code=404, detail="Conversation not found")
     return conv.to_dict(with_messages=True)


 @router.post("/conversations/{conversation_id}/close")
 async def close_conversation(conversation_id: int, db: Session = Depends(get_db)):
     conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
     if not conv:
         raise HTTPException(status_code=404, detail="Conversation not found")
     conv.status = "closed"
     db.commit()
     return {"status": "closed"}
