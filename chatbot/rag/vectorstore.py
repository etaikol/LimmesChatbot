"""
Vector store utilities.

Default backend: Chroma (file-persistent, no extra services required).

To swap to pgvector or another store, replace the body of `_make_chroma`
and `load_or_create_vectorstore`. The rest of the code only depends on the
`langchain_core.vectorstores.VectorStore` interface.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# `langchain_chroma` is the modern import path. Falls back to community for
# environments still on the legacy package.
try:
    from langchain_chroma import Chroma
except ImportError:  # pragma: no cover
    from langchain_community.vectorstores import Chroma  # type: ignore

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from chatbot.exceptions import ConfigError, RetrievalError
from chatbot.logging_setup import logger
from chatbot.rag.ingestion import ingest_data_directory
from chatbot.settings import Settings, get_settings

COLLECTION = "documents"
META_FILE = "ingestion_meta.json"


# ── Embeddings ───────────────────────────────────────────────────────────────


def _build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    if not settings.openai_api_key:
        msg = (
            "OPENAI_API_KEY is missing - required for embeddings. "
            "Add it to your .env file (see .env.example). "
            "Get one at https://platform.openai.com/api-keys."
        )
        raise ConfigError(msg, user_message=msg)
    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key,
    )


# ── Chroma constructors ──────────────────────────────────────────────────────


def _make_chroma(settings: Settings) -> Chroma:
    return Chroma(
        collection_name=COLLECTION,
        embedding_function=_build_embeddings(settings),
        persist_directory=str(settings.vectorstore_dir),
    )


def load_vectorstore(settings: Settings | None = None) -> Optional[Chroma]:
    """Open an existing on-disk vector store. Returns None if empty."""
    settings = settings or get_settings()

    if not settings.vectorstore_dir.exists():
        return None

    try:
        store = _make_chroma(settings)
        count = store._collection.count()  # type: ignore[attr-defined]
        if count == 0:
            return None
        logger.info("Loaded vector store ({} embeddings)", count)
        return store
    except Exception as e:
        logger.warning("Could not open vector store at {}: {}", settings.vectorstore_dir, e)
        return None


def build_vectorstore(
    documents: list[Document],
    settings: Settings | None = None,
) -> Chroma:
    """Embed and persist a fresh batch of Documents."""
    settings = settings or get_settings()

    if not documents:
        raise RetrievalError("No documents to embed.")

    settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)
    store = _make_chroma(settings)
    store.add_documents(documents)

    _save_meta(settings, documents)
    logger.info(
        "Vector store built: {} chunks -> {}", len(documents), settings.vectorstore_dir
    )
    return store


def load_or_create_vectorstore(settings: Settings | None = None) -> Chroma:
    """Convenience: load existing store, or build one from `data/` if missing.

    Pure RAG retrievers should call this once at startup.
    """
    settings = settings or get_settings()

    existing = load_vectorstore(settings)
    if existing is not None and not _data_changed(settings):
        return existing

    if existing is not None and _data_changed(settings):
        logger.info("Source files changed since last ingest — rebuilding vector store")
        # Wipe and rebuild
        try:
            existing.delete_collection()  # type: ignore[attr-defined]
        except Exception:
            pass

    documents = ingest_data_directory(settings.data_dir, settings)

    if not documents:
        # Return an empty store so the engine still starts (the bot will
        # answer from the LLM alone). The retriever will return [].
        logger.warning(
            "No data ingested. The chatbot will answer without retrieval. "
            "Drop files into {} and re-run ingestion.",
            settings.data_dir,
        )
        settings.vectorstore_dir.mkdir(parents=True, exist_ok=True)
        return _make_chroma(settings)

    return build_vectorstore(documents, settings)


# ── Change detection ─────────────────────────────────────────────────────────


def _hash_data_dir(data_dir: Path) -> str:
    h = hashlib.sha256()
    if not data_dir.exists():
        return h.hexdigest()
    for p in sorted(data_dir.rglob("*")):
        if p.is_file():
            try:
                stat = p.stat()
                h.update(str(p.relative_to(data_dir)).encode())
                h.update(str(stat.st_size).encode())
                h.update(str(int(stat.st_mtime)).encode())
            except OSError:
                continue
    return h.hexdigest()


def _meta_path(settings: Settings) -> Path:
    return settings.vectorstore_dir / META_FILE


def _save_meta(settings: Settings, documents: list[Document]) -> None:
    meta: dict[str, Any] = {
        "data_hash": _hash_data_dir(settings.data_dir),
        "embedding_model": settings.embedding_model,
        "chunk_count": len(documents),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        _meta_path(settings).write_text(json.dumps(meta, indent=2))
    except OSError as e:
        logger.warning("Could not save vector store meta: {}", e)


def _load_meta(settings: Settings) -> dict[str, Any]:
    path = _meta_path(settings)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _data_changed(settings: Settings) -> bool:
    meta = _load_meta(settings)
    if not meta:
        return True
    if meta.get("embedding_model") != settings.embedding_model:
        return True
    return meta.get("data_hash") != _hash_data_dir(settings.data_dir)
