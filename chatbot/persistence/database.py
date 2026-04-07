"""
Optional PostgreSQL backend for sessions.

This module is **only imported when** `MEMORY_BACKEND=postgres` in `.env`,
so the rest of the project does not require SQLAlchemy/asyncpg.

Schema:
    CREATE TABLE chatbot_sessions (
        session_id TEXT PRIMARY KEY,
        messages   JSONB NOT NULL,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

Install extras to enable:
    pip install "sqlalchemy[asyncio]>=2.0" "psycopg[binary]>=3.2"
"""

from __future__ import annotations

import json
from typing import Optional

from chatbot.core.memory import ConversationMemory
from chatbot.exceptions import ConfigError
from chatbot.logging_setup import logger
from chatbot.settings import get_settings


class PostgresSessionBackend:
    """Synchronous psycopg backend. Suitable for low/mid-volume deployments."""

    def __init__(self) -> None:
        try:
            import psycopg  # type: ignore
        except ImportError as e:
            raise ConfigError(
                "PostgreSQL backend requires psycopg. Install: "
                'pip install "psycopg[binary]>=3.2"'
            ) from e

        s = get_settings()
        if not s.postgres_dsn:
            raise ConfigError("POSTGRES_DSN is not set in your .env")

        self._psycopg = psycopg
        self._dsn = s.postgres_dsn
        self._ensure_schema()

    # ── Schema ──────────────────────────────────────────────────────────────

    def _ensure_schema(self) -> None:
        with self._psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS chatbot_sessions (
                    session_id TEXT PRIMARY KEY,
                    messages   JSONB NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            conn.commit()
            logger.debug("PostgreSQL chatbot_sessions table ensured")

    # ── CRUD ────────────────────────────────────────────────────────────────

    def load(self, session_id: str, max_turns: int = 10) -> ConversationMemory:
        with self._psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT messages FROM chatbot_sessions WHERE session_id = %s",
                (session_id,),
            )
            row: Optional[tuple] = cur.fetchone()

        if not row:
            return ConversationMemory(max_turns=max_turns)

        try:
            data = row[0] if isinstance(row[0], dict) else json.loads(row[0])
        except (TypeError, ValueError):
            return ConversationMemory(max_turns=max_turns)

        return ConversationMemory(messages=data.get("messages", []), max_turns=max_turns)

    def save(self, session_id: str, mem: ConversationMemory) -> None:
        payload = json.dumps({"messages": [m.model_dump() for m in mem.messages]})
        with self._psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chatbot_sessions (session_id, messages, updated_at)
                VALUES (%s, %s::jsonb, now())
                ON CONFLICT (session_id) DO UPDATE
                  SET messages = EXCLUDED.messages,
                      updated_at = now();
                """,
                (session_id, payload),
            )
            conn.commit()

    def clear(self, session_id: str) -> None:
        with self._psycopg.connect(self._dsn) as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chatbot_sessions WHERE session_id = %s", (session_id,)
            )
            conn.commit()
