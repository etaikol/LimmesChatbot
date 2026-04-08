"""
Token-bucket rate limiter.

Designed to be:

- **Process-local but thread-safe.** A single API process can use it
  directly. For horizontally scaled deployments, swap the backing dict
  for Redis (see `chatbot/security/__init__.py` docstring for the spec).
- **Multi-key.** One limiter typically tracks per-IP, another per-session,
  another per-channel. Each `RateLimiter` instance is independent.
- **Memory-bounded.** Idle buckets are evicted after `idle_ttl` seconds
  to avoid unbounded growth from random visitors.
- **Fail-closed friendly.** A `RateLimitExceeded` exception is raised
  with a human-readable `retry_after` so callers can return HTTP 429
  with a `Retry-After` header.

Algorithm: classic token bucket. Each key gets a bucket with `capacity`
tokens that refills at `refill_rate` tokens per second. A request costs
`cost` tokens (default 1). If the bucket has fewer than `cost` tokens
the request is denied and we report when enough tokens will accumulate.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional


class RateLimitExceeded(Exception):
    """Raised when a key has exhausted its rate-limit budget."""

    def __init__(self, key: str, retry_after: float, scope: str = "request") -> None:
        self.key = key
        self.retry_after = max(retry_after, 0.0)
        self.scope = scope
        super().__init__(
            f"Rate limit exceeded for {scope} key={key!r} "
            f"(retry in {self.retry_after:.1f}s)"
        )


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class RateLimiter:
    """Per-key token bucket limiter, thread-safe.

    Parameters
    ----------
    name:
        A short label used in logs and exceptions (e.g. ``"per_ip"``).
    capacity:
        Maximum burst size — the most requests a single key may make
        instantly after a long idle period.
    refill_rate:
        Tokens added per second. ``capacity / refill_rate`` is roughly
        the time it takes to recover from a full burst.
    idle_ttl:
        Buckets idle longer than this (seconds) are evicted on the next
        access. Keeps memory usage proportional to *active* keys only.
    """

    def __init__(
        self,
        name: str,
        capacity: float,
        refill_rate: float,
        idle_ttl: float = 600.0,
    ) -> None:
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError("capacity and refill_rate must be > 0")
        self.name = name
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self.idle_ttl = float(idle_ttl)
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()
        self._last_gc = time.monotonic()

    # ── Public API ──────────────────────────────────────────────────────────

    def check(self, key: str, cost: float = 1.0) -> None:
        """Raise :class:`RateLimitExceeded` if ``key`` cannot afford ``cost``.

        On success, ``cost`` tokens are debited from the bucket.
        """
        if not key:
            return  # never rate-limit anonymous traffic to zero — fail open
        retry_after = self._consume(key, cost)
        if retry_after is not None:
            raise RateLimitExceeded(key=key, retry_after=retry_after, scope=self.name)

    def remaining(self, key: str) -> float:
        """Return current tokens for ``key`` (for debugging / headers)."""
        with self._lock:
            now = time.monotonic()
            b = self._buckets.get(key)
            if b is None:
                return self.capacity
            return min(self.capacity, b.tokens + (now - b.updated_at) * self.refill_rate)

    def reset(self, key: Optional[str] = None) -> None:
        """Drop a single key (or all keys when ``key`` is ``None``)."""
        with self._lock:
            if key is None:
                self._buckets.clear()
            else:
                self._buckets.pop(key, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._buckets)

    # ── Internals ───────────────────────────────────────────────────────────

    def _consume(self, key: str, cost: float) -> Optional[float]:
        with self._lock:
            now = time.monotonic()
            self._maybe_gc(now)

            b = self._buckets.get(key)
            if b is None:
                b = _Bucket(tokens=self.capacity, updated_at=now)
                self._buckets[key] = b

            # Refill since last hit
            elapsed = now - b.updated_at
            b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_rate)
            b.updated_at = now

            if b.tokens >= cost:
                b.tokens -= cost
                return None  # allowed

            deficit = cost - b.tokens
            return deficit / self.refill_rate

    def _maybe_gc(self, now: float) -> None:
        # Run a sweep at most every 60s to amortize cost
        if now - self._last_gc < 60.0:
            return
        self._last_gc = now
        cutoff = now - self.idle_ttl
        stale = [k for k, b in self._buckets.items() if b.updated_at < cutoff]
        for k in stale:
            del self._buckets[k]
