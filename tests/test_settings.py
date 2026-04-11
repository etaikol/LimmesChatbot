"""Tests for chatbot.settings."""
from __future__ import annotations

import os

import pytest

from chatbot.settings import Settings, PROJECT_ROOT


def test_default_settings():
    """Settings should load with sane defaults even without env vars."""
    s = Settings(
        _env_file=None,  # Don't read .env for test isolation
        openai_api_key="sk-test-fake",
    )
    assert s.llm_model == "gpt-4o-mini"
    assert s.llm_temperature == 0.7
    assert s.llm_max_tokens == 1024
    assert s.llm_request_timeout == 30
    assert s.rate_limit_enabled is True
    assert s.spam_detection_enabled is True
    assert s.block_prompt_injection is True
    assert s.daily_usd_cap == 3.0
    assert s.api_strict_cors is True


def test_cors_origins_list():
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test",
        api_cors_origins="https://a.com,https://b.com",
    )
    assert s.cors_origins_list == ["https://a.com", "https://b.com"]


def test_cors_origins_wildcard():
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test",
        api_cors_origins="*",
    )
    assert s.cors_origins_list == ["*"]


def test_assert_production_safe_blocks_wildcard():
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test",
        api_cors_origins="*",
        api_strict_cors=True,
    )
    from chatbot.exceptions import ConfigError
    with pytest.raises(ConfigError):
        s.assert_production_safe()


def test_retrieval_min_score_default():
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test",
    )
    assert s.retrieval_min_score == 0.3


def test_ensure_dirs_creates_directories(tmp_path):
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test",
        vectorstore_dir=tmp_path / "vs",
        sessions_dir=tmp_path / "sessions",
        data_dir=tmp_path / "data",
        budget_state_file=tmp_path / "budget" / "state.json",
    )
    s.ensure_dirs()
    assert (tmp_path / "vs").exists()
    assert (tmp_path / "sessions").exists()
    assert (tmp_path / "data").exists()
    assert (tmp_path / "budget").exists()
