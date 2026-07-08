"""
Re-rank retrieved documents using Qwen3-Rerank API.

Calls the DashScope-compatible Qwen3-Rerank model online — a dedicated
Cross-Encoder reranker that scores (query, document) pairs for relevance.
Much more accurate than character-matching, and no local GPU needed.
"""

import json
from typing import List, Dict, Any

import httpx

from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()

# Qwen3-Rerank API endpoint (DashScope-compatible)
RERANK_API_PATH = "/api/v1/services/rerank/text-rerank/text-rerank"


class Reranker:
    """Qwen3-Rerank API-based semantic re-ranker.

    Calls a hosted Cross-Encoder that scores each (query, document) pair.
    Uses the same API key and base URL as the LLM client.
    """

    def __init__(self):
        self.score_threshold = 0.2
        # Build full rerank URL from the LLM base URL
        # llm_api_base = "https://xxx.maas.aliyuncs.com/compatible-mode/v1"
        # → rerank_url = "https://xxx.maas.aliyuncs.com/api/v1/services/rerank/..."
        base = settings.llm_api_base.rstrip("/")
        # Strip the /compatible-mode/v1 suffix
        if base.endswith("/compatible-mode/v1"):
            base = base[:-len("/compatible-mode/v1")]
        self.rerank_url = f"{base}{RERANK_API_PATH}"
        self.api_key = settings.llm_api_key
        self.model = "qwen3-rerank"

    # ── Public API ──────────────────────────────────────────

    def rerank(self, query: str, documents: List[Dict[str, Any]],
               top_k: int = None) -> List[Dict[str, Any]]:
        """Re-rank documents using Qwen3-Rerank API.

        Args:
            query: User query string
            documents: List of doc dicts with 'content' and 'score' keys
            top_k: Number of documents to return

        Returns:
            Re-ranked list with rerank_score and ce_score fields added
        """
        if top_k is None:
            top_k = settings.rerank_top_k

        if not documents:
            logger.info("[Reranker] No documents to rerank")
            return []

        # Truncate long documents (API may have limits)
        truncated = [d.get("content", "")[:2000] for d in documents]

        logger.info(f"[Reranker] Calling Qwen3-Rerank for {len(truncated)} docs")

        # ── Call Qwen3-Rerank API ──
        try:
            scores = self._call_rerank_api(query, truncated)
        except Exception as e:
            logger.error(f"[Reranker] API call failed: {e}")
            return self._fallback_rerank(documents, top_k)

        # ── Apply scores ──
        for i, doc in enumerate(documents):
            ce_score = float(scores[i]) if i < len(scores) else 0.0
            doc["ce_score"] = round(ce_score, 4)
            # Blend: 30% retrieval score + 70% reranker score
            original = doc.get("score", 0)
            doc["rerank_score"] = round(original * 0.3 + ce_score * 0.7, 4)

        # ── Filter & sort ──
        filtered = [d for d in documents if d["rerank_score"] >= self.score_threshold]
        filtered.sort(key=lambda x: x["rerank_score"], reverse=True)

        result = filtered[:top_k]
        logger.info(
            f"[Reranker] Qwen3-Rerank → {len(result)}/{len(documents)} docs"
        )
        if result:
            logger.info(
                f"[Reranker] Top: ce={result[0].get('ce_score', 0):.4f} "
                f"final={result[0]['rerank_score']:.4f} "
                f"content[:80]={result[0].get('content', '')[:80]}"
            )

        return result

    # ── API call ────────────────────────────────────────────

    def _call_rerank_api(self, query: str, documents: List[str]) -> List[float]:
        """Call Qwen3-Rerank and return a list of relevance scores [0..1].

        Sends all documents in one batch.  Returns one score per document
        in the same order as the input list.
        """
        payload = {
            "model": self.model,
            "input": {
                "query": query,
                "documents": documents,
            },
            "parameters": {
                "return_documents": False,
                "top_n": len(documents),
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"[Reranker] POST {self.rerank_url}")
        logger.debug(f"[Reranker] Query: {query[:120]}, {len(documents)} docs")

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self.rerank_url,
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"Rerank API returned {response.status_code}: "
                f"{response.text[:500]}"
            )

        data = response.json()

        # Parse response — handles both formats:
        #   {"output": {"results": [...]}}   (DashScope standard)
        #   {"results": [...]}               (some compatible APIs)
        output = data.get("output", data)
        results = output.get("results", [])
        if not results:
            raise RuntimeError(f"Rerank API returned empty results: {data}")

        # Build scores array ordered by original document index
        scores = [0.0] * len(documents)
        for r in results:
            idx = r.get("index", -1)
            score = r.get("relevance_score", 0.0)
            if 0 <= idx < len(scores):
                scores[idx] = score

        logger.info(
            f"[Reranker] API returned {len(results)} scores, "
            f"range=[{min(scores):.4f}, {max(scores):.4f}]"
        )
        return scores

    # ── Fallback ────────────────────────────────────────────

    def _fallback_rerank(self, documents: List[Dict[str, Any]],
                         top_k: int) -> List[Dict[str, Any]]:
        """Simple score-based sort when rerank API is unavailable."""
        logger.warning("[Reranker] Falling back to score-based sort")
        for doc in documents:
            doc["rerank_score"] = doc.get("score", 0)
            doc["ce_score"] = None
        documents.sort(key=lambda x: x["rerank_score"], reverse=True)
        filtered = [d for d in documents if d["rerank_score"] >= self.score_threshold]
        return filtered[:top_k]
