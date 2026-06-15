from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    fireflies_api_key: str | None = Field(default=None, alias="FIREFLIES_API_KEY")
    fireflies_graphql_url: str = Field(
        default="https://api.fireflies.ai/graphql",
        alias="FIREFLIES_GRAPHQL_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173"],
        alias="CORS_ORIGINS",
    )
    request_timeout_seconds: float = Field(default=30.0, alias="REQUEST_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
