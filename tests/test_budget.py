"""Tests for chatbot.security.budget."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatbot.security.budget import BudgetExceeded, BudgetGuard, estimate_tokens


@pytest.fixture
def tmp_state(tmp_path):
    return tmp_path / "budget" / "state.json"


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0


def test_estimate_tokens_nonempty():
    count = estimate_tokens("Hello, world!")
    assert count > 0


def test_budget_guard_disabled(tmp_state):
    bg = BudgetGuard(state_file=tmp_state, daily_token_cap=0, daily_usd_cap=0.0)
    assert not bg.enabled
    # Should not raise even with large estimates
    bg.check_can_spend(999_999)


def test_budget_guard_token_cap(tmp_state):
    bg = BudgetGuard(state_file=tmp_state, daily_token_cap=100, daily_usd_cap=0.0)
    assert bg.enabled
    bg.check_can_spend(50)  # Should pass
    bg.record(input_tokens=90, output_tokens=0)
    with pytest.raises(BudgetExceeded):
        bg.check_can_spend(50)  # Over cap


def test_budget_guard_usd_cap(tmp_state):
    bg = BudgetGuard(
        state_file=tmp_state,
        daily_token_cap=0,
        daily_usd_cap=0.001,
        model="gpt-4o-mini",
    )
    assert bg.enabled
    bg.record(input_tokens=10000, output_tokens=10000)
    with pytest.raises(BudgetExceeded):
        bg.check_can_spend(10000)


def test_budget_persists_to_file(tmp_state):
    bg = BudgetGuard(state_file=tmp_state, daily_token_cap=1000, daily_usd_cap=1.0)
    bg.record(input_tokens=100, output_tokens=50)
    assert tmp_state.exists()
    data = json.loads(tmp_state.read_text())
    assert data["tokens"] == 150


def test_budget_snapshot(tmp_state):
    bg = BudgetGuard(state_file=tmp_state, daily_token_cap=1000, daily_usd_cap=1.0)
    bg.record(input_tokens=100, output_tokens=50)
    snap = bg.snapshot()
    assert snap["tokens_used"] == 150
    assert snap["enabled"] is True
    assert snap["daily_token_cap"] == 1000
