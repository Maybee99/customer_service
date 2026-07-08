from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

INTENT_PROMPT = """你是智能客服系统的意图分类器。
分析用户的消息，将其分类为以下类别之一：
- simple_qa：用户询问事实性问题（常见问题、政策、流程、产品信息等）
- complex_task：用户的问题涉及多个话题或需要多步操作（如比较政策、多步骤流程、跨领域问题）
- chitchat：用户正在打招呼、感谢或闲聊
- transfer：用户明确要求转人工客服或投诉机器人

只回复类别名称，不要其他内容。"""


def intent_router(state: AgentState) -> Dict[str, Any]:
    """Classify user intent based on the latest message."""
    msgs = msgs_to_dicts(state["messages"])
    if not msgs:
        logger.warning("[intent_router] No messages, defaulting to chitchat")
        return {"intent": "chitchat"}

    last_text = msgs[-1].get("content", "")
    if not last_text:
        return {"intent": "chitchat"}

    logger.info(f"[intent_router] Classifying: {last_text[:60]}...")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在分析您的意图..."})
    resp = llm.generate_with_context(INTENT_PROMPT, last_text, max_tokens=20)
    intent = resp.strip().lower()

    if intent not in ("simple_qa", "complex_task", "chitchat", "transfer"):
        logger.warning(f"[intent_router] Unknown '{intent}', defaulting to simple_qa")
        intent = "simple_qa"

    logger.info(f"[intent_router] Intent: {intent}")
    steps.append({"type": "result", "content": f"意图分类: {intent}"})
    return {"intent": intent, "steps": steps}
