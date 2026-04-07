"""Pydantic models exchanged over the HTTP API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The user message")
    session_id: str = Field(default="default", description="Stable per-user identifier")


class SourceModel(BaseModel):
    source: str
    page: Optional[int] = None
    snippet: str = ""


class ChatReply(BaseModel):
    answer: str
    session_id: str
    sources: list[SourceModel] = Field(default_factory=list)


class HealthReply(BaseModel):
    status: str
    client: str
    personality: str
    model: str
    chain_ready: bool
    active_sessions: int
    channels: dict[str, bool]


class ClearReply(BaseModel):
    cleared: str
