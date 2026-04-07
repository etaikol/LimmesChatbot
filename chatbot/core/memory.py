"""
Conversation memory and session storage.

Two layers:
- `Message` / `ConversationMemory` — value objects (a single chat history).
- `SessionStore` — pluggable backend that maps `session_id -> ConversationMemory`.

Backends:
- "memory" — process-local dict, lost on restart (good for tests).
- "file" — JSON files under `settings.sessions_dir/`, survives restarts.
- "postgres" — see `chatbot.persistence.database` (optional).

The store is intentionally simple. For higher scale swap in Redis/DB.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal, Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import Settings, get_settings

Role = Literal["user", "assistant", "system"]


class Message(BaseModel):
    """Single chat message."""

    role: Role
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def as_text(self) -> str:
        label = {"user": "User", "assistant": "Assistant", "system": "System"}[self.role]
        return f"{label}: {self.content}"


class ConversationMemory(BaseModel):
    """A single conversation history with a soft cap on length."""

    messages: list[Message] = Field(default_factory=list)
    max_turns: int = 10  # one "turn" = a user msg + an assistant msg

    def add(self, role: Role, content: str) -> Message:
        msg = Message(role=role, content=content)
        self.messages.append(msg)
        self._trim()
        return msg

    def recent(self, n: Optional[int] = None) -> list[Message]:
        n = n if n is not None else self.max_turns * 2
        return self.messages[-n:]

    def as_history_text(self, n: Optional[int] = None) -> str:
        msgs = self.recent(n)
        if not msgs:
            return ""
        return "\n".join(m.as_text() for m in msgs)

    def clear(self) -> None:
        self.messages.clear()

    def _trim(self) -> None:
        cap = self.max_turns * 2 * 2  # allow some slack before trimming
        if len(self.messages) > cap:
            self.messages = self.messages[-self.max_turns * 2 :]


# ── Session store ────────────────────────────────────────────────────────────


class SessionStore:
    """Pluggable session store. Use `SessionStore.from_settings(...)` to build."""

    def __init__(
        self,
        backend: Literal["memory", "file", "postgres"] = "memory",
        sessions_dir: Optional[Path] = None,
        max_turns: int = 10,
    ) -> None:
        self.backend = backend
        self.max_turns = max_turns
        self.sessions_dir = sessions_dir
        self._memory: dict[str, ConversationMemory] = {}

        if backend == "file":
            assert sessions_dir is not None, "sessions_dir is required for file backend"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("SessionStore[file]: {}", sessions_dir)

        elif backend == "postgres":
            # Lazily import — postgres deps are optional.
            from chatbot.persistence.database import PostgresSessionBackend  # noqa: F401

            logger.debug("SessionStore[postgres]: enabled")

        else:
            logger.debug("SessionStore[memory]: enabled")

    # ── Public API ──────────────────────────────────────────────────────────

    def get(self, session_id: str) -> ConversationMemory:
        """Return the conversation memory for `session_id`, creating it lazily."""
        if session_id in self._memory:
            return self._memory[session_id]

        if self.backend == "file":
            mem = self._load_from_file(session_id)
        elif self.backend == "postgres":
            mem = self._load_from_postgres(session_id)
        else:
            mem = ConversationMemory(max_turns=self.max_turns)

        self._memory[session_id] = mem
        return mem

    def add_message(self, session_id: str, role: Role, content: str) -> None:
        mem = self.get(session_id)
        mem.add(role, content)
        self._persist(session_id, mem)

    def history_text(self, session_id: str) -> str:
        return self.get(session_id).as_history_text()

    def clear(self, session_id: str) -> None:
        self._memory.pop(session_id, None)
        if self.backend == "file":
            f = self._file_for(session_id)
            if f.exists():
                f.unlink()
        elif self.backend == "postgres":
            from chatbot.persistence.database import PostgresSessionBackend

            PostgresSessionBackend().clear(session_id)

    def list_sessions(self) -> Iterator[str]:
        if self.backend == "file" and self.sessions_dir:
            for f in self.sessions_dir.glob("*.json"):
                yield f.stem
        else:
            yield from self._memory.keys()

    # ── Internals ───────────────────────────────────────────────────────────

    def _file_for(self, session_id: str) -> Path:
        assert self.sessions_dir is not None
        # Sanitize id for filesystem use
        safe = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in session_id)
        return self.sessions_dir / f"{safe}.json"

    def _load_from_file(self, session_id: str) -> ConversationMemory:
        path = self._file_for(session_id)
        if not path.exists():
            return ConversationMemory(max_turns=self.max_turns)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ConversationMemory(**data)
        except Exception as e:
            logger.warning("Could not load session {}: {}", session_id, e)
            return ConversationMemory(max_turns=self.max_turns)

    def _load_from_postgres(self, session_id: str) -> ConversationMemory:
        from chatbot.persistence.database import PostgresSessionBackend

        return PostgresSessionBackend().load(session_id, max_turns=self.max_turns)

    def _persist(self, session_id: str, mem: ConversationMemory) -> None:
        if self.backend == "file":
            try:
                with open(self._file_for(session_id), "w", encoding="utf-8") as f:
                    json.dump(mem.model_dump(), f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning("Could not save session {}: {}", session_id, e)
        elif self.backend == "postgres":
            from chatbot.persistence.database import PostgresSessionBackend

            PostgresSessionBackend().save(session_id, mem)

    # ── Constructors ────────────────────────────────────────────────────────

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> SessionStore:
        s = settings or get_settings()
        return cls(
            backend=s.memory_backend,
            sessions_dir=s.sessions_dir,
            max_turns=s.max_history_turns,
        )
