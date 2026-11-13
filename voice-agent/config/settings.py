"""Voice-agent configuration loaded from the environment."""

from functools import lru_cache
from typing import Mapping

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(".env.local")

REQUIRED_ENV_VARS = (
    "LIVEKIT_URL",
    "LIVEKIT_API_KEY",
    "LIVEKIT_API_SECRET",
    "GOOGLE_API_KEY",
    "BACKEND_API_URL",
    "BACKEND_API_TOKEN",
)


class Settings(BaseSettings):
    """Settings required before the worker may contact LiveKit or Google."""

    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    google_api_key: str = ""
    backend_api_url: str = ""
    backend_api_token: str = ""
    google_realtime_model: str = "gemini-3.8-live"
    google_realtime_voice: str = "Puck"
    agent_name: str = "front-desk"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Readiness(BaseModel):
    """Local configuration check. This does not contact LiveKit or Google."""

    ready: bool
    missing: list[str] = Field(default_factory=list)
    livekit_connected: bool = False
    google_connected: bool = False


def assess_readiness(env: Mapping[str, str]) -> Readiness:
    missing = [name for name in REQUIRED_ENV_VARS if not env.get(name, "").strip()]
    return Readiness(ready=not missing, missing=missing)


@lru_cache
def get_settings() -> Settings:
    return Settings()
