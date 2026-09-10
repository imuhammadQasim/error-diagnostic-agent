from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- App identity ---
    app_name: str = "Production Incident Investigation Agent"
    environment: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"

    # --- LLM provider (switch via LLM_PROVIDER; only the selected provider's
    # key is required) ---
    llm_provider: Literal["anthropic", "groq", "gemini"] = "anthropic"
    llm_temperature: float = 0.0

    anthropic_api_key: str = Field(default="")
    anthropic_model: str = "claude-sonnet-5"

    groq_api_key: str = Field(default="")
    groq_model: str = "llama-3.3-70b-versatile"

    gemini_api_key: str = Field(default="")
    gemini_model: str = "gemini-2.0-flash"

    # --- LangSmith tracing ---
    # LangSmith reads LANGSMITH_TRACING / LANGSMITH_API_KEY / LANGSMITH_PROJECT
    # from the environment itself, so these fields exist to (a) give us one
    # place to see/validate the tracing config and (b) fail fast with a clear
    # error if tracing is enabled but no API key was provided.
    langsmith_tracing: bool = False
    langsmith_api_key: str = Field(default="")
    langsmith_project: str = "incident-investigation-agent"

    # --- Data source (static JSON files for now, see docs/data_strategy.md) ---
    data_dir: Path = PROJECT_ROOT / "data"

    # --- Agent safety limits ---
    # Hard ceiling on tool-call steps per investigation, so a confused agent
    # cannot loop indefinitely and run up cost/latency. Passed to LangGraph
    # as `recursion_limit` in app/services/incident_service.py.
    agent_max_iterations: int = 8

    # --- Real external APIs (see docs/real_apis.md for why these two) ---
    github_status_url: str = "https://www.githubstatus.com/api/v2/status.json"
    time_api_base_url: str = "https://timeapi.io/api"
    external_api_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so the .env file is parsed once per process, and so every part of
    the app (routes, services, tools) shares the same configuration object
    instead of each re-reading the environment.
    """
    return Settings()
