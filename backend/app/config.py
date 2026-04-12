from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./data/life_assistant.db"
    ai_provider: str = "ollama"
    ai_model: str = ""
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:latest"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_api_key: str = ""
    openrouter_site_url: str = "http://127.0.0.1:5173"
    openrouter_app_name: str = "ai-life-assistant"
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"

    @property
    def default_model(self) -> str:
        if self.ai_model:
            return self.ai_model
        if self.ai_provider == "openrouter":
            return "openai/gpt-4o-mini"
        return self.ollama_model


settings = Settings()
