"""Environment-driven settings. Copy .env.example -> .env and fill in."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-5-nano"

    sandbox_image: str = "parscript-sandbox"
    sandbox_timeout_seconds: int = 10

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
