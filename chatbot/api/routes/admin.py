"""
Admin dashboard API routes.

Provides read/write endpoints for:
- System overview (health, uptime, versions)
- Session management (list, view, clear)
- Budget monitoring (current usage, history)
- Rate limiter stats
- Spam tracker stats
- Configuration (view + update .env, client YAML, personality YAML)

All endpoints require the admin API key (``ADMIN_API_KEY`` env var).
When unset, the dashboard is disabled entirely.
"""

from __future__ import annotations

import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.responses import HTMLResponse
from fastapi.security.api_key import APIKeyHeader

from chatbot.logging_setup import logger
from chatbot.security.users import UserStore
from chatbot.settings import PROJECT_ROOT

router = APIRouter(prefix="/admin/api", tags=["admin"])

_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)
_auth_token_header = APIKeyHeader(name="X-Auth-Token", auto_error=False)

# Track when the server started (set in lifespan).
_start_time: float = time.time()


def set_start_time() -> None:
    global _start_time
    _start_time = time.time()


def _get_user_store(request: Request) -> UserStore:
    store = getattr(request.app.state, "user_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="User store not initialised.")
    return store


def _resolve_auth(
    request: Request,
    api_key: str | None = Security(_admin_key_header),
    token: str | None = Security(_auth_token_header),
) -> dict[str, str]:
    """Authenticate via session token *or* legacy API key.

    Returns ``{"username": ..., "role": ...}``.
    """
    expected_key = getattr(request.app.state, "admin_api_key", "")
    if not expected_key:
        raise HTTPException(status_code=403, detail="Admin dashboard is disabled.")

    # 1. Try session token first
    if token:
        store = _get_user_store(request)
        info = store.validate_token(token)
        if info:
            return info

    # 2. Fall back to legacy API key → treat as admin
    if api_key and hmac.compare_digest(expected_key, api_key):
        return {"username": "_api_key_", "role": "admin"}

    raise HTTPException(status_code=401, detail="Invalid credentials.")


def _require_auth(
    auth: dict[str, str] = Depends(_resolve_auth),
) -> dict[str, str]:
    """Any authenticated user (admin or viewer)."""
    return auth


def _require_admin_role(
    auth: dict[str, str] = Depends(_resolve_auth),
) -> dict[str, str]:
    """Only admin role."""
    if auth["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return auth


# Keep the old name so existing ``dependencies=[Depends(_require_admin_key)]``
# still compiles. It now resolves via the unified auth path.
def _require_admin_key(
    request: Request,
    key: str | None = Security(_admin_key_header),
    token: str | None = Security(_auth_token_header),
) -> None:
    expected = getattr(request.app.state, "admin_api_key", "")
    if not expected:
        raise HTTPException(status_code=403, detail="Admin dashboard is disabled.")

    # session-token path
    if token:
        store = _get_user_store(request)
        info = store.validate_token(token)
        if info:
            return

    if not key or not hmac.compare_digest(expected, key):
        raise HTTPException(status_code=401, detail="Invalid admin key.")


# ── Auth & User Management ───────────────────────────────────────────────────

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(..., min_length=4, max_length=128)
    role: str = Field(..., pattern=r"^(admin|viewer)$")


@router.post("/auth/login")
def login(body: LoginRequest, request: Request) -> dict:
    expected_key = getattr(request.app.state, "admin_api_key", "")
    if not expected_key:
        raise HTTPException(status_code=403, detail="Admin dashboard is disabled.")
    store = _get_user_store(request)
    result = store.authenticate(body.username, body.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    logger.info("Admin login: {} (role={})", body.username, result["role"])
    return result


@router.post("/auth/logout")
def logout(
    request: Request,
    token: str | None = Security(_auth_token_header),
) -> dict:
    if token:
        store = _get_user_store(request)
        store.revoke_token(token)
    return {"ok": True}


@router.get("/auth/me")
def auth_me(auth: dict = Depends(_require_auth)) -> dict:
    return auth


@router.get("/users", dependencies=[Depends(_require_admin_role)])
def list_users(request: Request) -> dict:
    store = _get_user_store(request)
    return {"users": store.list_users()}


@router.post("/users", dependencies=[Depends(_require_admin_role)])
def create_user(body: CreateUserRequest, request: Request, auth: dict = Depends(_require_admin_role)) -> dict:
    store = _get_user_store(request)
    ok = store.create_user(body.username, body.password, body.role, created_by=auth["username"])
    if not ok:
        raise HTTPException(status_code=409, detail="User already exists or invalid input.")
    return {"ok": True, "username": body.username, "role": body.role}


@router.delete("/users/{username}", dependencies=[Depends(_require_admin_role)])
def delete_user(username: str, request: Request, auth: dict = Depends(_require_admin_role)) -> dict:
    if username == auth["username"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself.")
    store = _get_user_store(request)
    if not store.delete_user(username):
        raise HTTPException(status_code=404, detail="User not found.")
    return {"ok": True}


# ── Overview ─────────────────────────────────────────────────────────────────

@router.get("/overview", dependencies=[Depends(_require_admin_key)])
def overview(request: Request) -> dict:
    bot = request.app.state.bot
    s = bot.settings

    uptime_secs = int(time.time() - _start_time)
    hours = uptime_secs // 3600
    minutes = (uptime_secs % 3600) // 60

    sessions = list(bot.memory.list_sessions())
    budget = bot.budget.snapshot()

    ip_limiter = request.app.state.ip_limiter
    sess_limiter = request.app.state.session_limiter
    spam_tracker = getattr(request.app.state.bot, "spam_tracker", None)

    return {
        "status": "running",
        "uptime": f"{hours}h {minutes}m",
        "uptime_seconds": uptime_secs,
        "client": {
            "id": bot.profile.client.id,
            "name": bot.profile.client.name,
            "personality": bot.profile.personality.name,
            "primary_language": bot.profile.client.language_primary,
            "languages_offered": bot.profile.client.languages_offered,
        },
        "model": s.llm_model,
        "provider": s.llm_provider,
        "sessions": {
            "active": len(sessions),
            "backend": s.memory_backend,
        },
        "budget": budget,
        "rate_limiting": {
            "enabled": s.rate_limit_enabled,
            "ip_per_minute": s.rate_limit_ip_per_minute,
            "ip_burst": s.rate_limit_ip_burst,
            "session_per_minute": s.rate_limit_session_per_minute,
            "session_burst": s.rate_limit_session_burst,
            "active_ip_buckets": len(ip_limiter) if ip_limiter else 0,
            "active_session_buckets": len(sess_limiter) if sess_limiter else 0,
        },
        "spam_detection": {
            "enabled": s.spam_detection_enabled,
            "max_strikes": s.spam_max_strikes,
            "cooldown_seconds": s.spam_cooldown_seconds,
            "active_trackers": len(spam_tracker) if spam_tracker else 0,
        },
        "channels": {
            "web": True,
            "whatsapp": bool(s.twilio_auth_token),
            "telegram": bool(s.telegram_bot_token),
            "line": bool(s.line_channel_access_token),
        },
        "security": {
            "cors_origins": s.cors_origins_list,
            "strict_cors": s.api_strict_cors,
            "hsts_enabled": s.api_hsts_enabled,
            "max_body_bytes": s.api_max_body_bytes,
            "max_message_chars": s.max_message_chars,
            "api_key_set": bool(s.chatbot_api_key),
        },
    }


# ── Sessions ─────────────────────────────────────────────────────────────────

@router.get("/sessions", dependencies=[Depends(_require_admin_key)])
def list_sessions(request: Request) -> dict:
    bot = request.app.state.bot
    sessions = []
    for sid in bot.memory.list_sessions():
        mem = bot.memory.get(sid)
        msg_count = len(mem.messages)
        last_msg = mem.messages[-1].timestamp if mem.messages else None
        sessions.append({
            "session_id": sid,
            "message_count": msg_count,
            "last_activity": last_msg,
        })
    sessions.sort(key=lambda x: x["last_activity"] or "", reverse=True)
    return {"sessions": sessions, "total": len(sessions)}


@router.get("/sessions/{session_id}", dependencies=[Depends(_require_admin_key)])
def get_session(session_id: str, request: Request) -> dict:
    bot = request.app.state.bot
    mem = bot.memory.get(session_id)
    return {
        "session_id": session_id,
        "messages": [m.model_dump() for m in mem.messages],
        "message_count": len(mem.messages),
    }


@router.delete("/sessions/{session_id}", dependencies=[Depends(_require_admin_role)])
def delete_session(session_id: str, request: Request) -> dict:
    bot = request.app.state.bot
    bot.memory.clear(session_id)
    logger.info("[admin] Cleared session: {}", session_id)
    return {"cleared": session_id}


@router.delete("/sessions", dependencies=[Depends(_require_admin_role)])
def clear_all_sessions(request: Request) -> dict:
    bot = request.app.state.bot
    sessions = list(bot.memory.list_sessions())
    for sid in sessions:
        bot.memory.clear(sid)
    logger.info("[admin] Cleared all {} sessions", len(sessions))
    return {"cleared": len(sessions)}


# ── Budget ───────────────────────────────────────────────────────────────────

@router.get("/budget", dependencies=[Depends(_require_admin_key)])
def budget_status(request: Request) -> dict:
    bot = request.app.state.bot
    return bot.budget.snapshot()


@router.post("/budget/reset", dependencies=[Depends(_require_admin_role)])
def reset_budget(request: Request) -> dict:
    bot = request.app.state.bot
    reset = getattr(bot.budget, "reset", None)
    if not callable(reset):
        raise HTTPException(
            status_code=500,
            detail="Budget reset is unavailable: bot.budget.reset() is not implemented",
        )

    reset()
    logger.info("[admin] Budget reset")
    return {"status": "reset", **bot.budget.snapshot()}


# ── Configuration ────────────────────────────────────────────────────────────

@router.get("/config", dependencies=[Depends(_require_admin_key)])
def get_config(request: Request) -> dict:
    """Return current configuration from .env and YAML files."""
    bot = request.app.state.bot
    s = bot.settings

    # Load client YAML
    client_path = PROJECT_ROOT / "config" / "clients" / f"{s.active_client}.yaml"
    client_yaml = _load_yaml(client_path)

    # Load personality YAML
    personality_name = client_yaml.get("personality", "default") if client_yaml else "default"
    personality_path = PROJECT_ROOT / "config" / "personalities" / f"{personality_name}.yaml"
    personality_yaml = _load_yaml(personality_path)

    # Load .env (safely, omitting secrets)
    env_settings = {
        "ACTIVE_CLIENT": s.active_client,
        "LLM_PROVIDER": s.llm_provider,
        "LLM_MODEL": s.llm_model,
        "LLM_TEMPERATURE": s.llm_temperature,
        "EMBEDDING_MODEL": s.embedding_model,
        "CHUNK_SIZE": s.chunk_size,
        "CHUNK_OVERLAP": s.chunk_overlap,
        "RETRIEVAL_K": s.retrieval_k,
        "MAX_HISTORY_TURNS": s.max_history_turns,
        "MAX_MESSAGE_CHARS": s.max_message_chars,
        "RATE_LIMIT_ENABLED": s.rate_limit_enabled,
        "RATE_LIMIT_IP_PER_MINUTE": s.rate_limit_ip_per_minute,
        "RATE_LIMIT_IP_BURST": s.rate_limit_ip_burst,
        "RATE_LIMIT_SESSION_PER_MINUTE": s.rate_limit_session_per_minute,
        "RATE_LIMIT_SESSION_BURST": s.rate_limit_session_burst,
        "SPAM_DETECTION_ENABLED": s.spam_detection_enabled,
        "SPAM_MAX_STRIKES": s.spam_max_strikes,
        "SPAM_COOLDOWN_SECONDS": s.spam_cooldown_seconds,
        "SPAM_MAX_COOLDOWN_SECONDS": s.spam_max_cooldown_seconds,
        "SPAM_MIN_MESSAGE_CHARS": s.spam_min_message_chars,
        "DAILY_TOKEN_CAP": s.daily_token_cap,
        "DAILY_USD_CAP": s.daily_usd_cap,
        "API_CORS_ORIGINS": s.api_cors_origins,
        "API_STRICT_CORS": s.api_strict_cors,
        "API_HSTS_ENABLED": s.api_hsts_enabled,
        "DEBUG": s.debug,
        "LOG_LEVEL": s.log_level,
        "LOG_FILE": str(s.log_file) if s.log_file else "",
        "HANDOFF_ENABLED": s.handoff_enabled,
        "PROACTIVE_DELAY_SECONDS": s.proactive_delay_seconds,
        "PROACTIVE_MESSAGE": s.proactive_message,
        "BLOCK_PROMPT_INJECTION": s.block_prompt_injection,
        # Secret presence indicators (never expose values)
        "_OPENAI_API_KEY_SET": bool(s.openai_api_key),
        "_ANTHROPIC_API_KEY_SET": bool(s.anthropic_api_key),
        "_CHATBOT_API_KEY_SET": bool(s.chatbot_api_key),
        "_TWILIO_AUTH_TOKEN_SET": bool(s.twilio_auth_token),
        "_TELEGRAM_BOT_TOKEN_SET": bool(s.telegram_bot_token),
        "_LINE_CHANNEL_ACCESS_TOKEN_SET": bool(s.line_channel_access_token),
    }

    return {
        "env": env_settings,
        "client": client_yaml,
        "client_file": str(client_path.relative_to(PROJECT_ROOT)),
        "personality": personality_yaml,
        "personality_file": str(personality_path.relative_to(PROJECT_ROOT)),
    }


@router.put("/config/env", dependencies=[Depends(_require_admin_role)])
async def update_env(request: Request) -> dict:
    """Update .env file settings. Body: {"KEY": "value", ...}."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "Expected a JSON object")

    # Whitelist of safe-to-update keys (no secrets via dashboard)
    SAFE_KEYS = {
        "LLM_MODEL", "LLM_TEMPERATURE", "LLM_PROVIDER", "EMBEDDING_MODEL",
        "CHUNK_SIZE", "CHUNK_OVERLAP", "RETRIEVAL_K",
        "MAX_HISTORY_TURNS", "MAX_MESSAGE_CHARS",
        "RATE_LIMIT_ENABLED", "RATE_LIMIT_IP_PER_MINUTE", "RATE_LIMIT_IP_BURST",
        "RATE_LIMIT_SESSION_PER_MINUTE", "RATE_LIMIT_SESSION_BURST",
        "SPAM_DETECTION_ENABLED", "SPAM_MAX_STRIKES", "SPAM_COOLDOWN_SECONDS",
        "SPAM_MAX_COOLDOWN_SECONDS", "SPAM_MIN_MESSAGE_CHARS",
        "DAILY_TOKEN_CAP", "DAILY_USD_CAP",
        "API_CORS_ORIGINS", "API_STRICT_CORS", "API_HSTS_ENABLED",
        "LOG_LEVEL", "DEBUG", "ACTIVE_CLIENT", "LOG_FILE",
        "HANDOFF_ENABLED", "PROACTIVE_DELAY_SECONDS", "PROACTIVE_MESSAGE",
        "BLOCK_PROMPT_INJECTION",
    }

    updated = {}
    rejected = {}
    for key, value in body.items():
        key_upper = key.upper()
        if key_upper not in SAFE_KEYS:
            rejected[key] = "not allowed"
            continue
        updated[key_upper] = str(value)

    if updated:
        _update_env_file(updated)
        logger.info("[admin] Updated .env keys: {}", list(updated.keys()))

    return {
        "updated": updated,
        "rejected": rejected,
        "note": "Restart the server for changes to take effect.",
    }


@router.put("/config/client", dependencies=[Depends(_require_admin_role)])
async def update_client_yaml(request: Request) -> dict:
    """Update the active client YAML. Body: full YAML content as JSON object."""
    bot = request.app.state.bot
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "Expected a JSON object")

    path = PROJECT_ROOT / "config" / "clients" / f"{bot.settings.active_client}.yaml"
    _save_yaml(path, body)
    logger.info("[admin] Updated client config: {}", path.name)
    return {"saved": str(path.relative_to(PROJECT_ROOT)), "note": "Restart to apply."}


@router.put("/config/personality", dependencies=[Depends(_require_admin_role)])
async def update_personality_yaml(request: Request) -> dict:
    """Update the active personality YAML. Body: full YAML content as JSON object."""
    bot = request.app.state.bot
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(400, "Expected a JSON object")

    personality_name = bot.profile.personality.name
    path = PROJECT_ROOT / "config" / "personalities" / f"{personality_name}.yaml"
    _save_yaml(path, body)
    logger.info("[admin] Updated personality config: {}", path.name)
    return {"saved": str(path.relative_to(PROJECT_ROOT)), "note": "Restart to apply."}


# ── Available clients/personalities ──────────────────────────────────────────

@router.get("/config/clients", dependencies=[Depends(_require_admin_key)])
def list_clients() -> dict:
    clients_dir = PROJECT_ROOT / "config" / "clients"
    clients = []
    for f in sorted(clients_dir.glob("*.yaml")):
        data = _load_yaml(f)
        clients.append({
            "id": data.get("id", f.stem) if data else f.stem,
            "name": data.get("name", f.stem) if data else f.stem,
            "file": f.name,
        })
    return {"clients": clients}


@router.get("/config/personalities", dependencies=[Depends(_require_admin_key)])
def list_personalities() -> dict:
    dir_ = PROJECT_ROOT / "config" / "personalities"
    personalities = []
    for f in sorted(dir_.glob("*.yaml")):
        data = _load_yaml(f)
        personalities.append({
            "name": data.get("name", f.stem) if data else f.stem,
            "description": (data.get("description", "") if data else "")[:100],
            "temperature": data.get("temperature", 0.7) if data else 0.7,
            "file": f.name,
        })
    return {"personalities": personalities}


# ── Logs (last N lines) ─────────────────────────────────────────────────────

@router.get("/logs", dependencies=[Depends(_require_admin_key)])
def get_logs(request: Request, lines: int = 100) -> dict:
    bot = request.app.state.bot
    log_file = bot.settings.log_file
    if not log_file:
        return {"lines": [], "note": "No log file configured (LOG_FILE env var)"}
    log_base = Path(log_file)
    # Logs are date-stamped (e.g. limmes.2026-04-11.log); find the most recent one
    log_files = sorted(
        log_base.parent.glob(f"{log_base.stem}.*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ) if log_base.parent.exists() else []
    log_path = log_files[0] if log_files else None
    if not log_path:
        return {"lines": [], "note": "Log file not created yet. Start the server and it will appear automatically."}

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        return {"lines": all_lines[-min(lines, 500):], "total": len(all_lines), "file": log_path.name}
    except Exception as e:
        return {"lines": [], "error": str(e)}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict | None:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("Could not load YAML {}: {}", path, e)
    return None


def _save_yaml(path: Path, data: dict) -> None:
    # Prevent path traversal — resolved path must be inside PROJECT_ROOT.
    # Use is_relative_to() to avoid the str-prefix bypass (e.g. /app2/ vs /app/).
    resolved = path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        raise HTTPException(403, "Path traversal denied.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def _update_env_file(updates: dict[str, str]) -> None:
    """Patch the .env file with new key=value pairs."""
    env_path = PROJECT_ROOT / ".env"
    resolved = env_path.resolve()
    try:
        resolved.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        raise HTTPException(403, "Path traversal denied.")
    lines: list[str] = []
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    updated_keys: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
                continue
        new_lines.append(line)

    # Append any keys that weren't already in the file
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


# ═══════════════════════════════════════════════════════════════════════════════
# LINE Channel Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/line/status", dependencies=[Depends(_require_admin_key)])
def line_status(request: Request) -> dict:
    """LINE channel configuration status."""
    s = request.app.state.bot.settings
    return {
        "configured": bool(s.line_channel_access_token),
        "channel_secret_set": bool(s.line_channel_secret),
        "access_token_set": bool(s.line_channel_access_token),
        "webhook_url": f"{request.base_url}webhook/line",
    }


@router.get("/line/rich-menus", dependencies=[Depends(_require_admin_key)])
async def line_list_rich_menus(request: Request) -> dict:
    """List all Rich Menus from LINE API."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured (LINE_CHANNEL_ACCESS_TOKEN missing)")
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    try:
        menus = await mgr.list_menus()
        default_id = await mgr.get_default_id()
        return {"menus": menus, "default_id": default_id}
    except Exception as e:
        raise HTTPException(502, f"LINE API error: {e}")


@router.post("/line/rich-menus", dependencies=[Depends(_require_admin_role)])
async def line_create_rich_menu(request: Request) -> dict:
    """Create a Rich Menu. Body: {layout, labels, texts, name, chat_bar_text}."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    body = await request.json()
    layout = body.get("layout", "2col")
    name = body.get("name", "Main Menu")
    chat_bar_text = body.get("chat_bar_text", "Tap to open")

    from chatbot.channels.line_rich_menu import (
        RichMenuManager,
        two_column_layout,
        three_column_layout,
        grid_2x3_layout,
    )

    if layout == "3col":
        labels = body.get("labels", ["Products", "Hours", "Contact"])
        texts = body.get("texts", ["Show products", "Opening hours", "Contact details"])
        areas = three_column_layout(labels=tuple(labels), texts=tuple(texts))
    elif layout == "2x3":
        labels = body.get("labels", ["Curtains", "Sofas", "Wallpapers", "Poufs", "Hours", "Contact"])
        texts = body.get("texts", ["Tell me about curtains", "Tell me about sofas", "Tell me about wallpapers", "Tell me about poufs", "Opening hours", "Contact details"])
        areas = grid_2x3_layout(labels=tuple(labels), texts=tuple(texts))
    else:
        left_l = body.get("labels", ["Products", "Contact Us"])[0]
        right_l = body.get("labels", ["Products", "Contact Us"])[1] if len(body.get("labels", ["Products", "Contact Us"])) > 1 else "Contact Us"
        left_t = body.get("texts", ["Show products", "Contact details"])[0]
        right_t = body.get("texts", ["Show products", "Contact details"])[1] if len(body.get("texts", ["Show products", "Contact details"])) > 1 else "Contact details"
        areas = two_column_layout(left_label=left_l, left_text=left_t, right_label=right_l, right_text=right_t)

    mgr = RichMenuManager(s.line_channel_access_token)
    try:
        menu_id = await mgr.create_menu(name=name, chat_bar_text=chat_bar_text, areas=areas)
        logger.info("[admin] Created LINE rich menu: {}", menu_id)
        return {"menu_id": menu_id, "areas": areas}
    except Exception as e:
        raise HTTPException(502, f"LINE API error: {e}")


@router.post("/line/rich-menus/{menu_id}/default", dependencies=[Depends(_require_admin_role)])
async def line_set_default_menu(menu_id: str, request: Request) -> dict:
    """Set a Rich Menu as default."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    try:
        await mgr.set_default(menu_id)
        return {"status": "ok", "default_menu_id": menu_id}
    except Exception as e:
        raise HTTPException(502, f"LINE API error: {e}")


@router.delete("/line/rich-menus/default", dependencies=[Depends(_require_admin_role)])
async def line_clear_default_menu(request: Request) -> dict:
    """Clear the default Rich Menu."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    try:
        await mgr.clear_default()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(502, f"LINE API error: {e}")


@router.delete("/line/rich-menus/{menu_id}", dependencies=[Depends(_require_admin_role)])
async def line_delete_rich_menu(menu_id: str, request: Request) -> dict:
    """Delete a Rich Menu."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    try:
        await mgr.delete_menu(menu_id)
        logger.info("[admin] Deleted LINE rich menu: {}", menu_id)
        return {"deleted": menu_id}
    except Exception as e:
        raise HTTPException(502, f"LINE API error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# Product Catalog Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/products", dependencies=[Depends(_require_admin_key)])
def list_products(request: Request) -> dict:
    """Return the full product catalog."""
    catalog = getattr(request.app.state, "product_catalog", None)
    if catalog is None:
        return {"products": [], "categories": []}
    return {
        "products": catalog.to_dicts(),
        "categories": catalog.categories,
        "total": len(catalog.products),
    }


@router.put("/products", dependencies=[Depends(_require_admin_role)])
async def update_products(request: Request) -> dict:
    """Replace the product catalog. Body: {"products": [...]}."""
    body = await request.json()
    if not isinstance(body, dict) or "products" not in body:
        raise HTTPException(400, 'Expected {"products": [...]}')

    bot = request.app.state.bot
    from chatbot.core.products import ProductCatalog

    path = ProductCatalog.save(bot.settings.active_client, body["products"])
    # Reload into the running instance
    new_catalog = ProductCatalog.load(bot.settings.active_client)
    request.app.state.product_catalog = new_catalog
    bot.product_catalog = new_catalog
    logger.info("[admin] Product catalog updated ({} products)", len(new_catalog.products))
    return {"saved": str(path), "total": len(new_catalog.products)}


# ═══════════════════════════════════════════════════════════════════════════════
# Contact Messages
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/contacts", dependencies=[Depends(_require_admin_key)])
def list_contacts(request: Request) -> dict:
    store = getattr(request.app.state, "contact_store", None)
    if store is None:
        return {"messages": [], "unread": 0}
    return {
        "messages": store.list_all(),
        "unread": store.count_unread(),
    }


@router.patch("/contacts/{message_id}/read", dependencies=[Depends(_require_admin_key)])
def mark_contact_read(message_id: str, request: Request) -> dict:
    store = getattr(request.app.state, "contact_store", None)
    if not store or not store.mark_read(message_id):
        raise HTTPException(404, "Message not found")
    return {"ok": True}


@router.patch("/contacts/{message_id}/replied", dependencies=[Depends(_require_admin_role)])
def mark_contact_replied(message_id: str, request: Request) -> dict:
    store = getattr(request.app.state, "contact_store", None)
    if not store or not store.mark_replied(message_id):
        raise HTTPException(404, "Message not found")
    return {"ok": True}


@router.delete("/contacts/{message_id}", dependencies=[Depends(_require_admin_role)])
def delete_contact(message_id: str, request: Request) -> dict:
    store = getattr(request.app.state, "contact_store", None)
    if not store or not store.delete(message_id):
        raise HTTPException(404, "Message not found")
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Human Handoff
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/handoff", dependencies=[Depends(_require_admin_key)])
def list_handoffs(request: Request, active_only: bool = True) -> dict:
    mgr = getattr(request.app.state, "handoff_manager", None)
    if mgr is None:
        return {"sessions": []}
    if active_only:
        return {"sessions": mgr.list_active()}
    return {"sessions": mgr.list_all()}


@router.get("/handoff/{session_id}", dependencies=[Depends(_require_admin_key)])
def get_handoff(session_id: str, request: Request) -> dict:
    mgr = getattr(request.app.state, "handoff_manager", None)
    if not mgr:
        raise HTTPException(404, "Handoff not found")
    session = mgr.get_session(session_id)
    if not session:
        raise HTTPException(404, "Handoff session not found")
    return session


@router.post("/handoff/{session_id}/start", dependencies=[Depends(_require_admin_role)])
async def start_handoff(session_id: str, request: Request) -> dict:
    """Admin takes over a session."""
    mgr = getattr(request.app.state, "handoff_manager", None)
    if not mgr:
        raise HTTPException(503, "Handoff not available")
    body = {}
    ct = request.headers.get("content-type", "")
    if ct.startswith("application/json"):
        body = await request.json()
    channel = body.get("channel", "web")
    reason = body.get("reason", "admin_takeover")
    mgr.start_handoff(session_id, channel=channel, reason=reason)
    logger.info("[admin] Handoff started for {}", session_id)
    return {"ok": True, "session_id": session_id}


@router.post("/handoff/{session_id}/reply", dependencies=[Depends(_require_admin_role)])
async def handoff_reply(session_id: str, request: Request) -> dict:
    """Admin sends a reply to a handed-off session."""
    mgr = getattr(request.app.state, "handoff_manager", None)
    if not mgr:
        raise HTTPException(503, "Handoff not available")
    body = await request.json()
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if not mgr.add_message(session_id, "admin", text):
        raise HTTPException(404, "Active handoff session not found")
    logger.info("[admin] Handoff reply to {} ({} chars)", session_id, len(text))

    # Push delivery — send the reply to the user in real time
    push = getattr(request.app.state, "push_service", None)
    if push:
        delivered = await push.deliver(session_id, text)
        # Mark as delivered so engine.ask() doesn't deliver it again
        if delivered:
            mgr.mark_delivered(session_id, text)
        return {"ok": True, "pushed": delivered}

    return {"ok": True, "pushed": False}


@router.post("/handoff/{session_id}/resolve", dependencies=[Depends(_require_admin_role)])
def resolve_handoff(session_id: str, request: Request) -> dict:
    """Return session to bot mode."""
    mgr = getattr(request.app.state, "handoff_manager", None)
    if not mgr or not mgr.resolve(session_id):
        raise HTTPException(404, "Active handoff session not found")
    logger.info("[admin] Handoff resolved for {}", session_id)

    # Close the SSE stream if the user is a web client
    push = getattr(request.app.state, "push_service", None)
    if push:
        q = push._web_queues.get(session_id)
        if q is not None:
            q.put_nowait(None)  # sentinel closes the stream

    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# Fallback / Unanswered Questions Log
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/fallback-log", dependencies=[Depends(_require_admin_key)])
def get_fallback_log(request: Request, unresolved_only: bool = True) -> dict:
    flog = getattr(request.app.state, "fallback_log", None)
    if flog is None:
        return {"questions": [], "unresolved": 0}
    return {
        "questions": flog.list_all(unresolved_only=unresolved_only),
        "unresolved": flog.count_unresolved(),
    }


@router.patch("/fallback-log/resolve", dependencies=[Depends(_require_admin_role)])
async def resolve_fallback(request: Request) -> dict:
    """Mark a fallback question as resolved. Body: {"question": "...", "note": "..."}."""
    flog = getattr(request.app.state, "fallback_log", None)
    if not flog:
        raise HTTPException(503, "Fallback log not available")
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")
    note = body.get("note", "")
    if not flog.resolve(question, admin_note=note):
        raise HTTPException(404, "Question not found")
    return {"ok": True}


@router.patch("/fallback-log/add-to-kb", dependencies=[Depends(_require_admin_role)])
async def fallback_add_to_kb(request: Request) -> dict:
    """Mark a question as added to the knowledge base."""
    flog = getattr(request.app.state, "fallback_log", None)
    if not flog:
        raise HTTPException(503, "Fallback log not available")
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")
    if not flog.mark_added_to_kb(question):
        raise HTTPException(404, "Question not found")
    return {"ok": True}


@router.delete("/fallback-log", dependencies=[Depends(_require_admin_role)])
async def delete_fallback(request: Request) -> dict:
    """Delete a question from the fallback log. Body: {"question": "..."}."""
    flog = getattr(request.app.state, "fallback_log", None)
    if not flog:
        raise HTTPException(503, "Fallback log not available")
    body = await request.json()
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(400, "question is required")
    if not flog.delete(question):
        raise HTTPException(404, "Question not found")
    return {"ok": True}


@router.post("/line/flex-preview", dependencies=[Depends(_require_admin_role)])
async def line_flex_preview(request: Request) -> dict:
    """Generate a Flex Message JSON preview.

    type=product: {title, description, price, image_url, action_label, action_uri}
    type=contact: {business_name, phone, whatsapp, email, website, address}
    type=carousel: {products: [...product objects]}
    """
    body = await request.json()
    from chatbot.channels.line_flex import (
        product_bubble,
        contact_bubble,
        carousel,
        flex_message,
    )

    msg_type = body.get("type", "product")

    if msg_type == "contact":
        bubble = contact_bubble(
            business_name=body.get("business_name", ""),
            phone=body.get("phone", ""),
            whatsapp=body.get("whatsapp", ""),
            email=body.get("email", ""),
            website=body.get("website", ""),
            address=body.get("address", ""),
        )
        return {"flex": flex_message("Contact", bubble)}

    if msg_type == "carousel":
        products = body.get("products", [])
        bubbles = [
            product_bubble(
                title=p.get("title", ""),
                description=p.get("description", ""),
                price=p.get("price", ""),
                image_url=p.get("image_url"),
                action_label=p.get("action_label", "Learn more"),
                action_uri=p.get("action_uri"),
            )
            for p in products
        ]
        return {"flex": flex_message("Products", carousel(bubbles))}

    # Default: single product
    bubble = product_bubble(
        title=body.get("title", "Product"),
        description=body.get("description", ""),
        price=body.get("price", ""),
        image_url=body.get("image_url"),
        action_label=body.get("action_label", "Learn more"),
        action_uri=body.get("action_uri"),
    )
    return {"flex": flex_message(body.get("title", "Product"), bubble)}


# ═══════════════════════════════════════════════════════════════════════════════
# Data Files (knowledge base)
# ═══════════════════════════════════════════════════════════════════════════════


def _safe_data_path(file_path: str, active_client: str) -> tuple[Path, Path]:
    """Resolve and verify a data file path is within the allowed data root.

    Returns (full_path, data_root). Raises HTTPException on traversal.
    """
    clean = Path(file_path.replace("..", "").strip("/"))
    data_root = (PROJECT_ROOT / "data" / active_client).resolve()
    full_path = (data_root / clean).resolve()
    try:
        full_path.relative_to(data_root)
    except ValueError:
        raise HTTPException(403, "Path traversal blocked")
    return full_path, data_root


@router.get("/data", dependencies=[Depends(_require_admin_key)])
def list_data_files(request: Request) -> dict:
    """List all data files for the active client."""
    s = request.app.state.bot.settings
    data_dir = PROJECT_ROOT / "data" / s.active_client
    if not data_dir.exists():
        return {"files": [], "data_dir": str(data_dir.relative_to(PROJECT_ROOT))}

    files = []
    for f in sorted(data_dir.rglob("*")):
        if f.is_file() and not f.name.startswith("."):
            rel = f.relative_to(data_dir)
            try:
                size = f.stat().st_size
            except OSError:
                size = 0
            files.append({
                "path": str(rel).replace("\\", "/"),
                "name": f.name,
                "folder": str(rel.parent).replace("\\", "/") if str(rel.parent) != "." else "",
                "size": size,
                "extension": f.suffix,
            })
    return {"files": files, "data_dir": f"data/{s.active_client}"}


@router.get("/data/{file_path:path}", dependencies=[Depends(_require_admin_key)])
def read_data_file(file_path: str, request: Request) -> dict:
    """Read a data file's content."""
    s = request.app.state.bot.settings
    full_path, data_root = _safe_data_path(file_path, s.active_client)
    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    if not full_path.is_file():
        raise HTTPException(400, f"Not a file: {file_path}")

    try:
        raw_content = full_path.read_bytes()
    except OSError as e:
        raise HTTPException(500, f"Could not read file: {e}")

    if b"\x00" in raw_content:
        raise HTTPException(
            415,
            "Only UTF-8 text files can be read via this endpoint; binary files are not supported.",
        )

    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            415,
            "Only UTF-8 text files can be read via this endpoint; this file is not valid UTF-8 text.",
        )

    return {"path": file_path, "content": content, "size": len(raw_content)}


@router.put("/data/{file_path:path}", dependencies=[Depends(_require_admin_role)])
async def update_data_file(file_path: str, request: Request) -> dict:
    """Update a data file. Body: {"content": "..."}."""
    s = request.app.state.bot.settings
    body = await request.json()
    content = body.get("content", "")
    if not isinstance(content, str):
        raise HTTPException(400, "content must be a string")

    clean = Path(file_path.replace("..", "").strip("/"))
    full_path, _ = _safe_data_path(file_path, s.active_client)

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    logger.info("[admin] Updated data file: {}", file_path)
    return {
        "saved": file_path,
        "size": len(content),
        "note": "Run 'ingest' to rebuild the vector store with updated content.",
    }


@router.post("/data", dependencies=[Depends(_require_admin_role)])
async def create_data_file(request: Request) -> dict:
    """Create a new data file. Body: {"path": "folder/name.md", "content": "..."}."""
    s = request.app.state.bot.settings
    body = await request.json()
    file_path = body.get("path", "")
    content = body.get("content", "")
    if not file_path or not isinstance(content, str):
        raise HTTPException(400, "path and content are required")

    clean = Path(file_path.replace("..", "").strip("/"))
    full_path, _ = _safe_data_path(file_path, s.active_client)
    if full_path.exists():
        raise HTTPException(409, f"File already exists: {file_path}")

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    logger.info("[admin] Created data file: {}", file_path)
    return {"created": file_path, "size": len(content)}


@router.delete("/data/{file_path:path}", dependencies=[Depends(_require_admin_role)])
def delete_data_file(file_path: str, request: Request) -> dict:
    """Delete a data file."""
    s = request.app.state.bot.settings
    clean = Path(file_path.replace("..", "").strip("/"))
    full_path, _ = _safe_data_path(file_path, s.active_client)
    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    full_path.unlink()
    logger.info("[admin] Deleted data file: {}", file_path)
    return {"deleted": file_path}


@router.post("/data/upload", dependencies=[Depends(_require_admin_role)])
async def upload_data_file(request: Request) -> dict:
    """Upload a data file via multipart form. Fields: folder, file."""
    from fastapi import UploadFile, File, Form

    # Parse multipart manually since we can't use Depends in this pattern
    form = await request.form()
    folder = form.get("folder", "")
    upload = form.get("file")
    if upload is None or not hasattr(upload, "filename"):
        raise HTTPException(400, "No file uploaded")

    filename = Path(upload.filename).name  # strip any path from filename
    if not filename:
        raise HTTPException(400, "Empty filename")

    s = request.app.state.bot.settings
    rel_path = f"{folder}/{filename}" if folder else filename
    full_path, data_root = _safe_data_path(rel_path, s.active_client)

    content = await upload.read()
    if b"\x00" in content:
        raise HTTPException(415, "Binary files are not supported — only UTF-8 text/markdown files.")

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(415, "File is not valid UTF-8 text.")

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(text, encoding="utf-8")
    logger.info("[admin] Uploaded data file: {}", rel_path)
    return {"uploaded": rel_path, "size": len(text)}


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/analytics", dependencies=[Depends(_require_admin_key)])
def analytics_dashboard(request: Request, days: int = 7) -> dict:
    """Return aggregated analytics for the dashboard."""
    tracker = getattr(request.app.state, "analytics_tracker", None)
    if tracker is None:
        return {"error": "Analytics not enabled", "period_days": days}
    return tracker.dashboard_summary(days=min(days, 90))


@router.delete("/analytics", dependencies=[Depends(_require_admin_role)])
def clear_analytics(request: Request) -> dict:
    tracker = getattr(request.app.state, "analytics_tracker", None)
    if tracker is None:
        raise HTTPException(503, "Analytics not enabled")
    count = tracker.clear()
    return {"cleared": count}


# ═══════════════════════════════════════════════════════════════════════════════
# Feedback
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/feedback", dependencies=[Depends(_require_admin_key)])
def list_feedback(request: Request, limit: int = 200) -> dict:
    store = getattr(request.app.state, "feedback_store", None)
    if store is None:
        return {"feedback": [], "stats": {}}
    return {
        "feedback": store.list_all(limit=min(limit, 500)),
        "stats": store.stats(),
    }


@router.get("/feedback/negative", dependencies=[Depends(_require_admin_key)])
def list_negative_feedback(request: Request, limit: int = 50) -> dict:
    store = getattr(request.app.state, "feedback_store", None)
    if store is None:
        return {"feedback": []}
    return {"feedback": store.recent_negative(limit=min(limit, 200))}


@router.delete("/feedback", dependencies=[Depends(_require_admin_role)])
def clear_feedback(request: Request) -> dict:
    store = getattr(request.app.state, "feedback_store", None)
    if store is None:
        raise HTTPException(503, "Feedback not enabled")
    count = store.clear()
    return {"cleared": count}


# ═══════════════════════════════════════════════════════════════════════════════
# A/B Testing
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/ab-test", dependencies=[Depends(_require_admin_key)])
def ab_test_status(request: Request) -> dict:
    mgr = getattr(request.app.state, "ab_test_manager", None)
    if mgr is None:
        return {"enabled": False}
    return {**mgr.stats(), "config": mgr.get_config()}


@router.put("/ab-test", dependencies=[Depends(_require_admin_role)])
async def update_ab_test(request: Request) -> dict:
    """Update A/B test config. Body: {enabled, name, variants: [{name, personality, weight}]}."""
    mgr = getattr(request.app.state, "ab_test_manager", None)
    if mgr is None:
        raise HTTPException(503, "A/B testing not available")
    body = await request.json()
    mgr.update_config(body)
    return {"ok": True, **mgr.stats()}


@router.delete("/ab-test/assignments", dependencies=[Depends(_require_admin_role)])
def clear_ab_assignments(request: Request) -> dict:
    mgr = getattr(request.app.state, "ab_test_manager", None)
    if mgr is None:
        raise HTTPException(503, "A/B testing not available")
    count = mgr.clear_assignments()
    return {"cleared": count}


# ═══════════════════════════════════════════════════════════════════════════════
# User Memory (Long-term)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/user-memory", dependencies=[Depends(_require_admin_key)])
def list_user_memories(request: Request, limit: int = 100) -> dict:
    store = getattr(request.app.state, "user_memory_store", None)
    if store is None:
        return {"users": [], "total": 0}
    users = store.list_users(limit=min(limit, 500))
    return {"users": users, "total": store.count()}


@router.get("/user-memory/{user_id}", dependencies=[Depends(_require_admin_key)])
def get_user_memory(user_id: str, request: Request) -> dict:
    store = getattr(request.app.state, "user_memory_store", None)
    if store is None:
        raise HTTPException(503, "User memory not enabled")
    user = store.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return user


@router.post("/user-memory/{user_id}/facts", dependencies=[Depends(_require_admin_role)])
async def add_user_fact(user_id: str, request: Request) -> dict:
    """Add a fact about a user. Body: {fact, category}."""
    store = getattr(request.app.state, "user_memory_store", None)
    if store is None:
        raise HTTPException(503, "User memory not enabled")
    body = await request.json()
    fact = body.get("fact", "").strip()
    if not fact:
        raise HTTPException(400, "fact is required")
    category = body.get("category", "general")
    store.add_fact(user_id, fact, category=category, source="admin")
    return {"ok": True}


@router.patch("/user-memory/{user_id}/tags", dependencies=[Depends(_require_admin_role)])
async def update_user_tags(user_id: str, request: Request) -> dict:
    """Update user tags for segmentation. Body: {tags: [...]}."""
    store = getattr(request.app.state, "user_memory_store", None)
    if store is None:
        raise HTTPException(503, "User memory not enabled")
    body = await request.json()
    tags = body.get("tags", [])
    if not isinstance(tags, list):
        raise HTTPException(400, "tags must be a list")
    if not store.update_user_tags(user_id, tags):
        raise HTTPException(404, "User not found")
    return {"ok": True}


@router.delete("/user-memory/{user_id}", dependencies=[Depends(_require_admin_role)])
def delete_user_memory(user_id: str, request: Request) -> dict:
    store = getattr(request.app.state, "user_memory_store", None)
    if store is None:
        raise HTTPException(503, "User memory not enabled")
    if not store.delete_user(user_id):
        raise HTTPException(404, "User not found")
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# LINE Push Campaigns
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/line/push/campaign", dependencies=[Depends(_require_admin_role)])
async def line_push_campaign(request: Request) -> dict:
    """Send a campaign message to selected LINE users.

    Body: {user_ids: [...], messages: [{type, text, ...}]} or {segment: "tag"}.
    """
    push = getattr(request.app.state, "push_service", None)
    if push is None:
        raise HTTPException(503, "Push service not available")
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")

    body = await request.json()

    # Resolve user IDs from segment tag if provided
    user_ids = body.get("user_ids", [])
    segment = body.get("segment", "")
    if segment and not user_ids:
        mem_store = getattr(request.app.state, "user_memory_store", None)
        if mem_store:
            user_ids = mem_store.get_segment(segment)

    messages = body.get("messages", [])
    if not messages:
        text = body.get("text", "")
        if text:
            messages = [{"type": "text", "text": text}]
        else:
            raise HTTPException(400, "messages or text is required")

    if user_ids:
        result = await push.line_multicast(user_ids, messages)
    else:
        # Broadcast to all followers
        result = await push.line_broadcast(messages)

    logger.info("[admin] LINE campaign sent: {}", result)
    return result


@router.post("/line/push/imagemap", dependencies=[Depends(_require_admin_role)])
async def line_push_imagemap_msg(request: Request) -> dict:
    """Push an imagemap message to a user or broadcast.

    Body: {user_id or broadcast: true, base_url, alt_text, areas: [...]}
    """
    push = getattr(request.app.state, "push_service", None)
    if push is None:
        raise HTTPException(503, "Push service not available")

    body = await request.json()
    from chatbot.channels.line_imagemap import imagemap_message

    msg = imagemap_message(
        base_url=body.get("base_url", ""),
        alt_text=body.get("alt_text", "Menu"),
        base_width=body.get("base_width", 1040),
        base_height=body.get("base_height", 1040),
        areas=body.get("areas", []),
    )

    user_id = body.get("user_id", "")
    if user_id:
        ok = await push.line_push_imagemap(user_id, msg)
        return {"ok": ok}

    if body.get("broadcast"):
        result = await push.line_broadcast([msg])
        return result

    raise HTTPException(400, "user_id or broadcast: true is required")


# ═══════════════════════════════════════════════════════════════════════════════
# LINE Rich Menu Per-User Targeting
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/line/rich-menus/{menu_id}/link-user", dependencies=[Depends(_require_admin_role)])
async def line_link_menu_to_user(menu_id: str, request: Request) -> dict:
    """Assign a rich menu to a specific user. Body: {user_id}."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    body = await request.json()
    user_id = body.get("user_id", "")
    if not user_id:
        raise HTTPException(400, "user_id is required")

    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    ok = await mgr.link_menu_to_user(menu_id, user_id)
    return {"ok": ok}


@router.post("/line/rich-menus/{menu_id}/link-segment", dependencies=[Depends(_require_admin_role)])
async def line_link_menu_to_segment(menu_id: str, request: Request) -> dict:
    """Assign a rich menu to all users in a segment. Body: {segment}."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    body = await request.json()
    segment = body.get("segment", "")
    if not segment:
        raise HTTPException(400, "segment is required")

    mem_store = getattr(request.app.state, "user_memory_store", None)
    if not mem_store:
        raise HTTPException(503, "User memory not enabled")

    user_ids = mem_store.get_segment(segment)
    if not user_ids:
        return {"ok": True, "linked": 0, "note": "No users in segment"}

    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    result = await mgr.link_menu_to_users(menu_id, user_ids)
    return {"ok": True, **result}


@router.delete("/line/rich-menus/user/{user_id}", dependencies=[Depends(_require_admin_role)])
async def line_unlink_user_menu(user_id: str, request: Request) -> dict:
    """Remove per-user rich menu override."""
    s = request.app.state.bot.settings
    if not s.line_channel_access_token:
        raise HTTPException(400, "LINE not configured")
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(s.line_channel_access_token)
    ok = await mgr.unlink_menu_from_user(user_id)
    return {"ok": ok}


# ═══════════════════════════════════════════════════════════════════════════════
# LINE Login Status
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/line/login-status", dependencies=[Depends(_require_admin_key)])
def line_login_status(request: Request) -> dict:
    s = request.app.state.bot.settings
    return {
        "enabled": bool(s.line_login_channel_id),
        "channel_id_set": bool(s.line_login_channel_id),
        "channel_secret_set": bool(s.line_login_channel_secret),
    }
