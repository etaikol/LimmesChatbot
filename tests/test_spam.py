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


# ── Thai / CJK short-word exceptions (should NOT be gibberish) ───────────────


def test_thai_two_char_word_not_gibberish():
    # ดี = "good" (consonant + upper vowel), 2 chars
    assert not is_gibberish("ดี")


def test_thai_leading_vowel_word_not_gibberish():
    # ไป = "go" (leading vowel + consonant), 2 chars
    assert not is_gibberish("ไป")


def test_thai_three_char_word_not_gibberish():
    # ไม่ = "no/not" (leading vowel + consonant + tone mark), 3 chars
    assert not is_gibberish("ไม่")


def test_cjk_two_char_word_not_gibberish():
    # 你好 = "hello" in Chinese, 2 CJK chars
    assert not is_gibberish("你好")


def test_cjk_single_common_char_not_gibberish_only_if_min_chars_adjusted():
    # A single CJK character is too short (below default min_meaningful_chars=2)
    # but should pass when the caller lowers the threshold
    assert not is_gibberish("好", min_meaningful_chars=1)


# ── Thai keyboard-mash detection (should be gibberish) ───────────────────────


def test_thai_leading_combining_mark_is_gibberish():
    # Starts with a tone mark (่ = U+0E48); no base consonant → mash
    assert is_gibberish("\u0e48\u0e01")  # ่ก


def test_thai_high_combining_ratio_is_gibberish():
    # ก (1 consonant) + ่่้ (3 tone marks) → ratio 3.0 > 1.5
    assert is_gibberish("\u0e01\u0e48\u0e48\u0e49")  # ก่่้


def test_thai_short_no_consonants_is_gibberish():
    # เเ = two leading-vowel chars, Thai block, no consonants, ≤4 chars
    assert is_gibberish("\u0e40\u0e40")  # เเ


def test_thai_short_consonants_only_no_vowels_is_gibberish():
    # กขค = 3 consonants, no vowels — random consonant mash
    assert is_gibberish("\u0e01\u0e02\u0e04")  # กขค
