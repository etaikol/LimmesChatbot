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


# ── LINE Login OAuth ─────────────────────────────────────────────────────────


@router.get("/line/login")
async def line_login_redirect(request: Request, session_id: str = ""):
    """Redirect user to LINE Login authorization page."""
    login_mgr = getattr(request.app.state, "line_login", None)
    if login_mgr is None:
        raise HTTPException(503, "LINE Login is not configured")

    # Update redirect URI dynamically
    base = str(request.base_url).rstrip("/")
    login_mgr._redirect_uri = f"{base}/webhook/line/callback"

    url, state = login_mgr.get_auth_url(session_id)

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=url)


@router.get("/line/callback")
async def line_login_callback(
    request: Request,
    code: str = "",
    state: str = "",
    error: str = "",
):
    """Handle LINE Login OAuth callback."""
    if error:
        return HTMLResponse(
            f"<html><body><h2>Login failed</h2><p>Authentication error</p></body></html>",
            status_code=400,
        )

    login_mgr = getattr(request.app.state, "line_login", None)
    if login_mgr is None:
        raise HTTPException(503, "LINE Login is not configured")

    # Update redirect URI
    base = str(request.base_url).rstrip("/")
    login_mgr._redirect_uri = f"{base}/webhook/line/callback"

    profile = await login_mgr.handle_callback(code, state)
    if profile is None:
        return HTMLResponse(
            "<html><body><h2>Login failed</h2><p>Could not verify your identity.</p></body></html>",
            status_code=400,
        )

    # Store in user memory
    mem_store = getattr(request.app.state, "user_memory_store", None)
    if mem_store:
        user_profile = mem_store.get_or_create(
            f"line:{profile.user_id}",
            channel="line",
        )
        if profile.display_name:
            user_profile.display_name = profile.display_name
        if profile.email:
            user_profile.add_fact(
                f"Email: {profile.email}",
                category="contact",
                source="line_login",
            )
        mem_store._save()

    # Safe display name (escape HTML)
    import html as html_mod
    safe_name = html_mod.escape(profile.display_name or "User")

    # Return a success page that communicates back to the opener
    return HTMLResponse(
        "<!DOCTYPE html><html><head><title>Login Successful</title></head>"
        f"<body><h2>Welcome, {safe_name}!</h2>"
        "<p>You have been successfully logged in. You can close this window.</p>"
        "<script>"
        "if(window.opener){"
        "window.opener.postMessage({type:'line_login_success'},'*');"
        "setTimeout(()=>window.close(),2000);}"
        "</script></body></html>"
    )
