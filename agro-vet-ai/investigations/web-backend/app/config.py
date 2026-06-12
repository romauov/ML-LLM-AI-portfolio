"""Управление конфигурацией для VetRetro backend."""

from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Конфигурация LLM (провайдер-агностик: OpenRouter, локальный прокси, и т.д.)
    # LLM_API_BASE: str = "https://openrouter.ai/api/v1"
    # LLM_API_KEY: str = ""
    LLM_API_BASE: str = ""
    LLM_API_KEY: str = ""
    # # Модель LLM (можно переопределить через переменную окружения LLM_MODEL)
    # # Хорошие варианты:
    # # - minimax/minimax-m2 (хорошая, но любит крупные заголовки и emoji)
    # # - qwen/qwen3-coder-plus (хорошая, сдержанная по стилю, не многословная)
    # # - qwen/qwen3-next-80b-a3b-instruct (быстрая, толковая)
    # LLM_MODEL: str = "minimax/minimax-m2" # "qwen/qwen3-coder-plus"
    # LLM_MODEL: str = "qwen/qwen3-30b-a3b-instruct-2507" # начинает циклить :( вызывает vet_search до ошибки
    # LLM_MODEL: str = "qwen/qwen3-next-80b-a3b-instruct"
    # LLM_MODEL: str = "qwen/qwen3-vl-30b-a3b-instruct"
    LLM_MODEL: str = "minimax/minimax-m2:nitro"

    # MCP сервер (vetretro)
    VETRETRO_MCP_URL: str = "http://localhost:8765"

    # Пути приложения
    INVESTIGATIONS_DIR: Path = Path("/agent-workspace/investigations")
    AGENT_WORKSPACE_DIR: Path = Path("/agent-workspace")

    # Настройки сервера
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Настройки CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    # API Key for authentication
    API_KEY: str | None = None


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get global settings instance (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
