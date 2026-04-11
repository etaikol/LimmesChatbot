"""
Security & abuse-prevention primitives.

This package centralizes everything that protects the bot from:

- Spam / DoS / cost abuse  →  `rate_limit`, `budget`
- Prompt injection / oversized input  →  `sanitize`
- Header / transport hardening  →  `headers`

Every primitive is designed to fail closed: if anything raises, the
caller treats it as "blocked" rather than "allowed".
"""

from chatbot.security.budget import BudgetGuard, BudgetExceeded
from chatbot.security.headers import SecurityHeadersMiddleware
from chatbot.security.rate_limit import RateLimiter, RateLimitExceeded
from chatbot.security.sanitize import (
    looks_like_prompt_injection,
    sanitize_session_id,
    sanitize_user_input,
)
from chatbot.security.spam import SpamTracker, is_gibberish

__all__ = [
    "BudgetGuard",
    "BudgetExceeded",
    "RateLimiter",
    "RateLimitExceeded",
    "SecurityHeadersMiddleware",
    "SpamTracker",
    "is_gibberish",
    "sanitize_user_input",
    "sanitize_session_id",
    "looks_like_prompt_injection",
]
