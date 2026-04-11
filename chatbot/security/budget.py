"""
Daily token / spend budget guard.

Why this exists
---------------
Even with rate limits, a single determined user (or a buggy script) can
walk right up to your wallet. The budget guard puts a hard ceiling on
how many tokens *and* how many dollars can be spent per UTC day for the
whole process.

It is intentionally **per-process and durable**: counters live in a JSON
file under ``.budget/`` so a restart does not reset the limit on the
same day. For multi-instance deployments you should externalize this to
Redis or PostgreSQL — see :class:`BudgetGuard` for the protocol.

How it is wired
---------------
- Before every LLM call (in :class:`chatbot.core.engine.Chatbot.ask`)
  the engine calls ``budget.check_can_spend(estimated_tokens)``.
- After the call returns, ``budget.record(input_tokens, output_tokens)``
  debits the actual usage and persists.

The estimate is rough on purpose — better to refuse a *probable* overrun
than to overshoot and discover it on next month's invoice.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from chatbot.logging_setup import logger


class BudgetExceeded(Exception):
    """Raised when the daily token or dollar budget would be exceeded."""

    def __init__(self, reason: str, *, retry_after_hours: float = 24.0) -> None:
        self.reason = reason
        self.retry_after_hours = retry_after_hours
        super().__init__(reason)


# Approximate prices in USD per 1K tokens. Used only when no explicit
# price is set. Update these once a year or set them via .env.
# These are intentionally CONSERVATIVE (rounded up) so the budget is hit
# *before* the bill is.
DEFAULT_PRICES_USD_PER_1K: dict[str, tuple[float, float]] = {
    # model_name: (input_per_1k, output_per_1k)
    "gpt-4o-mini":  (0.00020, 0.00080),
    "gpt-4o":       (0.00500, 0.01500),
    "gpt-4-turbo":  (0.01000, 0.03000),
    "gpt-3.5-turbo":(0.00050, 0.00150),
}


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _trim_history_dict(history: dict, keep: int = 30) -> None:
    """Trim *history* in-place, retaining only the most recent *keep* days."""
    if len(history) > keep:
        for old_day in sorted(history.keys())[:-keep]:
            del history[old_day]


def estimate_tokens(text: str) -> int:
    """Return a *conservative* token-count estimate.

    Uses tiktoken when available, otherwise falls back to a heuristic
    that intentionally over-counts (1 token per 3 characters) so the
    budget guard rejects rather than overshoots.
    """
    if not text:
        return 0
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, len(text) // 3)


class BudgetGuard:
    """Process-wide daily spend ceiling.

    Parameters
    ----------
    state_file:
        JSON file used to persist counters across restarts. Created
        on first write.
    daily_token_cap:
        Max input+output tokens per UTC day. ``0`` means unlimited.
    daily_usd_cap:
        Max dollars per UTC day. ``0`` means unlimited.
    model:
        Model name used to look up the default price table.
    price_in_usd_per_1k / price_out_usd_per_1k:
        Override prices (set them in ``.env`` if your model isn't in
        :data:`DEFAULT_PRICES_USD_PER_1K` or you negotiated a discount).
    """

    def __init__(
        self,
        state_file: Path,
        *,
        daily_token_cap: int = 0,
        daily_usd_cap: float = 0.0,
        model: str = "gpt-4o-mini",
        price_in_usd_per_1k: Optional[float] = None,
        price_out_usd_per_1k: Optional[float] = None,
    ) -> None:
        self.state_file = state_file
        self.daily_token_cap = max(0, int(daily_token_cap))
        self.daily_usd_cap = max(0.0, float(daily_usd_cap))
        self.model = model

        defaults = DEFAULT_PRICES_USD_PER_1K.get(model, (0.0, 0.0))
        self.price_in = (
            price_in_usd_per_1k if price_in_usd_per_1k is not None else defaults[0]
        )
        self.price_out = (
            price_out_usd_per_1k if price_out_usd_per_1k is not None else defaults[1]
        )

        self._lock = threading.Lock()
        self._state = self._load()

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def enabled(self) -> bool:
        return self.daily_token_cap > 0 or self.daily_usd_cap > 0

    def check_can_spend(self, estimated_input_tokens: int) -> None:
        """Raise :class:`BudgetExceeded` if today's caps would be hit."""
        if not self.enabled:
            return

        with self._lock:
            day = _today_utc()
            tokens, usd = self._counters_for(day)

            # Project both metrics assuming a similarly sized response
            est_total_tokens = estimated_input_tokens * 2
            est_cost = (
                estimated_input_tokens * self.price_in
                + estimated_input_tokens * self.price_out
            ) / 1000.0

            if (
                self.daily_token_cap
                and tokens + est_total_tokens > self.daily_token_cap
            ):
                raise BudgetExceeded(
                    f"Daily token budget reached "
                    f"({tokens}/{self.daily_token_cap})."
                )
            if self.daily_usd_cap and usd + est_cost > self.daily_usd_cap:
                raise BudgetExceeded(
                    f"Daily spend budget reached "
                    f"(${usd:.2f}/${self.daily_usd_cap:.2f})."
                )

    def record(self, input_tokens: int, output_tokens: int) -> None:
        """Persist actual usage from the latest LLM call."""
        if not self.enabled:
            return
        cost = (
            input_tokens * self.price_in + output_tokens * self.price_out
        ) / 1000.0

        with self._lock:
            day = _today_utc()
            self._ensure_day(day)
            entry = self._state["history"][day]
            entry["tokens"] = entry["tokens"] + input_tokens + output_tokens
            entry["usd"] = round(entry["usd"] + cost, 6)
            self._state["current_day"] = day
            self._trim_history()
            self._save()

    def snapshot(self) -> dict:
        with self._lock:
            day = _today_utc()
            self._ensure_day(day)
            self._trim_history()
            entry = self._state["history"][day]
            history = [
                {"day": d, "tokens": v["tokens"], "usd": round(v["usd"], 4)}
                for d, v in sorted(self._state["history"].items(), reverse=True)
            ]
            return {
                "day": day,
                "tokens_used": entry["tokens"],
                "usd_used": round(entry["usd"], 4),
                "daily_token_cap": self.daily_token_cap,
                "daily_usd_cap": self.daily_usd_cap,
                "model": self.model,
                "enabled": self.enabled,
                "history": history,
            }

    # ── Internals ───────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset today's counters to zero and persist."""
        with self._lock:
            day = _today_utc()
            self._state.setdefault("history", {})[day] = {"tokens": 0, "usd": 0.0}
            self._state["current_day"] = day
            self._trim_history()
            self._save()

    def _ensure_day(self, day: str) -> None:
        """Make sure today's entry exists in history dict."""
        history = self._state.setdefault("history", {})
        if day not in history:
            history[day] = {"tokens": 0, "usd": 0.0}
        self._state["current_day"] = day

    def _trim_history(self, keep: int = 30) -> None:
        """Keep only the most recent `keep` days."""
        _trim_history_dict(self._state.get("history", {}), keep)

    def _counters_for(self, day: str) -> tuple[int, float]:
        """Return (tokens, usd) for the given day from the history dict."""
        self._ensure_day(day)
        entry = self._state["history"][day]
        return int(entry.get("tokens", 0)), float(entry.get("usd", 0.0))

    def _load(self) -> dict:
        try:
            if self.state_file.exists():
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    # Migrate old format: {"day":..., "tokens":..., "usd":...}
                    if "history" not in data and "day" in data:
                        old_day = data.get("day", _today_utc())
                        data = {
                            "current_day": old_day,
                            "history": {
                                old_day: {
                                    "tokens": data.get("tokens", 0),
                                    "usd": data.get("usd", 0.0),
                                }
                            },
                        }
                    # Enforce 30-day retention on load
                    history = data.get("history", {})
                    if not isinstance(history, dict):
                        history = {}
                    data["history"] = history
                    if history:
                        _trim_history_dict(history)

                    history = data.get("history", {})
                    if not isinstance(history, dict):
                        history = {}
                    if len(history) > 30:
                        for old_day in sorted(history.keys())[:-30]:
                            del history[old_day]

                    return {
                        "current_day": data.get("current_day", _today_utc()),
                        "history": history,
                    }
        except Exception as e:
            logger.warning("Could not load budget state ({}): {}", self.state_file, e)
        return {"current_day": _today_utc(), "history": {}}

    def _save(self) -> None:
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(
                json.dumps(self._state, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning("Could not save budget state: {}", e)
