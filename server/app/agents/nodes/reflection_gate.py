import json
from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

REFLECTION_PROMPT = """你是客服AI的质量审核员。
评估AI对用户问题的回答质量。
返回一个JSON对象，包含：
- "score": 0.0-1.0 的浮点数（回答是否准确、完整地解决了问题）
- "feedback": 字符串（需要改进的地方）

评分标准：
- score >= 0.7：回答良好，没有重大问题
- score 0.4-0.7：部分正确，需要改进
- score < 0.4：错误或幻觉，必须重做

只返回JSON对象，不要其他内容。"""


def reflection_gate(state: AgentState) -> Dict[str, Any]:
    """Evaluate answer quality and produce score + feedback."""
    # Skip LLM evaluation for chitchat - always pass
    if state.get("intent") == "chitchat":
        logger.info("[reflection_gate] Chitchat, skipping reflection")
        steps = list(state.get("steps", []))
        steps.append({"type": "reflect", "content": "质量检查通过 ✓"})
        return {
            "reflection_score": 1.0,
            "reflection_feedback": "",
            "reflection_retries": state.get("reflection_retries", 0) + 1,
            "steps": steps,
        }

    answer = state.get("answer_draft", "")
    if not answer:
        return {"reflection_score": 0.0, "reflection_feedback": "No answer generated", "reflection_retries": state.get("reflection_retries", 0) + 1}

    msgs = msgs_to_dicts(state["messages"])
    last_q = msgs[-1].get("content", "") if msgs else ""
    prompt = f"User question: {last_q}\n\nAI answer: {answer}"

    logger.info("[reflection_gate] Evaluating answer quality")
    resp = llm.generate_with_context(REFLECTION_PROMPT, prompt, max_tokens=300)

    try:
        result = json.loads(resp.strip())
        score = float(result.get("score", 0.5))
        feedback = result.get("feedback", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        logger.warning(f"[reflection_gate] Failed to parse: {resp[:100]}")
        score = 0.5
        feedback = ""

    score = max(0.0, min(1.0, score))
    retries = state.get("reflection_retries", 0) + 1

    logger.info(f"[reflection_gate] Score={score:.2f}, Retry={retries}, Feedback={feedback[:60]}")
    steps = list(state.get("steps", []))
    if score >= 0.7:
        steps.append({"type": "reflect", "content": f"质量检查通过 ✓ (得分: {score:.2f})"})
    elif score >= 0.4:
        steps.append({"type": "reflect", "content": f"质量检查需改进 ⚠ (得分: {score:.2f}) - {feedback[:50]}"})
    else:
        steps.append({"type": "reflect", "content": f"质量检查不通过 ✗ (得分: {score:.2f}) - 需要重试"})
    return {
        "reflection_score": score,
        "reflection_feedback": feedback,
        "reflection_retries": retries,
        "steps": steps,
    }


def route_reflection(state: AgentState) -> str:
    """Conditional edge: decide pass / retry / escalate."""
    score = state.get("reflection_score", 0.0)
    retries = state.get("reflection_retries", 0)
    intent = state.get("intent", "")
    if score >= 0.7:
        logger.info("[route_reflection] -> pass")
        return "pass"
    elif retries >= 3:
        logger.info("[route_reflection] -> escalate")
        return "escalate"
    else:
        if intent == "complex_task":
            logger.info("[route_reflection] -> retry_synthesize")
            return "retry_synthesize"
        logger.info("[route_reflection] -> retry")
        return "retry"
