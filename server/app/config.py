 from pydantic_settings import BaseSettings
 from functools import lru_cache


 class Settings(BaseSettings):
     # Application
     app_name: str = "customer-service-agent"
     app_env: str = "development"
     debug: bool = True
     log_level: str = "INFO"

     # Database (MySQL)
     db_host: str = "localhost"
     db_port: int = 3307
     db_user: str = "customer"
     db_password: str = "customer123"
     db_name: str = "customer_service"

     # Redis
     redis_url: str = "redis://localhost:6380/0"

     # Milvus Vector Database
     milvus_host: str = "localhost"
     milvus_port: int = 19530
     milvus_collection: str = "customer_service_kb"
     milvus_dim: int = 1536  # text-embedding-v3 dimension

     # LLM API (Tongyi Qianwen / OpenAI-compatible)
     llm_api_key: str = ""
     llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
     llm_model: str = "qwen-plus"

     # Embedding
     embedding_model: str = "text-embedding-v3"
     embedding_dim: int = 1536

     # RAG Configuration
     data_dir: str = "./data"
     chunk_size: int = 512
     chunk_overlap: int = 128
     top_k_retrieval: int = 5
     rerank_top_k: int = 3
     vector_weight: float = 0.7
     bm25_weight: float = 0.3

     # Conversation
     conversation_timeout_minutes: int = 30
     max_context_messages: int = 5

     @property
     def database_url(self) -> str:
         return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

     @property
     def milvus_uri(self) -> str:
         return f"http://{self.milvus_host}:{self.milvus_port}"

     class Config:
         env_file = ".env"
         case_sensitive = False


 @lru_cache()
 def get_settings() -> Settings:
     return Settings()
