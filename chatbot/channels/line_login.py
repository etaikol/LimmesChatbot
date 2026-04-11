"""
LINE Login — OAuth 2.0 integration for user identification.

Optional feature that businesses can enable to identify users by their
LINE profile (display name, picture, email). When enabled, the chatbot
can greet returning users by name and track them across sessions.

Flow:
    1. User clicks a login link or button.
    2. Redirected to LINE Login authorization URL.
    3. LINE redirects back with an authorization code.
    4. We exchange the code for tokens + user profile.
    5. Profile is stored in user memory.

Setup:
    1. Create a LINE Login channel at https://developers.line.biz/console/
    2. Set LINE_LOGIN_CHANNEL_ID and LINE_LOGIN_CHANNEL_SECRET in .env
    3. Add callback URL: https://<host>/webhook/line/callback

LINE Login reference:
    https://developers.line.biz/en/docs/line-login/integrate-line-login/
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from chatbot.logging_setup import logger

AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
PROFILE_URL = "https://api.line.me/v2/profile"
VERIFY_URL = "https://api.line.me/oauth2/v2.1/verify"


class LineLoginProfile:
    """Parsed LINE user profile."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.user_id: str = data.get("userId", data.get("sub", ""))
        self.display_name: str = data.get("displayName", data.get("name", ""))
        self.picture_url: str = data.get("pictureUrl", data.get("picture", ""))
        self.email: str = data.get("email", "")
        self.status_message: str = data.get("statusMessage", "")

    def to_dict(self) -> dict[str, str]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "picture_url": self.picture_url,
            "email": self.email,
            "status_message": self.status_message,
        }


class LineLoginManager:
    """Manages LINE Login OAuth flow."""

    def __init__(
        self,
        channel_id: str,
        channel_secret: str,
        redirect_uri: str,
    ) -> None:
        if not channel_id or not channel_secret:
            raise ValueError(
                "LINE_LOGIN_CHANNEL_ID and LINE_LOGIN_CHANNEL_SECRET are required."
            )
        self._channel_id = channel_id
        self._channel_secret = channel_secret
        self._redirect_uri = redirect_uri
        # CSRF protection: state → True (pending)
        self._pending_states: dict[str, bool] = {}

    @property
    def enabled(self) -> bool:
        return bool(self._channel_id and self._channel_secret)

    def get_auth_url(self, session_id: str = "") -> tuple[str, str]:
        """Generate the LINE Login authorization URL.

        Returns (url, state) where state is a CSRF token.
        """
        state = secrets.token_urlsafe(32)
        self._pending_states[state] = True

        params = {
            "response_type": "code",
            "client_id": self._channel_id,
            "redirect_uri": self._redirect_uri,
            "state": state,
            "scope": "profile openid email",
            "bot_prompt": "aggressive",  # prompt user to add bot as friend
        }
        url = f"{AUTH_URL}?{urlencode(params)}"
        return url, state

    def validate_state(self, state: str) -> bool:
        """Validate and consume a CSRF state token."""
        if state in self._pending_states:
            del self._pending_states[state]
            return True
        return False

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                    "client_id": self._channel_id,
                    "client_secret": self._channel_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code != 200:
                logger.warning("[line-login] Token exchange failed: {}", resp.text)
                return {}
            return resp.json()

    async def get_profile(self, access_token: str) -> Optional[LineLoginProfile]:
        """Fetch user profile using the access token."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code != 200:
                logger.warning("[line-login] Profile fetch failed: {}", resp.text)
                return None
            return LineLoginProfile(resp.json())

    async def handle_callback(self, code: str, state: str) -> Optional[LineLoginProfile]:
        """Complete the OAuth flow: validate state, exchange code, get profile.

        Returns the user profile or None on failure.
        """
        if not self.validate_state(state):
            logger.warning("[line-login] Invalid state token")
            return None

        tokens = await self.exchange_code(code)
        if not tokens:
            return None

        access_token = tokens.get("access_token", "")
        if not access_token:
            logger.warning("[line-login] No access token in response")
            return None

        profile = await self.get_profile(access_token)
        if profile:
            logger.info(
                "[line-login] User authenticated: {} ({})",
                profile.display_name,
                profile.user_id,
            )
        return profile

    @classmethod
    def from_settings(cls, settings: Any, base_url: str = "") -> Optional["LineLoginManager"]:
        """Create from application settings. Returns None if not configured."""
        channel_id = getattr(settings, "line_login_channel_id", "")
        channel_secret = getattr(settings, "line_login_channel_secret", "")
        if not channel_id or not channel_secret:
            return None
        redirect_uri = f"{base_url.rstrip('/')}/auth/line/callback"
        return cls(
            channel_id=channel_id,
            channel_secret=channel_secret,
            redirect_uri=redirect_uri,
        )
