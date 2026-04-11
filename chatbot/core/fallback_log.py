"""
Fallback / unanswered-question logger.

When the bot's answer indicates it couldn't help (contains fallback phrases
like "I don't have that information"), the question is logged so the admin
can later add the answer to the knowledge base.

Persisted to a JSON file under ``.fallback/``.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT

# Phrases that indicate the bot couldn't answer.  Checked case-insensitively
# against the bot's reply.
FALLBACK_INDICATORS = [
    "i don't have that information",
    "i don't have information",
    "i'm not sure about",
    "i cannot find",
    "i couldn't find",
    "not in my knowledge",
    "outside my knowledge",
    "i don't know",
    "אין לי מידע",
    "לא מצאתי",
    "אני לא יודע",
    "אני לא בטוח",
    "ไม่มีข้อมูล",
    "ไม่ทราบ",
    "contact us for more",
    "please contact",
    "reach out to us",
]


class FallbackEntry(BaseModel):
    question: str
    answer_given: str = ""
    session_id: str = ""
    channel: str = "web"
    language: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    resolved: bool = False
    added_to_kb: bool = False
    admin_note: str = ""


def looks_like_fallback(answer: str) -> bool:
    """Return True if the bot's answer looks like it failed to find info."""
    lower = answer.lower()
    return any(phrase in lower for phrase in FALLBACK_INDICATORS)


class FallbackLog:
    """Thread-safe JSON-backed fallback question log."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (PROJECT_ROOT / ".fallback" / "questions.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def log(self, entry: FallbackEntry) -> None:
        with self._lock:
            data = self._load()
            # Deduplicate: don't log the exact same question twice
            for existing in data:
                if existing.get("question", "").strip() == entry.question.strip():
                    return
            data.append(entry.model_dump())
            self._save(data)
        logger.info("[fallback] Logged unanswered: {!r}", entry.question[:80])

    def list_all(self, limit: int = 100, unresolved_only: bool = False) -> list[dict]:
        with self._lock:
            data = self._load()
        if unresolved_only:
            data = [d for d in data if not d.get("resolved")]
        return list(reversed(data[-limit:]))

    def count_unresolved(self) -> int:
        with self._lock:
            data = self._load()
        return sum(1 for d in data if not d.get("resolved"))

    def resolve(self, question: str, admin_note: str = "") -> bool:
        with self._lock:
            data = self._load()
            for d in data:
                if d.get("question", "").strip() == question.strip():
                    d["resolved"] = True
                    d["admin_note"] = admin_note
                    self._save(data)
                    return True
        return False

    def mark_added_to_kb(self, question: str) -> bool:
        with self._lock:
            data = self._load()
            for d in data:
                if d.get("question", "").strip() == question.strip():
                    d["resolved"] = True
                    d["added_to_kb"] = True
                    self._save(data)
                    return True
        return False

    def delete(self, question: str) -> bool:
        with self._lock:
            data = self._load()
            new = [d for d in data if d.get("question", "").strip() != question.strip()]
            if len(new) == len(data):
                return False
            self._save(new)
        return True

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
