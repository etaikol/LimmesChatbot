"""
FastAPI application factory.

The app holds a single global `Chatbot` instance, built once at startup
through the lifespan context. Routes import the bot via dependency
injection (``request.app.state.bot``).

Security wiring:
    - SecurityHeadersMiddleware adds standard hardening headers and
      enforces a Content-Length cap *before* JSON parsing.
    - Two RateLimiters live on ``app.state``: per-IP and per-session.
      The ``/chat`` route consults both before delegating to the engine.
    - A global exception handler converts any ChatbotError into a clean
      HTTP response so we never leak provider tracebacks to clients.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from chatbot.api.routes import admin, chat, health, webhooks, widget
from chatbot.core.engine import Chatbot
from chatbot.exceptions import (
    AbuseError,
    BudgetError,
    ChatbotError,
    LLMError,
)
from chatbot.logging_setup import logger, setup_logging
from chatbot.security import RateLimiter, SecurityHeadersMiddleware, SpamTracker
from chatbot.security.rate_limit import RateLimitExceeded
from chatbot.settings import get_settings


# Map exception classes to HTTP status codes. Keep this in one place so
# every route returns the same status for the same failure mode.
_STATUS_FOR: dict[type[ChatbotError], int] = {
    AbuseError:    429,  # Too Many Requests
    BudgetError:   402,  # Payment Required (semantic match for spend cap)
    LLMError:      502,  # Bad Gateway — upstream provider failed
    ChatbotError:  500,
}


def _status_for(exc: ChatbotError) -> int:
    for cls, code in _STATUS_FOR.items():
        if isinstance(exc, cls):
            return code
    return 500


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        json_format=settings.log_format == "json",
    )
    settings.ensure_dirs()
    settings.assert_production_safe()

    logger.info(
        "API starting (client={}, model={})",
        settings.active_client,
        settings.llm_model,
    )

    bot = Chatbot.from_env()
    app.state.bot = bot

    # ── Rate limiters (per-IP and per-session) ─────────────────────────
    if settings.rate_limit_enabled:
        app.state.ip_limiter = RateLimiter(
            name="per_ip",
            capacity=settings.rate_limit_ip_burst,
            refill_rate=settings.rate_limit_ip_per_minute / 60.0,
        )
        app.state.session_limiter = RateLimiter(
            name="per_session",
            capacity=settings.rate_limit_session_burst,
            refill_rate=settings.rate_limit_session_per_minute / 60.0,
        )
        logger.info(
            "Rate limiting enabled: ip={}/min (burst {}) session={}/min (burst {})",
            settings.rate_limit_ip_per_minute,
            settings.rate_limit_ip_burst,
            settings.rate_limit_session_per_minute,
            settings.rate_limit_session_burst,
        )
    else:
        app.state.ip_limiter = None
        app.state.session_limiter = None
        logger.warning("Rate limiting DISABLED — every public endpoint is wide open")

    # ── Spam / gibberish detection ─────────────────────────────────────
    if settings.spam_detection_enabled:
        app.state.spam_tracker = SpamTracker(
            max_strikes=settings.spam_max_strikes,
            cooldown_seconds=settings.spam_cooldown_seconds,
            max_cooldown_seconds=settings.spam_max_cooldown_seconds,
        )
        logger.info(
            "Spam detection enabled: max_strikes={} cooldown={}s",
            settings.spam_max_strikes,
            settings.spam_cooldown_seconds,
        )
    else:
        app.state.spam_tracker = None

    # ── Admin dashboard ────────────────────────────────────────────────
    app.state.admin_api_key = settings.admin_api_key
    if settings.admin_api_key:
        admin.set_start_time()
        logger.info("Admin dashboard enabled at /admin")
    else:
        logger.info("Admin dashboard disabled (ADMIN_API_KEY not set)")

    logger.info("API ready: {}", bot.profile.client.name)
    yield
    logger.info("API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Limmes Chatbot API",
        version="0.3.0",
        description=(
            "Multi-channel AI chatbot template. Includes web widget, "
            "WhatsApp (Twilio), Telegram, and LINE webhooks. "
            "Hardened with rate limiting, body-size caps, prompt-injection "
            "heuristics and a daily token/spend budget."
        ),
        lifespan=lifespan,
    )

    # ── Middleware order matters: outermost runs first on requests ─────

    # 1. CORS — first because preflight OPTIONS requests must succeed
    #    even when other middleware would otherwise block them.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Session-Id", "X-Api-Key", "X-Admin-Key"],
        max_age=600,
    )

    # 2. Security headers + body-size guard.
    app.add_middleware(
        SecurityHeadersMiddleware,
        max_body_bytes=settings.api_max_body_bytes,
        hsts_enabled=settings.api_hsts_enabled,
        hsts_max_age=settings.api_hsts_max_age,
    )

    # ── Global exception handlers ─────────────────────────────────────

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(_: Request, exc: RateLimitExceeded):
        return JSONResponse(
            {
                "detail": (
                    "Too many requests. Please slow down and try again "
                    f"in {int(exc.retry_after) + 1}s."
                )
            },
            status_code=429,
            headers={"Retry-After": str(int(exc.retry_after) + 1)},
        )

    @app.exception_handler(ChatbotError)
    async def _chatbot_error_handler(_: Request, exc: ChatbotError):
        return JSONResponse(
            {"detail": exc.user_message},
            status_code=_status_for(exc),
        )

    # ── Routers ───────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(webhooks.router, prefix="/webhook")
    app.include_router(widget.router)
    app.include_router(admin.router)  # /admin/api/*

    @app.get("/admin", response_class=HTMLResponse)
    def admin_dashboard() -> str:
        from chatbot.api.routes.admin_ui import dashboard_html
        return dashboard_html()

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> str:
        from chatbot.api.routes.widget import demo_page

        bot = request.app.state.bot
        base = str(request.base_url).rstrip("/")
        return demo_page(base_url=base, bot=bot)

    return app


# Convenience for `uvicorn chatbot.api.app:app`
app = create_app()
