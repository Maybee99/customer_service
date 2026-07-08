from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

SYNTHESIS_PROMPT = """你是客服助手，需要将多个来源的结果整合成完整回答。
将以下各步骤的结果合并为一个全面、条理清晰的回答。
以清晰友好的方式呈现信息。不要提及步骤分解过程。
如有需要可以使用Markdown格式提高可读性。"""


def synthesizer(state: AgentState) -> Dict[str, Any]:
    """Merge sub-results into a final answer."""
    sub_results = state.get("sub_results", [])
    if not sub_results:
        logger.warning("[synthesizer] No sub-results, using LLM directly")
        msgs = msgs_to_dicts(state["messages"])
        last_q = msgs[-1].get("content", "") if msgs else ""
        resp = llm.generate_with_context("Answer the user's question.", last_q)
        return {"answer_draft": resp}

    parts = []
    for sr in sub_results:
        parts.append(f"Step: {sr.get('step', '?')}\nResult: {sr.get('result', 'N/A')}")
    context = "\n\n".join(parts)

    msgs = msgs_to_dicts(state["messages"])
    user_q = msgs[-1].get("content", "") if msgs else ""
    full_prompt = f"User question: {user_q}\n\nResults from each step:\n{context}\n\nPlease synthesize a complete answer using the above information."

    logger.info("[synthesizer] Synthesizing answer from sub-results")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在整合各步骤结果..."})
    answer = llm.generate_with_context(SYNTHESIS_PROMPT, full_prompt, max_tokens=1000)

    tool_calls = list(state.get("tool_calls_history", []))
    tool_calls.append({"type": "synthesized", "sub_results_count": len(sub_results)})
    return {"answer_draft": answer, "tool_calls_history": tool_calls, "steps": steps}
