"""Pydantic models exchanged over the HTTP API.

The ``max_length`` constraints here are a *second* wall on top of the
body-size middleware (``API_MAX_BODY_BYTES``). The middleware rejects
oversized bodies before JSON parsing; pydantic enforces the same cap on
individual fields so a small payload with a giant ``message`` is also
rejected. Defense in depth.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

# Hard ceiling — the engine also checks ``settings.max_message_chars``
# which is configurable per deployment. Whichever is smaller wins.
MAX_MESSAGE_CHARS_HARD = 8000
MAX_SESSION_ID_LEN = 128
MAX_LANGUAGE_LEN = 16


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=MAX_MESSAGE_CHARS_HARD,
        description="The user message",
    )
    session_id: str = Field(
        default="default",
        max_length=MAX_SESSION_ID_LEN,
        description="Stable per-user identifier",
    )
    language: Optional[str] = Field(
        default=None,
        max_length=MAX_LANGUAGE_LEN,
        description="Optional ISO 639-1 hint for the reply language",
    )


class SourceModel(BaseModel):
    source: str
    page: Optional[int] = None
    snippet: str = ""


class ChatReply(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceModel] = Field(default_factory=list)
    products: list[dict[str, Any]] = Field(default_factory=list)


class HealthReply(BaseModel):
    status: str
    client: str
    personality: str
    model: str
    chain_ready: bool
    active_sessions: int
    channels: dict[str, bool]
    security: dict[str, object] = Field(default_factory=dict)


class ClearReply(BaseModel):
    cleared: str
