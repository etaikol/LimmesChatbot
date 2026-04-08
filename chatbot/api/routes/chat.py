"""REST chat endpoint used by the web widget and any custom client.

The route enforces two rate limits before delegating to the engine:

- **Per IP** — protects the public surface from random scanners and
  brute-force scripts.
- **Per session_id** — protects from a single chat tab spamming once a
  user has connected.

Both limits are token buckets (see :mod:`chatbot.security.rate_limit`),
configured from environment variables and built once during startup
(see ``chatbot/api/app.py::lifespan``).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from chatbot.api.schemas import ChatReply, ChatRequest, ClearReply, SourceModel
from chatbot.exceptions import ChatbotError
from chatbot.i18n import resolve_language
from chatbot.logging_setup import logger
from chatbot.security.sanitize import sanitize_session_id

router = APIRouter(tags=["chat"])


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honoring X-Forwarded-For from a *trusted* proxy.

    The deployment guide tells you to terminate TLS in nginx/Caddy/Traefik
    and forward to the app. Those proxies set ``X-Forwarded-For``; we
    take the leftmost entry. If you expose the app *directly* to the
    internet, this header can be spoofed — set ``API_STRICT_CORS=true``
    and put a proxy in front.
    """
    xff = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if xff:
        return xff
    return request.client.host if request.client else "unknown"


@router.post("/chat", response_model=ChatReply)
async def chat_endpoint(req: ChatRequest, request: Request) -> ChatReply:
    bot = request.app.state.bot

    # ── Rate limiting (cheapest first: IP, then session) ──────────────
    ip_limiter = request.app.state.ip_limiter
    sess_limiter = request.app.state.session_limiter
    if ip_limiter is not None:
        ip_limiter.check(_client_ip(request))
    if sess_limiter is not None:
        sess_limiter.check(sanitize_session_id(req.session_id))

    language = resolve_language(req.language) if req.language else None

    try:
        resp = bot.ask(
            req.message,
            session_id=req.session_id,
            language=language,
        )
    except ChatbotError:
        # Let the global handler in app.py turn this into a JSON 4xx/5xx.
        raise
    except Exception as e:  # pragma: no cover
        logger.exception("[chat] unexpected: {}", e)
        raise HTTPException(status_code=500, detail="Internal error.")

    return ChatReply(
        answer=resp.answer,
        session_id=resp.session_id,
        sources=[SourceModel(**s.model_dump()) for s in resp.sources],
    )


@router.delete("/chat/{session_id}", response_model=ClearReply)
def clear_session(session_id: str, request: Request) -> ClearReply:
    bot = request.app.state.bot
    # Don't burn quota on clear; it's a free op. We still rate-limit by IP
    # so a script can't loop and rotate session ids forever.
    ip_limiter = request.app.state.ip_limiter
    if ip_limiter is not None:
        ip_limiter.check(_client_ip(request))

    bot.reset(session_id)
    return ClearReply(cleared=sanitize_session_id(session_id))
