 from typing import Dict, Any
 from app.utils.logger import logger
 class TransferHumanTool:
     def __init__(self):
         self.name = "transfer_to_human"
         self.description = "将对话转接给人工客服"
     @property
     def schema(self) -> Dict[str, Any]:
         return {
             "type": "function",
             "function": {
                 "name": self.name,
                 "description": self.description,
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "reason": {"type": "string", "description": "转接原因"},
                         "urgency": {"type": "string", "enum": ["low","medium","high"]},
                     },
                     "required": ["reason"],
                 },
             },
         }
     async def execute(self, reason: str, urgency: str = "medium") -> str:
         logger.info(f"transfer_to_human reason={reason}")
         return f"已将您的咨询转接给人工客服。原因：{reason}。请稍候。"
