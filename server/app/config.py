from pydantic_settings import BaseSettings
import os
from pydantic import field_validator
from functools import lru_cache


# Compute absolute path to project root (server/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # Application
    app_name: str = "customer-service-agent"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    server_url: str = "http://localhost:8000"

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
    milvus_dim: int = 1024

    # LLM API (Tongyi Qianwen / OpenAI-compatible)
    llm_api_key: str = ""
    llm_api_base: str = "https://llm-08gz321sv9ae7d2n.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen3.7-max"

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def resolve_api_key(cls, v):
        if not v:
            return os.environ.get("DASHSCOPE_API_KEY", "")
        return v

    # Embedding
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024

    # RAG Configuration
    data_dir: str = os.path.join(_PROJECT_ROOT, "data")
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
        return (f"mysql+pymysql://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
                f"?charset=utf8mb4")

    @property
    def milvus_uri(self) -> str:
        return f"http://{self.milvus_host}:{self.milvus_port}"

    class Config:
        env_file = os.path.join(_PROJECT_ROOT, ".env")
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
