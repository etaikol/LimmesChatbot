"""
Lightweight, dependency-free language detection.

Why a custom detector instead of `langdetect` / `langid` / `fasttext`?

* Zero extra dependencies — works in the slim Docker image.
* Deterministic and ~constant-time on short messages (chat-sized input).
* Tuned for the languages the template actually serves
  (see :data:`chatbot.i18n.SUPPORTED_LANGUAGES`).
* Most of those languages live in their own Unicode block, so a single
  pass over the characters is enough to be ~100% accurate. Latin-script
  languages get a small stop-word disambiguator.

The detector is intentionally **conservative**: when it isn't confident
it returns ``None`` so the caller can fall back to the prior turn's
language, an explicit user hint, or the client default — never a wrong
guess that the LLM would obey verbatim.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

# ── Script → language mapping ────────────────────────────────────────────────
#
# Each branch in ``_classify`` corresponds to a Unicode block (or set of
# blocks) that uniquely identifies a language family. ``"latin"`` is a
# pseudo-bucket — it requires a second pass (stop-word matching) to
# decide which Latin-script language is in use.

# Farsi-specific letters that don't appear in standard Arabic. Seeing
# any of these flips an Arabic-block character into Farsi.
_FARSI_MARKERS = frozenset({
    0x067E,  # پ  pe
    0x0686,  # چ  che
    0x0698,  # ژ  zhe
    0x06AF,  # گ  gaf
    0x06CC,  # ی  farsi yeh
    0x06A9,  # ک  keheh
})


def _classify(ch: str) -> Optional[str]:
    """Map a single character to a language code (or ``"latin"``)."""
    cp = ord(ch)

    # Hebrew
    if 0x0590 <= cp <= 0x05FF:
        return "he"

    # Thai
    if 0x0E00 <= cp <= 0x0E7F:
        return "th"

    # Devanagari (Hindi, Marathi, …)
    if 0x0900 <= cp <= 0x097F:
        return "hi"

    # Cyrillic (Russian, Ukrainian, Bulgarian, …)
    if 0x0400 <= cp <= 0x052F:
        return "ru"

    # Hangul → Korean
    if 0xAC00 <= cp <= 0xD7AF or 0x1100 <= cp <= 0x11FF:
        return "ko"

    # Hiragana / Katakana → Japanese (kana is Japanese-only)
    if 0x3040 <= cp <= 0x309F or 0x30A0 <= cp <= 0x30FF:
        return "ja"

    # CJK ideographs — default to Chinese, but ``detect_language``
    # will redirect these to Japanese/Korean if kana/hangul are also
    # present in the same string.
    if (
        0x4E00 <= cp <= 0x9FFF
        or 0x3400 <= cp <= 0x4DBF
        or 0x20000 <= cp <= 0x2A6DF
    ):
        return "zh"

    # Arabic script blocks (incl. presentation forms used by some keyboards)
    if (
        0x0600 <= cp <= 0x06FF
        or 0x0750 <= cp <= 0x077F
        or 0x08A0 <= cp <= 0x08FF
        or 0xFB50 <= cp <= 0xFDFF
        or 0xFE70 <= cp <= 0xFEFF
    ):
        return "fa" if cp in _FARSI_MARKERS else "ar"

    # Latin (basic + extended A/B + IPA)
    if (
        0x0041 <= cp <= 0x005A
        or 0x0061 <= cp <= 0x007A
        or 0x00C0 <= cp <= 0x024F
    ):
        return "latin"

    return None


# ── Latin-script disambiguation ──────────────────────────────────────────────
#
# Cheap, deterministic stop-word matching. Lists are intentionally short:
# only the highest-frequency function words, where one or two hits is
# usually enough to break a tie. English is also the safe fallback when
# nothing matches, since it's the lingua franca of the template.

_LATIN_STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset({
        "the", "is", "are", "was", "were", "you", "i", "and", "to", "of",
        "in", "it", "that", "this", "what", "how", "do", "does", "have",
        "not", "with", "on", "my", "your", "we", "they", "for", "be",
        "can", "hello", "hi", "thanks", "please",
    }),
    "fr": frozenset({
        "le", "la", "les", "et", "est", "vous", "je", "de", "une", "un",
        "pas", "que", "qui", "dans", "ce", "cette", "pour", "avec", "sur",
        "des", "du", "mes", "mon", "bonjour", "merci", "oui", "non",
    }),
    "es": frozenset({
        "el", "la", "los", "las", "y", "es", "tú", "tu", "yo", "de", "una",
        "un", "no", "que", "para", "con", "por", "mi", "muy", "hola",
        "gracias", "sí", "buenos", "días",
    }),
    "de": frozenset({
        "der", "die", "das", "und", "ist", "sie", "ich", "von", "ein",
        "eine", "nicht", "mit", "auf", "wir", "auch", "bin", "hallo",
        "danke", "bitte", "ja", "nein",
    }),
}

_WORD_RE = re.compile(r"[A-Za-z\u00C0-\u024F]+")


def _detect_latin(text: str) -> Optional[str]:
    """Pick the best Latin-script language by stop-word frequency.

    Returns ``None`` when no stop-word at all matches; the caller is
    expected to default to English (or a configured fallback) in that
    case.
    """
    words = _WORD_RE.findall(text.lower())
    if not words:
        return None

    scores = {lang: 0 for lang in _LATIN_STOPWORDS}
    for w in words:
        for lang, stop in _LATIN_STOPWORDS.items():
            if w in stop:
                scores[lang] += 1

    best_lang, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0:
        return None
    return best_lang


# ── Public API ───────────────────────────────────────────────────────────────


def detect_language(
    text: str,
    *,
    supported: Optional[Iterable[str]] = None,
    min_chars: int = 2,
    confidence: float = 0.5,
) -> Optional[str]:
    """Best-effort language detection for a chat message.

    Parameters
    ----------
    text:
        The user's message. Whitespace, digits and punctuation are
        ignored — only "scriptable" characters count.
    supported:
        Optional whitelist of ISO-639-1 codes. If the detected language
        is not in this set, return ``None``.
    min_chars:
        Minimum number of scriptable characters required to attempt a
        guess. Below this we return ``None``.
    confidence:
        Fraction of scriptable characters that the dominant script must
        cover. Below this threshold we return ``None`` (mixed scripts).

    Returns
    -------
    An ISO-639-1 code, or ``None`` when detection is not confident.
    Callers should treat ``None`` as "use the previous language".
    """
    if not text:
        return None

    counts: dict[str, int] = {}
    for ch in text:
        cls = _classify(ch)
        if cls is not None:
            counts[cls] = counts.get(cls, 0) + 1

    total = sum(counts.values())
    if total < min_chars:
        return None

    # Resolve CJK ambiguity: kana/hangul beats bare ideographs.
    if "ja" in counts and "zh" in counts:
        counts["ja"] += counts.pop("zh")
    if "ko" in counts and "zh" in counts:
        counts["ko"] += counts.pop("zh")

    best_lang, best_count = max(counts.items(), key=lambda kv: kv[1])
    if best_count / total < confidence:
        return None

    if best_lang == "latin":
        best_lang = _detect_latin(text)
        if best_lang is None:
            return None

    if supported is not None:
        allowed = {code.lower() for code in supported}
        if best_lang not in allowed:
            # Don't lie — better to admit "not sure" than to force a wrong
            # language onto the model.
            return None

    return best_lang


__all__ = ["detect_language"]
