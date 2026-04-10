"""
LLM provider abstraction.

Currently supports:
    - openai      (default; gpt-4o-mini, gpt-4o, ...)
    - anthropic   (claude-3.5-sonnet, claude-opus-4, ...)

Both adapters return a `langchain_core.language_models.BaseChatModel` so the
rest of the pipeline (chains.py) does not care which provider is configured.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.language_models import BaseChatModel

from chatbot.exceptions import ConfigError
from chatbot.logging_setup import logger
from chatbot.settings import Settings, get_settings


class LLMProvider:
    """Wraps a LangChain chat model and exposes it via `provider.client`."""

    def __init__(self, client: BaseChatModel, name: str) -> None:
        self.client = client
        self.name = name

    @classmethod
    def from_settings(
        cls,
        settings: Optional[Settings] = None,
        *,
        temperature_override: Optional[float] = None,
    ) -> "LLMProvider":
        s = settings or get_settings()
        temp = temperature_override if temperature_override is not None else s.llm_temperature

        if s.llm_provider == "openai":
            client = _build_openai(s, temperature=temp)
            return cls(client=client, name=f"openai:{s.llm_model}")

        if s.llm_provider == "anthropic":
            client = _build_anthropic(s, temperature=temp)
            return cls(client=client, name=f"anthropic:{s.llm_model}")

        raise ConfigError(f"Unknown LLM provider: {s.llm_provider}")


# ── Provider builders ───────────────────────────────────────────────────────


def _build_openai(s: Settings, temperature: float) -> BaseChatModel:
    if not s.openai_api_key:
        logger.error("OPENAI_API_KEY is missing")
        raise ConfigError(
            "OPENAI_API_KEY is missing",
            user_message="The chatbot is misconfigured. Please contact support.",
        )
    from langchain_openai import ChatOpenAI

    logger.debug("Building OpenAI client model={} temp={}", s.llm_model, temperature)
    return ChatOpenAI(
        model=s.llm_model,
        temperature=temperature,
        max_tokens=s.llm_max_tokens,
        api_key=s.openai_api_key,
        request_timeout=s.llm_request_timeout,
    )


def _build_anthropic(s: Settings, temperature: float) -> BaseChatModel:
    if not s.anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY is missing")
        raise ConfigError(
            "ANTHROPIC_API_KEY is missing",
            user_message="The chatbot is misconfigured. Please contact support.",
        )
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        logger.error("langchain-anthropic not installed")
        raise ConfigError(
            "langchain-anthropic not installed",
            user_message="The chatbot is misconfigured. Please contact support.",
        ) from e

    logger.debug("Building Anthropic client model={} temp={}", s.llm_model, temperature)
    return ChatAnthropic(
        model=s.llm_model,
        temperature=temperature,
        max_tokens=s.llm_max_tokens or 1024,
        api_key=s.anthropic_api_key,
        default_request_timeout=s.llm_request_timeout,
    )
