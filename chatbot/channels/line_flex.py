"""
LINE Flex Message builders.

Provides pre-built Flex Message templates for common chatbot responses:

- **Product cards** — display a product with image, title, price, and CTA.
- **Carousel** — swipeable row of up to 12 product/info cards.
- **Contact card** — business contact details with tap-to-call/email actions.
- **Quick replies** — suggestion chips below the message.

All builders return plain dicts ready to be passed as a LINE message
object inside the ``messages`` array of a reply/push request.

LINE Flex Message reference:
    https://developers.line.biz/en/docs/messaging-api/using-flex-messages/
"""

from __future__ import annotations

from typing import Any, Optional


# ── Helpers ──────────────────────────────────────────────────────────────────

def _text(text: str, **kwargs: Any) -> dict:
    """Flex text component."""
    obj: dict[str, Any] = {"type": "text", "text": text}
    obj.update(kwargs)
    return obj


def _button(label: str, action: dict, **kwargs: Any) -> dict:
    """Flex button component."""
    obj: dict[str, Any] = {
        "type": "button",
        "action": action,
        "style": kwargs.pop("style", "primary"),
        "height": kwargs.pop("height", "sm"),
    }
    obj.update(kwargs)
    return obj


def _uri_action(label: str, uri: str) -> dict:
    return {"type": "uri", "label": label, "uri": uri}


def _message_action(label: str, text: str) -> dict:
    return {"type": "message", "label": label, "text": text}


def _postback_action(label: str, data: str, display_text: str = "") -> dict:
    action: dict[str, str] = {"type": "postback", "label": label, "data": data}
    if display_text:
        action["displayText"] = display_text
    return action


# ── Bubble builders ──────────────────────────────────────────────────────────

def product_bubble(
    *,
    title: str,
    description: str = "",
    price: str = "",
    image_url: Optional[str] = None,
    action_label: str = "Learn more",
    action_text: str = "",
    action_uri: Optional[str] = None,
    color: str = "#1DB446",
) -> dict:
    """Build a single product card bubble.

    Parameters
    ----------
    title:        Product name.
    description:  Short description (max ~2 lines).
    price:        Price string, e.g. "₪440 – ₪550".
    image_url:    HTTPS image URL (must be publicly accessible).
    action_label: Button label.
    action_text:  If set, tapping sends this message back (message action).
    action_uri:   If set, tapping opens this URL (URI action).
    color:        Accent color hex.
    """
    hero: dict[str, Any] | None = None
    if image_url:
        hero = {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        }

    body_contents: list[dict] = [
        _text(title, weight="bold", size="xl", wrap=True),
    ]
    if description:
        body_contents.append(
            _text(description, size="sm", color="#666666",
                  wrap=True, margin="md")
        )
    if price:
        body_contents.append(
            _text(price, size="lg", weight="bold",
                  color=color, margin="md")
        )

    # Action: prefer URI over message action.
    if action_uri:
        action = _uri_action(action_label, action_uri)
    else:
        action = _message_action(action_label, action_text or title)

    footer_contents: list[dict] = [
        _button(action_label, action, color=color),
    ]

    bubble: dict[str, Any] = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": body_contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": footer_contents,
            "flex": 0,
        },
    }
    if hero:
        bubble["hero"] = hero

    return bubble


def contact_bubble(
    *,
    business_name: str,
    phone: str = "",
    whatsapp: str = "",
    email: str = "",
    website: str = "",
    address: str = "",
    color: str = "#1DB446",
) -> dict:
    """Build a contact-info card bubble with tap-to-call/email actions."""
    body_contents: list[dict] = [
        _text(business_name, weight="bold", size="lg", wrap=True),
        {"type": "separator", "margin": "md"},
    ]

    details: list[dict] = []
    if phone:
        details.append({
            "type": "box", "layout": "baseline", "spacing": "sm",
            "contents": [
                _text("Phone", size="sm", color="#aaaaaa", flex=2),
                _text(phone, size="sm", color="#666666", wrap=True, flex=5,
                      action=_uri_action("Call", f"tel:{phone.replace(' ', '').replace('-', '')}")),
            ],
        })
    if whatsapp:
        wa_num = whatsapp.replace(" ", "").replace("-", "").replace("+", "")
        details.append({
            "type": "box", "layout": "baseline", "spacing": "sm",
            "contents": [
                _text("WhatsApp", size="sm", color="#aaaaaa", flex=2),
                _text(whatsapp, size="sm", color="#666666", wrap=True, flex=5,
                      action=_uri_action("Chat", f"https://wa.me/{wa_num}")),
            ],
        })
    if email:
        details.append({
            "type": "box", "layout": "baseline", "spacing": "sm",
            "contents": [
                _text("Email", size="sm", color="#aaaaaa", flex=2),
                _text(email, size="sm", color="#666666", wrap=True, flex=5,
                      action=_uri_action("Email", f"mailto:{email}")),
            ],
        })
    if address:
        details.append({
            "type": "box", "layout": "baseline", "spacing": "sm",
            "contents": [
                _text("Address", size="sm", color="#aaaaaa", flex=2),
                _text(address, size="sm", color="#666666", wrap=True, flex=5),
            ],
        })

    if details:
        body_contents.append({
            "type": "box", "layout": "vertical", "margin": "md",
            "spacing": "sm", "contents": details,
        })

    bubble: dict[str, Any] = {"type": "bubble", "body": {
        "type": "box", "layout": "vertical", "contents": body_contents,
    }}

    # Add website button if available.
    if website:
        bubble["footer"] = {
            "type": "box", "layout": "vertical", "spacing": "sm",
            "contents": [
                _button("Visit Website", _uri_action("Website", website),
                        color=color),
            ],
            "flex": 0,
        }

    return bubble


# ── Container builders ───────────────────────────────────────────────────────

def carousel(bubbles: list[dict]) -> dict:
    """Wrap bubbles into a carousel container (max 12)."""
    return {
        "type": "carousel",
        "contents": bubbles[:12],
    }


# ── Message wrappers (ready for messages[] array) ───────────────────────────

def flex_message(alt_text: str, contents: dict) -> dict:
    """Wrap a Flex container (bubble or carousel) into a full message object."""
    return {
        "type": "flex",
        "altText": alt_text[:400],
        "contents": contents,
    }


def text_message(text: str) -> dict:
    """Plain text message object."""
    return {"type": "text", "text": text[:5000]}


def quick_reply_message(
    text: str,
    items: list[dict],
) -> dict:
    """Text message with quick reply buttons at the bottom.

    Each item in ``items`` should be:
        {"label": "...", "text": "..."} for message actions, or
        {"label": "...", "uri": "..."} for URI actions.
    """
    qr_items = []
    for item in items[:13]:  # LINE limit: 13 quick reply items
        if "uri" in item:
            action = _uri_action(item["label"], item["uri"])
        else:
            action = _message_action(item["label"], item.get("text", item["label"]))
        qr_items.append({"type": "action", "action": action})

    msg: dict[str, Any] = {"type": "text", "text": text[:5000]}
    if qr_items:
        msg["quickReply"] = {"items": qr_items}
    return msg
