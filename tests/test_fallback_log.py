"""Tests for chatbot.core.fallback_log."""
from __future__ import annotations

import pytest

from chatbot.core.fallback_log import FallbackEntry, FallbackLog, looks_like_fallback


# ── looks_like_fallback ──────────────────────────────────────────────────────


def test_fallback_english():
    assert looks_like_fallback("I don't have that information right now.") is True
    assert looks_like_fallback("I'm not sure about the pricing for that.") is True
    assert looks_like_fallback("Please contact us for more details.") is True


def test_fallback_hebrew():
    assert looks_like_fallback("אין לי מידע על זה") is True
    assert looks_like_fallback("לא מצאתי תשובה") is True


def test_fallback_thai():
    assert looks_like_fallback("ไม่มีข้อมูลเรื่องนี้ครับ") is True


def test_not_fallback():
    assert looks_like_fallback("Our store is open from 9 AM to 6 PM.") is False
    assert looks_like_fallback("The price of the sheer curtain starts at 340 ₪.") is False


# ── FallbackLog ──────────────────────────────────────────────────────────────


@pytest.fixture
def flog(tmp_path):
    return FallbackLog(path=tmp_path / "fallback.json")


def test_log_and_list(flog):
    flog.log(FallbackEntry(question="What is your return policy?", answer_given="I don't know"))
    items = flog.list_all()
    assert len(items) == 1
    assert items[0]["question"] == "What is your return policy?"


def test_deduplication(flog):
    flog.log(FallbackEntry(question="Same question"))
    flog.log(FallbackEntry(question="Same question"))
    assert len(flog.list_all()) == 1


def test_count_unresolved(flog):
    flog.log(FallbackEntry(question="Q1"))
    flog.log(FallbackEntry(question="Q2"))
    assert flog.count_unresolved() == 2


def test_resolve(flog):
    flog.log(FallbackEntry(question="Q1"))
    assert flog.resolve("Q1", admin_note="Added to FAQ") is True
    assert flog.count_unresolved() == 0

    items = flog.list_all()
    assert items[0]["resolved"] is True
    assert items[0]["admin_note"] == "Added to FAQ"


def test_resolve_nonexistent(flog):
    assert flog.resolve("no such question") is False


def test_mark_added_to_kb(flog):
    flog.log(FallbackEntry(question="Q1"))
    assert flog.mark_added_to_kb("Q1") is True

    items = flog.list_all()
    assert items[0]["added_to_kb"] is True
    assert items[0]["resolved"] is True


def test_delete(flog):
    flog.log(FallbackEntry(question="To delete"))
    assert flog.delete("To delete") is True
    assert len(flog.list_all()) == 0


def test_delete_nonexistent(flog):
    assert flog.delete("no such") is False


def test_list_unresolved_only(flog):
    flog.log(FallbackEntry(question="Q1"))
    flog.log(FallbackEntry(question="Q2"))
    flog.resolve("Q1")

    unresolved = flog.list_all(unresolved_only=True)
    assert len(unresolved) == 1
    assert unresolved[0]["question"] == "Q2"


def test_persistence(tmp_path):
    path = tmp_path / "fallback.json"
    log1 = FallbackLog(path=path)
    log1.log(FallbackEntry(question="Persist test"))

    log2 = FallbackLog(path=path)
    assert len(log2.list_all()) == 1
