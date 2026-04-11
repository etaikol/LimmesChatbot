"""Tests for chatbot.core.push."""
from __future__ import annotations

import asyncio

import pytest

from chatbot.core.push import PushService


class _FakeSettings:
    """Minimal settings stub for push tests."""
    line_channel_access_token = ""
    telegram_bot_token = ""
    twilio_account_sid = ""
    twilio_auth_token = ""
    twilio_whatsapp_number = ""


@pytest.fixture
def push():
    return PushService(_FakeSettings())


# ── Session parsing ──────────────────────────────────────────────────────


def test_parse_line():
    assert PushService._parse_session("line:Uabc123") == ("line", "Uabc123")


def test_parse_telegram():
    assert PushService._parse_session("telegram:99887766") == ("telegram", "99887766")


def test_parse_whatsapp():
    assert PushService._parse_session("whatsapp:+972501234567") == ("whatsapp", "+972501234567")


def test_parse_web():
    assert PushService._parse_session("web_a1b2c3d4") == ("web", "web_a1b2c3d4")


def test_parse_unknown_defaults_web():
    assert PushService._parse_session("random_session") == ("web", "random_session")


# ── Web SSE subscribe/unsubscribe ─────────────────────────────────────────


def test_subscribe_creates_queue(push):
    q = push.subscribe("web_testid")
    assert q is not None
    assert "web_testid" in push._web_queues


def test_subscribe_returns_same_queue(push):
    q1 = push.subscribe("web_testid")
    q2 = push.subscribe("web_testid")
    assert q1 is q2


def test_unsubscribe(push):
    push.subscribe("web_testid")
    push.unsubscribe("web_testid")
    assert "web_testid" not in push._web_queues


def test_unsubscribe_nonexistent(push):
    # Should not raise
    push.unsubscribe("web_nonexistent")


# ── Web push delivery ───────────────────────────────────────────────────


def test_push_web_with_listener(push):
    q = push.subscribe("web_testid")
    result = push._push_web("web_testid", "hello from admin")
    assert result is True
    assert q.qsize() == 1
    assert q.get_nowait() == "hello from admin"


def test_push_web_no_listener(push):
    result = push._push_web("web_testid", "hello")
    assert result is False


async def test_deliver_web(push):
    q = push.subscribe("web_testid")
    result = await push.deliver("web_testid", "admin says hi")
    assert result is True
    assert q.get_nowait() == "admin says hi"


async def test_deliver_web_no_listener(push):
    result = await push.deliver("web_nope", "test")
    assert result is False


# ── Channel push without configured credentials (should fail gracefully) ──


async def test_deliver_line_unconfigured(push):
    result = await push.deliver("line:Uabc", "test")
    assert result is False


async def test_deliver_telegram_unconfigured(push):
    result = await push.deliver("telegram:12345", "test")
    assert result is False


async def test_deliver_whatsapp_unconfigured(push):
    result = await push.deliver("whatsapp:+1234", "test")
    assert result is False


# ── Multiple messages queue in order ──────────────────────────────────────


def test_push_web_multiple_messages(push):
    q = push.subscribe("web_testid")
    push._push_web("web_testid", "msg1")
    push._push_web("web_testid", "msg2")
    push._push_web("web_testid", "msg3")
    assert q.get_nowait() == "msg1"
    assert q.get_nowait() == "msg2"
    assert q.get_nowait() == "msg3"


# ── Sentinel closes stream ───────────────────────────────────────────────


def test_push_web_sentinel(push):
    q = push.subscribe("web_testid")
    q.put_nowait(None)  # sentinel
    assert q.get_nowait() is None
