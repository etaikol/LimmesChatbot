"""
Centralized logging setup using Loguru.

Why Loguru? It gives us a single, easy-to-configure logger with structured
output, colors in the terminal, JSON output for production, and an "intercept"
handler that routes stdlib `logging` calls (used by FastAPI, LangChain, etc.)
through the same pipeline.

Usage:
    from chatbot.logging_setup import setup_logging, logger
    setup_logging(level="DEBUG")
    logger.info("Hello")

In modules, just do:
    from chatbot.logging_setup import logger
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# Re-export the loguru logger so other modules can do
#   from chatbot.logging_setup import logger
__all__ = ["logger", "setup_logging"]


class _InterceptHandler(logging.Handler):
    """Forward standard `logging` records to Loguru.

    LangChain, FastAPI, uvicorn and other libraries log via stdlib logging.
    Without this handler their logs would not appear alongside our own.
    """

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the original caller frame so the log line shows the *real*
        # source file/line, not this handler.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = False,
) -> None:
    """Configure Loguru sinks and intercept stdlib logging.

    Args:
        level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional file path to write logs to (rotated daily).
        json_format: When True, write structured JSON instead of pretty text.
    """
    # Reset Loguru's default handlers
    logger.remove()

    # Console sink
    if json_format:
        logger.add(
            sys.stderr,
            level=level,
            serialize=True,
            backtrace=True,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> "
                "- <level>{message}</level>"
            ),
        )

    # Optional file sink (always pretty/text, daily rotation, 14-day retention)
    if log_file:
        log_path = Path(log_file).expanduser().resolve()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_path,
            level=level,
            rotation="00:00",
            retention="14 days",
            compression="zip",
            enqueue=True,
            backtrace=True,
            diagnose=False,
            serialize=json_format,
        )

    # Route stdlib logging through Loguru
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Quiet down chatty libraries
    for noisy in ("httpx", "httpcore", "openai", "chromadb", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger.debug(
        "Logging configured (level={}, file={}, json={})", level, log_file, json_format
    )
