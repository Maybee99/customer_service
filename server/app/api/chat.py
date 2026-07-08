 from fastapi import APIRouter, HTTPException
 from pydantic import BaseModel
 from typing import Optional
 from app.agents.orchestrator import AgentOrchestrator
 from app.agents.state import ConversationState
 from app.utils.logger import logger

 router = APIRouter()
 orchestrator = AgentOrchestrator()


 class ChatRequest(BaseModel):
     question: str
     session_id: str
     user_id: str
     user_name: str = ""
     stream: bool = False


 class ChatResponse(BaseModel):
     answer: str
     session_id: str
     sources: list = []


 @router.post("/chat", response_model=ChatResponse)
 async def chat(request: ChatRequest):
     try:
         logger.info(f"[Chat] session={request.session_id}, user={request.user_id}")
         logger.info(f"  Question: {request.question}")

         state = ConversationState(
             session_id=request.session_id,
             user_id=request.user_id,
             user_name=request.user_name,
         )
         state.add_message("user", request.question)

         result = await orchestrator.process_message(state)

         return ChatResponse(
             answer=result["answer"],
             session_id=request.session_id,
             sources=result.get("tool_calls", []),
         )

     except Exception as e:
         logger.error(f"Chat error: {e}")
         raise HTTPException(status_code=500, detail=str(e))
