"""
Internationalization for the user-facing surface (widget, channels,
error messages).

The LLM itself already speaks every language we list here — this
package only translates the *chrome*: button labels, placeholders,
"thinking..." indicator, language picker, error toasts.

Add a new language by appending an entry to :data:`SUPPORTED_LANGUAGES`
and a row to :data:`MESSAGES`. Anything missing in a translation falls
back to English so partial coverage is safe.
"""

from chatbot.i18n.messages import (
    LanguageInfo,
    MESSAGES,
    SUPPORTED_LANGUAGES,
    get_language,
    get_messages,
    is_rtl,
    resolve_language,
)

__all__ = [
    "LanguageInfo",
    "MESSAGES",
    "SUPPORTED_LANGUAGES",
    "get_language",
    "get_messages",
    "is_rtl",
    "resolve_language",
]
