 from typing import List, Dict, Any
 from app.utils.logger import logger


 class Reranker:
     """Re-rank retrieved documents using cross-encoder or score-based method"""

     def __init__(self):
         self.score_threshold = 0.5

     def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
         if not documents:
             return []
         reranked = []
         for doc in documents:
             score = doc.get("score", 0)
             query_terms = set(query.lower().split())
             content_lower = doc.get("content", "").lower()
             term_matches = sum(1 for t in query_terms if t in content_lower)
             relevance_boost = term_matches / max(len(query_terms), 1) * 0.2
             final_score = score + relevance_boost
             doc["rerank_score"] = round(final_score, 4)
             if final_score >= self.score_threshold:
                 reranked.append(doc)
         reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
         return reranked[:top_k]
