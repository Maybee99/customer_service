 from typing import List
 from app.config import get_settings
 from app.utils.logger import logger

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

     def embed_query(self, text: str) -> List[float]:
         client = self._get_client()
         response = client.embeddings.create(model=self.model, input=[text])
         return response.data[0].embedding

     def embed_documents(self, texts: List[str]) -> List[List[float]]:
         if not texts:
             return []
         client = self._get_client()
         response = client.embeddings.create(model=self.model, input=texts)
         sorted_data = sorted(response.data, key=lambda x: x.index)
         return [item.embedding for item in sorted_data]
