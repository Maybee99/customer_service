import json
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agents.orchestrator import AgentOrchestrator
from ..utils.logger import logger

router = APIRouter()
orchestrator = AgentOrchestrator()


class StreamChatRequest(BaseModel):
    question: str
    session_id: str
    user_id: str
    user_name: str = ""


@router.post("/chat/stream")
async def stream_chat(request: StreamChatRequest):
    logger.info(f"[SSE Chat] session={request.session_id}, user={request.user_id}")
    logger.info(f"  Question: {request.question}")

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in orchestrator.process_message_stream(
                session_id=request.session_id,
                user_id=request.user_id,
                user_name=request.user_name,
                question=request.question,
            ):
                event_type = event["type"]
                data = event["data"]
                yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"[SSE Chat] Error: {e}")
            yield f"event: error\ndata: {json.dumps({'detail': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
