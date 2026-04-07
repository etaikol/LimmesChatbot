"""
WhatsApp channel via Twilio.

Twilio sends incoming WhatsApp messages as form-encoded POSTs to your webhook.
The expected reply is TwiML XML with a `<Message>` body.

Setup:
    1. Sign up at twilio.com and enable the WhatsApp sandbox.
    2. Set TWILIO_AUTH_TOKEN in your .env (used to verify request signatures).
    3. Point the sandbox webhook at:
        POST https://<your-domain>/webhook/whatsapp
"""

from __future__ import annotations

from typing import Optional

from chatbot.core.engine import Chatbot
from chatbot.exceptions import ChatbotError, ChannelError
from chatbot.logging_setup import logger
from chatbot.settings import get_settings


class WhatsAppChannel:
    """Stateless adapter — used by the FastAPI route."""

    def __init__(self, bot: Chatbot) -> None:
        self.bot = bot
        self.settings = bot.settings

    # ── Inbound ─────────────────────────────────────────────────────────────

    def handle(self, body: str, from_number: str) -> str:
        """Process an incoming message and return TwiML."""
        if not body.strip():
            return self._twiml("I didn't catch that. Could you say it again?")

        session_id = f"whatsapp:{from_number}"

        try:
            resp = self.bot.ask(body, session_id=session_id)
            return self._twiml(resp.answer)
        except ChatbotError as e:
            logger.warning("[whatsapp:{}] {}", from_number, e)
            return self._twiml(e.user_message)
        except Exception as e:  # pragma: no cover
            logger.exception("[whatsapp:{}] unexpected: {}", from_number, e)
            return self._twiml(self.bot.profile.fallback)

    # ── Signature validation ────────────────────────────────────────────────

    def validate_signature(
        self, url: str, params: dict, signature: Optional[str]
    ) -> bool:
        """Verify Twilio's X-Twilio-Signature header. Returns True if missing
        token (dev mode) or signature matches."""
        if not self.settings.twilio_auth_token:
            logger.debug("TWILIO_AUTH_TOKEN not set — skipping signature validation")
            return True

        try:
            from twilio.request_validator import RequestValidator
        except ImportError as e:
            raise ChannelError(
                "Twilio integration requires the `twilio` package. "
                "Install with: pip install twilio"
            ) from e

        validator = RequestValidator(self.settings.twilio_auth_token)
        return validator.validate(url, params, signature or "")

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _twiml(message: str) -> str:
        message = (
            message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Response><Message>" + message + "</Message></Response>"
        )
