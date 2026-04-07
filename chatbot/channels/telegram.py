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

from chatbot.core.engine import Chatbot
from chatbot.exceptions import ChannelError, ChatbotError
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
        else:
            session_id = f"telegram:{chat_id}"
            try:
                resp = self.bot.ask(text, session_id=session_id)
                reply = resp.answer
            except ChatbotError as e:
                reply = e.user_message
            except Exception as e:  # pragma: no cover
                logger.exception("[telegram:{}] {}", chat_id, e)
                reply = self.bot.profile.fallback

        await self._send_message(chat_id, reply)
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
