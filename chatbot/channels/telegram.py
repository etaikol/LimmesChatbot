"""
Telegram channel using the Bot API directly via httpx (no SDK required).

Setup:
    1. Create a bot via @BotFather on Telegram, copy the token.
    2. Set TELEGRAM_BOT_TOKEN in your .env.
    3. Register the webhook (one-time):
        curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<host>/webhook/telegram"
"""

from __future__ import annotations

from typing import Any

import httpx

from chatbot.core.engine import Chatbot, ChatResponse
from chatbot.exceptions import ChannelError, ChatbotError
from chatbot.i18n import SUPPORTED_LANGUAGE_CODES
from chatbot.i18n.detect import detect_language
from chatbot.logging_setup import logger


class TelegramChannel:
    """Adapter for inbound Telegram updates."""

    def __init__(self, bot: Chatbot) -> None:
        self.bot = bot
        self.settings = bot.settings

        if not self.settings.telegram_bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN not set — Telegram channel disabled")

    # ── Inbound ─────────────────────────────────────────────────────────────

    async def handle(self, update: dict[str, Any]) -> dict:
        """Process a Telegram Update payload and reply via the Bot API."""
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return {"ok": True}

        chat_id = msg["chat"]["id"]
        text = (msg.get("text") or "").strip()
        if not text:
            return {"ok": True}

        # Handle slash commands
        if text.startswith("/"):
            reply = self._handle_command(text, chat_id)
            await self._send_message(chat_id, reply)
        else:
            session_id = f"telegram:{chat_id}"
            language = detect_language(text, supported=SUPPORTED_LANGUAGE_CODES)
            try:
                resp = self.bot.ask(text, session_id=session_id, language=language)
                await self._send_message(chat_id, resp.answer)
                # Send product images if mentioned
                await self._send_product_images(chat_id, resp)
            except ChatbotError as e:
                await self._send_message(chat_id, e.user_message)
            except Exception as e:  # pragma: no cover
                logger.exception("[telegram:{}] {}", chat_id, e)
                await self._send_message(chat_id, self.bot.profile.fallback)

        return {"ok": True}

    # ── Slash commands ──────────────────────────────────────────────────────

    def _handle_command(self, text: str, chat_id: int) -> str:
        cmd = text.split()[0].lower()
        if cmd == "/start":
            return f"{self.bot.greet()}\n\n(Type /help for commands.)"
        if cmd == "/help":
            return (
                "Just type your question.\n"
                "/start — greeting\n/clear — reset our conversation\n/help — this message"
            )
        if cmd == "/clear":
            self.bot.reset(f"telegram:{chat_id}")
            return "Conversation cleared."
        return "Unknown command. Try /help."

    # ── Outbound ────────────────────────────────────────────────────────────

    async def _send_message(self, chat_id: int, text: str) -> None:
        if not self.settings.telegram_bot_token:
            raise ChannelError("TELEGRAM_BOT_TOKEN is not configured.")

        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(
                    url,
                    json={"chat_id": chat_id, "text": text},
                )
                if resp.status_code >= 400:
                    logger.warning(
                        "Telegram sendMessage failed [{}]: {}", resp.status_code, resp.text
                    )
            except httpx.HTTPError as e:
                logger.warning("Telegram sendMessage error: {}", e)

    async def _send_photo(self, chat_id: int, photo_url: str, caption: str = "") -> None:
        """Send a photo via the Telegram Bot API."""
        if not self.settings.telegram_bot_token:
            return
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendPhoto"
        payload: dict[str, Any] = {"chat_id": chat_id, "photo": photo_url}
        if caption:
            payload["caption"] = caption[:1024]
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code >= 400:
                    logger.warning("Telegram sendPhoto failed [{}]: {}", resp.status_code, resp.text)
            except httpx.HTTPError as e:
                logger.warning("Telegram sendPhoto error: {}", e)

    async def _send_product_images(self, chat_id: int, resp: ChatResponse) -> None:
        """Send product images from the response metadata."""
        products = resp.metadata.get("products", [])
        for p in products[:3]:  # Limit to 3 images per reply
            img = p.get("image_url", "")
            if img:
                caption = p.get("name", "")
                if p.get("price"):
                    caption += f" — {p['price']}"
                await self._send_photo(chat_id, img, caption=caption)
