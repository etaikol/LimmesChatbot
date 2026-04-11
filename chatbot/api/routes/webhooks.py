"""Webhook endpoints for WhatsApp (Twilio), Telegram, and LINE.

Each webhook does *three* things before handing off to the channel
adapter, in this order:

1. **Provider auth** — Twilio HMAC, LINE HMAC, or the Telegram secret
   token. In production (``DEBUG=false``) any unset secret causes the
   webhook to refuse the request rather than fall through to dev mode.
2. **Per-source rate limiting** — protects upstream LLM spend from a
   provider that goes crazy and replays the same user 200 times.
3. **Hand off to the channel adapter**, which itself goes through the
   sanitization + budget guard inside the engine.
"""

from __future__ import annotations

import hmac

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from chatbot.channels.line import LineChannel
from chatbot.channels.telegram import TelegramChannel
from chatbot.channels.whatsapp import WhatsAppChannel
from chatbot.logging_setup import logger

router = APIRouter(tags=["webhooks"])


def _peer_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _check_ip_limit(request: Request, label: str) -> None:
    limiter = request.app.state.ip_limiter
    if limiter is None:
        return
    try:
        limiter.check(f"{label}:{_peer_ip(request)}")
    except Exception as exc:
        logger.warning("[webhook:{}] rate-limited {}: {}", label, _peer_ip(request), exc)
        raise HTTPException(429, "Too many requests")


# ── WhatsApp / Twilio ────────────────────────────────────────────────────────


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: str | None = Header(default=None),
):
    _check_ip_limit(request, "whatsapp")
    bot = request.app.state.bot
    channel = WhatsAppChannel(bot)

    form = await request.form()
    params = {k: form.get(k, "") for k in form.keys()}
    url = str(request.url)

    if not channel.validate_signature(url, params, x_twilio_signature):
        client = _peer_ip(request)
        logger.warning("Rejected unsigned Twilio webhook from {}", client)
        raise HTTPException(403, "Invalid Twilio signature")

    body = str(form.get("Body", ""))
    sender = str(form.get("From", "unknown"))

    twiml = channel.handle(body, sender)
    return HTMLResponse(content=twiml, media_type="application/xml")


# ── Telegram ─────────────────────────────────────────────────────────────────


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    _check_ip_limit(request, "telegram")
    bot = request.app.state.bot
    s = bot.settings

    if not s.telegram_bot_token:
        raise HTTPException(503, "Telegram is not configured.")

    # Production-only: require the secret token Telegram echoes back.
    if s.telegram_webhook_secret:
        if not x_telegram_bot_api_secret_token or not hmac.compare_digest(
            s.telegram_webhook_secret, x_telegram_bot_api_secret_token
        ):
            logger.warning("Rejected Telegram webhook with bad secret from {}", _peer_ip(request))
            raise HTTPException(403, "Invalid Telegram secret token")
    elif not s.debug:
        logger.error(
            "TELEGRAM_WEBHOOK_SECRET unset in production — refusing webhook"
        )
        raise HTTPException(403, "Telegram webhook secret not configured")

    channel = TelegramChannel(bot)
    payload = await request.json()
    return JSONResponse(await channel.handle(payload))


# ── LINE ─────────────────────────────────────────────────────────────────────


@router.post("/line")
async def line_webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None),
):
    _check_ip_limit(request, "line")
    bot = request.app.state.bot
    if not bot.settings.line_channel_access_token:
        raise HTTPException(503, "LINE is not configured.")

    channel = LineChannel(bot)
    raw = await request.body()

    if not channel.validate_signature(raw, x_line_signature):
        client = _peer_ip(request)
        logger.warning("Rejected unsigned LINE webhook from {}", client)
        raise HTTPException(403, "Invalid LINE signature")

    payload = await request.json()
    return JSONResponse(await channel.handle(payload))
