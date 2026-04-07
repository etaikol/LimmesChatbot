"""Health and status endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request

from chatbot.api.schemas import HealthReply

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthReply)
def health(request: Request) -> HealthReply:
    bot = request.app.state.bot
    s = bot.settings

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
    )
