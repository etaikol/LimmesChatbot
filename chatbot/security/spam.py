"""
Spam & gibberish detection — blocks token-wasting messages before the LLM.

Problem this solves
-------------------
Rate limiting caps *velocity*, but a user can still send 12 garbage
messages per minute (e.g. ``שדג``, ``abc``, random key-mashing) and
each one costs LLM tokens.  This module adds a *quality* gate:

1. **Gibberish detection** — rejects messages that are clearly not
   meaningful text (very short, highly repetitive, random characters).
2. **Duplicate detection** — rejects the same message sent twice in a
   row within the same session.
3. **Per-session abuse scoring** — tracks how many messages a session
   has had rejected.  After ``max_strikes`` consecutive bad messages
   the session is temporarily blocked (``cooldown_seconds``).

All thresholds are configurable via ``Settings`` and tuned for a
Hebrew-primary chatbot that also serves English, Arabic, Russian, Thai.

Wiring
------
This module is intended to be invoked by request-handling code after
``sanitize_user_input()`` and before any budget check or LLM call.
The cost is negligible (string comparisons, no network, no model
inference).
"""

from __future__ import annotations

import re
import time
import threading
from dataclasses import dataclass


# ── Gibberish heuristics ──────────────────────────────────────────────────

# A message consisting entirely of the same character repeated.
_REPEAT_CHAR_RE = re.compile(r"^(.)\1{2,}$", re.UNICODE)

# Messages that are just punctuation, whitespace, or symbol soup.
_SYMBOL_ONLY_RE = re.compile(
    r"^[\s\d\W]+$", re.UNICODE
)

# Thai combining marks (above/below vowels, tone marks, etc.) that cannot
# appear at the start of a syllable or in isolation. When the *majority* of
# Thai characters in a message are combining marks, the text is gibberish
# produced by mashing the keyboard with a Thai layout.
_THAI_COMBINING = set(
    "\u0e31"           # mai han akat (อั)
    "\u0e34\u0e35\u0e36\u0e37\u0e38\u0e39"  # upper/lower vowels (อิีึืุู)
    "\u0e47"           # mai tai khu (อ็)
    "\u0e48\u0e49\u0e4a\u0e4b"  # tone marks (อ่้๊๋)
    "\u0e4c\u0e4d\u0e4e"        # thanthakhat, nikhahit, yamakkan
)
# Thai consonant range: ก (0E01) – ฮ (0E2E)
_THAI_CONSONANT_RANGE = range(0x0E01, 0x0E2F)
# Full Thai block range
_THAI_BLOCK_RANGE = range(0x0E00, 0x0E80)


def _is_thai_gibberish(text: str) -> bool:
    """Return True if the text looks like Thai keyboard mashing.

    Two heuristics:
    1. If the message starts with a Thai combining mark (no consonant
       base), it is almost certainly accidental key-mashing.
    2. If Thai characters are present and the ratio of combining marks
       to consonants is >= 1.0, the text has more modifiers than
       letters — not meaningful Thai.
    3. Very short Thai-only text (≤4 chars) with no consonant is gibberish.
    """
    stripped = text.strip()
    if not stripped:
        return False

    thai_chars = [c for c in stripped if ord(c) in _THAI_BLOCK_RANGE]
    if not thai_chars:
        return False  # not Thai text, skip

    # Heuristic 1: starts with a combining mark
    if stripped[0] in _THAI_COMBINING:
        return True

    consonants = sum(1 for c in thai_chars if ord(c) in _THAI_CONSONANT_RANGE)
    combining = sum(1 for c in thai_chars if c in _THAI_COMBINING)

    # Heuristic 2: far more combining marks than consonants (ratio > 1.5)
    # Normal Thai has ≤1 mark per consonant; gibberish mashing produces
    # ratios of 2-3+.  We use 1.5 so real words like ดี (ratio 1.0) pass.
    if consonants > 0 and combining / consonants > 1.5:
        return True

    # Heuristic 3: very short Thai-only, no consonants at all
    if len(stripped) <= 4 and consonants == 0:
        return True

    # Heuristic 4: short Thai text (≤4 chars) with only consonants
    # and no vowels = random consonant mash like "พดไพ"
    if len(thai_chars) <= 4 and len(thai_chars) == len(stripped):
        vowels_and_marks = combining + sum(
            1 for c in thai_chars
            if c in "\u0e40\u0e41\u0e42\u0e43\u0e44"  # leading vowels (เแโใไ)
            or c in "\u0e30\u0e32\u0e33"  # sara a, sara aa, sara am
        )
        if consonants >= 2 and vowels_and_marks == 0 and " " not in stripped:
            return True

    return False


