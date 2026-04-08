"""
Security headers + body-size middleware for FastAPI.

Two responsibilities, packaged together so a single ``add_middleware``
call wires both:

1. **Body size limit.** Reject any request whose ``Content-Length``
   header exceeds ``max_body_bytes``. This is a *cheap* first line of
   defense against gigantic uploads — well before pydantic, JSON
   parsing, or the LLM ever see the bytes.
2. **Standard hardening headers.** Adds ``X-Content-Type-Options``,
   ``Referrer-Policy``, ``Permissions-Policy``, ``X-Frame-Options``
   and (optionally) ``Strict-Transport-Security`` on every response.

These are deliberately conservative defaults — override one by setting
``API_HSTS_ENABLED=true`` once you have HTTPS terminating in front of
the app, and add a ``Content-Security-Policy`` if you serve a real UI.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers and rejects oversized bodies."""

    def __init__(
        self,
        app,
        *,
        max_body_bytes: int = 64 * 1024,
        hsts_enabled: bool = False,
        hsts_max_age: int = 31536000,
    ) -> None:
        super().__init__(app)
        self.max_body_bytes = int(max_body_bytes)
        self.hsts_enabled = bool(hsts_enabled)
        self.hsts_max_age = int(hsts_max_age)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # ── 1. Body-size guard (Content-Length only; streaming bodies
        #       are length-checked again inside the route via Pydantic
        #       max_length on the request models). ─────────────────────
        if self.max_body_bytes > 0:
            length_hdr = request.headers.get("content-length")
            if length_hdr and length_hdr.isdigit():
                if int(length_hdr) > self.max_body_bytes:
                    return JSONResponse(
                        {
                            "detail": (
                                f"Request body too large "
                                f"(max {self.max_body_bytes} bytes)."
                            )
                        },
                        status_code=413,
                    )

        response = await call_next(request)

        # ── 2. Hardening headers ───────────────────────────────────────
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()",
        )
        # X-XSS-Protection is dead in modern browsers; we omit it on
        # purpose so old scanners do not complain when it's missing.

        if self.hsts_enabled:
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={self.hsts_max_age}; includeSubDomains",
            )

        return response
