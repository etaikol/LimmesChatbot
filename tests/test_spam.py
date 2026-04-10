"""Tests for chatbot.security.spam detection."""
from __future__ import annotations

from chatbot.security.spam import is_gibberish, SpamTracker


# ── is_gibberish ─────────────────────────────────────────────────────────────


def test_normal_message_not_gibberish():
    assert not is_gibberish("What are your opening hours?")


def test_repeated_chars_is_gibberish():
    assert is_gibberish("aaaa")


def test_symbols_only_is_gibberish():
    assert is_gibberish("!!! ??? ...")


def test_digits_only_is_gibberish():
    assert is_gibberish("123 456 789")


def test_hebrew_short_is_gibberish():
    # Very short without spaces is treated as key-mash
    assert is_gibberish("שדג")


def test_thai_greeting_not_gibberish():
    # "สวัสดี" = 6 chars, should pass
    assert not is_gibberish("สวัสดี")


def test_single_char_too_short():
    assert is_gibberish("x", min_meaningful_chars=2)


# ── SpamTracker ──────────────────────────────────────────────────────────────


def test_spam_tracker_allows_normal():
    tracker = SpamTracker(max_strikes=3, cooldown_seconds=10.0, max_cooldown_seconds=60.0)
    result = tracker.check("session1", "What are your hours?")
    assert result is None  # None means allowed


def test_spam_tracker_blocks_repeated_gibberish():
    tracker = SpamTracker(max_strikes=2, cooldown_seconds=1.0, max_cooldown_seconds=10.0)
    # Send enough gibberish to trigger block
    for _ in range(3):
        tracker.check("session1", "x")
    result = tracker.check("session1", "y")
    assert result is not None  # Should be blocked


def test_spam_tracker_separate_sessions():
    tracker = SpamTracker(max_strikes=2, cooldown_seconds=1.0, max_cooldown_seconds=10.0)
    for _ in range(5):
        tracker.check("session1", "x")
    # session2 should not be affected
    result = tracker.check("session2", "What are your hours?")
    assert result is None


def test_spam_tracker_detects_duplicates():
    tracker = SpamTracker(max_strikes=3, cooldown_seconds=1.0, max_cooldown_seconds=10.0)
    tracker.check("s1", "same message")
    result = tracker.check("s1", "same message")
    assert result is not None  # duplicate detected
