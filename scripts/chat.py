"""
CLI chatbot launcher.

Examples:
    python -m scripts.chat
    python -m scripts.chat --client limmes
    python -m scripts.chat --client limmes --debug
"""

from __future__ import annotations

import argparse
import sys

from chatbot.channels.cli import CLIChannel
from chatbot.core.engine import Chatbot
from chatbot.exceptions import ChatbotError
from chatbot.logging_setup import logger, setup_logging
from chatbot.settings import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the chatbot in the terminal.")
    parser.add_argument(
        "--client",
        help="Client id (matches config/clients/<id>.yaml). Defaults to ACTIVE_CLIENT.",
    )
    parser.add_argument("--session", default="cli", help="Session id (default: 'cli')")
    parser.add_argument("--debug", action="store_true", help="Enable DEBUG logging")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(
        level="DEBUG" if args.debug else settings.log_level,
        log_file=settings.log_file,
        json_format=settings.log_format == "json",
    )
    settings.ensure_dirs()

    try:
        bot = (
            Chatbot.from_client(args.client, settings=settings)
            if args.client
            else Chatbot.from_env()
        )
    except ChatbotError as e:
        logger.error("Failed to start chatbot: {}", e)
        print(f"\n[error] {e.user_message}")
        if str(e) and str(e) != e.user_message:
            print(f"        {e}")
        return 1
    except Exception as e:
        logger.exception("Failed to start chatbot")
        print(f"\n[error] {type(e).__name__}: {e}")
        return 1

    return CLIChannel(bot, session_id=args.session).run()


if __name__ == "__main__":
    sys.exit(main())
