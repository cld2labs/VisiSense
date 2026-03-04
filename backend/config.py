from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """VisiSense - CatalogIQ Backend Configuration"""

    SERVICE_NAME: str = "VisiSense - CatalogIQ API"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8000

    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"

    TEMPERATURE: float = 0.3
    MAX_TOKENS: int = 2048
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 120

    MAX_IMAGE_SIZE_MB: int = 10
    MAX_IMAGES_PER_REQUEST: int = 5
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/webp"]

    CHAT_SESSION_TTL_MINUTES: int = 30
    CHAT_MAX_HISTORY_TURNS: int = 10

    CORS_ORIGINS: list = ["http://localhost:3000", "http://frontend:3000", "http://localhost:5173"]

    PYTHON_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
