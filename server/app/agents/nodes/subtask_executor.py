import json
from typing import Any, Dict

from ...services.rag.llm_client import LLMClient
from ..state import AgentState, msgs_to_dicts
from ..tools.search_knowledge import SearchKnowledgeTool
from ..tools.get_user_info import GetUserInfoTool
from ..tools.transfer_human import TransferHumanTool
from ...utils.logger import logger

llm = LLMClient()
_search = SearchKnowledgeTool()
_user_info = GetUserInfoTool()
_transfer = TransferHumanTool()
_tools = {
    _search.name: _search,
    _user_info.name: _user_info,
    _transfer.name: _transfer,
}

STEP_PROMPT = """你正在执行一个多步骤任务中的一个步骤。
根据步骤描述，决定调用哪个工具（search_knowledge_base 或 get_user_info）。
如果该步骤已经有答案，只需总结结果。"""


async def subtask_executor(state: AgentState) -> Dict[str, Any]:
    """Execute one step of a multi-step plan."""
    plan = state.get("plan", [])
    step_idx = state.get("current_step", 0)

    if step_idx >= len(plan):
        return {"current_step": step_idx}

    step_desc = plan[step_idx]
    logger.info(f"[subtask_executor] Step {step_idx + 1}/{len(plan)}: {step_desc}")
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": f"执行步骤 {step_idx+1}/{len(plan)}: {step_desc}"})

    msgs = msgs_to_dicts(state["messages"])
    ctx = [{"role": "system", "content": f"{STEP_PROMPT}\n\nCurrent step: {step_desc}"}]
    for m in msgs:
        ctx.append({"role": m["role"], "content": m.get("content", "")})

    schemas = [t.schema for t in _tools.values()]
    result_text = ""

    for i in range(2):
        resp = llm.chat_with_tools(messages=ctx, tools=schemas)
        msg = resp.choices[0].message

        if not msg.tool_calls:
            result_text = msg.content or "Done."
            break

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            tool = _tools.get(name)
            if tool:
                r = await tool.execute(**args)
                result_text += f"[{name}]: {r}\n"
                steps.append({"type": "tool", "content": f"调用: {name}"})
                steps.append({"type": "result", "content": f"步骤完成 ✓"})
                ctx.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                ctx.append({"role": "tool", "tool_call_id": tc.id, "content": str(r)})

    sub_results = list(state.get("sub_results", []))
    sub_results.append({"step": step_desc, "result": result_text.strip()})

    return {"current_step": step_idx + 1, "sub_results": sub_results, "steps": steps}
