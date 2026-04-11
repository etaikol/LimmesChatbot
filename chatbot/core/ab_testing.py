"""
A/B testing for chatbot personalities.

Routes a percentage of users to different system prompts (personality
variants) and tracks which converts better via analytics.

Usage:
    ab = ABTestManager.from_config(settings)
    variant = ab.assign(session_id)
    # variant.personality_name → use this personality for the session
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT


class ABVariant(BaseModel):
    """A single A/B test variant."""

    name: str  # e.g. "control", "variant_b"
    personality: str  # personality config name to use
    weight: int = 50  # % weight (all weights normalized at runtime)
    description: str = ""


class ABTest(BaseModel):
    """An A/B test configuration."""

    enabled: bool = False
    name: str = "default_ab_test"
    variants: list[ABVariant] = Field(default_factory=list)


class ABTestManager:
    """Deterministic A/B test assignment based on session ID hash."""

    def __init__(self, test: ABTest, storage_dir: Optional[Path] = None) -> None:
        self.test = test
        self._assignments: dict[str, str] = {}  # session_id → variant name
        self._storage_dir = storage_dir or (PROJECT_ROOT / ".abtest")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._storage_dir / "assignments.json"
        self._load()

    def _load(self) -> None:
        if self._file.exists():
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    self._assignments = json.load(f)
            except Exception as e:
                logger.warning("Could not load A/B assignments: {}", e)

    def _save(self) -> None:
        try:
            tmp = self._file.with_suffix(".json.tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._assignments, f, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._file)
        except Exception as e:
            logger.warning("Could not save A/B assignments: {}", e)

    @property
    def enabled(self) -> bool:
        return self.test.enabled and len(self.test.variants) >= 2

    def assign(self, session_id: str) -> ABVariant | None:
        """Assign a session to a variant. Returns None if A/B testing is off."""
        if not self.enabled:
            return None

        # Sticky assignment
        if session_id in self._assignments:
            name = self._assignments[session_id]
            for v in self.test.variants:
                if v.name == name:
                    return v
            # Variant was removed — re-assign
            del self._assignments[session_id]

        # Deterministic hash-based assignment
        variant = self._hash_assign(session_id)
        self._assignments[session_id] = variant.name
        self._save()
        logger.debug(
            "[ab] Assigned session {} to variant '{}'",
            session_id,
            variant.name,
        )
        return variant

    def _hash_assign(self, session_id: str) -> ABVariant:
        """Use consistent hashing to assign a session to a variant."""
        h = hashlib.md5(session_id.encode(), usedforsecurity=False).hexdigest()
        bucket = int(h[:8], 16) % 100  # 0-99

        total_weight = sum(v.weight for v in self.test.variants)
        if total_weight == 0:
            return self.test.variants[0]

        cumulative = 0
        for v in self.test.variants:
            cumulative += (v.weight / total_weight) * 100
            if bucket < cumulative:
                return v
        return self.test.variants[-1]

    def get_variant(self, session_id: str) -> str:
        """Return the variant name for a session (empty if not assigned)."""
        return self._assignments.get(session_id, "")

    def get_config(self) -> dict[str, Any]:
        """Return current A/B test configuration."""
        return self.test.model_dump()

    def update_config(self, data: dict[str, Any]) -> None:
        """Update A/B test configuration."""
        self.test = ABTest(**data)
        logger.info("[ab] Updated A/B test config: {}", self.test.name)

    def stats(self) -> dict[str, Any]:
        """Return assignment distribution."""
        counts: dict[str, int] = {}
        for name in self._assignments.values():
            counts[name] = counts.get(name, 0) + 1
        return {
            "enabled": self.enabled,
            "test_name": self.test.name,
            "total_assigned": len(self._assignments),
            "distribution": counts,
            "variants": [v.model_dump() for v in self.test.variants],
        }

    def clear_assignments(self) -> int:
        n = len(self._assignments)
        self._assignments.clear()
        self._save()
        return n

    @classmethod
    def from_config(cls, client_id: str) -> ABTestManager:
        """Load A/B test config from config/clients/<id>.yaml ab_test section."""
        config_path = PROJECT_ROOT / "config" / "clients" / f"{client_id}.yaml"
        test = ABTest()
        if config_path.exists():
            try:
                import yaml

                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                ab_data = data.get("ab_test")
                if ab_data and isinstance(ab_data, dict):
                    test = ABTest(**ab_data)
            except Exception as e:
                logger.warning("Could not load A/B test config: {}", e)
        return cls(test)
