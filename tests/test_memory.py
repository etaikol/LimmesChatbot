"""Tests for chatbot.core.memory."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from chatbot.core.memory import ConversationMemory, Message, SessionStore


# ── Message ──────────────────────────────────────────────────────────────────


def test_message_as_text():
    msg = Message(role="user", content="Hello")
    assert msg.as_text() == "User: Hello"


def test_message_assistant():
    msg = Message(role="assistant", content="Hi there")
    assert msg.as_text() == "Assistant: Hi there"


# ── ConversationMemory ───────────────────────────────────────────────────────


def test_add_and_recent():
    mem = ConversationMemory(max_turns=5)
    mem.add("user", "Hello")
    mem.add("assistant", "Hi")
    msgs = mem.recent()
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"


def test_history_text():
    mem = ConversationMemory()
    mem.add("user", "hi")
    mem.add("assistant", "hello")
    text = mem.as_history_text()
    assert "User: hi" in text
    assert "Assistant: hello" in text


def test_trim_on_overflow():
    mem = ConversationMemory(max_turns=2)
    for i in range(20):
        mem.add("user", f"msg-{i}")
        mem.add("assistant", f"reply-{i}")
    # Should have trimmed to max_turns * 2 = 4 messages
    assert len(mem.messages) <= mem.max_turns * 2 + 4  # with slack


def test_clear():
    mem = ConversationMemory()
    mem.add("user", "hi")
    mem.clear()
    assert len(mem.messages) == 0


def test_empty_history():
    mem = ConversationMemory()
    assert mem.as_history_text() == ""


# ── SessionStore (memory backend) ────────────────────────────────────────────


def test_memory_backend_basic():
    store = SessionStore(backend="memory", max_turns=5)
    store.add_message("s1", "user", "hello")
    store.add_message("s1", "assistant", "hi")
    text = store.history_text("s1")
    assert "hello" in text
    assert "hi" in text


def test_memory_backend_separate_sessions():
    store = SessionStore(backend="memory")
    store.add_message("s1", "user", "question 1")
    store.add_message("s2", "user", "question 2")
    assert "question 1" in store.history_text("s1")
    assert "question 2" in store.history_text("s2")
    assert "question 2" not in store.history_text("s1")


def test_memory_backend_clear():
    store = SessionStore(backend="memory")
    store.add_message("s1", "user", "hello")
    store.clear("s1")
    assert store.history_text("s1") == ""


def test_memory_backend_eviction():
    store = SessionStore(backend="memory", max_turns=5)
    store.MAX_MEMORY_SESSIONS = 3
    for i in range(5):
        store.add_message(f"session-{i}", "user", f"msg-{i}")
    # Should have evicted oldest sessions
    assert len(store._memory) <= 3


# ── SessionStore (file backend) ──────────────────────────────────────────────


def test_file_backend_persist_and_load(tmp_path):
    store = SessionStore(backend="file", sessions_dir=tmp_path, max_turns=5)
    store.add_message("s1", "user", "hello file")
    store.add_message("s1", "assistant", "hi file")

    # Create a new store pointing to the same dir — should reload
    store2 = SessionStore(backend="file", sessions_dir=tmp_path, max_turns=5)
    text = store2.history_text("s1")
    assert "hello file" in text


def test_file_backend_atomic_write(tmp_path):
    store = SessionStore(backend="file", sessions_dir=tmp_path, max_turns=5)
    store.add_message("s1", "user", "test atomic")
    # The real file should exist but the tmp file should not
    session_files = list(tmp_path.glob("*.json"))
    assert len(session_files) == 1
    tmp_files = list(tmp_path.glob("*.json.tmp"))
    assert len(tmp_files) == 0


def test_file_backend_clear_deletes_file(tmp_path):
    store = SessionStore(backend="file", sessions_dir=tmp_path, max_turns=5)
    store.add_message("s1", "user", "hello")
    store.clear("s1")
    session_files = list(tmp_path.glob("*.json"))
    assert len(session_files) == 0


def test_file_backend_list_sessions(tmp_path):
    store = SessionStore(backend="file", sessions_dir=tmp_path, max_turns=5)
    store.add_message("s1", "user", "hello")
    store.add_message("s2", "user", "world")
    sessions = list(store.list_sessions())
    assert "s1" in sessions
    assert "s2" in sessions
