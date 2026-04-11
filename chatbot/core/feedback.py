"""
Feedback collection — thumbs up/down per answer.

Stores user feedback in-memory with optional JSON persistence.
Used by the analytics dashboard and for retrieval improvement.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Literal, Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT

FeedbackType = Literal["up", "down"]


class FeedbackEntry(BaseModel):
    """A single feedback event."""

    session_id: str
    message_index: int = 0  # which assistant message in the session
    question: str = ""
    answer: str = ""
    feedback: FeedbackType
    comment: str = ""  # optional user comment
    language: str = ""
    channel: str = "web"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class FeedbackStore:
    """In-memory feedback store with JSON file persistence."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._entries: list[FeedbackEntry] = []
        self._storage_dir = storage_dir or (PROJECT_ROOT / ".feedback")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._storage_dir / "feedback.json"
        self._load()

    def _load(self) -> None:
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._entries = [FeedbackEntry(**e) for e in data]
            except Exception as e:
                logger.warning("Could not load feedback: {}", e)

    def _save(self) -> None:
        try:
            tmp = self._file.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    [e.model_dump() for e in self._entries],
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._file)
        except Exception as e:
            logger.warning("Could not save feedback: {}", e)

    def add(self, entry: FeedbackEntry) -> None:
        self._entries.append(entry)
        self._save()
        logger.debug(
            "[feedback] {} from {} (session={})",
            entry.feedback,
            entry.channel,
            entry.session_id,
        )

    def list_all(self, limit: int = 500) -> list[dict[str, Any]]:
        return [e.model_dump() for e in reversed(self._entries[-limit:])]

    def stats(self) -> dict[str, Any]:
        total = len(self._entries)
        ups = sum(1 for e in self._entries if e.feedback == "up")
        downs = total - ups
        return {
            "total": total,
            "thumbs_up": ups,
            "thumbs_down": downs,
            "satisfaction_rate": round(ups / total * 100, 1) if total else 0,
        }

    def recent_negative(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent negative feedback for review."""
        negatives = [e for e in self._entries if e.feedback == "down"]
        return [e.model_dump() for e in reversed(negatives[-limit:])]

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> int:
        n = len(self._entries)
        self._entries.clear()
        self._save()
        return n
