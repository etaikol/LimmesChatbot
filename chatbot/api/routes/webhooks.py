"""Webhook endpoints for WhatsApp (Twilio), Telegram, and LINE."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from chatbot.channels.line import LineChannel
from chatbot.channels.telegram import TelegramChannel
from chatbot.channels.whatsapp import WhatsAppChannel
from chatbot.logging_setup import logger

router = APIRouter(tags=["webhooks"])


# ── WhatsApp / Twilio ────────────────────────────────────────────────────────


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    x_twilio_signature: str | None = Header(default=None),
):
    bot = request.app.state.bot
    channel = WhatsAppChannel(bot)

    form = await request.form()
    params = {k: form.get(k, "") for k in form.keys()}
    url = str(request.url)

    if not channel.validate_signature(url, params, x_twilio_signature):
        client = request.client.host if request.client else "unknown"
        logger.warning("Rejected unsigned Twilio webhook from {}", client)
        raise HTTPException(403, "Invalid Twilio signature")

    body = str(form.get("Body", ""))
    sender = str(form.get("From", "unknown"))

    twiml = channel.handle(body, sender)
    return HTMLResponse(content=twiml, media_type="application/xml")


# ── Telegram ─────────────────────────────────────────────────────────────────


@router.post("/telegram")
async def telegram_webhook(request: Request):
    bot = request.app.state.bot
    if not bot.settings.telegram_bot_token:
        raise HTTPException(503, "Telegram is not configured.")

    channel = TelegramChannel(bot)
    payload = await request.json()
    return JSONResponse(await channel.handle(payload))


# ── LINE ─────────────────────────────────────────────────────────────────────


@router.post("/line")
async def line_webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None),
):
    bot = request.app.state.bot
    if not bot.settings.line_channel_access_token:
        raise HTTPException(503, "LINE is not configured.")

    channel = LineChannel(bot)
    raw = await request.body()

    if not channel.validate_signature(raw, x_line_signature):
        client = request.client.host if request.client else "unknown"
        logger.warning("Rejected unsigned LINE webhook from {}", client)
        raise HTTPException(403, "Invalid LINE signature")

    payload = await request.json()
    return JSONResponse(await channel.handle(payload))
