"""
LINE Rich Menu management helper.

Automates the 4-step Rich Menu setup via the LINE Messaging API:

1. Create the rich menu structure (tap areas, labels, actions).
2. Upload the menu image.
3. Set it as the default menu for all users.

Usage (CLI):
    python -m chatbot.channels.line_rich_menu create --image menu.png
    python -m chatbot.channels.line_rich_menu delete --menu-id richmenu-xxx

Or use programmatically:
    from chatbot.channels.line_rich_menu import RichMenuManager
    mgr = RichMenuManager(access_token="...")
    menu_id = await mgr.create_default_menu(image_path="menu.png", areas=[...])

LINE Rich Menu reference:
    https://developers.line.biz/en/docs/messaging-api/using-rich-menus/
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

import httpx

from chatbot.logging_setup import logger


API_BASE = "https://api.line.me/v2/bot"
API_DATA = "https://api-data.line.me/v2/bot"

# Standard rich menu sizes.
RICH_MENU_FULL = {"width": 2500, "height": 1686}     # full-size (wide)
RICH_MENU_HALF = {"width": 2500, "height": 843}      # compact (half-height)

# ── Pre-built menu layouts ───────────────────────────────────────────────────

def two_column_layout(
    *,
    left_label: str = "Products",
    left_text: str = "Show products",
    right_label: str = "Contact Us",
    right_text: str = "Contact details",
) -> list[dict]:
    """Two equally sized columns (full width, full height)."""
    return [
        {
            "bounds": {"x": 0, "y": 0, "width": 1250, "height": 1686},
            "action": {"type": "message", "label": left_label, "text": left_text},
        },
        {
            "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 1686},
            "action": {"type": "message", "label": right_label, "text": right_text},
        },
    ]


def three_column_layout(
    *,
    labels: tuple[str, str, str] = ("Products", "Hours", "Contact"),
    texts: tuple[str, str, str] = ("Show products", "Opening hours", "Contact details"),
) -> list[dict]:
    """Three equally spaced columns, full height."""
    col_w = 2500 // 3
    areas = []
    for i, (label, text) in enumerate(zip(labels, texts)):
        areas.append({
            "bounds": {"x": i * col_w, "y": 0,
                       "width": col_w + (1 if i == 2 else 0),  # rounding
                       "height": 1686},
            "action": {"type": "message", "label": label, "text": text},
        })
    return areas


def grid_2x3_layout(
    *,
    labels: tuple[str, ...] = (
        "Curtains", "Sofas", "Wallpapers",
        "Poufs", "Hours", "Contact",
    ),
    texts: tuple[str, ...] = (
        "Tell me about curtains", "Tell me about sofas",
        "Tell me about wallpapers", "Tell me about poufs",
        "Opening hours", "Contact details",
    ),
) -> list[dict]:
    """2 rows x 3 columns grid (6 areas)."""
    col_w = 2500 // 3
    row_h = 1686 // 2
    areas = []
    for idx, (label, text) in enumerate(zip(labels, texts)):
        row = idx // 3
        col = idx % 3
        areas.append({
            "bounds": {
                "x": col * col_w,
                "y": row * row_h,
                "width": col_w + (1 if col == 2 else 0),
                "height": row_h + (1 if row == 1 else 0),
            },
            "action": {"type": "message", "label": label, "text": text},
        })
    return areas


# ── Rich Menu Manager ────────────────────────────────────────────────────────

class RichMenuManager:
    """Manages LINE Rich Menus via the Messaging API."""

    def __init__(self, access_token: str) -> None:
        if not access_token:
            raise ValueError("LINE_CHANNEL_ACCESS_TOKEN is required.")
        self._token = access_token
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    # ── High-level operations ────────────────────────────────────────────

    async def create_default_menu(
        self,
        *,
        name: str = "Main Menu",
        chat_bar_text: str = "Tap to open",
        areas: list[dict],
        image_path: Optional[str | Path] = None,
        size: Optional[dict] = None,
        selected: bool = False,
    ) -> str:
        """Create a rich menu, upload image, and set as default.

        Returns the rich menu ID.
        """
        menu_id = await self.create_menu(
            name=name,
            chat_bar_text=chat_bar_text,
            areas=areas,
            size=size or RICH_MENU_FULL,
            selected=selected,
        )
        logger.info("Created rich menu: {}", menu_id)

        if image_path:
            await self.upload_image(menu_id, Path(image_path))
            logger.info("Uploaded image for menu: {}", menu_id)

        await self.set_default(menu_id)
        logger.info("Set default rich menu: {}", menu_id)

        return menu_id

    # ── Low-level API calls ──────────────────────────────────────────────

    async def create_menu(
        self,
        *,
        name: str,
        chat_bar_text: str,
        areas: list[dict],
        size: dict = RICH_MENU_FULL,
        selected: bool = False,
    ) -> str:
        """POST /v2/bot/richmenu → returns richMenuId."""
        body = {
            "size": size,
            "selected": selected,
            "name": name[:300],
            "chatBarText": chat_bar_text[:14],
            "areas": areas,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_BASE}/richmenu",
                headers=self._headers,
                json=body,
            )
            resp.raise_for_status()
            return resp.json()["richMenuId"]

    async def upload_image(
        self,
        menu_id: str,
        image_path: Path,
    ) -> None:
        """POST /v2/bot/richmenu/{id}/content — upload the menu image.

        Supported: JPEG or PNG, max 1 MB.
        Image should be 2500×1686 (full) or 2500×843 (compact).
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        suffix = image_path.suffix.lower()
        content_type = "image/png" if suffix == ".png" else "image/jpeg"

        data = image_path.read_bytes()
        if len(data) > 1_048_576:
            raise ValueError(
                f"Image too large ({len(data)} bytes). LINE limit is 1 MB."
            )

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{API_DATA}/richmenu/{menu_id}/content",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": content_type,
                },
                content=data,
            )
            resp.raise_for_status()

    async def set_default(self, menu_id: str) -> None:
        """POST /v2/bot/user/all/richmenu/{id} — set as default for all users."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{API_BASE}/user/all/richmenu/{menu_id}",
                headers=self._headers,
            )
            resp.raise_for_status()

    async def clear_default(self) -> None:
        """DELETE /v2/bot/user/all/richmenu — remove the default rich menu."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{API_BASE}/user/all/richmenu",
                headers=self._headers,
            )
            resp.raise_for_status()

    async def delete_menu(self, menu_id: str) -> None:
        """DELETE /v2/bot/richmenu/{id}."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.delete(
                f"{API_BASE}/richmenu/{menu_id}",
                headers=self._headers,
            )
            resp.raise_for_status()

    async def list_menus(self) -> list[dict]:
        """GET /v2/bot/richmenu/list."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{API_BASE}/richmenu/list",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json().get("richmenus", [])

    async def get_default_id(self) -> Optional[str]:
        """GET /v2/bot/user/all/richmenu → returns the current default menu ID."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{API_BASE}/user/all/richmenu",
                headers=self._headers,
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json().get("richMenuId")


# ── CLI entry point ──────────────────────────────────────────────────────────

def _cli():
    """Simple CLI for managing LINE Rich Menus.

    Usage:
        python -m chatbot.channels.line_rich_menu list
        python -m chatbot.channels.line_rich_menu create --layout 3col --image menu.png
        python -m chatbot.channels.line_rich_menu create --layout 2x3 --image menu.png
        python -m chatbot.channels.line_rich_menu delete --menu-id richmenu-xxx
        python -m chatbot.channels.line_rich_menu clear-default
    """
    import argparse

    from chatbot.settings import get_settings

    parser = argparse.ArgumentParser(
        description="LINE Rich Menu management",
        prog="python -m chatbot.channels.line_rich_menu",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    sub.add_parser("list", help="List all rich menus")

    # create
    cp = sub.add_parser("create", help="Create and set default rich menu")
    cp.add_argument(
        "--layout", choices=["2col", "3col", "2x3"], default="3col",
        help="Pre-built area layout",
    )
    cp.add_argument("--image", type=str, help="Path to menu image (PNG/JPEG)")
    cp.add_argument("--name", default="Main Menu", help="Menu name")
    cp.add_argument("--chat-bar", default="Tap to open", help="Chat bar text")

    # delete
    dp = sub.add_parser("delete", help="Delete a rich menu")
    dp.add_argument("--menu-id", required=True, help="Rich menu ID")

    # clear-default
    sub.add_parser("clear-default", help="Clear the default rich menu")

    args = parser.parse_args()
    settings = get_settings()

    if not settings.line_channel_access_token:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN not set in .env")
        sys.exit(1)

    mgr = RichMenuManager(settings.line_channel_access_token)

    async def run():
        if args.command == "list":
            menus = await mgr.list_menus()
            default_id = await mgr.get_default_id()
            if not menus:
                print("No rich menus found.")
                return
            for m in menus:
                marker = " (DEFAULT)" if m.get("richMenuId") == default_id else ""
                print(f"  {m['richMenuId']}{marker}")
                print(f"    name: {m.get('name', '?')}")
                print(f"    size: {m.get('size', {})}")
                print(f"    areas: {len(m.get('areas', []))}")
                print()

        elif args.command == "create":
            layouts = {
                "2col": two_column_layout,
                "3col": three_column_layout,
                "2x3": grid_2x3_layout,
            }
            areas = layouts[args.layout]()
            menu_id = await mgr.create_default_menu(
                name=args.name,
                chat_bar_text=args.chat_bar,
                areas=areas,
                image_path=args.image,
            )
            print(f"Created and set default: {menu_id}")

        elif args.command == "delete":
            await mgr.delete_menu(args.menu_id)
            print(f"Deleted: {args.menu_id}")

        elif args.command == "clear-default":
            await mgr.clear_default()
            print("Default rich menu cleared.")

    asyncio.run(run())


if __name__ == "__main__":
    _cli()
