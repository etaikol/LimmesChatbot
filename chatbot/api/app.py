"""
FastAPI application factory.

The app holds a single global `Chatbot` instance, built once at startup
through the lifespan context. Routes import the bot via dependency injection
(`request.app.state.bot`).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from chatbot.api.routes import chat, health, webhooks, widget
from chatbot.core.engine import Chatbot
from chatbot.logging_setup import logger, setup_logging
from chatbot.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        json_format=settings.log_format == "json",
    )
    settings.ensure_dirs()

    logger.info("API starting (client={}, model={})", settings.active_client, settings.llm_model)

    bot = Chatbot.from_env()
    app.state.bot = bot

    logger.info("API ready: {}", bot.profile.client.name)
    yield
    logger.info("API shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Limmes Chatbot API",
        version="0.2.0",
        description=(
            "Multi-channel AI chatbot template. Includes web widget, "
            "WhatsApp (Twilio), Telegram, and LINE webhooks."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(webhooks.router, prefix="/webhook")
    app.include_router(widget.router)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> str:
        from chatbot.api.routes.widget import demo_page

        bot = request.app.state.bot
        base = str(request.base_url).rstrip("/")
        return demo_page(base_url=base, bot=bot)

    return app


# Convenience for `uvicorn chatbot.api.app:app`
app = create_app()
