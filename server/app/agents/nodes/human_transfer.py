from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

SUMMARY_PROMPT = """总结对话内容并生成转接给人工客服的记录。
包括：用户问了什么、AI尝试了什么、为什么需要人工介入。"""


def human_transfer(state: AgentState) -> Dict[str, Any]:
    """Mark for human handoff and generate a transfer summary."""
    msgs = msgs_to_dicts(state["messages"])
    ctx = [{"role": "system", "content": SUMMARY_PROMPT}]
    for m in msgs:
        ctx.append({"role": m["role"], "content": m.get("content", "")})

    logger.info("[human_transfer] Generating handoff summary")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在转接人工客服..."})
    resp = llm.chat(messages=ctx)
    summary = resp.choices[0].message.content or ""

    answer = f"[Transfer to human agent]\n\nSummary:\n{summary}"
    return {
        "needs_human": True,
        "answer_draft": answer,
        "steps": steps,
    }
