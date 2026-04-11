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

import asyncio
import hmac
import json

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security.api_key import APIKeyHeader
from starlette.responses import StreamingResponse

from chatbot.api.schemas import ChatReply, ChatRequest, ClearReply, FeedbackReply, FeedbackRequest, SourceModel
from chatbot.exceptions import ChatbotError
from chatbot.i18n import SUPPORTED_LANGUAGE_CODES, resolve_language
from chatbot.i18n.detect import detect_language
from chatbot.logging_setup import logger
from chatbot.security.sanitize import sanitize_session_id

router = APIRouter(tags=["chat"])

_api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)


def _require_api_key(
    request: Request,
    key: str | None = Security(_api_key_header),
) -> None:
    """FastAPI dependency: enforce X-Api-Key when CHATBOT_API_KEY is set.

    When the setting is empty (default) the endpoint is open.
    When set, any request without the correct header gets HTTP 401.
    """
    expected = request.app.state.bot.settings.chatbot_api_key
    if expected and not hmac.compare_digest(expected, key or ""):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _client_ip(request: Request) -> str:
    """Best-effort client IP, honoring X-Forwarded-For only from trusted proxies.

    Only trusts the header when the *direct* peer is a private/loopback
    address (i.e. a reverse proxy like nginx running locally or in Docker).
    If the app is exposed directly to the internet, the raw peer IP is used
    and X-Forwarded-For is ignored — preventing spoofing.
    """
    peer = request.client.host if request.client else "unknown"

    # Only trust X-Forwarded-For from local/private peers (reverse proxy)
    _TRUSTED_PREFIXES = ("127.", "10.", "172.16.", "172.17.", "172.18.",
                         "172.19.", "172.20.", "172.21.", "172.22.",
                         "172.23.", "172.24.", "172.25.", "172.26.",
                         "172.27.", "172.28.", "172.29.", "172.30.",
                         "172.31.", "192.168.", "::1", "fd")

    if peer.startswith(_TRUSTED_PREFIXES):
        xff = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if xff:
            return xff

    return peer


@router.post("/chat", response_model=ChatReply, dependencies=[Depends(_require_api_key)])
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

    # Auto-detect language from the actual message text.  Detected language
    # takes priority over the widget dropdown — the dropdown is a fallback
    # for short/ambiguous messages where script detection doesn't fire.
    detected = detect_language(req.message, supported=SUPPORTED_LANGUAGE_CODES)
    if detected:
        language = detected

    try:
        # Run synchronous bot.ask() in a thread so that any time.sleep()
        # inside the retry logic does not block the async event loop.
        resp = await asyncio.to_thread(
            bot.ask,
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
        products=resp.metadata.get("products", []),
        handoff=resp.metadata.get("handoff", False),
    )


@router.delete("/chat/{session_id}", response_model=ClearReply, dependencies=[Depends(_require_api_key)])
def clear_session(session_id: str, request: Request) -> ClearReply:
    bot = request.app.state.bot
    # Don't burn quota on clear; it's a free op. We still rate-limit by IP
    # so a script can't loop and rotate session ids forever.
    ip_limiter = request.app.state.ip_limiter
    if ip_limiter is not None:
        ip_limiter.check(_client_ip(request))

    bot.reset(session_id)
    return ClearReply(cleared=sanitize_session_id(session_id))


# ── Feedback ─────────────────────────────────────────────────────────────────


@router.post("/chat/feedback", response_model=FeedbackReply, dependencies=[Depends(_require_api_key)])
async def submit_feedback(req: FeedbackRequest, request: Request) -> FeedbackReply:
    """Submit thumbs up/down feedback for a bot answer."""
    bot = request.app.state.bot

    # Rate limit by IP
    ip_limiter = request.app.state.ip_limiter
    if ip_limiter is not None:
        ip_limiter.check(_client_ip(request))

    feedback_store = getattr(bot, "feedback", None)
    if feedback_store is None:
        raise HTTPException(503, "Feedback collection is disabled")

    from chatbot.core.feedback import FeedbackEntry

    # Get the question/answer from session history if available
    question = ""
    answer = ""
    try:
        mem = bot.memory.get(req.session_id)
        msgs = mem.messages
        # Find the nth assistant message
        assistant_msgs = [m for m in msgs if m.role == "assistant"]
        if req.message_index < len(assistant_msgs):
            answer = assistant_msgs[req.message_index].content
            # Find the preceding user message
            idx = msgs.index(assistant_msgs[req.message_index])
            for i in range(idx - 1, -1, -1):
                if msgs[i].role == "user":
                    question = msgs[i].content
                    break
    except Exception:
        pass

    entry = FeedbackEntry(
        session_id=req.session_id,
        message_index=req.message_index,
        question=question,
        answer=answer,
        feedback=req.feedback,
        comment=req.comment,
    )
    feedback_store.add(entry)

    # Also track in analytics
    analytics = getattr(bot, "analytics", None)
    if analytics:
        from chatbot.core.analytics import AnalyticsEvent

        analytics.track(AnalyticsEvent(
            event_type="feedback",
            session_id=req.session_id,
            feedback=req.feedback,
        ))

    return FeedbackReply(ok=True)


# ── SSE push stream (handoff replies) ───────────────────────────────────────


@router.get("/chat/events")
async def chat_events(request: Request, session_id: str):
    """Server-Sent Events stream for real-time handoff replies.

    The web widget opens this connection when the session enters handoff
    mode.  Admin replies are pushed instantly instead of waiting for the
    user's next message.
    """
    push = getattr(request.app.state, "push_service", None)
    if push is None:
        raise HTTPException(503, "Push service not available")

    sid = sanitize_session_id(session_id)
    queue = push.subscribe(sid)
    logger.debug("[sse] Client connected: {}", sid)

    async def event_stream():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send keepalive comment to prevent proxy timeouts
                    yield ": keepalive\n\n"
                    continue
                if msg is None:
                    # Sentinel: close stream (e.g. handoff resolved)
                    yield f"event: close\ndata: {{}}\n\n"
                    break
                payload = json.dumps({"text": msg}, ensure_ascii=False)
                yield f"event: handoff_reply\ndata: {payload}\n\n"
        finally:
            push.unsubscribe(sid)
            logger.debug("[sse] Client disconnected: {}", sid)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # nginx: don't buffer SSE
        },
    )
