"""Health and status endpoints."""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict:
    """Public health check returns minimal 'ok' status.

    Full diagnostics (model, rate limits, budget, CORS config) are only
    shown when a valid ``X-Admin-Key`` **header** is provided.
    The key is intentionally not accepted as a query parameter so it
    cannot appear in server logs or browser history.
    """
    bot = request.app.state.bot
    s = bot.settings

    # Minimal public response — no internals leaked.
    public = {
        "status": "ok",
        "client": bot.profile.client.name,
        "channels": {
            "web": True,
            "whatsapp": bool(s.twilio_auth_token or s.twilio_account_sid),
            "telegram": bool(s.telegram_bot_token),
            "line": bool(s.line_channel_access_token),
        },
    }

    # If a valid admin key is provided via header, include full diagnostics.
    admin_key = request.headers.get("x-admin-key", "")
    expected = getattr(request.app.state, "admin_api_key", "")
    if expected and admin_key and hmac.compare_digest(expected, admin_key):
        public["personality"] = bot.profile.personality.name
        public["model"] = s.llm_model
        public["chain_ready"] = bot.chain is not None
        public["active_sessions"] = sum(1 for _ in bot.memory.list_sessions())
        public["security"] = {
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

    return public
