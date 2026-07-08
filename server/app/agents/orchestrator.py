 from typing import List, Dict, Any, Optional, Callable
 from app.agents.state import ConversationState
 from app.agents.tools.search_knowledge import SearchKnowledgeTool
 from app.agents.tools.transfer_human import TransferHumanTool
 from app.agents.tools.get_user_info import GetUserInfoTool
 from app.services.rag.llm_client import LLMClient
 from app.utils.logger import logger


 class AgentOrchestrator:
     """
     Agent orchestrator that manages multi-turn conversations.
     Uses LLM function calling to decide which tools to invoke.
     """

     def __init__(self):
         self.tools: Dict[str, Callable] = {}
         self.llm = LLMClient()
         self._register_tools()

     def _register_tools(self):
         search_tool = SearchKnowledgeTool()
         transfer_tool = TransferHumanTool()
         user_info_tool = GetUserInfoTool()
         for tool in [search_tool, transfer_tool, user_info_tool]:
             self.tools[tool.name] = tool

     def get_tool_schemas(self) -> List[Dict[str, Any]]:
         return [tool.schema for tool in self.tools.values()]

     async def process_message(self, state: ConversationState) -> Dict[str, Any]:
         """
         Process a user message through the agent loop:
         1. LLM decides intent and whether to call a tool
         2. If tool call: execute tool, feed result back to LLM
         3. LLM generates final answer
         """
         max_iterations = 3
         current_messages = state.get_context()

         for iteration in range(max_iterations):
             logger.info(f"  [Agent] Iteration {iteration + 1}")
             response = self.llm.chat_with_tools(
                 messages=current_messages,
                 tools=self.get_tool_schemas(),
             )

             choice = response.choices[0]
             msg = choice.message

             if not msg.tool_calls:
                 # LLM decided to answer directly
                 state.add_message("assistant", msg.content)
                 return {"answer": msg.content, "tool_calls": []}

             # Execute tools
             tool_results = []
             for tool_call in msg.tool_calls:
                 tool_name = tool_call.function.name
                 tool_args = json.loads(tool_call.function.arguments)

                 if tool_name in self.tools:
                     logger.info(f"  [Agent] Calling tool: {tool_name}({tool_args})")
                     result = await self.tools[tool_name].execute(**tool_args)
                     tool_results.append({"tool": tool_name, "result": result})

                     current_messages.append({
                         "role": "assistant",
                         "content": None,
                         "tool_calls": [tool_call],
                     })
                     current_messages.append({
                         "role": "tool",
                         "tool_call_id": tool_call.id,
                         "content": result,
                     })

             state.tool_results = tool_results

         # Final answer after max iterations
         final = self.llm.chat(messages=current_messages)
         answer = final.choices[0].message.content
         state.add_message("assistant", answer)
         return {"answer": answer, "tool_calls": state.tool_results}


 import json
