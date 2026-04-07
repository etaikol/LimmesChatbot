"""
Build the RAG vector store from `data/`.

This always rebuilds the vector store from scratch — it's the explicit
"re-index everything" command. The engine itself detects file changes
on startup automatically (see `load_or_create_vectorstore`), so you only
need to run this when you want to force a clean rebuild or have just
added new files and want them embedded immediately.

Examples:
    python -m scripts.ingest
    python -m scripts.ingest --client limmes
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from chatbot.core.profile import ClientConfig
from chatbot.exceptions import ChatbotError
from chatbot.logging_setup import logger, setup_logging
from chatbot.rag.ingestion import ingest_data_directory
from chatbot.rag.vectorstore import build_vectorstore
from chatbot.settings import PROJECT_ROOT, get_settings


def _resolve(p: str) -> Path:
    """Resolve a string path relative to the project root."""
    path = Path(p).expanduser()
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ingest data into the vector store (rebuild from scratch)."
    )
    parser.add_argument("--client", help="Client id to take data_paths from.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="(deprecated) Kept for backwards compatibility — ingest always rebuilds.",
    )
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    _ = args.rebuild  # accepted but always-on

    settings = get_settings()
    setup_logging(level="DEBUG" if args.debug else settings.log_level)
    settings.ensure_dirs()

    # Decide which directories to ingest.
    if args.client:
        try:
            client = ClientConfig.load(args.client)
        except ChatbotError as e:
            logger.error("Could not load client '{}': {}", args.client, e)
            print(f"\n[error] {e.user_message}\n        {e}")
            return 1
        data_paths = [_resolve(p) for p in client.data_paths]
        logger.info("Using data paths from client '{}': {}", args.client, data_paths)
    else:
        data_paths = [settings.data_dir]

    # Always wipe — explicit rebuild from scratch.
    if settings.vectorstore_dir.exists():
        logger.info("Removing existing vector store at {}", settings.vectorstore_dir)
        shutil.rmtree(settings.vectorstore_dir)

    # Walk every data directory and collect chunks.
    all_chunks = []
    for path in data_paths:
        all_chunks.extend(ingest_data_directory(path, settings))

    if not all_chunks:
        logger.warning("Nothing to ingest. Add files under one of: {}", data_paths)
        print(
            f"\n[warning] No supported files found.\n"
            f"          Drop documents into one of: {[str(p) for p in data_paths]}"
        )
        return 0

    try:
        build_vectorstore(all_chunks, settings)
    except ChatbotError as e:
        logger.error("Failed to build vector store: {}", e)
        print(f"\n[error] {e.user_message}\n        {e}")
        return 1

    print(f"\nIndexed {len(all_chunks)} chunks into {settings.vectorstore_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
