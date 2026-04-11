"""
LINE Imagemap messages — clickable image regions for visual menus.

Imagemap messages display a full-width image where each region can be
tapped to trigger an action (send a message or open a URL).

LINE Imagemap reference:
    https://developers.line.biz/en/docs/messaging-api/message-types/#imagemap-messages
"""

from __future__ import annotations

from typing import Any, Optional


def imagemap_message(
    *,
    base_url: str,
    alt_text: str = "Menu",
    base_width: int = 1040,
    base_height: int = 1040,
    areas: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a LINE Imagemap message.

    Parameters
    ----------
    base_url:
        Base URL of the image. LINE appends /{size} (e.g. /1040) to
        fetch resolution variants. Must serve images at:
        {base_url}/1040, {base_url}/700, {base_url}/460, {base_url}/300, {base_url}/240.
    alt_text:
        Text shown on devices that can't display imagemaps.
    base_width:
        Image width in pixels (usually 1040).
    base_height:
        Image height in pixels.
    areas:
        List of clickable areas. Each should have:
        - type: "message" or "uri"
        - text: message text (for type="message")
        - uri: URL (for type="uri")
        - x, y, width, height: tap region bounds
    """
    actions = []
    for area in areas:
        action: dict[str, Any] = {
            "type": area.get("type", "message"),
            "area": {
                "x": area.get("x", 0),
                "y": area.get("y", 0),
                "width": area.get("width", base_width),
                "height": area.get("height", base_height),
            },
        }
        if area.get("type") == "uri":
            action["linkUri"] = area["uri"]
            action["label"] = area.get("label", "Open")[:50]
        else:
            action["text"] = area.get("text", "")[:400]
            action["label"] = area.get("label", "")[:50]

        actions.append(action)

    return {
        "type": "imagemap",
        "baseUrl": base_url,
        "altText": alt_text[:400],
        "baseSize": {
            "width": base_width,
            "height": base_height,
        },
        "actions": actions,
    }


def grid_imagemap(
    *,
    base_url: str,
    alt_text: str = "Menu",
    cols: int = 2,
    rows: int = 2,
    width: int = 1040,
    height: int = 1040,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a grid-layout imagemap (evenly divided cells).

    Parameters
    ----------
    items:
        List of dicts with keys:
        - text: message to send on tap (type=message)
        - uri: URL to open on tap (type=uri)
        - label: display label
    """
    cell_w = width // cols
    cell_h = height // rows

    areas = []
    for idx, item in enumerate(items[: cols * rows]):
        row = idx // cols
        col = idx % cols
        area: dict[str, Any] = {
            "x": col * cell_w,
            "y": row * cell_h,
            "width": cell_w,
            "height": cell_h,
            "label": item.get("label", ""),
        }
        if "uri" in item:
            area["type"] = "uri"
            area["uri"] = item["uri"]
        else:
            area["type"] = "message"
            area["text"] = item.get("text", item.get("label", ""))
        areas.append(area)

    return imagemap_message(
        base_url=base_url,
        alt_text=alt_text,
        base_width=width,
        base_height=height,
        areas=areas,
    )


def category_imagemap(
    *,
    base_url: str,
    categories: list[str],
    cols: int = 2,
) -> dict[str, Any]:
    """Build a product-category imagemap from a list of category names."""
    rows = (len(categories) + cols - 1) // cols
    items = [
        {"text": f"Show me {cat}", "label": cat}
        for cat in categories
    ]
    return grid_imagemap(
        base_url=base_url,
        alt_text="Browse categories",
        cols=cols,
        rows=rows,
        items=items,
    )
