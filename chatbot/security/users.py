"""
User store for the admin dashboard.

Manages admin/viewer accounts persisted as a JSON file.  Passwords are
hashed with PBKDF2-HMAC-SHA256; session tokens are random 32-byte hex
strings with a configurable TTL.

Why a flat JSON file?
---------------------
The admin dashboard is a low-traffic, single-process concern.  A simple
JSON file avoids a database dependency while keeping the code auditable
and easy to back up.  For multi-instance deployments, replace this class
with one backed by Redis or PostgreSQL using the same interface.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Optional

from chatbot.logging_setup import logger

# Session tokens expire after 8 hours by default.
_TOKEN_TTL_SECONDS: int = 8 * 3600

_DEFAULT_ADMIN_USERNAME = "admin"


def _hash_password(password: str, salt: str) -> str:
    """Return a hex PBKDF2-HMAC-SHA256 digest."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=260_000,
    ).hex()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


class UserStore:
    """Persistent user + session-token store for the admin dashboard.

    Parameters
    ----------
    path:
        JSON file that holds user records and active tokens.
        Created (with parent directories) on first write.
    token_ttl:
        How many seconds a session token remains valid.
    """

    def __init__(
        self,
        path: Path,
        *,
        token_ttl: int = _TOKEN_TTL_SECONDS,
    ) -> None:
        self.path = Path(path)
        self.token_ttl = token_ttl
        self._lock = threading.Lock()
        self._data: dict = self._load()

    # ── Public API ──────────────────────────────────────────────────────────

    def seed_default_admin(self, api_key: str) -> None:
        """Ensure at least one admin account exists.

        If the store has no users, create an ``admin`` account whose
        initial password is the supplied *api_key*.  The caller (usually
        the lifespan hook) should log a reminder to change it.
        """
        with self._lock:
            if not self._data.get("users"):
                salt = secrets.token_hex(16)
                self._data.setdefault("users", {})[_DEFAULT_ADMIN_USERNAME] = {
                    "role": "admin",
                    "salt": salt,
                    "hash": _hash_password(api_key, salt),
                    "created_by": "system",
                    "created_at": time.time(),
                }
                self._save_locked()
                logger.info(
                    "UserStore: seeded default admin account '{}' "
                    "(change this password after first login).",
                    _DEFAULT_ADMIN_USERNAME,
                )

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Verify credentials and return a new session token dict, or ``None``."""
        with self._lock:
            record = self._data.get("users", {}).get(username)
            if not record:
                return None
            if not _verify_password(password, record["salt"], record["hash"]):
                return None
            token = secrets.token_hex(32)
            self._data.setdefault("tokens", {})[token] = {
                "username": username,
                "role": record["role"],
                "expires_at": time.time() + self.token_ttl,
            }
            self._save_locked()
            return {"username": username, "role": record["role"], "token": token}

    def validate_token(self, token: str) -> Optional[dict]:
        """Return ``{"username": ..., "role": ...}`` if the token is valid, else ``None``."""
        if not token:
            return None
        with self._lock:
            record = self._data.get("tokens", {}).get(token)
            if not record:
                return None
            if time.time() > record["expires_at"]:
                # Lazily expire
                del self._data["tokens"][token]
                self._save_locked()
                return None
            return {"username": record["username"], "role": record["role"]}

    def revoke_token(self, token: str) -> None:
        """Invalidate a session token (logout)."""
        if not token:
            return
        with self._lock:
            if token in self._data.get("tokens", {}):
                del self._data["tokens"][token]
                self._save_locked()

    def list_users(self) -> list[dict]:
        """Return all users (without password material)."""
        with self._lock:
            return [
                {
                    "username": uname,
                    "role": rec["role"],
                    "created_by": rec.get("created_by", ""),
                    "created_at": rec.get("created_at"),
                }
                for uname, rec in self._data.get("users", {}).items()
            ]

    def create_user(
        self,
        username: str,
        password: str,
        role: str,
        *,
        created_by: str = "admin",
    ) -> bool:
        """Create a new user.

        Returns ``True`` on success, ``False`` if the username already exists
        or the role is invalid.
        """
        if role not in ("admin", "viewer"):
            return False
        with self._lock:
            users = self._data.setdefault("users", {})
            if username in users:
                return False
            salt = secrets.token_hex(16)
            users[username] = {
                "role": role,
                "salt": salt,
                "hash": _hash_password(password, salt),
                "created_by": created_by,
                "created_at": time.time(),
            }
            self._save_locked()
            return True

    def delete_user(self, username: str) -> bool:
        """Delete a user and revoke all their tokens.

        Returns ``True`` if the user existed, ``False`` otherwise.
        """
        with self._lock:
            users = self._data.get("users", {})
            if username not in users:
                return False
            del users[username]
            # Revoke all tokens belonging to the deleted user.
            tokens = self._data.get("tokens", {})
            stale = [t for t, r in tokens.items() if r.get("username") == username]
            for t in stale:
                del tokens[t]
            self._save_locked()
            return True

    # ── Internals ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception as exc:  # noqa: BLE001
            logger.warning("UserStore: could not read {}: {}", self.path, exc)
        return {"users": {}, "tokens": {}}

    def _save_locked(self) -> None:
        """Persist ``_data`` to disk. **Must be called while holding ``_lock``.**"""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Write atomically via a temp file.
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError as exc:
            logger.warning("UserStore: could not save {}: {}", self.path, exc)
