"""
File loaders for RAG ingestion.

Supports:
    .pdf            — PyPDFLoader (langchain-community)
    .txt / .md      — TextLoader (UTF-8)
    .html / .htm    — BeautifulSoup → plain text
    .docx           — Docx2txtLoader (langchain-community)
    .csv            — CSVLoader (langchain-community)
    .json / .jsonl  — JSONLoader (langchain-community)

Add your own by registering a callable in `LOADER_REGISTRY`. The function
signature is `(path: Path) -> list[langchain_core.documents.Document]`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from langchain_core.documents import Document

from chatbot.exceptions import IngestionError
from chatbot.logging_setup import logger

LoaderFn = Callable[[Path], list[Document]]


# ── Individual loaders ───────────────────────────────────────────────────────


def _load_pdf(path: Path) -> list[Document]:
    from langchain_community.document_loaders import PyPDFLoader

    docs = PyPDFLoader(str(path)).load()
    for d in docs:
        d.metadata["source"] = path.name
        d.metadata["file_type"] = "pdf"
    return docs


def _load_text(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [
        Document(
            page_content=text,
            metadata={"source": path.name, "file_type": path.suffix.lstrip(".")},
        )
    ]


def _load_html(path: Path) -> list[Document]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as e:  # pragma: no cover
        raise IngestionError(
            "HTML loader requires beautifulsoup4. Install: pip install beautifulsoup4"
        ) from e

    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "html.parser")
    # Strip script/style noise
    for s in soup(["script", "style", "noscript"]):
        s.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return [
        Document(
            page_content=text,
            metadata={"source": path.name, "file_type": "html"},
        )
    ]


def _load_docx(path: Path) -> list[Document]:
    try:
        from langchain_community.document_loaders import Docx2txtLoader
    except ImportError as e:  # pragma: no cover
        raise IngestionError(
            "DOCX loader requires docx2txt. Install: pip install docx2txt"
        ) from e

    docs = Docx2txtLoader(str(path)).load()
    for d in docs:
        d.metadata["source"] = path.name
        d.metadata["file_type"] = "docx"
    return docs


def _load_csv(path: Path) -> list[Document]:
    from langchain_community.document_loaders import CSVLoader

    docs = CSVLoader(str(path), encoding="utf-8").load()
    for d in docs:
        d.metadata["source"] = path.name
        d.metadata["file_type"] = "csv"
    return docs


def _load_json(path: Path) -> list[Document]:
    # Treat JSON as raw text for the simplest path. For structured loading
    # the user can write their own loader and register it.
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [
        Document(
            page_content=text,
            metadata={"source": path.name, "file_type": path.suffix.lstrip(".")},
        )
    ]


# ── Registry ─────────────────────────────────────────────────────────────────

LOADER_REGISTRY: dict[str, LoaderFn] = {
    ".pdf": _load_pdf,
    ".txt": _load_text,
    ".md": _load_text,
    ".markdown": _load_text,
    ".html": _load_html,
    ".htm": _load_html,
    ".docx": _load_docx,
    ".csv": _load_csv,
    ".json": _load_json,
    ".jsonl": _load_json,
}


def supported_extensions() -> list[str]:
    return sorted(LOADER_REGISTRY.keys())


def load_file(path: Path) -> list[Document]:
    """Load a single file using the registry. Raises IngestionError on unknown extension."""
    ext = path.suffix.lower()
    loader = LOADER_REGISTRY.get(ext)
    if loader is None:
        raise IngestionError(f"No loader registered for {ext} ({path.name})")
    try:
        docs = loader(path)
    except IngestionError:
        raise
    except Exception as e:
        raise IngestionError(f"Failed to load {path.name}: {e}") from e

    logger.debug("Loaded {} -> {} document(s)", path.name, len(docs))
    return docs
