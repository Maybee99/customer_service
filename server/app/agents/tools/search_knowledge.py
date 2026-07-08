 from typing import Dict, Any
 from app.rag.hybrid_retrieval import HybridRetrieval
 from app.utils.logger import logger
 class SearchKnowledgeTool:
     def __init__(self):
         self.retrieval = HybridRetrieval()
         self.name = "search_knowledge_base"
         self.description = "搜索客服知识库"
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
                         "query": {"type": "string", "description": "用户的问题"},
                         "category": {"type": "string", "description": "分类过滤"},
                     },
                     "required": ["query"],
                 },
             },
         }
     async def execute(self, query: str, category: str = None) -> str:
         logger.info(f"search_knowledge_base query={query}")
         results = self.retrieval.search(query, category=category)
         if not results:
             return "知识库中未找到相关信息。"
         context = ""
         for i, doc in enumerate(results, 1):
             context += f"[{i}] {doc['content']}\n来源: {doc.get('source_file','未知')}\n\n"
         return context.strip()
