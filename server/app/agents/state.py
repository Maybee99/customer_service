 from typing import List, Dict, Any, Optional
 from dataclasses import dataclass, field


 @dataclass
 class Message:
     role: str  # "user" | "assistant" | "tool"
     content: str
     name: Optional[str] = None
     tool_call_id: Optional[str] = None


 @dataclass
 class ConversationState:
     session_id: str
     user_id: str
     user_name: str = ""
     messages: List[Message] = field(default_factory=list)
     metadata: Dict[str, Any] = field(default_factory=dict)
     current_intent: str = ""
     tool_results: List[Dict[str, Any]] = field(default_factory=list)

     def add_message(self, role: str, content: str, **kwargs):
         self.messages.append(Message(role=role, content=content, **kwargs))

     def get_context(self, max_messages: int = 5) -> List[Dict[str, str]]:
         return [{"role": m.role, "content": m.content} for m in self.messages[-max_messages:]]

     def to_dict(self) -> Dict[str, Any]:
         return {
             "session_id": self.session_id,
             "user_id": self.user_id,
             "user_name": self.user_name,
             "messages": [{"role": m.role, "content": m.content} for m in self.messages],
             "current_intent": self.current_intent,
         }
