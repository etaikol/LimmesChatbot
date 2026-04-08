"""Health and status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from chatbot.api.schemas import HealthReply

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthReply)
def health(request: Request) -> HealthReply:
    bot = request.app.state.bot
    s = bot.settings

    security = {
        "rate_limit_enabled": s.rate_limit_enabled,
        "rate_limit_ip_per_minute": s.rate_limit_ip_per_minute,
        "rate_limit_session_per_minute": s.rate_limit_session_per_minute,
        "max_body_bytes": s.api_max_body_bytes,
        "max_message_chars": s.max_message_chars,
        "hsts_enabled": s.api_hsts_enabled,
        "strict_cors": s.api_strict_cors,
        "cors_origins": s.cors_origins_list,
        "budget": bot.budget.snapshot(),
    }

    return HealthReply(
        status="ok",
        client=bot.profile.client.name,
        personality=bot.profile.personality.name,
        model=s.llm_model,
        chain_ready=bot.chain is not None,
        active_sessions=sum(1 for _ in bot.memory.list_sessions()),
        channels={
            "web": True,
            "whatsapp": bool(s.twilio_auth_token or s.twilio_account_sid),
            "telegram": bool(s.telegram_bot_token),
            "line": bool(s.line_channel_access_token),
        },
        security=security,
    )
