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
        msg = (
            "OPENAI_API_KEY is missing. Add it to your .env file "
            "(see .env.example). Get one at https://platform.openai.com/api-keys."
        )
        raise ConfigError(msg, user_message=msg)
    from langchain_openai import ChatOpenAI

    logger.debug("Building OpenAI client model={} temp={}", s.llm_model, temperature)
    return ChatOpenAI(
        model=s.llm_model,
        temperature=temperature,
        max_tokens=s.llm_max_tokens,
        api_key=s.openai_api_key,
    )


def _build_anthropic(s: Settings, temperature: float) -> BaseChatModel:
    if not s.anthropic_api_key:
        msg = (
            "ANTHROPIC_API_KEY is missing. Add it to your .env file. "
            "Get one at https://console.anthropic.com/."
        )
        raise ConfigError(msg, user_message=msg)
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        msg = (
            "Anthropic provider requires langchain-anthropic. "
            "Install: pip install langchain-anthropic"
        )
        raise ConfigError(msg, user_message=msg) from e

    logger.debug("Building Anthropic client model={} temp={}", s.llm_model, temperature)
    return ChatAnthropic(
        model=s.llm_model,
        temperature=temperature,
        max_tokens=s.llm_max_tokens or 1024,
        api_key=s.anthropic_api_key,
    )
