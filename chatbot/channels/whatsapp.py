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

from chatbot.core.engine import Chatbot, ChatResponse
from chatbot.exceptions import ChatbotError, ChannelError
from chatbot.i18n import SUPPORTED_LANGUAGE_CODES
from chatbot.i18n.detect import detect_language
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
        language = detect_language(body, supported=SUPPORTED_LANGUAGE_CODES)

        try:
            resp = self.bot.ask(body, session_id=session_id, language=language)
            return self._twiml_with_products(resp)
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
        """Verify Twilio's X-Twilio-Signature header.

        Behaviour:

        - **Production** (``DEBUG=false``): if ``TWILIO_AUTH_TOKEN`` is not
          set, the webhook is rejected outright. Unsigned webhooks are
          never accepted.
        - **Dev** (``DEBUG=true``): an unset token logs a warning and lets
          the request through so you can test with the Twilio sandbox
          before wiring real signatures.
        """
        if not self.settings.twilio_auth_token:
            if self.settings.debug:
                logger.warning(
                    "TWILIO_AUTH_TOKEN unset — accepting webhook because DEBUG=true. "
                    "NEVER do this in production."
                )
                return True
            logger.error(
                "TWILIO_AUTH_TOKEN unset in production — refusing webhook"
            )
            return False

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

    @staticmethod
    def _twiml_with_products(resp: ChatResponse) -> str:
        """Build TwiML with optional media URLs for product images."""
        text = resp.answer.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        products = resp.metadata.get("products", [])
        media_tags = ""
        for p in products[:1]:  # WhatsApp TwiML: one media per message
            img = p.get("image_url", "")
            if img:
                safe_url = img.replace("&", "&amp;")
                media_tags += f"<Media>{safe_url}</Media>"
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f"<Response><Message><Body>{text}</Body>{media_tags}</Message></Response>"
        )
