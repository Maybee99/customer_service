from typing import Any, AsyncGenerator, Dict

from langgraph.graph import StateGraph, END, START

from .state import AgentState
from .nodes.intent_router import intent_router
from .nodes.simple_qa import simple_qa
from .nodes.chitchat import chitchat
from .nodes.human_transfer import human_transfer
from .nodes.complex_planner import complex_planner
from .nodes.subtask_executor import subtask_executor
from .nodes.synthesizer import synthesizer
from ..config import get_settings
from ..services.rag.llm_client import LLMClient
from ..services.conversation_service import ConversationService
from ..utils.logger import logger

settings = get_settings()


def route_intent(state: AgentState) -> str:
    """Route based on classified intent."""
    return state.get("intent", "chitchat")


def route_subtask(state: AgentState) -> str:
    """Loop: continue executing steps or go to synthesizer."""
    plan = state.get("plan", [])
    step = state.get("current_step", 0)
    if step < len(plan):
        logger.info(f"[route_subtask] Step {step+1}/{len(plan)} -> continue")
        return "continue"
    logger.info("[route_subtask] All steps done -> synthesizer")
    return "done"


def build_graph() -> StateGraph:
    """Build and compile the LangGraph agent graph."""
    builder = StateGraph(AgentState)

    builder.add_node("intent_router", intent_router)
    builder.add_node("simple_qa", simple_qa)
    builder.add_node("chitchat", chitchat)
    builder.add_node("human_transfer", human_transfer)
    builder.add_node("complex_planner", complex_planner)
    builder.add_node("subtask_executor", subtask_executor)
    builder.add_node("synthesizer", synthesizer)

    builder.add_edge(START, "intent_router")

    builder.add_conditional_edges(
        "intent_router",
        route_intent,
        {
            "simple_qa": "simple_qa",
            "complex_task": "complex_planner",
            "chitchat": "chitchat",
            "transfer": "human_transfer",
        }
    )

    # Complex task pipeline
    builder.add_edge("complex_planner", "subtask_executor")
    builder.add_conditional_edges(
        "subtask_executor",
        route_subtask,
        {
            "continue": "subtask_executor",
            "done": "synthesizer",
        }
    )
    builder.add_edge("synthesizer", END)  # skip reflection, go directly to END

    builder.add_edge("simple_qa", END)     # skip reflection
    builder.add_edge("chitchat", END)      # skip reflection

    # Reflection gate disconnected — kept for reference but not used
    # builder.add_conditional_edges("reflection_gate", route_reflection, {...})

    builder.add_edge("human_transfer", END)

    return builder.compile()


agent_graph = build_graph()
logger.info("LangGraph agent graph compiled")

STREAMING_ANSWER_PROMPT = """你是一个有帮助的智能客服助手。根据对话历史和工具调用结果，生成一个准确、完整、友好的回答。

要求：
- 基于提供的信息回答用户的问题
- 如果信息不足，诚实地说明
- 保持友好、专业的语气
- 使用 Markdown 格式输出，合理使用标题、列表、加粗等提高可读性
- 直接回答用户的问题，不要提及内部过程（如"根据知识库"等）
- 不要在回答中标注来源，来源信息由系统自动添加
- 如果上下文中包含操作截图（![...](url)格式），请在对应步骤说明中引用这些截图，让用户图文对照操作"""


def _build_streaming_messages(state: AgentState, history: list = None) -> list:
    """Build messages for the streaming final answer generation.

    Includes conversation history (previous user/assistant exchanges)
    so the LLM maintains context across multiple turns.
    """
    messages = [{"role": "system", "content": STREAMING_ANSWER_PROMPT}]

    # ── Include conversation history (previous exchanges) ──
    if history:
        for h in history:
            role = h.get("role", "user")
            content = h.get("content", "")
            if role == "user" or role == "assistant":
                if content:
                    messages.append({"role": role, "content": content})

    # ── Include current state messages ──
    msgs = state.get("messages", [])
    for m in msgs:
        if isinstance(m, dict):
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            if content:
                messages.append({"role": role, "content": content})
        else:
            role = getattr(m, "type", "user")
            if role == "human":
                role = "user"
            elif role == "ai":
                role = "assistant"
            content = getattr(m, "content", "")
            if content:
                messages.append({"role": role, "content": content})

    # Also include tool call results as context (they contain RAG sources)
    for tc in state.get("tool_calls_history", []):
        result = tc.get("result", "")
        if result:
            messages.append({"role": "user", "content": f"[工具返回结果]: {result}"})

    return messages


def _extract_images(state: AgentState) -> list:
    """Extract image URLs from tool call results as fallback."""
    import re
    seen = set()
    imgs = []
    for tc in state.get("tool_calls_history", []):
        for m in re.finditer(r'!\[(.*?)\]\(([^)]+)\)', str(tc.get("result", ""))):
            page = m.group(1)
            url = m.group(2)
            if url not in seen:
                seen.add(url)
                imgs.append({"page": page, "url": url})
    return imgs


