"""
Hybrid retrieval combining Milvus vector search, BM25 keyword search,
and query expansion for improved recall.
"""

import hashlib
import re
from typing import List, Dict, Any, Optional

from ..rag.milvus_store import MilvusStore
from ..rag.bm25_search import BM25Search
from ..rag.reranker import Reranker
from ..rag.embeddings import EmbeddingService
from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()

QUERY_EXPANSION_PROMPT = """将以下用户问题改写为 2-3 个同义查询，用于知识库检索。
每个改写应该使用不同的关键词和表达方式，但保持原意不变。

用户问题：{query}

只输出改写后的查询，每行一个，不要编号，不要其他内容。"""


class HybridRetrieval:
    """Hybrid retrieval with vector search, BM25, and query expansion."""

    def __init__(self):
        self.milvus = MilvusStore()
        self.bm25 = BM25Search()
        self.reranker = Reranker()
        self.embeddings = EmbeddingService()
        self.vector_weight = settings.vector_weight
        self.bm25_weight = settings.bm25_weight
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from ..services.rag.llm_client import LLMClient
            self._llm = LLMClient()
        return self._llm

    # ── Public API ──────────────────────────────────────────

    def search(self, query: str, top_k: int = None,
               category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform hybrid search with query expansion:

        1. Expand query → 2-3 alternative phrasings
        2. For each query: vector search + BM25 search
        3. Merge all results with weighted scores
        4. Rerank with Qwen LLM
        """
        if top_k is None:
            top_k = settings.top_k_retrieval

        milvus_count = self.milvus.count()
        bm25_count = len(self.bm25.documents)
        logger.info(f"[HybridRetrieval] Searching: '{query[:60]}' | "
                     f"Milvus docs={milvus_count}, BM25 docs={bm25_count}")

        # ── Step 0: Query expansion ──
        expanded_queries = self._expand_query(query)
        logger.info(f"[HybridRetrieval] Expanded to {len(expanded_queries)} queries: "
                     f"{[q[:40] for q in expanded_queries]}")

        # ── Step 1: Search with each expanded query ──
        all_vector_results = []
        all_bm25_results = []

        for q in expanded_queries:
            # Vector search
            try:
                q_embedding = self.embeddings.embed_query(q)
                vec_results = self.milvus.search(
                    q_embedding, top_k=top_k, category=category
                )
                all_vector_results.extend(vec_results)
            except Exception as e:
                logger.error(f"[HybridRetrieval] Embedding failed for '{q[:30]}': {e}")

            # BM25 search
            bm_results = self.bm25.search(q, top_k=top_k)
            all_bm25_results.extend(bm_results)

        logger.info(f"[HybridRetrieval] Vector: {len(all_vector_results)} results "
                     f"(from {len(expanded_queries)} queries)")
        logger.info(f"[HybridRetrieval] BM25: {len(all_bm25_results)} results "
                     f"(top score={all_bm25_results[0].get('score', 0):.4f})"
                     if all_bm25_results else "[HybridRetrieval] BM25: 0 results")

        # ── Step 2: Deduplicate & normalize ──
        all_vector_results = self._deduplicate(all_vector_results)
        all_bm25_results = self._deduplicate(all_bm25_results)

        all_vector_results = self._normalize_scores(all_vector_results)
        all_bm25_results = self._normalize_scores(all_bm25_results)

        # ── Step 3: Merge with weighted scores ──
        merged = self._merge_results(all_vector_results, all_bm25_results)
        logger.info(f"[HybridRetrieval] Merged: {len(merged)} unique docs "
                     f"(vec_weight={self.vector_weight}, bm25_weight={self.bm25_weight})")

        # ── Step 4: Rerank with Qwen LLM ──
        reranked = self.reranker.rerank(query, merged, top_k=settings.rerank_top_k)

        return reranked

    # ── Query expansion ─────────────────────────────────────

    def _expand_query(self, query: str) -> List[str]:
        """Generate alternative phrasings of the query via LLM.

        Falls back to the original query if LLM expansion fails.
        """
        # Short queries don't need expansion
        if len(query) <= 3:
            return [query]

        try:
            prompt = QUERY_EXPANSION_PROMPT.format(query=query)
            response = self.llm.generate_with_context(
                system_prompt="",
                user_message=prompt,
                max_tokens=200,
            )
            if response:
                lines = [q.strip() for q in response.strip().split('\n')
                         if q.strip()]
                # Remove numbering if present
                cleaned = []
                for line in lines:
                    line = re.sub(r'^[\d]+[\.\)、]?\s*', '', line)
                    if line and line not in cleaned:
                        cleaned.append(line)
                if cleaned:
                    # Always include the original query
                    if query not in cleaned:
                        cleaned.insert(0, query)
                    logger.info(f"[HybridRetrieval] Expanded '{query[:40]}' → "
                                 f"{[q[:40] for q in cleaned[1:]]}")
                    return cleaned[:4]  # Max 4 queries (original + 3 expanded)
        except Exception as e:
            logger.warning(f"[HybridRetrieval] Query expansion failed: {e}")

        return [query]

    # ── Score normalization ─────────────────────────────────

    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Min-max normalize scores to [0, 1] range."""
        if not results:
            return []
        scores = [r["score"] for r in results]
        min_s, max_s = min(scores), max(scores)
        if max_s == min_s:
            # All same score: give moderate normalized score (not 1.0)
            for r in results:
                r["normalized_score"] = 0.5 if max_s > 0 else 0.0
        else:
            for r in results:
                r["normalized_score"] = (r["score"] - min_s) / (max_s - min_s)
        return results

    # ── Merge ───────────────────────────────────────────────

    def _merge_results(self, vector_results: List[Dict[str, Any]],
                       bm25_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge vector and BM25 results by content hash key."""
        merged: Dict[str, dict] = {}

        for r in vector_results:
            key = self._make_key(r["content"])
            merged[key] = {
                **r,
                "score": r["normalized_score"] * self.vector_weight,
                "sources": ["vector"],
            }

        for r in bm25_results:
            key = self._make_key(r["content"])
            if key in merged:
                merged[key]["score"] += r["normalized_score"] * self.bm25_weight
                merged[key]["sources"].append("bm25")
            else:
                merged[key] = {
                    **r,
                    "score": r["normalized_score"] * self.bm25_weight,
                    "sources": ["bm25"],
                }

        return list(merged.values())

    # ── Deduplication ───────────────────────────────────────

    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate chunks (same content hash).

        Keeps the highest-scoring version of each unique chunk.
        """
        seen: Dict[str, dict] = {}
        for r in results:
            key = self._make_key(r["content"])
            if key not in seen or r.get("score", 0) > seen[key].get("score", 0):
                seen[key] = r
        return list(seen.values())

    # ── Utilities ───────────────────────────────────────────

    @staticmethod
    def _make_key(content: str) -> str:
        """Create a stable deduplication key from content via SHA256.

        More robust than content[:100] which could collide for
        different chunks that share a common prefix.
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
