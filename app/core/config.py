from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    # Session
    session_ttl_minutes: int = 60
    session_enable_summarization: bool = False

    # RAG
    rag_similarity_threshold: float = 0.35
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # App
    app_env: str = "production"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
