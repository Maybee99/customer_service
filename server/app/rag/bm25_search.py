import pickle
import os
from typing import List, Dict, Any
from ..config import get_settings
from ..rag.tokenizer import tokenize
from ..utils.logger import logger

settings = get_settings()


class BM25Search:
    """BM25 keyword-based search for lexical matching"""

    def __init__(self):
        self.index_path = os.path.join(settings.data_dir, "bm25_index.pkl")
        self.bm25 = None
        self.documents = []
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "rb") as f:
                    data = pickle.load(f)
                    self.bm25 = data.get("bm25")
                    self.documents = data.get("documents", [])
                logger.info(f"Loaded BM25 index ({len(self.documents)} docs)")
            except Exception as e:
                logger.error(f"Failed to load BM25 index: {e}")

    def save_index(self, bm25, documents: List[Dict[str, Any]]):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": bm25, "documents": documents}, f)
        self.bm25 = bm25
        self.documents = documents
        logger.info(f"Saved BM25 index ({len(documents)} docs)")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # Auto-reload if index is empty (may have been rebuilt by importer)
        if self.bm25 is None or not self.documents:
            self._load_index()
        if self.bm25 is None or not self.documents:
            return []
        try:
            # Use shared jieba tokenizer — same as index build
            tokenized = tokenize(query, remove_stopwords=True)
            if not tokenized:
                return []
            scores = self.bm25.get_scores(tokenized)
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append({**self.documents[idx], "score": float(scores[idx]), "type": "bm25"})
            return results
        except Exception as e:
            logger.error(f"BM25 search failed: {e}")
            return []
