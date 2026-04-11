"""Tests for chatbot.core.handoff."""
from __future__ import annotations

import pytest

from chatbot.core.handoff import HandoffManager


@pytest.fixture
def mgr(tmp_path):
    return HandoffManager(path=tmp_path / "handoff.json")


def test_start_and_check(mgr):
    assert mgr.is_handed_off("sess1") is False
    mgr.start_handoff("sess1", channel="web", reason="user_request")
    assert mgr.is_handed_off("sess1") is True


def test_no_duplicate_active_handoff(mgr):
    mgr.start_handoff("sess1")
    mgr.start_handoff("sess1")  # should not create a second entry
    assert len(mgr.list_active()) == 1


def test_add_message(mgr):
    mgr.start_handoff("sess1")

    assert mgr.add_message("sess1", "user", "Hello") is True
    assert mgr.add_message("sess1", "admin", "Hi there") is True

    session = mgr.get_session("sess1")
    assert len(session["pending_messages"]) == 2


def test_add_message_no_active_session(mgr):
    assert mgr.add_message("nonexistent", "user", "test") is False


def test_get_pending_admin_reply(mgr):
    mgr.start_handoff("sess1")
    mgr.add_message("sess1", "user", "question")
    mgr.add_message("sess1", "admin", "answer")

    reply = mgr.get_pending_admin_reply("sess1")
    assert reply == "answer"

    # Should be consumed (popped)
    assert mgr.get_pending_admin_reply("sess1") is None


def test_get_pending_admin_reply_skips_user_messages(mgr):
    mgr.start_handoff("sess1")
    mgr.add_message("sess1", "user", "question1")
    mgr.add_message("sess1", "user", "question2")

    assert mgr.get_pending_admin_reply("sess1") is None


def test_resolve(mgr):
    mgr.start_handoff("sess1")
    assert mgr.is_handed_off("sess1") is True

    assert mgr.resolve("sess1") is True
    assert mgr.is_handed_off("sess1") is False


def test_resolve_nonexistent(mgr):
    assert mgr.resolve("nonexistent") is False


def test_list_active_vs_all(mgr):
    mgr.start_handoff("sess1")
    mgr.start_handoff("sess2")
    mgr.resolve("sess1")

    active = mgr.list_active()
    assert len(active) == 1
    assert active[0]["session_id"] == "sess2"

    all_sessions = mgr.list_all()
    assert len(all_sessions) == 2


def test_get_session(mgr):
    mgr.start_handoff("sess1", channel="line", reason="low_confidence")
    session = mgr.get_session("sess1")
    assert session is not None
    assert session["channel"] == "line"
    assert session["reason"] == "low_confidence"


def test_get_session_returns_none_after_resolve(mgr):
    mgr.start_handoff("sess1")
    mgr.resolve("sess1")
    assert mgr.get_session("sess1") is None


def test_persistence(tmp_path):
    path = tmp_path / "handoff.json"
    mgr1 = HandoffManager(path=path)
    mgr1.start_handoff("sess1")
    mgr1.add_message("sess1", "user", "hello")

    mgr2 = HandoffManager(path=path)
    assert mgr2.is_handed_off("sess1") is True
    session = mgr2.get_session("sess1")
    assert len(session["pending_messages"]) == 1
