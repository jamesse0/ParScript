"""Environment-driven settings. Copy .env.example -> .env and fill in."""

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_jwt_secret: str = ""

    openai_api_key: str = ""
    openai_model: str = "gpt-5-nano"
    # Output-token ceiling per call. gpt-5-* are reasoning models: hidden
    # reasoning tokens bill as output and count against this, so leave headroom.
    openai_max_completion_tokens: int = 6000

    sandbox_image: str = "parscript-sandbox"
    sandbox_timeout_seconds: int = 10

    # CORS_ORIGINS is a plain comma-separated string in .env, e.g.
    #   CORS_ORIGINS=http://localhost:5173,https://parscript.example
    # NoDecode stops pydantic-settings from trying to JSON-parse it first.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("supabase_url", mode="after")
    @classmethod
    def _normalize_supabase_url(cls, value: str) -> str:
        # Accept a pasted REST endpoint (…supabase.co/rest/v1/) or a trailing
        # slash; the client wants just the bare project URL.
        value = value.strip().rstrip("/")
        if value.endswith("/rest/v1"):
            value = value[: -len("/rest/v1")]
        return value


settings = Settings()
