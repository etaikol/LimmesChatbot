"""Unit tests for chatbot.core.analytics — dashboard_summary() aggregation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from chatbot.core.analytics import AnalyticsEvent, AnalyticsTracker


# ── helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ago(days: float = 0, hours: float = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days, hours=hours)
    return dt.isoformat()


def _tracker(tmp_path):
    return AnalyticsTracker(storage_dir=tmp_path / "analytics")


def _question(
    session_id: str = "s1",
    question: str = "hello",
    response_time_ms: int = 100,
    was_fallback: bool = False,
    language: str = "en",
    channel: str = "web",
    ab_variant: str = "",
    timestamp: str | None = None,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_type="question",
        session_id=session_id,
        question=question,
        response_time_ms=response_time_ms,
        was_fallback=was_fallback,
        language=language,
        channel=channel,
        ab_variant=ab_variant,
        timestamp=timestamp or _now(),
    )


def _feedback(
    session_id: str = "s1",
    feedback: str = "up",
    ab_variant: str = "",
    timestamp: str | None = None,
) -> AnalyticsEvent:
    return AnalyticsEvent(
        event_type="feedback",
        session_id=session_id,
        feedback=feedback,
        ab_variant=ab_variant,
        timestamp=timestamp or _now(),
    )


# ── basic counts ─────────────────────────────────────────────────────────────

def test_empty_summary(tmp_path):
    t = _tracker(tmp_path)
    s = t.dashboard_summary(days=7)
    assert s["total_questions"] == 0
    assert s["total_sessions"] == 0
    assert s["unanswered_count"] == 0
    assert s["unanswered_rate"] == 0
    assert s["avg_response_time_ms"] == 0
    assert s["feedback"]["total"] == 0
    assert s["feedback"]["satisfaction_rate"] == 0


def test_total_questions_and_sessions(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", "q1"))
    t.track(_question("s1", "q2"))
    t.track(_question("s2", "q3"))
    s = t.dashboard_summary(days=7)
    assert s["total_questions"] == 3
    assert s["total_sessions"] == 2


# ── unanswered rate ───────────────────────────────────────────────────────────

def test_unanswered_rate(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", "answered", was_fallback=False))
    t.track(_question("s1", "fallback", was_fallback=True))
    t.track(_question("s1", "fallback2", was_fallback=True))
    s = t.dashboard_summary(days=7)
    assert s["unanswered_count"] == 2
    assert s["unanswered_rate"] == pytest.approx(66.7, abs=0.1)


def test_unanswered_rate_zero_when_no_fallbacks(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1"))
    s = t.dashboard_summary(days=7)
    assert s["unanswered_rate"] == 0.0


# ── average response time ─────────────────────────────────────────────────────

def test_avg_response_time(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", response_time_ms=200))
    t.track(_question("s1", response_time_ms=400))
    s = t.dashboard_summary(days=7)
    assert s["avg_response_time_ms"] == 300


def test_avg_response_time_ignores_zero(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", response_time_ms=0))
    t.track(_question("s1", response_time_ms=500))
    s = t.dashboard_summary(days=7)
    # response_time_ms=0 is excluded from average
    assert s["avg_response_time_ms"] == 500


# ── language / channel breakdowns ─────────────────────────────────────────────

def test_language_breakdown(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", language="en"))
    t.track(_question("s1", language="th"))
    t.track(_question("s2", language="en"))
    s = t.dashboard_summary(days=7)
    assert s["language_breakdown"]["en"] == 2
    assert s["language_breakdown"]["th"] == 1


def test_channel_breakdown(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", channel="web"))
    t.track(_question("s1", channel="line"))
    s = t.dashboard_summary(days=7)
    assert s["channel_breakdown"]["web"] == 1
    assert s["channel_breakdown"]["line"] == 1


# ── top questions ─────────────────────────────────────────────────────────────

def test_top_questions(tmp_path):
    t = _tracker(tmp_path)
    for _ in range(3):
        t.track(_question("s1", question="hello"))
    t.track(_question("s1", question="what is your name?"))
    s = t.dashboard_summary(days=7)
    top = {item["question"]: item["count"] for item in s["top_questions"]}
    assert top["hello"] == 3
    assert top["what is your name"] == 1  # trailing ? stripped by normalization


# ── feedback stats ─────────────────────────────────────────────────────────────

def test_feedback_stats(tmp_path):
    t = _tracker(tmp_path)
    t.track(_feedback("s1", "up"))
    t.track(_feedback("s1", "up"))
    t.track(_feedback("s1", "down"))
    s = t.dashboard_summary(days=7)
    fb = s["feedback"]
    assert fb["total"] == 3
    assert fb["thumbs_up"] == 2
    assert fb["thumbs_down"] == 1
    assert fb["satisfaction_rate"] == pytest.approx(66.7, abs=0.1)


def test_feedback_satisfaction_zero_when_no_feedback(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1"))
    s = t.dashboard_summary(days=7)
    assert s["feedback"]["satisfaction_rate"] == 0


# ── time window filtering ─────────────────────────────────────────────────────

def test_window_filters_old_events(tmp_path):
    t = _tracker(tmp_path)
    # Event from 10 days ago — should be excluded from a 7-day window
    t.track(_question("s1", timestamp=_ago(days=10)))
    t.track(_question("s2", timestamp=_now()))
    s = t.dashboard_summary(days=7)
    assert s["total_questions"] == 1


# ── A/B test results ──────────────────────────────────────────────────────────

def test_ab_test_results(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", response_time_ms=100, ab_variant="control"))
    t.track(_question("s2", response_time_ms=200, ab_variant="variant_b"))
    t.track(_feedback("s1", "up", ab_variant="control"))
    t.track(_feedback("s2", "down", ab_variant="variant_b"))
    s = t.dashboard_summary(days=7)
    ab = s["ab_test_results"]
    assert ab["control"]["questions"] == 1
    assert ab["control"]["satisfaction_rate"] == 100.0
    assert ab["control"]["avg_response_time_ms"] == 100
    assert ab["variant_b"]["questions"] == 1
    assert ab["variant_b"]["satisfaction_rate"] == 0.0
    assert ab["variant_b"]["avg_response_time_ms"] == 200


def test_ab_fallback_rate(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1", was_fallback=True, ab_variant="control"))
    t.track(_question("s1", was_fallback=False, ab_variant="control"))
    s = t.dashboard_summary(days=7)
    ab = s["ab_test_results"]
    assert ab["control"]["fallback_rate"] == pytest.approx(50.0, abs=0.1)


# ── batching (no premature disk flush) ───────────────────────────────────────

def test_batch_flush(tmp_path):
    """Events accumulate in memory; only flush after FLUSH_BATCH_SIZE events."""
    t = _tracker(tmp_path)
    events_file = tmp_path / "analytics" / "events.json"

    # Add fewer events than the batch threshold — file should not exist yet
    for i in range(t.FLUSH_BATCH_SIZE - 1):
        t.track(_question(f"s{i}"))
    assert not events_file.exists(), "Should not flush before batch threshold"

    # Explicit flush writes the file
    t.flush()
    assert events_file.exists()


def test_clear_resets_pending(tmp_path):
    t = _tracker(tmp_path)
    t.track(_question("s1"))
    n = t.clear()
    assert n == 1
    assert t.count() == 0
