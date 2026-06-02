from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="LEGAL_AGENT_", extra="ignore")

    model: str = Field(default="gpt-5.2", description="OpenAI model used by the agent.")
    jurisdiction: str = Field(default="United States", description="Default legal jurisdiction.")
    source_dir: Path = Field(default=Path("data/legal_sources"), description="Local legal source folder.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
