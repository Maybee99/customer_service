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

QA_PROMPT = """你是一个有帮助的智能客服助手。基于知识库中的信息回答用户的问题。
你可以使用工具来查找相关信息。
要求：
- 基于工具返回的信息准确回答
- 使用 Markdown 格式，合理使用标题、列表、加粗等
- 在回答末尾注明信息来源，格式为：\n\n---\n📚 **参考来源**：{来源文件名}
- 如果之前的回答有问题，请根据反馈进行改进。"""


async def simple_qa(state: AgentState) -> Dict[str, Any]:
    """ReAct loop: Think -> Tool Call -> Observe -> Answer."""
    steps = list(state.get("steps", []))
    steps.append({"type": "thinking", "content": "正在分析您的问题..."})
    msgs = msgs_to_dicts(state["messages"])
    ctx = [{"role": "system", "content": QA_PROMPT}]
    prev_answer = state.get("answer_draft", "")
    prev_feedback = state.get("reflection_feedback", "")
    if prev_answer and prev_feedback:
        ctx.append({"role": "system", "content": (
            f"Prev answer had issues: {prev_feedback}\n"
            "Please improve and provide a better answer."
        )})

    for msg in msgs:
        ctx.append({"role": msg["role"], "content": msg.get("content", "")})

    schemas = [t.schema for t in _tools.values()]
    history = []

    for i in range(3):
        logger.info(f"[simple_qa] Iteration {i+1}")
        if i == 0:
            steps.append({"type": "thinking", "content": "正在搜索知识库..."})
        resp = llm.chat_with_tools(messages=ctx, tools=schemas)
        choice = resp.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            answer = msg.content or ""
            steps.append({"type": "thinking", "content": "正在生成回答..."})
            logger.info(f"[simple_qa] Answer ({len(answer)} chars)")
            return {"answer_draft": answer, "tool_calls_history": history, "steps": steps}

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            steps.append({"type": "tool", "content": f"调用工具: {name}"})
            steps.append({"type": "result", "content": f"参数: {json.dumps(args, ensure_ascii=False)[:100]}"})
            tool = _tools.get(name)
            if tool:
                result = await tool.execute(**args)
                steps.append({"type": "result", "content": f"获取到相关信息" if name == "search_knowledge_base" else f"查询完成"})
                history.append({"tool": name, "args": args, "result": result})
                ctx.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                ctx.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})

    final = llm.chat(messages=ctx)
    answer = final.choices[0].message.content or ""
    return {"answer_draft": answer, "tool_calls_history": history, "steps": steps}
