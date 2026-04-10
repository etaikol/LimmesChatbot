"""
Thin wrapper around the vector store that exposes both a plain retrieval
helper (`retrieve`) and a LangChain `BaseRetriever` (`as_langchain_retriever`).
"""

from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from chatbot.logging_setup import logger
from chatbot.rag.vectorstore import load_or_create_vectorstore
from chatbot.settings import Settings, get_settings


class RAGRetriever:
    """Pluggable retriever that wraps a vector store."""

    def __init__(self, vectorstore, k: int = 4, min_score: float = 0.0) -> None:
        self.vectorstore = vectorstore
        self.k = k
        self.min_score = min_score

    def retrieve(self, query: str, k: Optional[int] = None) -> list[Document]:
        if not query.strip():
            return []
        try:
            if self.min_score > 0:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=k or self.k
                )
                return [doc for doc, score in results if score >= self.min_score]
            return self.vectorstore.similarity_search(query, k=k or self.k)
        except Exception as e:
            logger.warning("Retrieval failed for query={!r}: {}", query, e)
            return []

    def as_langchain_retriever(self, k: Optional[int] = None) -> BaseRetriever:
        return self.vectorstore.as_retriever(search_kwargs={"k": k or self.k})

    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "RAGRetriever":
        s = settings or get_settings()
        store = load_or_create_vectorstore(s)
        return cls(vectorstore=store, k=s.retrieval_k, min_score=s.retrieval_min_score)