def _extract_sources(state: AgentState) -> list:
    """Extract source filenames with confidence scores from tool call results.

    Scans tool_calls_history for '来源: {filename}' and '相关度: {score}'
    lines inserted by the search_knowledge_base tool.

    Returns list of {source, score} dicts, deduplicated by filename
    (keeping the highest score).
    """
    import re
    sources_map = {}  # filename → max_score

    for tc in state.get("tool_calls_history", []):
        result = tc.get("result", "")
        if not result:
            continue

        # Find source/score pairs in the formatted tool output:
        #   [1] content...
        #   来源: filename.pdf
        #   相关度: 95.7%
        text = str(result)
        chunks = text.split('\n\n')
        for chunk in chunks:
            src_match = re.search(r'来源[：:]\s*(.+?\.(?:pdf|docx?))', chunk)
            score_match = re.search(r'相关度[：:]\s*([\d.]+)%', chunk)
            if src_match:
                fname = src_match.group(1).strip()
                score = float(score_match.group(1)) / 100.0 if score_match else 0.0
                # Keep the highest score for each filename
                if fname not in sources_map or score > sources_map[fname]:
                    sources_map[fname] = score

    # Convert to sorted list (highest score first)
    return [
        {"source": name, "score": score}
        for name, score in sorted(sources_map.items(), key=lambda x: -x[1])
    ]


