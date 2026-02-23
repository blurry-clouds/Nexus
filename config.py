from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    server_name: str = "NEXUS"
    discord_token: str = ""

    # AI provider routing
    # anthropic | puter_js | openai_compatible
    ai_provider: str = "anthropic"
    ai_model: str = "claude-sonnet-4-6"
    ai_base_url: str = ""

    # Direct Anthropic API
    anthropic_api_key: str = ""

    # OpenAI-compatible key (for proxies exposing /chat/completions)
    openai_compatible_api_key: str = ""

    # Puter.js runtime tuning
    puter_script_url: str = "https://js.puter.com/v2/"
    puter_timeout_seconds: int = 90

    twitch_client_id: str = ""
    twitch_client_secret: str = ""

    database_url: str = "postgresql+asyncpg://nexus:change_me@postgres:5432/nexus"
    redis_url: str = "redis://redis:6379/0"

    log_level: str = "INFO"
    tz: str = "UTC"


@lru_cache
def get_settings() -> Settings:
    return Settings()
