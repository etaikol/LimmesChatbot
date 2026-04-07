"""
Application settings.

All values are loaded from environment variables (or a `.env` file) using
pydantic-settings. Sensible defaults make it possible to run with zero config
besides an `OPENAI_API_KEY`.

Edit `.env` to override anything. See `.env.example` for the full list.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Top-level application settings.

    Environment variables map directly to fields below (case-insensitive).
    Example: `OPENAI_API_KEY=sk-...` sets `settings.openai_api_key`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Runtime ──────────────────────────────────────────────────────────────
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_file: Optional[Path] = None
    log_format: Literal["pretty", "json"] = "pretty"

    # Active client config (looks under `config/clients/<name>.yaml`)
    active_client: str = "default"

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    llm_max_tokens: Optional[int] = None
    embedding_model: str = "text-embedding-3-small"

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # ── RAG ──────────────────────────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4
    vectorstore_dir: Path = PROJECT_ROOT / ".vectorstore"
    data_dir: Path = PROJECT_ROOT / "data"

    # ── Memory / sessions ────────────────────────────────────────────────────
    memory_backend: Literal["memory", "file", "postgres"] = "file"
    sessions_dir: Path = PROJECT_ROOT / ".sessions"
    max_history_turns: int = 10

    # ── PostgreSQL (optional) ───────────────────────────────────────────────
    postgres_dsn: str = ""

    # ── HTTP API ─────────────────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "*"  # comma-separated; "*" allows all

    # ── Twilio (WhatsApp / SMS) ──────────────────────────────────────────────
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    # ── Telegram ─────────────────────────────────────────────────────────────
    telegram_bot_token: str = ""

    # ── LINE Messaging ───────────────────────────────────────────────────────
    line_channel_secret: str = ""
    line_channel_access_token: str = ""

    # ── Validators ───────────────────────────────────────────────────────────
    @field_validator("vectorstore_dir", "sessions_dir", "data_dir", mode="before")
    @classmethod
    def _expand_paths(cls, v):
        if isinstance(v, str):
            v = Path(v).expanduser()
        if isinstance(v, Path) and not v.is_absolute():
            v = (PROJECT_ROOT / v).resolve()
        return v

    # ── Helpers ──────────────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> list[str]:
        if self.api_cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.api_cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        """Create runtime directories if they don't yet exist."""
        for path in (self.vectorstore_dir, self.sessions_dir, self.data_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]
