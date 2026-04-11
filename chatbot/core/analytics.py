"""
Analytics tracking — records events for the analytics dashboard.

Tracks: questions asked, response times, languages used, sessions,
unanswered rates, handoffs, feedback, and drop-off points.
"""

from __future__ import annotations

import json
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT


class AnalyticsEvent(BaseModel):
    """A single analytics event."""

    event_type: str  # "question", "handoff", "fallback", "feedback", "session_start", "session_end"
    session_id: str = ""
    channel: str = "web"
    language: str = ""
    question: str = ""
    response_time_ms: int = 0
    was_fallback: bool = False
    feedback: str = ""  # "up" / "down" / ""
    personality: str = ""
    ab_variant: str = ""  # A/B test variant name
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class AnalyticsTracker:
    """In-memory analytics with JSON persistence and aggregation."""

    MAX_EVENTS = 50000  # cap to prevent unbounded growth

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._events: list[AnalyticsEvent] = []
        self._storage_dir = storage_dir or (PROJECT_ROOT / ".analytics")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._storage_dir / "events.json"
        self._load()

    def _load(self) -> None:
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._events = [AnalyticsEvent(**e) for e in data[-self.MAX_EVENTS :]]
            except Exception as e:
                logger.warning("Could not load analytics: {}", e)

    def _save(self) -> None:
        try:
            tmp = self._file.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    [e.model_dump() for e in self._events[-self.MAX_EVENTS :]],
                    f,
                    ensure_ascii=False,
                )
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._file)
        except Exception as e:
            logger.warning("Could not save analytics: {}", e)

    def track(self, event: AnalyticsEvent) -> None:
        self._events.append(event)
        # Trim old events
        if len(self._events) > self.MAX_EVENTS:
            self._events = self._events[-self.MAX_EVENTS :]
        self._save()

    def track_question(
        self,
        session_id: str,
        question: str,
        response_time_ms: int,
        language: str = "",
        channel: str = "web",
        was_fallback: bool = False,
        personality: str = "",
        ab_variant: str = "",
    ) -> None:
        self.track(AnalyticsEvent(
            event_type="question",
            session_id=session_id,
            question=question,
            response_time_ms=response_time_ms,
            language=language,
            channel=channel,
            was_fallback=was_fallback,
            personality=personality,
            ab_variant=ab_variant,
        ))

    def dashboard_summary(self, days: int = 7) -> dict[str, Any]:
        """Return aggregated analytics for the dashboard."""
        cutoff = datetime.now(timezone.utc).timestamp() - (days * 86400)
        recent = [
            e for e in self._events
            if _parse_ts(e.timestamp) >= cutoff
        ]

        questions = [e for e in recent if e.event_type == "question"]
        fallbacks = [e for e in questions if e.was_fallback]
        feedbacks = [e for e in recent if e.event_type == "feedback"]

        # Most asked (top 20 by grouping similar questions - simplified)
        q_counter: Counter = Counter()
        for e in questions:
            # Normalize: lowercase, strip punctuation
            norm = e.question.lower().strip("?!. ")
            if norm:
                q_counter[norm] += 1
        top_questions = [
            {"question": q, "count": c}
            for q, c in q_counter.most_common(20)
        ]

        # Language breakdown
        lang_counter: Counter = Counter()
        for e in questions:
            lang_counter[e.language or "unknown"] += 1

        # Channel breakdown
        channel_counter: Counter = Counter()
        for e in questions:
            channel_counter[e.channel or "web"] += 1

        # Session stats
        session_ids = set(e.session_id for e in questions if e.session_id)
        session_msgs: dict[str, int] = defaultdict(int)
        for e in questions:
            if e.session_id:
                session_msgs[e.session_id] += 1

        avg_session_length = (
            sum(session_msgs.values()) / len(session_msgs)
            if session_msgs
            else 0
        )

        # Response time
        resp_times = [e.response_time_ms for e in questions if e.response_time_ms > 0]
        avg_response_time = (
            sum(resp_times) / len(resp_times) if resp_times else 0
        )

        # Feedback stats
        fb_ups = sum(1 for e in feedbacks if e.feedback == "up")
        fb_downs = sum(1 for e in feedbacks if e.feedback == "down")

        # A/B test results
        ab_results = self._ab_summary(recent)

        # Daily volume (last N days)
        daily: dict[str, int] = defaultdict(int)
        for e in questions:
            day = e.timestamp[:10]  # YYYY-MM-DD
            daily[day] += 1

        return {
            "period_days": days,
            "total_questions": len(questions),
            "total_sessions": len(session_ids),
            "unanswered_count": len(fallbacks),
            "unanswered_rate": round(
                len(fallbacks) / len(questions) * 100, 1
            ) if questions else 0,
            "avg_session_length": round(avg_session_length, 1),
            "avg_response_time_ms": round(avg_response_time),
            "top_questions": top_questions,
            "language_breakdown": dict(lang_counter.most_common()),
            "channel_breakdown": dict(channel_counter.most_common()),
            "feedback": {
                "total": fb_ups + fb_downs,
                "thumbs_up": fb_ups,
                "thumbs_down": fb_downs,
                "satisfaction_rate": round(
                    fb_ups / (fb_ups + fb_downs) * 100, 1
                ) if (fb_ups + fb_downs) else 0,
            },
            "daily_volume": dict(sorted(daily.items())),
            "ab_test_results": ab_results,
        }

    def _ab_summary(self, events: list[AnalyticsEvent]) -> dict[str, Any]:
        """Compute A/B test performance by variant."""
        variants: dict[str, dict[str, Any]] = {}
        for e in events:
            if not e.ab_variant:
                continue
            v = e.ab_variant
            if v not in variants:
                variants[v] = {
                    "questions": 0,
                    "feedbacks_up": 0,
                    "feedbacks_down": 0,
                    "fallbacks": 0,
                    "total_response_time": 0,
                }
            if e.event_type == "question":
                variants[v]["questions"] += 1
                variants[v]["total_response_time"] += e.response_time_ms
                if e.was_fallback:
                    variants[v]["fallbacks"] += 1
            elif e.event_type == "feedback":
                if e.feedback == "up":
                    variants[v]["feedbacks_up"] += 1
                elif e.feedback == "down":
                    variants[v]["feedbacks_down"] += 1

        result = {}
        for v, stats in variants.items():
            total_fb = stats["feedbacks_up"] + stats["feedbacks_down"]
            result[v] = {
                "questions": stats["questions"],
                "satisfaction_rate": round(
                    stats["feedbacks_up"] / total_fb * 100, 1
                ) if total_fb else 0,
                "fallback_rate": round(
                    stats["fallbacks"] / stats["questions"] * 100, 1
                ) if stats["questions"] else 0,
                "avg_response_time_ms": round(
                    stats["total_response_time"] / stats["questions"]
                ) if stats["questions"] else 0,
            }
        return result

    def clear(self) -> int:
        n = len(self._events)
        self._events.clear()
        self._save()
        return n

    def count(self) -> int:
        return len(self._events)


def _parse_ts(ts: str) -> float:
    """Parse ISO timestamp to epoch seconds."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0
