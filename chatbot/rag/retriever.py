"""
Thin wrapper around the vector store that exposes both a plain retrieval
helper (`retrieve`) and a LangChain `BaseRetriever` (`as_langchain_retriever`).

Supports hybrid search (vector + BM25) when enabled.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from chatbot.logging_setup import logger
from chatbot.rag.vectorstore import load_or_create_vectorstore
from chatbot.settings import Settings, get_settings


class RAGRetriever:
    """Pluggable retriever that wraps a vector store with optional hybrid search."""

    def __init__(self, vectorstore, k: int = 4, min_score: float = 0.0) -> None:
        self.vectorstore = vectorstore
        self.k = k
        self.min_score = min_score
        self._hybrid = None

    def enable_hybrid(self, settings: Settings) -> None:
        """Enable hybrid (vector + BM25) retrieval."""
        if not settings.hybrid_search_enabled:
            return
        try:
            from chatbot.rag.hybrid import HybridRetriever

            self._hybrid = HybridRetriever(
                vectorstore=self.vectorstore,
                k=self.k,
                min_score=self.min_score,
                vector_weight=settings.hybrid_vector_weight,
                bm25_weight=settings.hybrid_bm25_weight,
            )
            # Index existing documents for BM25
            try:
                docs = self.vectorstore.similarity_search("", k=10000)
                if docs:
                    self._hybrid.index_documents(docs)
                    logger.info(
                        "Hybrid search enabled: {} documents indexed for BM25",
                        len(docs),
                    )
                else:
                    logger.debug("Hybrid search: no documents to index")
            except Exception as e:
                # If similarity_search with empty query fails, try getting all docs
                logger.debug("BM25 indexing deferred: {}", e)
        except ImportError:
            logger.debug("Hybrid search not available")

    def retrieve(self, query: str, k: Optional[int] = None) -> list[Document]:
        if not query.strip():
            return []
        # Use hybrid if available
        if self._hybrid is not None:
            try:
                return self._hybrid.retrieve(query, k=k or self.k)
            except Exception as e:
                logger.warning("Hybrid retrieval failed, falling back to vector: {}", e)

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
        if self._hybrid is not None:
            return self._hybrid.as_langchain_retriever(k=k or self.k)
        return self.vectorstore.as_retriever(search_kwargs={"k": k or self.k})

    @classmethod
    def from_settings(cls, settings: Optional[Settings] = None) -> "RAGRetriever":
        s = settings or get_settings()
        store = load_or_create_vectorstore(s)
        retriever = cls(vectorstore=store, k=s.retrieval_k, min_score=s.retrieval_min_score)
        retriever.enable_hybrid(s)
        return retriever
