"""
Custom exception types used across the package.

Catching these in a single place lets the API and CLI return clean,
user-friendly messages instead of leaking provider-specific tracebacks.
"""

from __future__ import annotations


class ChatbotError(Exception):
    """Base class for all expected chatbot errors."""

    user_message: str = "Sorry, something went wrong on our end."

    def __init__(self, message: str = "", *, user_message: str | None = None) -> None:
        super().__init__(message or self.user_message)
        if user_message:
            self.user_message = user_message


class ConfigError(ChatbotError):
    """Raised when configuration is missing or invalid."""

    user_message = "The chatbot is misconfigured. Please contact support."


class IngestionError(ChatbotError):
    """Raised when document ingestion fails."""

    user_message = "We could not load the knowledge base."


class LLMError(ChatbotError):
    """Raised on LLM provider failures (auth, quota, network, etc.)."""

    user_message = "I'm having trouble reaching my brain right now. Please try again shortly."


class RetrievalError(ChatbotError):
    """Raised when vector retrieval fails."""

    user_message = "I could not search my knowledge base."


class ChannelError(ChatbotError):
    """Raised on channel adapter failures (Twilio, Telegram, LINE, ...)."""

    user_message = "Could not deliver the message through this channel."


def explain_llm_error(exc: BaseException) -> str:
    """Return a friendly explanation for common LLM provider errors."""
    text = str(exc).lower()

    if "invalid_api_key" in text or "unauthorized" in text or "401" in text:
        return (
            "API key is invalid or missing. Set OPENAI_API_KEY in your .env file. "
            "Get one at https://platform.openai.com/api-keys."
        )
    if "rate_limit" in text or "429" in text:
        return "Rate limit reached. Please wait a moment and try again."
    if "insufficient_quota" in text or "quota" in text or "billing" in text:
        return (
            "Your provider account has run out of credits. "
            "Top up at https://platform.openai.com/account/billing."
        )
    if "timeout" in text or "connection" in text:
        return "Cannot reach the LLM provider. Check your network connection."
    if "model" in text and "not found" in text:
        return "The configured model is not available for this account."
    return f"LLM provider error: {exc}"
