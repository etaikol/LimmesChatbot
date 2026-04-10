"""Tests for chatbot.core.profile and personality loading."""
from __future__ import annotations

from pathlib import Path

import pytest

from chatbot.core.profile import (
    ChatbotProfile,
    ClientConfig,
    PersonalityConfig,
    _language_label,
)


# ── _language_label ──────────────────────────────────────────────────────────


def test_language_label_english():
    label = _language_label("en")
    assert "English" in label


def test_language_label_thai():
    label = _language_label("th")
    assert "Thai" in label
    assert "ไทย" in label


def test_language_label_hebrew():
    label = _language_label("he")
    assert "Hebrew" in label


def test_language_label_unknown_fallback():
    # Unknown codes should not crash
    label = _language_label("zz")
    assert isinstance(label, str)
    assert len(label) > 0


# ── PersonalityConfig ────────────────────────────────────────────────────────


def test_default_personality():
    p = PersonalityConfig()
    assert p.name == "default"
    assert p.temperature == 0.7
    assert "helpful" in p.system_prompt.lower() or "assistant" in p.system_prompt.lower()


def test_personality_from_file(tmp_path):
    yaml_content = """
name: test_persona
system_prompt: "You are a test bot."
temperature: 0.5
greeting: "Test greeting"
fallback_message: "Test fallback"
style_keywords:
  - test
"""
    path = tmp_path / "test.yaml"
    path.write_text(yaml_content)
    p = PersonalityConfig.from_file(path)
    assert p.name == "test_persona"
    assert p.temperature == 0.5
    assert p.greeting == "Test greeting"


def test_personality_missing_file():
    with pytest.raises(Exception):
        PersonalityConfig.from_file(Path("/nonexistent/path.yaml"))


def test_load_all_bundled_personalities():
    """All personality YAML files in config/personalities/ must load without error."""
    from chatbot.settings import PROJECT_ROOT

    personalities_dir = PROJECT_ROOT / "config" / "personalities"
    for path in personalities_dir.glob("*.yaml"):
        p = PersonalityConfig.from_file(path)
        assert p.name, f"{path.name} missing 'name'"
        assert p.system_prompt, f"{path.name} missing 'system_prompt'"
        assert 0 <= p.temperature <= 1.0, f"{path.name} temperature {p.temperature} out of range"


# ── ClientConfig ─────────────────────────────────────────────────────────────


def test_default_client():
    c = ClientConfig()
    assert c.id == "default"
    assert c.language_primary == "en"


def test_client_from_file(tmp_path):
    yaml_content = """
id: test_client
name: Test Corp
language_primary: he
personality: sales
"""
    path = tmp_path / "test.yaml"
    path.write_text(yaml_content)
    c = ClientConfig.from_file(path)
    assert c.id == "test_client"
    assert c.name == "Test Corp"
    assert c.language_primary == "he"
    assert c.personality == "sales"


# ── ChatbotProfile ───────────────────────────────────────────────────────────


def test_build_system_prompt_contains_language():
    profile = ChatbotProfile(
        client=ClientConfig(language_primary="th"),
        personality=PersonalityConfig(),
    )
    prompt = profile.build_system_prompt(language="th")
    assert "Thai" in prompt
    assert "HIGHEST PRIORITY" in prompt


def test_build_system_prompt_contains_security_rules():
    profile = ChatbotProfile(
        client=ClientConfig(),
        personality=PersonalityConfig(),
    )
    prompt = profile.build_system_prompt(language="en")
    assert "SECURITY RULES" in prompt
    assert "never override" in prompt.lower()


def test_build_system_prompt_contains_refuse_topics():
    profile = ChatbotProfile(
        client=ClientConfig(),
        personality=PersonalityConfig(refuse_topics=["politics", "religion"]),
    )
    prompt = profile.build_system_prompt(language="en")
    assert "politics" in prompt
    assert "religion" in prompt


def test_build_system_prompt_with_client_extras():
    profile = ChatbotProfile(
        client=ClientConfig(system_prompt_extra="We are open 9-5."),
        personality=PersonalityConfig(),
    )
    prompt = profile.build_system_prompt(language="en")
    assert "9-5" in prompt


def test_greeting_override():
    profile = ChatbotProfile(
        client=ClientConfig(greeting_override="Custom hello!"),
        personality=PersonalityConfig(greeting="Default hello"),
    )
    assert profile.greeting == "Custom hello!"


def test_greeting_fallback_to_personality():
    profile = ChatbotProfile(
        client=ClientConfig(),
        personality=PersonalityConfig(greeting="Personality greeting"),
    )
    assert profile.greeting == "Personality greeting"
