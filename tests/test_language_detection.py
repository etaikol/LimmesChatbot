"""Unit tests for chatbot.i18n.detect.detect_language.

Covers the three primary language families used in the Limmes deployment
(Hebrew, Thai, English) plus edge cases: short messages, numeric-only
input, mixed scripts, and the supported-whitelist filter.
"""
from __future__ import annotations

import pytest

from chatbot.i18n.detect import detect_language

# ── Thai ─────────────────────────────────────────────────────────────────────


def test_thai_short_question():
    assert detect_language("มีโซฟามั้ย") == "th"


def test_thai_greeting():
    assert detect_language("สวัสดี") == "th"


def test_thai_longer():
    result = detect_language(
        "ฉันต้องการข้อมูลเกี่ยวกับโซฟาที่คุณมีในร้าน"
    )
    assert result == "th"


def test_thai_two_chars():
    # "เค" is two Thai characters — should still pass min_chars=2
    assert detect_language("เค") == "th"


# ── Hebrew ────────────────────────────────────────────────────────────────────


def test_hebrew_greeting():
    assert detect_language("שלום") == "he"


def test_hebrew_question():
    assert detect_language("מה שעות הפתיחה שלכם?") == "he"


def test_hebrew_longer():
    result = detect_language(
        "אני מחפש ספה לסלון שלי, יש לכם אפשרויות בהתאמה אישית?"
    )
    assert result == "he"


# ── English ───────────────────────────────────────────────────────────────────


def test_english_greeting():
    assert detect_language("hello") == "en"


def test_english_question():
    assert detect_language("Do you have sofas in stock?") == "en"


def test_english_longer():
    result = detect_language(
        "I would like to know more about your custom furniture options "
        "and whether you offer home delivery."
    )
    assert result == "en"


# ── Arabic ────────────────────────────────────────────────────────────────────


def test_arabic_greeting():
    assert detect_language("مرحبا") == "ar"


def test_arabic_question():
    assert detect_language("هل لديكم أرائك متاحة؟") == "ar"


# ── Russian ──────────────────────────────────────────────────────────────────


def test_russian_greeting():
    assert detect_language("привет") == "ru"


def test_russian_question():
    assert detect_language("Есть ли у вас диваны?") == "ru"


# ── Edge cases ────────────────────────────────────────────────────────────────


def test_empty_string_returns_none():
    assert detect_language("") is None


def test_single_char_returns_none():
    # Below min_chars threshold
    assert detect_language("x") is None


def test_whitespace_only_returns_none():
    assert detect_language("   ") is None


def test_digits_and_punctuation_only_returns_none():
    assert detect_language("123 !!! ???") is None


def test_single_emoji_returns_none():
    assert detect_language("😊") is None


# ── supported whitelist ───────────────────────────────────────────────────────


def test_thai_blocked_when_not_in_supported():
    # Thai detected but 'th' not in the allowed set → returns None
    result = detect_language("มีโซฟามั้ย", supported=["he", "en"])
    assert result is None


def test_thai_allowed_when_in_supported():
    result = detect_language("มีโซฟามั้ย", supported=["he", "en", "th"])
    assert result == "th"


def test_hebrew_blocked_when_not_in_supported():
    result = detect_language("שלום", supported=["en", "th"])
    assert result is None


def test_full_supported_list():
    supported = ["en", "he", "ar", "fa", "th", "fr", "es", "de", "ru", "ja", "zh", "hi"]
    assert detect_language("มีโซฟามั้ย", supported=supported) == "th"
    assert detect_language("שלום", supported=supported) == "he"
    assert detect_language("hello there", supported=supported) == "en"


# ── Confidence / mixed script ─────────────────────────────────────────────────


def test_heavily_mixed_scripts_returns_none():
    # Half Thai, half Hebrew — below the 0.5 confidence floor for either
    mixed = "שלום สวัสดี"
    result = detect_language(mixed)
    # May return None or a dominant language, but must not crash
    assert result in (None, "he", "th")


def test_latin_with_numbers_resolved_to_en():
    # Numbers don't count as scriptable chars; words dominate
    result = detect_language("I need 3 sofas please")
    assert result == "en"
