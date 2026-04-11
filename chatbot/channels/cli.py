"""
Interactive command-line channel.

Run from a terminal:

    python -m scripts.chat                # uses ACTIVE_CLIENT from .env
    python -m scripts.chat --client limmes

Type `quit`, `exit`, or hit Ctrl-C to leave. Type `clear` to reset history.
Type `sources` to print the most recent retrieval citations.
"""

from __future__ import annotations

import sys

from chatbot.core.engine import Chatbot
from chatbot.exceptions import ChatbotError
from chatbot.i18n import SUPPORTED_LANGUAGE_CODES
from chatbot.i18n.detect import detect_language
from chatbot.logging_setup import logger


class CLIChannel:
    """Pretty-printed REPL for the local terminal."""

    PROMPT = "\nyou > "

    def __init__(self, bot: Chatbot, session_id: str = "cli") -> None:
        self.bot = bot
        self.session_id = session_id

    # ── UI helpers ──────────────────────────────────────────────────────────

    def _banner(self) -> None:
        bar = "═" * 60
        print(bar)
        print(f"  {self.bot.profile.client.name}")
        print(f"  personality: {self.bot.profile.personality.name}")
        print(f"  language:    {self.bot.profile.client.language_primary}")
        print(f"  model:       {self.bot.settings.llm_model}")
        print(bar)
        print(f"\nbot > {self.bot.greet()}")
        print("\nCommands:  quit | clear | sources")

    def _print_response(self, answer: str) -> None:
        print(f"\nbot > {answer}")

    def _print_sources(self, sources) -> None:
        if not sources:
            print("(no sources retrieved)")
            return
        print("\nsources:")
        for i, s in enumerate(sources, 1):
            page = f" p.{s.page}" if s.page is not None else ""
            print(f"  {i}. {s.source}{page}")

    # ── Main loop ───────────────────────────────────────────────────────────

    def run(self) -> int:
        self._banner()
        last_sources = []

        while True:
            try:
                question = input(self.PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                print("\nbye!")
                return 0

            if not question:
                continue

            cmd = question.lower()
            if cmd in ("quit", "exit", ":q"):
                print("bye!")
                return 0
            if cmd == "clear":
                self.bot.reset(self.session_id)
                print("(history cleared)")
                continue
            if cmd == "sources":
                self._print_sources(last_sources)
                continue

            try:
                language = detect_language(question, supported=SUPPORTED_LANGUAGE_CODES)
                resp = self.bot.ask(
                    question, session_id=self.session_id, language=language
                )
            except ChatbotError as e:
                print(f"\n[error] {e.user_message}")
                continue
            except Exception as e:  # pragma: no cover
                logger.exception("CLI error: {}", e)
                print(f"\n[error] {e}")
                continue

            self._print_response(resp.answer)
            last_sources = resp.sources

        return 0


def run_cli(client_id: str | None = None) -> int:
    bot = Chatbot.from_client(client_id) if client_id else Chatbot.from_env()
    return CLIChannel(bot).run()


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run_cli())
