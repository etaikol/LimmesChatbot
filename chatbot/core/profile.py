"""
Chatbot profiles = client + personality.

A *personality* is a reusable preset (sales, clinic, friendly_official, ...)
defined under `config/personalities/<name>.yaml`.

A *client* is a specific business that picks a personality and adds its own
data (system-prompt extras, language preferences, channels, ingestion paths)
under `config/clients/<id>.yaml`.

A `ChatbotProfile` is the merged view passed to the engine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from chatbot.exceptions import ConfigError
from chatbot.settings import PROJECT_ROOT


# ── PersonalityConfig ────────────────────────────────────────────────────────


class PersonalityConfig(BaseModel):
    """A reusable bot tone/behavior preset.

    Lives at `config/personalities/<name>.yaml`. Designed to be swapped per
    client without rewriting any code — change one line in the client config.
    """

    name: str = "default"
    description: str = ""
    system_prompt: str = "You are a helpful AI assistant."
    temperature: float = 0.7
    greeting: str = "Hello! How can I help you today?"
    fallback_message: str = "I'm sorry, I don't have that information."
    style_keywords: list[str] = Field(default_factory=list)
    refuse_topics: list[str] = Field(default_factory=list)

    @classmethod
    def from_file(cls, path: Path) -> PersonalityConfig:
        if not path.exists():
            raise ConfigError(f"Personality file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def load(cls, name: str) -> PersonalityConfig:
        """Load preset by name from `config/personalities/`."""
        path = PROJECT_ROOT / "config" / "personalities" / f"{name}.yaml"
        return cls.from_file(path)


# ── ClientConfig ─────────────────────────────────────────────────────────────


class ChannelToggle(BaseModel):
    """Per-channel enable flag + free-form options."""

    enabled: bool = False
    options: dict[str, Any] = Field(default_factory=dict)


class ClientConfig(BaseModel):
    """Client-specific configuration loaded from YAML."""

    id: str = "default"
    name: str = "AI Assistant"
    language_primary: str = "en"
    language_fallback: str = "en"
    location: str = ""
    timezone: str = "UTC"

    # Personality preset to use (must exist in config/personalities/)
    personality: str = "default"

    # Optional system prompt suffix (e.g. business facts, hours, products)
    system_prompt_extra: str = ""

    # Greeting override (otherwise uses personality's)
    greeting_override: str = ""

    # Knowledge sources
    data_paths: list[str] = Field(default_factory=lambda: ["data"])
    scrape_urls: list[str] = Field(default_factory=list)

    # Channel toggles
    channels: dict[str, ChannelToggle] = Field(default_factory=dict)

    @classmethod
    def from_file(cls, path: Path) -> ClientConfig:
        if not path.exists():
            raise ConfigError(f"Client config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    @classmethod
    def load(cls, client_id: str) -> ClientConfig:
        """Load client config by ID from `config/clients/`."""
        path = PROJECT_ROOT / "config" / "clients" / f"{client_id}.yaml"
        return cls.from_file(path)


# ── Combined profile ─────────────────────────────────────────────────────────


class ChatbotProfile(BaseModel):
    """Combined client + personality, ready to drive an engine."""

    client: ClientConfig
    personality: PersonalityConfig

    @property
    def effective_system_prompt(self) -> str:
        """Personality prompt + client extras + a tiny standard footer."""
        sections = [self.personality.system_prompt.strip()]

        if self.client.system_prompt_extra.strip():
            sections.append(self.client.system_prompt_extra.strip())

        # Language hint (helps the LLM decide the reply language)
        sections.append(
            f"Reply in the language of the user. Default to "
            f"'{self.client.language_primary}' if unclear."
        )

        if self.personality.refuse_topics:
            joined = ", ".join(self.personality.refuse_topics)
            sections.append(
                f"Politely refuse to discuss: {joined}. Redirect to relevant topics."
            )

        if self.personality.style_keywords:
            joined = ", ".join(self.personality.style_keywords)
            sections.append(f"Tone: {joined}.")

        return "\n\n".join(sections)

    @property
    def greeting(self) -> str:
        return self.client.greeting_override or self.personality.greeting

    @property
    def fallback(self) -> str:
        return self.personality.fallback_message

    @classmethod
    def load(cls, client_id: str) -> ChatbotProfile:
        """Load a complete profile by client id."""
        client = ClientConfig.load(client_id)
        personality = PersonalityConfig.load(client.personality)
        return cls(client=client, personality=personality)
