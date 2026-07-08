from typing import Dict, Any
from ...rag.hybrid_retrieval import HybridRetrieval
from ...utils.logger import logger


class SearchKnowledgeTool:
    def __init__(self):
        self.retrieval = HybridRetrieval()
        self.name = "search_knowledge_base"
        self.description = "搜索客服知识?"

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
                        "query": {"type": "string", "description": "用户的问题?"},
                        "category": {"type": "string", "description": "分类过滤"},
                    },
                    "required": ["query"],
                },
            },
        }

    async def execute(self, query: str, category: str = None) -> str:
        logger.info(f"[search_knowledge] === START: query='{query}', category={category} ===")
        results = self.retrieval.search(query, category=category)
        if not results:
            logger.warning(f"[search_knowledge] === NO RESULTS for '{query}' ===")
            return "知识库中未找到相关信息"
        context = ""
        for i, doc in enumerate(results, 1):
            chunk = doc['content']
            source = doc.get('source_file', '未知')
            score = doc.get('rerank_score', doc.get('score', 'N/A'))
            score_pct = f"{score * 100:.1f}%" if isinstance(score, (int, float)) else str(score)
            logger.info(f"[search_knowledge] Result #{i}: score={score}, source={source}, "
                         f"content[:100]={chunk[:100]}")
            context += (f"[{i}] {chunk}\n"
                        f"来源: {source}\n"
                        f"相关度: {score_pct}\n\n")
        logger.info(f"[search_knowledge] === RETURNING {len(results)} chunks ===")
        return context.strip()
