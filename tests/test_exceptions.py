"""Tests for chatbot.exceptions."""
from __future__ import annotations

from chatbot.exceptions import (
    AbuseError,
    BudgetError,
    ChatbotError,
    ConfigError,
    LLMError,
    explain_llm_error,
)


# ── Exception hierarchy ──────────────────────────────────────────────────────


def test_chatbot_error_is_exception():
    assert issubclass(ChatbotError, Exception)


def test_chatbot_error_default_message():
    err = ChatbotError()
    assert err.user_message == "Sorry, something went wrong on our end."


def test_chatbot_error_custom_message():
    err = ChatbotError("internal", user_message="Custom for user")
    assert err.user_message == "Custom for user"
    assert str(err) == "internal"


def test_config_error_user_message():
    err = ConfigError("bad key")
    assert "misconfigured" in err.user_message.lower()


def test_llm_error_user_message():
    err = LLMError("timeout")
    assert "brain" in err.user_message.lower() or "trouble" in err.user_message.lower()


def test_abuse_error_user_message():
    err = AbuseError("spam")
    assert "slow down" in err.user_message.lower() or "too many" in err.user_message.lower()


def test_budget_error_user_message():
    err = BudgetError("exceeded cap")
    assert "limit" in err.user_message.lower()


# ── explain_llm_error ────────────────────────────────────────────────────────


def test_explain_auth_error():
    msg = explain_llm_error(Exception("HTTP 401 Unauthorized"))
    assert "misconfigured" in msg.lower() or "contact support" in msg.lower()
    # Must NOT leak internal hints
    assert ".env" not in msg
    assert "api-keys" not in msg.lower()


def test_explain_quota_error():
    msg = explain_llm_error(Exception("insufficient_quota"))
    assert "billing" in msg.lower() or "unavailable" in msg.lower()
    assert "platform.openai.com" not in msg


def test_explain_rate_limit():
    msg = explain_llm_error(Exception("rate_limit_exceeded"))
    assert "wait" in msg.lower()


def test_explain_timeout():
    msg = explain_llm_error(Exception("Connection timeout"))
    assert "try again" in msg.lower()


def test_explain_model_not_found():
    msg = explain_llm_error(Exception("model gpt-5 not found"))
    assert "misconfigured" in msg.lower() or "contact" in msg.lower()


def test_explain_unknown_error():
    msg = explain_llm_error(Exception("some random error XYZ"))
    # Must NOT leak the raw exception text
    assert "XYZ" not in msg
    assert "try again" in msg.lower() or "went wrong" in msg.lower()
