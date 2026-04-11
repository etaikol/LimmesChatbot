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

from pydantic import Field, field_validator, model_validator
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
    llm_max_tokens: Optional[int] = 1024
    llm_request_timeout: int = 30
    embedding_model: str = "text-embedding-3-small"

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # ── RAG ──────────────────────────────────────────────────────────────────
    chunk_size: int = 1000
    chunk_overlap: int = 200
    retrieval_k: int = 4
    retrieval_min_score: float = 0.3
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
    api_cors_origins: str = "http://localhost:8000"  # comma-separated; set to your real domain(s) in production
    # When true (recommended for production) the app refuses to start if
    # API_CORS_ORIGINS is "*" or empty.
    api_strict_cors: bool = True
    # Optional shared secret for the /chat endpoint. When set the caller
    # (e.g. a WordPress site) must send:  X-Api-Key: <value>
    # Empty string = disabled (open access, rate-limiting still applies).
    chatbot_api_key: str = ""

    # ── Security: input + transport hardening ────────────────────────────────
    # Hard cap on the request body in bytes (Content-Length). 64 KiB is
    # plenty for chat. Anything bigger is rejected at the middleware layer
    # before pydantic ever sees it.
    api_max_body_bytes: int = 64 * 1024
    # Hard cap on a single user message in characters.
    max_message_chars: int = 4000
    # Add Strict-Transport-Security header (only enable behind real HTTPS).
    api_hsts_enabled: bool = False
    api_hsts_max_age: int = 31536000  # 1 year

    # ── Security: rate limiting (token bucket) ───────────────────────────────
    # All limits are *per process*. For multi-instance deployments, swap
    # the in-memory bucket store for Redis.
    rate_limit_enabled: bool = True
    # Per source IP — protects the public surface from random scanners.
    rate_limit_ip_per_minute: int = 20
    rate_limit_ip_burst: int = 6
    # Per session_id — protects against a single chat tab spamming.
    rate_limit_session_per_minute: int = 8
    rate_limit_session_burst: int = 3

    # ── Security: spam / gibberish detection ─────────────────────────────────
    # Blocks meaningless messages (key-mashing, single chars, duplicates)
    # BEFORE they reach the LLM, saving tokens and money.
    spam_detection_enabled: bool = True
    # Consecutive bad messages before a temporary session block.
    spam_max_strikes: int = 5
    # Initial cooldown (seconds) after max_strikes. Doubles each time.
    spam_cooldown_seconds: float = 30.0
    # Upper bound on the escalating cooldown.
    spam_max_cooldown_seconds: float = 300.0
    # Minimum characters for a message to be considered meaningful.
    spam_min_message_chars: int = 2

    # ── Security: prompt injection ───────────────────────────────────────────
    # When true, messages that match prompt-injection heuristics are
    # rejected outright (HTTP 400) rather than just logged.
    block_prompt_injection: bool = True

    # ── Security: daily spend / token budget ─────────────────────────────────
    # 0 = disabled. Recommended starting point: a few dollars / day until
    # you have telemetry from real traffic.
    daily_token_cap: int = 500_000
    daily_usd_cap: float = 3.0
    budget_state_file: Path = PROJECT_ROOT / ".budget" / "state.json"
    # Override price table when your model isn't covered by defaults.
    price_in_usd_per_1k: float = 0.0
    price_out_usd_per_1k: float = 0.0

    # ── Twilio (WhatsApp / SMS) ──────────────────────────────────────────────
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_number: str = ""

    # ── Telegram ─────────────────────────────────────────────────────────────
    telegram_bot_token: str = ""
    # Telegram lets you pass a secret token when registering the webhook
    # via setWebhook(secret_token=...). They then send it back in the
    # X-Telegram-Bot-Api-Secret-Token header on every update. Set this
    # to the same string and we will reject webhooks without it.
    telegram_webhook_secret: str = ""

    # ── Admin dashboard ────────────────────────────────────────────────────────
    # API key for the /admin endpoints. When empty the dashboard is disabled.
    admin_api_key: str = "Admin5!"

    # ── LINE Messaging ───────────────────────────────────────────────────────
    line_channel_secret: str = ""
    line_channel_access_token: str = ""

    # ── Contact / Email ──────────────────────────────────────────────────────
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    contact_to_email: str = ""      # admin inbox
    contact_from_email: str = ""    # defaults to smtp_user when empty

    # ── Human handoff ────────────────────────────────────────────────────────
    handoff_enabled: bool = True

    # ── Proactive widget message ─────────────────────────────────────────────
    proactive_delay_seconds: int = 60
    proactive_message: str = ""     # empty = use i18n default

    # ── Validators ───────────────────────────────────────────────────────────
    @model_validator(mode="after")
    def _default_log_file(self) -> "Settings":
        """Auto-set log_file to logs/<client>/<client>.log when not explicitly set.

        Convention: logs/limmes/limmes.log — loguru daily rotation then creates
        timestamped archives like logs/limmes/limmes.2026-04-11_00-00-00.log.
        """
        if self.log_file is None:
            self.log_file = (
                PROJECT_ROOT / "logs" / self.active_client / f"{self.active_client}.log"
            )
        return self

    @field_validator(
        "vectorstore_dir",
        "sessions_dir",
        "data_dir",
        "budget_state_file",
        mode="before",
    )
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
        self.budget_state_file.parent.mkdir(parents=True, exist_ok=True)
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def assert_production_safe(self) -> None:
        """Raise ConfigError when running prod with insecure defaults.

        Called from the FastAPI lifespan when ``api_strict_cors`` is on.
        """
        from chatbot.exceptions import ConfigError

        if self.api_strict_cors and self.api_cors_origins.strip() in ("", "*"):
            raise ConfigError(
                "API_STRICT_CORS=true but API_CORS_ORIGINS is unset or '*'. "
                "Set it to your real client domains, e.g. "
                "API_CORS_ORIGINS=https://example.com,https://www.example.com"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton Settings instance."""
    return Settings()  # type: ignore[call-arg]
