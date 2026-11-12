"""Environment-backed application settings."""

from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from the environment and an optional .env file."""

    app_env: str = "development"
    app_name: str = "front-desk-backend"
    log_level: str = "INFO"
    cors_allowed_origins: str = "http://localhost:3000"
    agent_api_token: str = ""
    mews_nolita_api_url: str = ""
    mews_nolita_client_token: str = ""
    mews_nolita_access_token: str = ""
    mews_nap_york_api_url: str = ""
    mews_nap_york_client_token: str = ""
    mews_nap_york_access_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    def mews_property(self, property_id: "BookingProperty") -> "MewsPropertySettings | None":
        values = {
            BookingProperty.NOLITA: (
                self.mews_nolita_api_url,
                self.mews_nolita_client_token,
                self.mews_nolita_access_token,
            ),
            BookingProperty.NAP_YORK: (
                self.mews_nap_york_api_url,
                self.mews_nap_york_client_token,
                self.mews_nap_york_access_token,
            ),
        }[property_id]
        api_url, client_token, access_token = (value.strip() for value in values)
        if not all((api_url, client_token, access_token)):
            return None
        return MewsPropertySettings(
            api_url=api_url.rstrip("/"),
            client_token=client_token,
            access_token=access_token,
        )


class BookingProperty(str, Enum):
    NOLITA = "nolita"
    NAP_YORK = "nap_york"


@dataclass(frozen=True)
class MewsPropertySettings:
    api_url: str
    client_token: str
    access_token: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
