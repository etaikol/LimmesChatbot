"""
Input sanitation and prompt-injection heuristics.

This module provides three small functions used by every channel and
the HTTP API:

- :func:`sanitize_user_input` — strips control characters, normalizes
  whitespace, enforces a hard length cap, and rejects obviously empty or
  binary payloads. The cap protects token budgets *before* the message
  ever reaches the LLM.
- :func:`sanitize_session_id` — limits length and character set so a
  malicious user cannot escape the file-backed session store with
  ``../../etc/passwd``-style ids.
- :func:`looks_like_prompt_injection` — a *non-blocking* heuristic that
  flags messages containing classic injection markers ("ignore previous
  instructions", "disregard the system prompt", ...). The flag is logged
  and forwarded to the prompt as a hint; we deliberately do not refuse
  outright because false positives are common.

The goal is defense in depth, not perfect protection. The system prompt,
the retrieval-only answering rule, and rate limits are the real walls.
"""

from __future__ import annotations

import re
import unicodedata


# Control characters that have no business in chat input.
# We keep \t, \n, \r and strip everything else in the C0/C1 ranges.
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Excessive whitespace runs (>= 5 newlines or >= 80 spaces) → collapse.
_MULTI_NL_RE = re.compile(r"\n{5,}")
_MULTI_SP_RE = re.compile(r" {80,}")

_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore the above",
    "disregard the system prompt",
    "disregard previous",
    "you are now",
    "act as",
    "pretend you are",
    "developer mode",
    "jailbreak",
    "system prompt",
    "reveal your prompt",
    "print your instructions",
)


def sanitize_user_input(text: str, *, max_chars: int) -> str:
    """Return a normalized, length-capped version of ``text``.

    Raises ``ValueError`` for empty or oversized input so the caller can
    return HTTP 400 cleanly.
    """
    if text is None:
        raise ValueError("Empty message.")
    if not isinstance(text, str):
        raise ValueError("Message must be a string.")

    # Unicode normalize so visually identical characters compare equal,
    # and to neutralize lookalike-character attacks against keyword filters.
    text = unicodedata.normalize("NFKC", text)

    # Drop dangerous control characters but keep newlines and tabs.
    text = _CTRL_RE.sub("", text)

    # Collapse pathological whitespace runs.
    text = _MULTI_NL_RE.sub("\n\n\n\n", text)
    text = _MULTI_SP_RE.sub(" " * 8, text)

    text = text.strip()
    if not text:
        raise ValueError("Empty message.")

    if max_chars > 0 and len(text) > max_chars:
        raise ValueError(
            f"Message too long ({len(text)} chars, max {max_chars})."
        )
    return text


# Session ids are user-controlled (the channel uses sender id, the widget
# generates a random one). Sanitize so they are safe as filenames and as
# log keys.
_SESSION_RE = re.compile(r"[^A-Za-z0-9_\-:.@]")


def sanitize_session_id(session_id: str, *, max_len: int = 128) -> str:
    """Replace unsafe characters with ``_`` and truncate."""
    if not session_id:
        return "anonymous"
    cleaned = _SESSION_RE.sub("_", session_id)[:max_len]
    return cleaned or "anonymous"


def looks_like_prompt_injection(text: str) -> bool:
    """Heuristic flag for obvious injection attempts. Non-blocking."""
    if not text:
        return False
    lower = text.lower()
    return any(marker in lower for marker in _INJECTION_MARKERS)
