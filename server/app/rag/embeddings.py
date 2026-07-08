from typing import List
from ..config import get_settings
from ..utils.logger import logger

settings = get_settings()


class EmbeddingService:
    """Text embedding service via DashScope / OpenAI-compatible API"""

    def __init__(self):
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=settings.llm_api_key,
                    base_url=settings.llm_api_base,
                )
                logger.info(f"Embedding client initialized (model={self.model})")
            except Exception as e:
                logger.error(f"Failed to init embedding client: {e}")
                raise
        return self._client

    def _create_embedding(self, client, texts):
        """Call embedding API, falling back if 'dimensions' param is not supported."""
        try:
            return client.embeddings.create(
                model=self.model, input=texts, dimensions=self.dim
            )
        except Exception as e:
            err_msg = str(e).lower()
            if 'dimension' in err_msg or 'unsupported' in err_msg or 'invalid' in err_msg:
                logger.warning(f"[Embedding] 'dimensions' param failed ({e}), retrying without")
                return client.embeddings.create(model=self.model, input=texts)
            raise

    def embed_query(self, text: str) -> List[float]:
        client = self._get_client()
        response = self._create_embedding(client, [text])
        embedding = response.data[0].embedding
        logger.info(f"[Embedding] Generated query embedding (dim={len(embedding)})")
        return embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        client = self._get_client()
        response = self._create_embedding(client, texts)
        sorted_data = sorted(response.data, key=lambda x: x.index)
        embeddings = [item.embedding for item in sorted_data]
        logger.info(f"[Embedding] Generated {len(embeddings)} doc embeddings (dim={len(embeddings[0]) if embeddings else 0})")
        return embeddings
