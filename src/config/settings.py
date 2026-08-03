import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://smartinbox_user:smartinbox_password@localhost:5432/smartinbox_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SPEECH_TO_TEXT_PROVIDER: str = "local"  # 'cloud' or 'local'
    OCR_PROVIDER: str = "local"             # 'cloud' or 'local'
    EMBEDDING_PROVIDER: str = "local"       # 'cloud' or 'local'
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    OPENAI_API_KEY: str = "mock-key"
    GEMINI_API_KEY: str = "mock-key"

    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.6
    SEMANTIC_LIMIT: int = 3

    PORT: int = 8000
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
