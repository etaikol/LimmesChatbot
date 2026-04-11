"""
Contact message system — lets visitors leave a message for the business owner.

When the bot detects the user wants to speak with a human or leave a message,
the engine stores the contact request and optionally sends it by email.

Contact messages are persisted to a JSON file under ``.contacts/`` and
exposed via the admin API.
"""

from __future__ import annotations

import json
import smtplib
import threading
import uuid
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from chatbot.logging_setup import logger
from chatbot.settings import PROJECT_ROOT


class ContactMessage(BaseModel):
    """A single contact / leave-a-message entry."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = ""
    channel: str = "web"
    customer_name: str = ""
    customer_contact: str = ""  # email, phone, or LINE id
    message: str = ""
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    read: bool = False
    replied: bool = False


class ContactStore:
    """Thread-safe JSON-backed contact message store."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (PROJECT_ROOT / ".contacts" / "messages.json")
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def add(self, msg: ContactMessage) -> str:
        with self._lock:
            data = self._load()
            data.append(msg.model_dump())
            self._save(data)
        logger.info("[contact] New message from {} ({})", msg.session_id, msg.channel)
        return msg.id

    def list_all(self, limit: int = 100) -> list[dict]:
        with self._lock:
            data = self._load()
        return list(reversed(data[-limit:]))

    def count_unread(self) -> int:
        with self._lock:
            data = self._load()
        return sum(1 for m in data if not m.get("read"))

    def mark_read(self, message_id: str) -> bool:
        with self._lock:
            data = self._load()
            for m in data:
                if m.get("id") == message_id:
                    m["read"] = True
                    self._save(data)
                    return True
        return False

    def mark_replied(self, message_id: str) -> bool:
        with self._lock:
            data = self._load()
            for m in data:
                if m.get("id") == message_id:
                    m["replied"] = True
                    m["read"] = True
                    self._save(data)
                    return True
        return False

    def delete(self, message_id: str) -> bool:
        with self._lock:
            data = self._load()
            new = [m for m in data if m.get("id") != message_id]
            if len(new) == len(data):
                return False
            self._save(new)
        return True

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []

    def _save(self, data: list[dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        tmp.replace(self._path)


def send_contact_email(
    msg: ContactMessage,
    *,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_pass: str,
    to_email: str,
    from_email: str = "",
) -> bool:
    """Send a contact message notification via SMTP.

    Returns True on success, False on failure (never raises).
    """
    sender = from_email or smtp_user
    subject = f"New message from {msg.customer_name or msg.session_id} ({msg.channel})"
    body = (
        f"Channel: {msg.channel}\n"
        f"Session: {msg.session_id}\n"
        f"Name: {msg.customer_name}\n"
        f"Contact: {msg.customer_contact}\n"
        f"Time: {msg.created_at}\n"
        f"\n--- Message ---\n{msg.message}\n"
    )

    mime = MIMEText(body, "plain", "utf-8")
    mime["Subject"] = subject
    mime["From"] = sender
    mime["To"] = to_email

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            if smtp_port != 25:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(sender, [to_email], mime.as_string())
        logger.info("[contact] Email sent to {} for message {}", to_email, msg.id)
        return True
    except Exception as e:
        logger.warning("[contact] Email failed: {}", e)
        return False
