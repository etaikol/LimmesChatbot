"""Retrieval-Augmented Generation pipeline."""

from chatbot.rag.ingestion import ingest_paths, ingest_data_directory
from chatbot.rag.loaders import LOADER_REGISTRY, load_file, supported_extensions
from chatbot.rag.retriever import RAGRetriever
from chatbot.rag.vectorstore import (
    build_vectorstore,
    load_or_create_vectorstore,
    load_vectorstore,
)

__all__ = [
    "RAGRetriever",
    "ingest_paths",
    "ingest_data_directory",
    "build_vectorstore",
    "load_or_create_vectorstore",
    "load_vectorstore",
    "load_file",
    "LOADER_REGISTRY",
    "supported_extensions",
]
