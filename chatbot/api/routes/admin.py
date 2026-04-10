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
from chatbot.settings import PROJECT_ROOT

router = APIRouter(prefix="/admin/api", tags=["admin"])

_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

# Track when the server started (set in lifespan).
_start_time: float = time.time()


def set_start_time() -> None:
    global _start_time
    _start_time = time.time()


def _require_admin_key(
    request: Request,
    key: str | None = Security(_admin_key_header),
) -> None:
    expected = getattr(request.app.state, "admin_api_key", "")
    if not expected:
        raise HTTPException(status_code=403, detail="Admin dashboard is disabled.")
    if not key or not hmac.compare_digest(expected, key):
        raise HTTPException(status_code=401, detail="Invalid admin key.")


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


@router.delete("/sessions/{session_id}", dependencies=[Depends(_require_admin_key)])
def delete_session(session_id: str, request: Request) -> dict:
    bot = request.app.state.bot
    bot.memory.clear(session_id)
    logger.info("[admin] Cleared session: {}", session_id)
    return {"cleared": session_id}


@router.delete("/sessions", dependencies=[Depends(_require_admin_key)])
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


@router.post("/budget/reset", dependencies=[Depends(_require_admin_key)])
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


@router.put("/config/env", dependencies=[Depends(_require_admin_key)])
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
        "SPAM_MAX_COOLDOWN_SECONDS",
        "DAILY_TOKEN_CAP", "DAILY_USD_CAP",
        "API_CORS_ORIGINS", "API_STRICT_CORS", "API_HSTS_ENABLED",
        "LOG_LEVEL", "DEBUG", "ACTIVE_CLIENT", "LOG_FILE",
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


@router.put("/config/client", dependencies=[Depends(_require_admin_key)])
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


@router.put("/config/personality", dependencies=[Depends(_require_admin_key)])
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
    log_path = Path(log_file)
    if not log_path.exists():
        return {"lines": [], "note": f"Log file not created yet: {log_path.name}. Start the server and it will appear automatically."}

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


@router.post("/line/rich-menus", dependencies=[Depends(_require_admin_key)])
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


@router.post("/line/rich-menus/{menu_id}/default", dependencies=[Depends(_require_admin_key)])
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


@router.delete("/line/rich-menus/default", dependencies=[Depends(_require_admin_key)])
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


@router.delete("/line/rich-menus/{menu_id}", dependencies=[Depends(_require_admin_key)])
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


@router.post("/line/flex-preview", dependencies=[Depends(_require_admin_key)])
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
    # Sanitize: prevent path traversal
    clean = Path(file_path.replace("..", "").strip("/"))
    full_path = (PROJECT_ROOT / "data" / s.active_client / clean).resolve()
    data_root = (PROJECT_ROOT / "data" / s.active_client).resolve()

    if not str(full_path).startswith(str(data_root)):
        raise HTTPException(403, "Path traversal blocked")
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


@router.put("/data/{file_path:path}", dependencies=[Depends(_require_admin_key)])
async def update_data_file(file_path: str, request: Request) -> dict:
    """Update a data file. Body: {"content": "..."}."""
    s = request.app.state.bot.settings
    body = await request.json()
    content = body.get("content", "")
    if not isinstance(content, str):
        raise HTTPException(400, "content must be a string")

    clean = Path(file_path.replace("..", "").strip("/"))
    full_path = (PROJECT_ROOT / "data" / s.active_client / clean).resolve()
    data_root = (PROJECT_ROOT / "data" / s.active_client).resolve()

    if not str(full_path).startswith(str(data_root)):
        raise HTTPException(403, "Path traversal blocked")

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    logger.info("[admin] Updated data file: {}", file_path)
    return {
        "saved": file_path,
        "size": len(content),
        "note": "Run 'ingest' to rebuild the vector store with updated content.",
    }


@router.post("/data", dependencies=[Depends(_require_admin_key)])
async def create_data_file(request: Request) -> dict:
    """Create a new data file. Body: {"path": "folder/name.md", "content": "..."}."""
    s = request.app.state.bot.settings
    body = await request.json()
    file_path = body.get("path", "")
    content = body.get("content", "")
    if not file_path or not isinstance(content, str):
        raise HTTPException(400, "path and content are required")

    clean = Path(file_path.replace("..", "").strip("/"))
    full_path = (PROJECT_ROOT / "data" / s.active_client / clean).resolve()
    data_root = (PROJECT_ROOT / "data" / s.active_client).resolve()

    if not str(full_path).startswith(str(data_root)):
        raise HTTPException(403, "Path traversal blocked")
    if full_path.exists():
        raise HTTPException(409, f"File already exists: {file_path}")

    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    logger.info("[admin] Created data file: {}", file_path)
    return {"created": file_path, "size": len(content)}


@router.delete("/data/{file_path:path}", dependencies=[Depends(_require_admin_key)])
def delete_data_file(file_path: str, request: Request) -> dict:
    """Delete a data file."""
    s = request.app.state.bot.settings
    clean = Path(file_path.replace("..", "").strip("/"))
    full_path = (PROJECT_ROOT / "data" / s.active_client / clean).resolve()
    data_root = (PROJECT_ROOT / "data" / s.active_client).resolve()

    if not str(full_path).startswith(str(data_root)):
        raise HTTPException(403, "Path traversal blocked")
    if not full_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")

    full_path.unlink()
    logger.info("[admin] Deleted data file: {}", file_path)
    return {"deleted": file_path}


@router.post("/data/upload", dependencies=[Depends(_require_admin_key)])
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
    clean = Path(rel_path.replace("..", "").strip("/"))
    full_path = (PROJECT_ROOT / "data" / s.active_client / clean).resolve()
    data_root = (PROJECT_ROOT / "data" / s.active_client).resolve()

    if not str(full_path).startswith(str(data_root)):
        raise HTTPException(403, "Path traversal blocked")

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