def is_gibberish(text: str, *, min_meaningful_chars: int = 2) -> bool:
    """Return True if ``text`` looks like gibberish / key-mashing.

    This is intentionally conservative — it only catches *obvious* junk
    so real Hebrew/Arabic/Thai short messages are not blocked.
    """
    stripped = text.strip()

    # Too short to be meaningful (single char or two random chars).
    if len(stripped) < min_meaningful_chars:
        return True

    # Same character repeated: "ааааа", "שששש"
    if _REPEAT_CHAR_RE.match(stripped):
        return True

    # Pure symbols/digits/whitespace, no letters at all.
    if _SYMBOL_ONLY_RE.match(stripped):
        return True

    # Very short + no spaces = likely random key hit (e.g. "שדג", "abc").
    # We allow up to 3 chars only if they form a single "word" with no
    # spaces — real questions are longer or contain spaces.
    # Exception: Thai, CJK, and other scripts where 2-3 character words
    # are common (ดี=good, ไป=go, ไม่=no, 是=yes, etc.).
    if len(stripped) <= 3 and " " not in stripped:
        has_thai = any(ord(c) in _THAI_BLOCK_RANGE for c in stripped)
        has_cjk = any(0x4E00 <= ord(c) <= 0x9FFF for c in stripped)
        if not (has_thai or has_cjk):
            return True

    # Multi-line key mashing: lines of 1-3 chars each.
    lines = [ln.strip() for ln in stripped.splitlines() if ln.strip()]
    if len(lines) >= 2 and all(len(ln) <= 3 for ln in lines):
        return True

    # Thai-specific keyboard-mashing detection.
    if _is_thai_gibberish(stripped):
        return True

    return False


# ── Per-session spam tracker ──────────────────────────────────────────────

@dataclass
class _SessionRecord:
    """Mutable spam state for one session."""
    strikes: int = 0
    last_message: str = ""
    last_message_time: float = 0.0
    blocked_until: float = 0.0
    total_rejected: int = 0
    block_count: int = 0


class SpamTracker:
    """Per-session abuse tracker with progressive cooldowns.

    Parameters
    ----------
    max_strikes:
        Consecutive bad messages before the session is temp-blocked.
    cooldown_seconds:
        How long to block after ``max_strikes`` is reached. Doubles
        on each subsequent offence (capped at ``max_cooldown_seconds``).
    max_cooldown_seconds:
        Upper bound on the cooldown escalation.
    duplicate_window:
        Seconds within which an identical message is considered a
        duplicate.
    idle_ttl:
        Evict session records idle longer than this (seconds).
    """

    def __init__(
        self,
        *,
        max_strikes: int = 5,
        cooldown_seconds: float = 30.0,
        max_cooldown_seconds: float = 300.0,
        duplicate_window: float = 60.0,
        idle_ttl: float = 3600.0,
        min_meaningful_chars: int = 2,
    ) -> None:
        self.max_strikes = max(1, max_strikes)
        self.cooldown_seconds = max(1.0, cooldown_seconds)
        self.max_cooldown_seconds = max(cooldown_seconds, max_cooldown_seconds)
        self.duplicate_window = max(0.0, duplicate_window)
        self.idle_ttl = idle_ttl
        self.min_meaningful_chars = max(1, min_meaningful_chars)
        self._sessions: dict[str, _SessionRecord] = {}
        self._lock = threading.Lock()
        self._last_gc = time.monotonic()

    def check(self, session_id: str, message: str) -> str | None:
        """Check message quality for a session.

        Returns ``None`` if the message is allowed, or a short rejection
        reason string if it should be blocked.
        """
        now = time.monotonic()

        with self._lock:
            self._maybe_gc(now)
            rec = self._sessions.get(session_id)
            if rec is None:
                rec = _SessionRecord()
                self._sessions[session_id] = rec

            # 1. Is this session currently blocked?
            if rec.blocked_until > now:
                remaining = int(rec.blocked_until - now) + 1
                return (
                    f"spam:blocked_temporarily:{remaining}"
                )

            # 2. Duplicate check.
            normalized = message.strip().lower()
            if (
                self.duplicate_window > 0
                and normalized == rec.last_message
                and (now - rec.last_message_time) < self.duplicate_window
            ):
                rec.strikes += 1
                rec.total_rejected += 1
                rec.last_message_time = now
                return self._maybe_block(rec, now, "spam:duplicate_message")

            # 3. Gibberish check.
            if is_gibberish(message, min_meaningful_chars=self.min_meaningful_chars):
                rec.strikes += 1
                rec.total_rejected += 1
                rec.last_message = normalized
                rec.last_message_time = now
                return self._maybe_block(rec, now, "spam:gibberish")

            # Good message — reset strikes.
            rec.strikes = 0
            rec.last_message = normalized
            rec.last_message_time = now
            return None

    def _maybe_block(self, rec: _SessionRecord, now: float, reason: str) -> str:
        """Apply progressive cooldown if strikes exceeded."""
        if rec.strikes >= self.max_strikes:
            multiplier = min(
                2 ** rec.block_count,
                self.max_cooldown_seconds / self.cooldown_seconds,
            )
            cooldown = min(
                self.cooldown_seconds * multiplier,
                self.max_cooldown_seconds,
            )
            rec.blocked_until = now + cooldown
            rec.strikes = 0
            rec.block_count += 1
            remaining = int(cooldown)
            return f"spam:session_blocked:{remaining}"
        return reason

    def reset(self, session_id: str) -> None:
        """Clear spam state for a session."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def _maybe_gc(self, now: float) -> None:
        if now - self._last_gc < 120.0:
            return
        self._last_gc = now
        cutoff = now - self.idle_ttl
        stale = [
            k for k, v in self._sessions.items()
            if v.last_message_time < cutoff and v.blocked_until < now
        ]
        for k in stale:
            del self._sessions[k]

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)
