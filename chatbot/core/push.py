"""
Push delivery service — delivers admin handoff replies to users in real time.

Session IDs encode the channel: ``line:<userId>``, ``telegram:<chatId>``,
``whatsapp:<number>``, ``web_<random>``.  The service parses this prefix,
then pushes through the appropriate channel API:

- **Web**: Server-Sent Events (SSE).  The widget opens a persistent
  ``GET /chat/events?session_id=…`` connection.  We write into an
  ``asyncio.Queue`` that the SSE endpoint drains.
- **LINE**: Push Message API (no reply-token needed).
- **Telegram**: ``sendMessage`` Bot API.
- **WhatsApp**: Twilio REST API ``messages.create``.

Usage from the admin reply route::

    push: PushService = request.app.state.push_service
    await push.deliver(session_id, text)
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

import httpx

from chatbot.logging_setup import logger


class PushService:
    """Dispatch admin messages to the user's channel in real time."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        # Web SSE: session_id → asyncio.Queue[str | None]
        # None sentinel = close the stream.
        self._web_queues: dict[str, asyncio.Queue[str | None]] = {}

    # ── Public API ──────────────────────────────────────────────────────

    async def deliver(self, session_id: str, text: str) -> bool:
        """Push *text* to the user identified by *session_id*.

        Returns True if the message was dispatched (not necessarily
        received — channel delivery is best-effort).
        """
        channel, uid = self._parse_session(session_id)

        if channel == "web":
            return self._push_web(session_id, text)
        if channel == "line":
            return await self._push_line(uid, text)
        if channel == "telegram":
            return await self._push_telegram(uid, text)
        if channel == "whatsapp":
            return await self._push_whatsapp(uid, text)

        logger.warning("[push] Unknown channel for session {}", session_id)
        return False

    # ── Web / SSE ───────────────────────────────────────────────────────

    def subscribe(self, session_id: str) -> asyncio.Queue[str | None]:
        """Register a web session for SSE push.  Returns the queue the
        SSE endpoint should read from."""
        if session_id not in self._web_queues:
            self._web_queues[session_id] = asyncio.Queue()
        return self._web_queues[session_id]

    def unsubscribe(self, session_id: str) -> None:
        """Remove a web session's SSE queue (client disconnected)."""
        self._web_queues.pop(session_id, None)

    def _push_web(self, session_id: str, text: str) -> bool:
        q = self._web_queues.get(session_id)
        if q is None:
            logger.debug("[push] No SSE listener for web session {}", session_id)
            return False
        q.put_nowait(text)
        logger.debug("[push] Queued SSE message for {}", session_id)
        return True

    # ── LINE Push API ───────────────────────────────────────────────────

    async def _push_line(self, user_id: str, text: str) -> bool:
        token = self.settings.line_channel_access_token
        if not token:
            logger.warning("[push] LINE not configured — cannot push to {}", user_id)
            return False

        url = "https://api.line.me/v2/bot/message/push"
        payload = {
            "to": user_id,
            "messages": [{"type": "text", "text": text}],
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if resp.status_code >= 400:
                    logger.warning("[push] LINE push failed [{}]: {}", resp.status_code, resp.text)
                    return False
            logger.info("[push] LINE message sent to {}", user_id)
            return True
        except httpx.HTTPError as e:
            logger.warning("[push] LINE push error: {}", e)
            return False

    # ── Telegram Push ───────────────────────────────────────────────────

    async def _push_telegram(self, chat_id: str, text: str) -> bool:
        token = self.settings.telegram_bot_token
        if not token:
            logger.warning("[push] Telegram not configured — cannot push to {}", chat_id)
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    json={"chat_id": chat_id, "text": text},
                )
                if resp.status_code >= 400:
                    logger.warning("[push] Telegram push failed [{}]: {}", resp.status_code, resp.text)
                    return False
            logger.info("[push] Telegram message sent to {}", chat_id)
            return True
        except httpx.HTTPError as e:
            logger.warning("[push] Telegram push error: {}", e)
            return False

    # ── WhatsApp Push (Twilio REST) ─────────────────────────────────────

    async def _push_whatsapp(self, to_number: str, text: str) -> bool:
        sid = self.settings.twilio_account_sid
        auth = self.settings.twilio_auth_token
        from_number = self.settings.twilio_whatsapp_number
        if not all([sid, auth, from_number]):
            logger.warning("[push] Twilio not configured — cannot push to {}", to_number)
            return False

        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        payload = {
            "From": f"whatsapp:{from_number}" if not from_number.startswith("whatsapp:") else from_number,
            "To": f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            "Body": text,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    data=payload,
                    auth=(sid, auth),
                )
                if resp.status_code >= 400:
                    logger.warning("[push] WhatsApp push failed [{}]: {}", resp.status_code, resp.text)
                    return False
            logger.info("[push] WhatsApp message sent to {}", to_number)
            return True
        except httpx.HTTPError as e:
            logger.warning("[push] WhatsApp push error: {}", e)
            return False

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _parse_session(session_id: str) -> tuple[str, str]:
        """Extract (channel, user_identifier) from a session id.

        Formats: ``line:Uabc``, ``telegram:12345``, ``whatsapp:+1234``,
        ``web_<random>``.
        """
        if session_id.startswith("line:"):
            return "line", session_id[5:]
        if session_id.startswith("telegram:"):
            return "telegram", session_id[9:]
        if session_id.startswith("whatsapp:"):
            return "whatsapp", session_id[9:]
        # web sessions: web_<hex>
        return "web", session_id
