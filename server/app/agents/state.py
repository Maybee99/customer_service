from typing import List, Dict, Any, Optional
from typing import TypedDict, List, Dict, Any, Annotated
from langgraph.graph import add_messages


def msgs_to_dicts(messages) -> List[Dict[str, Any]]:
    """Normalize LangGraph message objects to plain dicts."""
    result = []
    for m in messages:
        if isinstance(m, dict):
            result.append(m)
        else:
            role = getattr(m, "type", "user")
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            result.append({
                "role": role,
                "content": getattr(m, "content", ""),
                "tool_calls": getattr(m, "tool_calls", None),
            })
    return result


class AgentState(TypedDict):
    """LangGraph state for the customer service agent.

    messages is managed by LangGraph's add_messages reducer,
    which appends new messages and handles tool call tracking.
    """
    session_id: str
    user_id: str
    user_name: str
    messages: Annotated[List[Dict[str, Any]], add_messages]
    intent: str
    answer_draft: str
    reflection_score: float
    reflection_feedback: str
    reflection_retries: int
    needs_human: bool
    retrieved_docs: List[Dict[str, Any]]
    tool_calls_history: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    plan: List[str]
    current_step: int
    sub_results: List[Dict[str, Any]]
