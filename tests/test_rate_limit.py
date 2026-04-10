"""Tests for chatbot.security.rate_limit."""
from __future__ import annotations

import pytest

from chatbot.security.rate_limit import RateLimitExceeded, RateLimiter


def test_allows_within_capacity():
    rl = RateLimiter(name="test", capacity=5, refill_rate=1.0)
    # Should not raise for 5 requests
    for _ in range(5):
        rl.check("user1")


def test_rejects_over_capacity():
    rl = RateLimiter(name="test", capacity=3, refill_rate=0.1)
    for _ in range(3):
        rl.check("user1")
    with pytest.raises(RateLimitExceeded) as exc_info:
        rl.check("user1")
    assert exc_info.value.retry_after > 0


def test_separate_keys_independent():
    rl = RateLimiter(name="test", capacity=2, refill_rate=0.1)
    rl.check("user1")
    rl.check("user1")
    # user2 should still have full capacity
    rl.check("user2")
    rl.check("user2")


def test_remaining_returns_capacity_for_new_key():
    rl = RateLimiter(name="test", capacity=10, refill_rate=1.0)
    assert rl.remaining("unknown_key") == 10


def test_remaining_decreases_after_check():
    rl = RateLimiter(name="test", capacity=5, refill_rate=0.01)
    rl.check("user1", cost=2.0)
    assert rl.remaining("user1") < 5


def test_reset_single_key():
    rl = RateLimiter(name="test", capacity=3, refill_rate=0.01)
    for _ in range(3):
        rl.check("user1")
    rl.reset("user1")
    # Should work again
    rl.check("user1")


def test_reset_all_keys():
    rl = RateLimiter(name="test", capacity=1, refill_rate=0.01)
    rl.check("a")
    rl.check("b")
    rl.reset()
    assert len(rl) == 0


def test_empty_key_not_rate_limited():
    rl = RateLimiter(name="test", capacity=1, refill_rate=0.01)
    # Empty key should never be rate-limited (fail open)
    for _ in range(100):
        rl.check("")


def test_invalid_capacity_raises():
    with pytest.raises(ValueError):
        RateLimiter(name="test", capacity=0, refill_rate=1.0)


def test_invalid_refill_rate_raises():
    with pytest.raises(ValueError):
        RateLimiter(name="test", capacity=5, refill_rate=0)


def test_exception_has_retry_after():
    rl = RateLimiter(name="test", capacity=1, refill_rate=1.0)
    rl.check("user1")
    with pytest.raises(RateLimitExceeded) as exc_info:
        rl.check("user1")
    assert exc_info.value.retry_after >= 0
    assert exc_info.value.key == "user1"
    assert exc_info.value.scope == "test"
