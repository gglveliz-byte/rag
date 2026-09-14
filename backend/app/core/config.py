"""Global application settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings loaded from environment or .env."""

    # Project metadata
    PROJECT_NAME: str = "RAG Knowledge Engine"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = False

    # Alibaba DashScope Embeddings (Singapore)
    DASHSCOPE_API_KEY: str = ""
    DASHSCOPE_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    DASHSCOPE_MODEL: str = "text-embedding-v3"
    EMBEDDING_DIMENSIONS: int = 1024
    EMBEDDING_BATCH_SIZE: int = 10
    USE_MOCK_EMBEDDINGS: bool = False
    DASHSCOPE_RPM_LIMIT: int = 60

    # Alibaba Qwen LLM Generation (US Virginia)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://ws-lghtetahpb40cmex.us-east-1.maas.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.8-flash"

    # Vector Databases
    POSTGRES_URL: str = "postgresql://rag:rag@localhost:5432/ragdb"
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "ragdb"

    # Security & Multi-Tenancy
    SECRET_KEY: str = "rag-knowledge-engine-insecure-secret-key-change-in-prod-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    GUEST_SESSION_TTL_HOURS: int = 24

    # Limits & Storage
    MAX_FILE_SIZE_MB: int = 500
    MAX_CONCURRENT_JOBS: int = 3
    STORAGE_DIR: Path = Path("storage")
    UPLOAD_DIR: Path = Path("storage/uploads")
    BACKUP_DIR: Path = Path("storage/backups")

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert comma-separated CORS origins to a string list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
