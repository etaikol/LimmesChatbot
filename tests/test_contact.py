"""Tests for chatbot.core.contact."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatbot.core.contact import ContactMessage, ContactStore


@pytest.fixture
def store(tmp_path):
    return ContactStore(path=tmp_path / "contacts.json")


def test_add_and_list(store):
    msg = ContactMessage(
        session_id="web:abc",
        channel="web",
        customer_name="Alice",
        customer_contact="alice@example.com",
        message="Hello, I want to order a curtain.",
    )
    msg_id = store.add(msg)
    assert msg_id == msg.id

    items = store.list_all()
    assert len(items) == 1
    assert items[0]["customer_name"] == "Alice"
    assert items[0]["message"] == "Hello, I want to order a curtain."


def test_count_unread(store):
    store.add(ContactMessage(message="msg1"))
    store.add(ContactMessage(message="msg2"))
    assert store.count_unread() == 2


def test_mark_read(store):
    msg = ContactMessage(message="test")
    store.add(msg)
    assert store.count_unread() == 1

    assert store.mark_read(msg.id) is True
    assert store.count_unread() == 0

    items = store.list_all()
    assert items[0]["read"] is True


def test_mark_replied(store):
    msg = ContactMessage(message="test")
    store.add(msg)

    assert store.mark_replied(msg.id) is True
    items = store.list_all()
    assert items[0]["replied"] is True
    assert items[0]["read"] is True  # mark_replied also marks as read


def test_delete(store):
    msg = ContactMessage(message="to-delete")
    store.add(msg)
    assert len(store.list_all()) == 1

    assert store.delete(msg.id) is True
    assert len(store.list_all()) == 0


def test_delete_nonexistent(store):
    assert store.delete("fake-id") is False


def test_mark_read_nonexistent(store):
    assert store.mark_read("fake-id") is False


def test_list_most_recent_first(store):
    store.add(ContactMessage(message="first", customer_name="A"))
    store.add(ContactMessage(message="second", customer_name="B"))
    items = store.list_all()
    assert items[0]["customer_name"] == "B"  # most recent first


def test_persistence(tmp_path):
    path = tmp_path / "contacts.json"
    store1 = ContactStore(path=path)
    store1.add(ContactMessage(message="persist-test"))

    store2 = ContactStore(path=path)
    assert len(store2.list_all()) == 1


def test_corrupt_json_recovery(tmp_path):
    path = tmp_path / "contacts.json"
    path.write_text("not valid json {{{")

    store = ContactStore(path=path)
    assert store.list_all() == []
    # Should still work after recovery
    store.add(ContactMessage(message="after-corrupt"))
    assert len(store.list_all()) == 1
