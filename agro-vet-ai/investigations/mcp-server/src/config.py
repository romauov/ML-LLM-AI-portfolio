"""Модуль конфигурации для VetRetro MCP Server.

Загружает конфигурацию из переменных окружения с использованием pydantic-settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения, загружаемые из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Конфигурация базы данных
    db_host: str = Field(default="10.0.3.123", description="Хост PostgreSQL")
    db_port: int = Field(default=5432, description="Порт PostgreSQL")
    db_name: str = Field(default="vetbot", description="Имя базы данных")
    db_user: str = Field(default="vetbot", description="Пользователь БД")
    db_password: str = Field(default="vetbot", description="Пароль БД")

    # Конфигурация OpenAI API
    openai_api_key: str = Field(..., description="API ключ OpenAI для эмбеддингов")
    openai_api_base: str = Field(
        default="https://api.vsegpt.ru/v1",
        description="Базовый URL OpenAI API",
    )

    # Конфигурация эмбеддингов
    # ВАЖНО: Модель фиксирована и должна соответствовать эмбеддингам в БД
    # Не переопределяется через переменные окружения
    @property
    def embedding_model(self) -> str:
        """Модель эмбеддингов (фиксированная, соответствует данным в БД)."""
        return "text-embedding-3-small"

    @property
    def embedding_dimension(self) -> int:
        """Размерность векторов эмбеддингов (фиксированная)."""
        return 1536

    # Конфигурация векторного поиска
    similarity_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=2.0,
        description="Максимальное расстояние (distance) для результатов поиска (меньше = лучше)",
    )

    # Логирование
    log_level: str = Field(
        default="INFO",
        description="Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    @property
    def database_url(self) -> str:
        """Формирование URL подключения к PostgreSQL."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# Глобальный экземпляр настроек
settings = Settings()
