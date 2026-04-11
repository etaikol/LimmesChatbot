"""
Long-term user memory — remembers returning users across sessions.

Stores per-user facts, preferences, and conversation summaries that
persist beyond the session window. E.g. "User asked about Roman blinds
last week" or "Prefers communication in Thai".

Facts are free-text entries tagged with timestamps. The system injects
relevant user memory into the system prompt so the LLM can reference it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT

MAX_FACTS_PER_USER = 50
MAX_FACT_LENGTH = 500


class UserFact(BaseModel):
    """A single remembered fact about a user."""

    fact: str
    category: str = "general"  # general, preference, inquiry, purchase
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str = "auto"  # auto (LLM-extracted) or admin (manually added)


class UserProfile(BaseModel):
    """Long-term memory profile for a single user."""

    user_id: str
    display_name: str = ""
    language: str = ""
    channel: str = ""
    first_seen: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_seen: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_sessions: int = 0
    facts: list[UserFact] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)  # for user segmentation

    def add_fact(self, fact: str, category: str = "general", source: str = "auto") -> None:
        if len(fact) > MAX_FACT_LENGTH:
            fact = fact[:MAX_FACT_LENGTH]
        # Avoid exact duplicates
        for existing in self.facts:
            if existing.fact.lower().strip() == fact.lower().strip():
                return
        self.facts.append(UserFact(fact=fact, category=category, source=source))
        # Trim old facts
        if len(self.facts) > MAX_FACTS_PER_USER:
            self.facts = self.facts[-MAX_FACTS_PER_USER:]

    def for_system_prompt(self) -> str:
        """Format user memory for injection into the system prompt."""
        if not self.facts:
            return ""
        lines = ["RETURNING USER MEMORY (use naturally, don't list these):"]
        if self.display_name:
            lines.append(f"- Name: {self.display_name}")
        if self.language:
            lines.append(f"- Preferred language: {self.language}")
        for f in self.facts[-10:]:  # recent 10 facts
            lines.append(f"- [{f.category}] {f.fact}")
        return "\n".join(lines)

    def touch(self) -> None:
        """Update last_seen timestamp."""
        self.last_seen = datetime.now(timezone.utc).isoformat()


class UserMemoryStore:
    """Persistent per-user long-term memory store."""

    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self._profiles: dict[str, UserProfile] = {}
        self._storage_dir = storage_dir or (PROJECT_ROOT / ".user_memory")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._storage_dir / "profiles.json"
        self._load()

    def _load(self) -> None:
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for uid, profile_data in data.items():
                    self._profiles[uid] = UserProfile(**profile_data)
            except Exception as e:
                logger.warning("Could not load user memory: {}", e)

    def _save(self) -> None:
        try:
            tmp = self._file.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(
                    {uid: p.model_dump() for uid, p in self._profiles.items()},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._file)
        except Exception as e:
            logger.warning("Could not save user memory: {}", e)

    def _user_id_from_session(self, session_id: str) -> str:
        """Extract a stable user ID from a session ID.

        LINE: line:U1234 → U1234
        Telegram: telegram:12345 → tg_12345
        WhatsApp: whatsapp:+1234 → wa_+1234
        Web: web_abc123 → web_abc123
        """
        if session_id.startswith("line:"):
            return session_id[5:]
        if session_id.startswith("telegram:"):
            return f"tg_{session_id[9:]}"
        if session_id.startswith("whatsapp:"):
            return f"wa_{session_id[9:]}"
        return session_id

    def get_or_create(
        self,
        session_id: str,
        channel: str = "",
        language: str = "",
    ) -> UserProfile:
        """Get or create a user profile from a session ID."""
        uid = self._user_id_from_session(session_id)
        if uid in self._profiles:
            profile = self._profiles[uid]
            profile.touch()
            if language and not profile.language:
                profile.language = language
            if channel and not profile.channel:
                profile.channel = channel
            return profile

        profile = UserProfile(
            user_id=uid,
            channel=channel,
            language=language,
        )
        self._profiles[uid] = profile
        self._save()
        return profile

    def record_interaction(
        self,
        session_id: str,
        question: str = "",
        answer: str = "",
        language: str = "",
        channel: str = "",
    ) -> UserProfile:
        """Record that a user interacted. Extracts facts from the Q&A."""
        profile = self.get_or_create(session_id, channel=channel, language=language)
        profile.touch()

        # Auto-extract facts from questions (simple keyword extraction)
        if question:
            self._auto_extract_facts(profile, question)

        self._save()
        return profile

    def _auto_extract_facts(self, profile: UserProfile, question: str) -> None:
        """Extract memorable facts from user questions."""
        q_lower = question.lower()

        # Detect product inquiries
        inquiry_keywords = [
            "interested in", "looking for", "want to buy", "tell me about",
            "price of", "how much", "do you have", "available",
            "מעוניין ב", "מחפש", "כמה עולה", "יש לכם",
            "สนใจ", "ราคา", "มีไหม", "อยากได้",
        ]
        for kw in inquiry_keywords:
            if kw in q_lower:
                # Store the inquiry topic
                topic = question[:200]
                profile.add_fact(
                    f"Asked about: {topic}",
                    category="inquiry",
                )
                break

        # Detect preferences
        pref_keywords = [
            "i prefer", "i like", "my favorite", "i usually",
            "אני מעדיף", "אני אוהב",
            "ชอบ", "ต้องการ",
        ]
        for kw in pref_keywords:
            if kw in q_lower:
                profile.add_fact(
                    f"Preference: {question[:200]}",
                    category="preference",
                )
                break

    def add_fact(
        self,
        session_id: str,
        fact: str,
        category: str = "general",
        source: str = "admin",
    ) -> None:
        """Manually add a fact about a user."""
        profile = self.get_or_create(session_id)
        profile.add_fact(fact, category=category, source=source)
        self._save()

    def get_prompt_context(self, session_id: str) -> str:
        """Get user memory formatted for system prompt injection."""
        uid = self._user_id_from_session(session_id)
        profile = self._profiles.get(uid)
        if not profile:
            return ""
        return profile.for_system_prompt()

    def list_users(self, limit: int = 100) -> list[dict[str, Any]]:
        """List all known users with summary info."""
        users = []
        for uid, profile in sorted(
            self._profiles.items(),
            key=lambda x: x[1].last_seen,
            reverse=True,
        )[:limit]:
            users.append({
                "user_id": uid,
                "display_name": profile.display_name,
                "channel": profile.channel,
                "language": profile.language,
                "first_seen": profile.first_seen,
                "last_seen": profile.last_seen,
                "total_sessions": profile.total_sessions,
                "facts_count": len(profile.facts),
                "tags": profile.tags,
            })
        return users

    def get_user(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get full profile for a user."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        return profile.model_dump()

    def update_user_tags(self, user_id: str, tags: list[str]) -> bool:
        """Set tags for user segmentation."""
        profile = self._profiles.get(user_id)
        if not profile:
            return False
        profile.tags = tags
        self._save()
        return True

    def delete_user(self, user_id: str) -> bool:
        if user_id in self._profiles:
            del self._profiles[user_id]
            self._save()
            return True
        return False

    def count(self) -> int:
        return len(self._profiles)

    def get_segment(self, tag: str) -> list[str]:
        """Get all user IDs with a specific tag (for rich menu targeting)."""
        return [
            uid for uid, p in self._profiles.items()
            if tag in p.tags
        ]
