"""
End-to-end ingestion: walk a directory, load every supported file, split into
chunks, and return Documents ready to be embedded.

Usage:
    from chatbot.rag.ingestion import ingest_data_directory
    docs = ingest_data_directory(Path("data"), settings)
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from chatbot.exceptions import IngestionError
from chatbot.logging_setup import logger
from chatbot.rag.loaders import load_file, supported_extensions
from chatbot.settings import Settings, get_settings


def _build_splitter(settings: Settings) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        add_start_index=True,
    )


def ingest_paths(
    paths: Iterable[Path],
    settings: Settings | None = None,
) -> list[Document]:
    """Load and split a list of file paths into chunked Documents."""
    settings = settings or get_settings()
    splitter = _build_splitter(settings)
    # Materialize so we can both iterate and count without consuming twice.
    paths_list = list(paths)

    chunks: list[Document] = []
    failures: list[str] = []
    for path in paths_list:
        try:
            docs = load_file(path)
        except IngestionError as e:
            failures.append(f"{path.name}: {e}")
            logger.warning("Skipping {}: {}", path.name, e)
            continue

        split = splitter.split_documents(docs)
        for chunk in split:
            chunk.metadata.setdefault("source", path.name)
        chunks.extend(split)
        logger.info("Ingested {} -> {} chunks", path.name, len(split))

    if failures and not chunks:
        raise IngestionError(
            "All files failed to load:\n" + "\n".join(failures)
        )

    logger.info("Total chunks: {} from {} file(s)", len(chunks), len(paths_list))
    return chunks


def ingest_data_directory(
    data_dir: Path,
    settings: Settings | None = None,
) -> list[Document]:
    """Recursively walk `data_dir` and ingest every supported file.

    Files with unsupported extensions are silently ignored. The function
    returns an empty list (rather than raising) when no data is found, so
    the caller can decide whether that is fatal.
    """
    if not data_dir.exists():
        logger.warning("Data directory does not exist: {}", data_dir)
        return []

    exts = set(supported_extensions())
    files = sorted(p for p in data_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts)

    if not files:
        logger.warning(
            "No supported files in {}. Supported extensions: {}",
            data_dir,
            ", ".join(sorted(exts)),
        )
        return []

    logger.info("Ingesting {} file(s) from {}", len(files), data_dir)
    return ingest_paths(files, settings=settings)
