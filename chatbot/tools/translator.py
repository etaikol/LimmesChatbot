"""
Translation helper that uses the configured LLM (no extra service required).

Two ways to use it:

    # 1. Translate a string
    from chatbot.tools.translator import Translator
    t = Translator()
    he = t.translate("Hello, how can I help you?", target="he")

    # 2. Auto-translate a chat reply if the user wrote in another language
    #    (handled in the engine via the personality `language_primary`)

For Hebrew, OpenAI's gpt-4o-mini already handles the language natively;
this helper exists for cases where you want to force a target language.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.output_parsers import StrOutputParser

from chatbot.core.prompts import TRANSLATE_TEMPLATE
from chatbot.llm.providers import LLMProvider
from chatbot.logging_setup import logger
from chatbot.settings import Settings, get_settings


# ISO-639-1 -> human label (used in prompts).
LANGUAGE_NAMES = {
    "en": "English",
    "he": "Hebrew",
    "ar": "Arabic",
    "ru": "Russian",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "tr": "Turkish",
}


class Translator:
    """LLM-backed translator. Reuses the project's LLM provider."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.llm = LLMProvider.from_settings(self.settings)
        self.chain = TRANSLATE_TEMPLATE | self.llm.client | StrOutputParser()

    def translate(self, text: str, target: str = "en") -> str:
        """Translate `text` into `target` (ISO-639-1 code or full name)."""
        if not text.strip():
            return text

        target_label = LANGUAGE_NAMES.get(target.lower(), target)
        logger.debug("Translating -> {}", target_label)

        try:
            return self.chain.invoke({"text": text, "target_language": target_label})
        except Exception as e:
            logger.exception("Translation failed: {}", e)
            return text  # Fail open: return original text rather than crash
