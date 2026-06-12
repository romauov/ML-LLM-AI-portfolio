from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Secrets(BaseSettings):
    # Telegram
    api_token: str

    # LLM настройки
    use_ollama_only: bool | None = None
    
    vsegpt_api_key: str
    inline_api_key: str | None = None
    openrouter_api_key: str | None = None
    ollama_api_key: str | None = None
    deepseek_api_key: str | None = None # для судьи

    vsegpt_base_url: str
    inline_base_url: str
    openrouter_base_url: str
    ollama_base_url: str

    organization: str | None = None
    project_id: str | None = None
    request_timeout: int = 30

    # API Key for authentication
    api_key: str | None = None

    # Database
    postgres_user: str
    postgres_password: str
    postgres_db: str
    db_host: str
    db_port_container: int
    db_port_host: int

    # Application settings
    mode: str
    proxy: str | None = None

    # Knowledge base settings
    knowledge_base_type: str = "file"
    knowledge_base_path: str = "knowledge/data"

    # InlineGPT parameters (используется для InlineGPT и VseGPT)
    inline_temperature: float = 0.7
    inline_top_p: float = 0.8
    inline_max_tokens: int = 2000
    inline_frequency_penalty: float = 0.1
    inline_presence_penalty: float = 0.1

    # Ollama parameters
    ollama_temperature: float = 0.3
    ollama_top_p: float = 0.8
    ollama_top_k: int = 20
    ollama_repeat_penalty: float = 1.1
    ollama_num_predict: int = 300
    ollama_num_ctx: int = 4096

    # Docker
    # compose_project_name: str
    api_service_host_port: str | None = None
    api_service_container_port: str | None = None
    pgadmin_port: str | None = None
    pgadmin_email: str | None = None
    pgadmin_password: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def validated_mode(self):
        """Validate that mode is one of the allowed values."""
        valid_modes = ['prod', 'dev', 'debug']
        if self.mode not in valid_modes:
            print(f"Warning: Invalid mode '{self.mode}'. Using 'prod' mode.")
            self.mode = 'prod'
        return self.mode


secrets = Secrets()
