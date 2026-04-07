"""
Run the FastAPI server with uvicorn.

Examples:
    python -m scripts.serve
    python -m scripts.serve --host 127.0.0.1 --port 9000 --reload
"""

from __future__ import annotations

import argparse
import sys

from chatbot.logging_setup import setup_logging
from chatbot.settings import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the chatbot HTTP API.")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--reload", action="store_true", help="Hot-reload (dev only)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(level="DEBUG" if args.debug else settings.log_level)

    try:
        import uvicorn
    except ImportError:
        print("[error] uvicorn is not installed. Install with: pip install uvicorn[standard]")
        return 1

    uvicorn.run(
        "chatbot.api.app:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
        reload=args.reload,
        log_level=("debug" if args.debug else settings.log_level.lower()),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
