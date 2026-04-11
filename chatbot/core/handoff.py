"""
Human handoff manager.

Tracks sessions that need human attention.  When a session is flagged
(either by the bot detecting low confidence, by the user explicitly
requesting a human, or by an admin taking over), all subsequent messages
in that session are routed to a live-agent queue instead of the LLM.

The admin can reply through the admin panel; the reply is delivered
back through the originating channel.

Handoff state is persisted to a JSON file under ``.handoff/``.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT


class HandoffSession(BaseModel):
    """Tracks a single session in handoff mode."""

    session_id: str
    channel: str = "web"
    reason: str = ""  # "user_request", "low_confidence", "admin_takeover"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved_at: str = ""
    is_active: bool = True
    pending_messages: list[dict] = Field(default_factory=list)
    # pending_messages: [{"role": "user"|"admin", "text": "...", "at": "ISO"}]


class HandoffManager:
    """Thread-safe JSON-backed handoff session tracker."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (PROJECT_ROOT / ".handoff" / "sessions.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def is_handed_off(self, session_id: str) -> bool:
        """Check if a session is currently in handoff mode."""
        with self._lock:
            data = self._load()
        for s in data:
            if s.get("session_id") == session_id and s.get("is_active"):
                return True
        return False

    def start_handoff(
        self, session_id: str, channel: str = "web", reason: str = "user_request"
    ) -> str:
        """Flag a session for human handoff.  Returns the handoff id."""
        with self._lock:
            data = self._load()
            # Don't create duplicate active handoffs for the same session
            for s in data:
                if s.get("session_id") == session_id and s.get("is_active"):
                    return s.get("session_id", session_id)
            entry = HandoffSession(
                session_id=session_id,
                channel=channel,
                reason=reason,
            )
            data.append(entry.model_dump())
            self._save(data)
        logger.info("[handoff] Started for {} ({}): {}", session_id, channel, reason)
        return session_id

    def add_message(self, session_id: str, role: str, text: str) -> bool:
        """Append a message to the handoff queue (user or admin)."""
        with self._lock:
            data = self._load()
            for s in data:
                if s.get("session_id") == session_id and s.get("is_active"):
                    s.setdefault("pending_messages", []).append({
                        "role": role,
                        "text": text,
                        "at": datetime.now(timezone.utc).isoformat(),
                    })
                    self._save(data)
                    return True
        return False

    def get_pending_admin_reply(self, session_id: str) -> str | None:
        """Pop the oldest admin reply for delivery to the user."""
        with self._lock:
            data = self._load()
            for s in data:
                if s.get("session_id") == session_id and s.get("is_active"):
                    msgs = s.get("pending_messages", [])
                    for i, m in enumerate(msgs):
                        if m.get("role") == "admin":
                            msgs.pop(i)
                            self._save(data)
                            return m.get("text", "")
        return None

    def resolve(self, session_id: str) -> bool:
        """End handoff, returning session to bot mode."""
        with self._lock:
            data = self._load()
            for s in data:
                if s.get("session_id") == session_id and s.get("is_active"):
                    s["is_active"] = False
                    s["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    self._save(data)
                    logger.info("[handoff] Resolved {}", session_id)
                    return True
        return False

    def list_active(self) -> list[dict]:
        with self._lock:
            data = self._load()
        return [s for s in data if s.get("is_active")]

    def list_all(self, limit: int = 50) -> list[dict]:
        with self._lock:
            data = self._load()
        return list(reversed(data[-limit:]))

    def get_session(self, session_id: str) -> dict | None:
        with self._lock:
            data = self._load()
        for s in data:
            if s.get("session_id") == session_id and s.get("is_active"):
                return s
        return None

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

    def _save(self, data: list[dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self._path)
