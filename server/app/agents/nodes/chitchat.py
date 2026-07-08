from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

CHITCHAT_PROMPT = """你是一个友好的智能客服助手。
自然地回复问候、感谢或闲聊。
保持热情但简洁。如果用户问到需要查询知识库的问题，请建议他们直接提问。"""


def chitchat(state: AgentState) -> Dict[str, Any]:
    """Direct LLM response for greetings / small talk."""
    msgs = msgs_to_dicts(state["messages"])
    ctx = [{"role": "system", "content": CHITCHAT_PROMPT}]
    for m in msgs:
        ctx.append({"role": m["role"], "content": m.get("content", "")})

    logger.info("[chitchat] Generating response")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在回复..."})
    resp = llm.chat(messages=ctx)
    answer = resp.choices[0].message.content or ""
    return {"answer_draft": answer, "steps": steps}
