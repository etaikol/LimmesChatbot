"""
Channel adapters.

A *channel* is a delivery surface (CLI, WhatsApp, Telegram, LINE, ...).
Each adapter knows how to:
    1. Receive an inbound message from its provider.
    2. Build a stable session id from the sender.
    3. Hand the message to a `Chatbot` instance.
    4. Send the response back through the provider's API.

The web channel is implemented directly in `chatbot.api.routes.chat` since
it ships as part of the FastAPI app.
"""

from chatbot.channels.cli import CLIChannel
from chatbot.channels.line import LineChannel
from chatbot.channels.telegram import TelegramChannel
from chatbot.channels.whatsapp import WhatsAppChannel

__all__ = [
    "CLIChannel",
    "LineChannel",
    "TelegramChannel",
    "WhatsAppChannel",
]
