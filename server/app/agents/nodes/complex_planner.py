import json
from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ...utils.logger import logger

llm = LLMClient()

PLANNER_PROMPT = """你是智能客服系统的任务规划器。
用户的问题需要多个独立的步骤来完成。
将问题分解为一系列子任务。每个子任务应该能独立使用以下工具之一完成：search_knowledge_base（搜索知识库）、get_user_info（获取用户信息）。

只输出一个JSON数组，包含步骤描述，例如：
["搜索知识库了解年假政策",
 "搜索知识库了解报销流程",
 "获取用户信息"]

每一步都应该是一个清晰、可执行的描述。
只输出JSON数组，不要其他内容。"""


def complex_planner(state: AgentState) -> Dict[str, Any]:
    """Decompose a complex user question into a list of sub-tasks."""
    msgs = msgs_to_dicts(state["messages"])
    last_q = msgs[-1].get("content", "") if msgs else ""
    if not last_q:
        return {"plan": [], "intent": "simple_qa"}

    logger.info(f"[complex_planner] Planning steps for: {last_q[:60]}...")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在分解复杂任务..."})
    resp = llm.generate_with_context(PLANNER_PROMPT, last_q, max_tokens=500)

    try:
        plan = json.loads(resp.strip())
        if not isinstance(plan, list):
            raise ValueError("Not a list")
        plan = [str(s).strip() for s in plan if str(s).strip()]
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"[complex_planner] Parse error: {e}, resp={resp[:100]}")
        plan = [f"Search knowledge base about: {last_q}"]

    logger.info(f"[complex_planner] Plan: {plan}")
    step_list = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(plan)])
    steps.append({"type": "result", "content": f"任务分解完成:\n{step_list}"})
    return {"plan": plan, "steps": steps}
