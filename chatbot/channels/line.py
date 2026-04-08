"""
LINE Messaging API channel.

LINE sends each event as a JSON POST signed with your channel secret.
We verify the signature manually (HMAC-SHA256 base64) so the line-bot-sdk
package is *optional* — only needed if you want richer features.

Setup:
    1. Create a Messaging API channel at https://developers.line.biz/console/.
    2. Copy the channel secret + channel access token.
    3. Set LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN in your .env.
    4. Webhook URL:  POST https://<host>/webhook/line
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from typing import Any

import httpx

from chatbot.core.engine import Chatbot
from chatbot.exceptions import ChannelError, ChatbotError
from chatbot.i18n import SUPPORTED_LANGUAGE_CODES
from chatbot.i18n.detect import detect_language
from chatbot.logging_setup import logger

REPLY_ENDPOINT = "https://api.line.me/v2/bot/message/reply"


class LineChannel:
    """Adapter for inbound LINE webhook events."""

    def __init__(self, bot: Chatbot) -> None:
        self.bot = bot
        self.settings = bot.settings

        if not self.settings.line_channel_access_token:
            logger.warning("LINE_CHANNEL_ACCESS_TOKEN not set — LINE channel disabled")

    # ── Signature ───────────────────────────────────────────────────────────

    def validate_signature(self, body: bytes, signature: str | None) -> bool:
        """Verify the X-Line-Signature header (HMAC-SHA256, base64).

        Production (``DEBUG=false``) refuses requests when the channel
        secret is unset. Dev mode logs a warning and lets them through.
        """
        if not self.settings.line_channel_secret:
            if self.settings.debug:
                logger.warning(
                    "LINE_CHANNEL_SECRET unset — accepting because DEBUG=true. "
                    "NEVER do this in production."
                )
                return True
            logger.error(
                "LINE_CHANNEL_SECRET unset in production — refusing webhook"
            )
            return False
        if not signature:
            return False

        digest = hmac.new(
            self.settings.line_channel_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature)

    # ── Inbound ─────────────────────────────────────────────────────────────

    async def handle(self, payload: dict[str, Any]) -> dict:
        events = payload.get("events", [])
        for event in events:
            try:
                await self._handle_event(event)
            except Exception as e:  # pragma: no cover
                logger.exception("LINE event failed: {}", e)
        return {"ok": True}

    async def _handle_event(self, event: dict[str, Any]) -> None:
        if event.get("type") != "message":
            return
        message = event.get("message") or {}
        if message.get("type") != "text":
            return

        text = (message.get("text") or "").strip()
        reply_token = event.get("replyToken")
        source = event.get("source") or {}
        user_id = source.get("userId") or source.get("groupId") or "unknown"

        if not text or not reply_token:
            return

        session_id = f"line:{user_id}"
        language = detect_language(text, supported=SUPPORTED_LANGUAGE_CODES)
        try:
            resp = self.bot.ask(text, session_id=session_id, language=language)
            reply = resp.answer
        except ChatbotError as e:
            reply = e.user_message
        except Exception as e:  # pragma: no cover
            logger.exception("[line:{}] {}", user_id, e)
            reply = self.bot.profile.fallback

        await self._reply(reply_token, reply)

    # ── Outbound ────────────────────────────────────────────────────────────

    async def _reply(self, reply_token: str, text: str) -> None:
        token = self.settings.line_channel_access_token
        if not token:
            raise ChannelError("LINE_CHANNEL_ACCESS_TOKEN not configured.")

        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    REPLY_ENDPOINT,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "replyToken": reply_token,
                        "messages": [{"type": "text", "text": text[:5000]}],
                    },
                )
                if resp.status_code >= 400:
                    logger.warning(
                        "LINE reply failed [{}]: {}", resp.status_code, resp.text
                    )
            except httpx.HTTPError as e:
                logger.warning("LINE reply error: {}", e)
