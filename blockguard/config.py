from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "dev"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/blockguard"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    vectorstore_dir: str = "/workspace/data/vectorstore"
    knowledge_base_dir: str = "/workspace/data/knowledge_base"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()