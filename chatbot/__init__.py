"""
Limmes Chatbot Template
=======================

A modular AI chatbot template for any business with:
- Retrieval-Augmented Generation (RAG) over PDFs, text, markdown, HTML, etc.
- Configurable personality presets (sales, clinic, official, friendly, ...)
- Multi-channel delivery (Web widget, WhatsApp, Telegram, LINE)
- Conversation memory + session persistence
- Hebrew + multi-language support
- Optional PostgreSQL backing
- Strong structured logging

Quick start:
    from chatbot import Chatbot
    bot = Chatbot.from_client("limmes")
    response = bot.ask("What are your opening hours?", session_id="user-1")
    print(response.answer)
"""

from chatbot.core.engine import Chatbot, ChatResponse
from chatbot.core.profile import ChatbotProfile, ClientConfig, PersonalityConfig
from chatbot.settings import Settings, get_settings

__all__ = [
    "Chatbot",
    "ChatResponse",
    "ChatbotProfile",
    "ClientConfig",
    "PersonalityConfig",
    "Settings",
    "get_settings",
]

__version__ = "0.2.0"
