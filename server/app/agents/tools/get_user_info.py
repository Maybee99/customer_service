from typing import Dict, Any
from ...utils.logger import logger


class GetUserInfoTool:
    def __init__(self):
        self.name = "get_user_info"
        self.description = "获取用户基本信息"

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
                        "user_id": {"type": "string", "description": "用户ID"},
                    },
                    "required": ["user_id"],
                },
            },
        }

    async def execute(self, user_id: str) -> str:
        logger.info(f"get_user_info user_id={user_id}")
        return f"用户 {user_id}：技术部，正式员"
