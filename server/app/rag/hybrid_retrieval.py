 from typing import List, Dict, Any, Optional
 from app.rag.milvus_store import MilvusStore
 from app.rag.bm25_search import BM25Search
 from app.rag.reranker import Reranker
 from app.rag.embeddings import EmbeddingService
 from app.config import get_settings
 from app.utils.logger import logger

 settings = get_settings()


 class HybridRetrieval:
     """Hybrid retrieval combining Milvus vector search and BM25 keyword search"""

     def __init__(self):
         self.milvus = MilvusStore()
         self.bm25 = BM25Search()
         self.reranker = Reranker()
         self.embeddings = EmbeddingService()
         self.vector_weight = settings.vector_weight
         self.bm25_weight = settings.bm25_weight

     def search(self, query: str, top_k: int = None,
                category: Optional[str] = None) -> List[Dict[str, Any]]:
         """
         Perform hybrid search:
         1. Embed query -> Milvus vector search
         2. BM25 keyword search
         3. Merge, normalize, and rerank
         """
         if top_k is None:
             top_k = settings.top_k_retrieval

         # Step 1: Vector search via Milvus
         query_embedding = self.embeddings.embed_query(query)
         vector_results = self.milvus.search(query_embedding, top_k=top_k, category=category)
         vector_results = self._normalize_scores(vector_results)

         # Step 2: BM25 search
         bm25_results = self.bm25.search(query, top_k=top_k)
         bm25_results = self._normalize_scores(bm25_results)

         # Step 3: Merge with weighted scores
         merged = self._merge_results(vector_results, bm25_results)

         # Step 4: Rerank
         reranked = self.reranker.rerank(query, merged, top_k=settings.rerank_top_k)

         return reranked

     def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
         if not results:
             return []
         scores = [r["score"] for r in results]
         min_s, max_s = min(scores), max(scores)
         for r in results:
             if max_s == min_s:
                 r["normalized_score"] = 1.0
             else:
                 r["normalized_score"] = (r["score"] - min_s) / (max_s - min_s)
         return results

     def _merge_results(self, vector_results: List[Dict[str, Any]],
                        bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
         merged = {}
         for r in vector_results:
             key = r["content"][:100]
             merged[key] = {**r, "score": r["normalized_score"] * self.vector_weight, "sources": ["vector"]}
         for r in bm25_results:
             key = r["content"][:100]
             if key in merged:
                 merged[key]["score"] += r["normalized_score"] * self.bm25_weight
                 merged[key]["sources"].append("bm25")
             else:
                 merged[key] = {**r, "score": r["normalized_score"] * self.bm25_weight, "sources": ["bm25"]}
         return list(merged.values())