class AgentOrchestrator:
    """Wrapper around the compiled LangGraph graph for API integration."""

    def __init__(self):
        self.conv_service = ConversationService()

    def _make_initial_state(self, session_id: str, user_id: str,
                            user_name: str, question: str,
                            history: list = None) -> AgentState:
        """Build initial AgentState, optionally including conversation history."""
        messages = []
        # Prepend conversation history so the graph nodes see prior context
        if history:
            for h in history:
                role = h.get("role", "user")
                content = h.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        # Current question
        messages.append({"role": "user", "content": question})

        return {
            "session_id": session_id,
            "user_id": user_id,
            "user_name": user_name,
            "messages": messages,
            "intent": "",
            "answer_draft": "",
            "reflection_score": 0.0,
            "reflection_feedback": "",
            "reflection_retries": 0,
            "needs_human": False,
            "retrieved_docs": [],
            "tool_calls_history": [],
            "steps": [],
            "plan": [],
            "current_step": 0,
            "sub_results": [],
        }

    async def process_message(self, session_id: str, user_id: str,
                              user_name: str, question: str) -> Dict[str, Any]:
        """Run the agent graph and return the result dict."""

        # Persist: get or create conversation, fetch history, save user message
        conv_id = None
        conversation_history: list = []
        try:
            conv = self.conv_service.get_or_create(session_id, user_id, user_name)
            conv_id = conv.id
            max_ctx = settings.max_context_messages
            conversation_history = self.conv_service.get_recent_messages(
                conv_id, limit=max_ctx
            )
            self.conv_service.save_message(conv_id, "user", question)
        except Exception as e:
            logger.warning(f"[Orchestrator] Failed to persist user message: {e}")

        # Create state with conversation history
        initial = self._make_initial_state(
            session_id, user_id, user_name, question,
            history=conversation_history,
        )

        result = await agent_graph.ainvoke(initial)
        answer = result.get("answer_draft", "")
        intent = result.get("intent", "?")
        needs_human = result.get("needs_human", False)
        reflection_score = result.get("reflection_score", 0.0)

        logger.info(f"[Orchestrator] Done. intent={intent}, "
                     f"score={reflection_score:.2f}, "
                     f"needs_human={needs_human}")

        # Persist: save AI answer
        if conv_id and answer:
            try:
                self.conv_service.save_message(conv_id, "assistant", answer)
            except Exception as e:
                logger.warning(f"[Orchestrator] Failed to persist AI message: {e}")

        return {
            "answer": answer,
            "intent": intent,
            "needs_human": needs_human,
            "tool_calls": result.get("tool_calls_history", []),
            "steps": result.get("steps", []),
        }

    async def process_message_stream(
        self, session_id: str, user_id: str,
        user_name: str, question: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the agent graph with real-time step streaming and token-level answer streaming.

        Yields events: step, answer_token, done, error

        Persists the conversation and messages to MySQL so the sidebar
        history is always up-to-date.
        """
        # ── Persist: get-or-create conversation, fetch history, save user msg ──
        conv_id = None
        conversation_history: list = []
        try:
            conv = self.conv_service.get_or_create(session_id, user_id, user_name)
            conv_id = conv.id
            # Fetch previous messages BEFORE saving the current one so we
            # can pass them as conversation context to the LLM.
            max_ctx = settings.max_context_messages
            conversation_history = self.conv_service.get_recent_messages(
                conv_id, limit=max_ctx
            )
            self.conv_service.save_message(conv_id, "user", question)
            logger.info(f"[Orchestrator] Persisted user message → conv #{conv_id}"
                         f" (history: {len(conversation_history)} msgs)")
        except Exception as e:
            logger.warning(f"[Orchestrator] Failed to persist user message: {e}")

        # Create initial state WITH conversation history so graph nodes
        # (intent router, QA, etc.) also see prior context.
        initial = self._make_initial_state(
            session_id, user_id, user_name, question,
            history=conversation_history,
        )
        llm = LLMClient()

        # Phase 1: Stream graph execution — emit steps as nodes complete
        last_step_count = 0
        final_state = None

        try:
            async for state in agent_graph.astream(initial, stream_mode="values"):
                final_state = state
                steps = state.get("steps", [])
                # Emit new steps that were added by the most recent node
                new_steps = steps[last_step_count:]
                for step in new_steps:
                    yield {"type": "step", "data": step}
                last_step_count = len(steps)
        except Exception as e:
            logger.error(f"[Orchestrator] Graph execution error: {e}")
            yield {"type": "error", "data": {"detail": str(e)}}
            return

        if final_state is None:
            yield {"type": "error", "data": {"detail": "Graph produced no state"}}
            return

        intent = final_state.get("intent", "")
        needs_human = final_state.get("needs_human", False)
        reflection_score = final_state.get("reflection_score", 0.0)

        logger.info(f"[Orchestrator] Graph done. intent={intent}, "
                     f"score={reflection_score:.2f}, needs_human={needs_human}")

        # Phase 2: Stream the final answer token-by-token
        if needs_human:
            yield {"type": "step", "data": {"type": "result", "content": "正在为您转接人工客服..."}}
            yield {"type": "done", "data": {"session_id": session_id, "needs_human": True}}
            # Persist the transfer message
            if conv_id:
                try:
                    self.conv_service.save_message(conv_id, "assistant", "已转接人工客服")
                except Exception:
                    pass
            return

        # Build messages from conversation context (history is already in state)
        messages = _build_streaming_messages(final_state)

        # Collect all answer tokens so we can persist the full answer
        answer_buffer: list[str] = []

        try:
            token_count = 0
            for token in llm.chat_stream(messages, max_tokens=1000):
                answer_buffer.append(token)
                yield {"type": "answer_token", "data": {"content": token}}
                token_count += 1
            logger.info(f"[Orchestrator] Streamed {token_count} tokens")
        except Exception as e:
            logger.error(f"[Orchestrator] Streaming error: {e}")
            # Fallback: use the pre-generated answer_draft from the graph
            fallback = final_state.get("answer_draft", "")
            if fallback:
                logger.info(f"[Orchestrator] Using fallback answer ({len(fallback)} chars)")
                answer_buffer.append(fallback)
                for i in range(0, len(fallback), 8):
                    yield {"type": "answer_token", "data": {"content": fallback[i:i+8]}}

        # ── Images: LLM should include them from context, but if not, append ──
        full_answer = "".join(answer_buffer)
        if '![' not in full_answer:
            images = _extract_images(final_state)
            if images:
                imgs_md = ''.join(
                    f"\n![{img['page']}]({img['url']})" for img in images
                )
                logger.info(f"[Orchestrator] LLM missed {len(images)} images, appending")
                answer_buffer.append(imgs_md)
                for ch in imgs_md:
                    yield {"type": "answer_token", "data": {"content": ch}}

        # Append source citations with confidence scores + clickable links
        sources = _extract_sources(final_state)
        if sources:
            citation = "\n\n---\n📊 **参考来源**："
            for src in sources:
                name = src["source"]
                score = src["score"]
                score_pct = f"{score * 100:.1f}%"
                # Emoji indicator based on confidence level
                if score >= 0.8:
                    indicator = "🟢"
                elif score >= 0.5:
                    indicator = "🟡"
                else:
                    indicator = "🔴"
                download_url = f"{settings.server_url}/api/knowledge/download/{name}"
                citation += f"\n- {indicator} [{name}]({download_url}) — 相关度: {score_pct}"
            logger.info(f"[Orchestrator] Appending {len(sources)} source(s): "
                         f"{[s['source'] for s in sources]}")
            answer_buffer.append(citation)
            for ch in citation:
                yield {"type": "answer_token", "data": {"content": ch}}

        # ── Persist: save the full AI answer ──
        if conv_id and answer_buffer:
            try:
                full_answer = "".join(answer_buffer)
                self.conv_service.save_message(conv_id, "assistant", full_answer)
                logger.info(f"[Orchestrator] Persisted AI answer → conv #{conv_id} "
                            f"({len(full_answer)} chars)")
            except Exception as e:
                logger.warning(f"[Orchestrator] Failed to persist AI answer: {e}")

        yield {"type": "done", "data": {"session_id": session_id, "needs_human": False}}
