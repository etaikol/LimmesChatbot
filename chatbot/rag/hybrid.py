"""
Hybrid search — combines vector (semantic) search with keyword (BM25) search.

Better for exact product names, codes, and specific terms that embedding
models sometimes miss. The final ranking merges results from both sources
using Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any, Optional

from langchain_core.documents import Document

from chatbot.logging_setup import logger


class BM25Index:
    """Simple in-memory BM25 index for keyword search.

    No external dependencies required. Sufficient for catalogs up to
    ~50k documents. For larger corpora, swap in Elasticsearch or similar.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._documents: list[Document] = []
        self._doc_freqs: Counter = Counter()
        self._doc_lengths: list[int] = []
        self._avg_dl: float = 0.0
        self._term_freqs: list[Counter] = []
        self._n: int = 0

    def index(self, documents: list[Document]) -> None:
        """Build the BM25 index from a list of documents."""
        self._documents = documents
        self._n = len(documents)
        self._doc_freqs = Counter()
        self._term_freqs = []
        self._doc_lengths = []

        for doc in documents:
            tokens = self._tokenize(doc.page_content)
            tf = Counter(tokens)
            self._term_freqs.append(tf)
            self._doc_lengths.append(len(tokens))
            for term in set(tokens):
                self._doc_freqs[term] += 1

        total_length = sum(self._doc_lengths)
        self._avg_dl = total_length / self._n if self._n else 1.0
        logger.debug("[bm25] Indexed {} documents", self._n)

    def search(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        """Search the index and return (document, score) pairs."""
        if not self._documents:
            return []

        tokens = self._tokenize(query)
        scores: list[float] = [0.0] * self._n

        for term in tokens:
            if term not in self._doc_freqs:
                continue

            df = self._doc_freqs[term]
            idf = math.log((self._n - df + 0.5) / (df + 0.5) + 1)

            for i in range(self._n):
                tf = self._term_freqs[i].get(term, 0)
                if tf == 0:
                    continue
                dl = self._doc_lengths[i]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * dl / self._avg_dl
                )
                scores[i] += idf * (numerator / denominator)

        # Get top-k
        indexed = [(self._documents[i], scores[i]) for i in range(self._n) if scores[i] > 0]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed[:k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        # Keep alphanumeric and common non-Latin scripts
        tokens = re.findall(r"[\w\u0590-\u05FF\u0E00-\u0E7F\u4E00-\u9FFF\u3040-\u30FF]+", text)
        return tokens


class HybridRetriever:
    """Combines vector similarity search with BM25 keyword search.

    Uses Reciprocal Rank Fusion to merge the two result sets.
    """

    def __init__(
        self,
        vectorstore: Any,
        k: int = 4,
        min_score: float = 0.0,
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
        rrf_k: int = 60,
    ) -> None:
        self.vectorstore = vectorstore
        self.k = k
        self.min_score = min_score
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k
        self.bm25 = BM25Index()
        self._indexed = False

    def index_documents(self, documents: list[Document]) -> None:
        """Build the BM25 index. Call after loading/creating the vectorstore."""
        self.bm25.index(documents)
        self._indexed = True

    def retrieve(self, query: str, k: Optional[int] = None) -> list[Document]:
        """Perform hybrid retrieval."""
        k = k or self.k
        if not query.strip():
            return []

        # Vector search
        vector_results = self._vector_search(query, k=k * 2)

        # BM25 search
        bm25_results = []
        if self._indexed:
            bm25_results = self.bm25.search(query, k=k * 2)

        if not bm25_results:
            # Fall back to vector-only
            return [doc for doc, _ in vector_results[:k]]

        # Reciprocal Rank Fusion
        fused = self._rrf_merge(vector_results, bm25_results, k)
        return fused

    def _vector_search(
        self, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        """Run vector similarity search."""
        try:
            if self.min_score > 0:
                results = self.vectorstore.similarity_search_with_relevance_scores(
                    query, k=k
                )
                return [(doc, score) for doc, score in results if score >= self.min_score]
            docs = self.vectorstore.similarity_search(query, k=k)
            return [(doc, 1.0) for doc in docs]
        except Exception as e:
            logger.warning("[hybrid] Vector search failed: {}", e)
            return []

    def _rrf_merge(
        self,
        vector_results: list[tuple[Document, float]],
        bm25_results: list[tuple[Document, float]],
        k: int,
    ) -> list[Document]:
        """Merge two ranked lists using Reciprocal Rank Fusion."""
        doc_scores: dict[str, float] = defaultdict(float)
        doc_map: dict[str, Document] = {}

        # Score vector results
        for rank, (doc, _) in enumerate(vector_results):
            doc_id = self._doc_id(doc)
            doc_scores[doc_id] += self.vector_weight * (1.0 / (self.rrf_k + rank + 1))
            doc_map[doc_id] = doc

        # Score BM25 results
        for rank, (doc, _) in enumerate(bm25_results):
            doc_id = self._doc_id(doc)
            doc_scores[doc_id] += self.bm25_weight * (1.0 / (self.rrf_k + rank + 1))
            doc_map[doc_id] = doc

        # Sort by fused score
        sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
        return [doc_map[did] for did in sorted_ids[:k]]

    @staticmethod
    def _doc_id(doc: Document) -> str:
        """Create a stable ID for deduplication."""
        content = doc.page_content[:200]
        source = doc.metadata.get("source", "")
        return f"{source}:{hash(content)}"

    def as_langchain_retriever(self, k: Optional[int] = None):
        """Return a LangChain-compatible retriever wrapper."""
        return HybridLangChainRetriever(self, k=k or self.k)


class HybridLangChainRetriever:
    """Thin wrapper to make HybridRetriever compatible with LangChain chains."""

    def __init__(self, hybrid: HybridRetriever, k: int = 4) -> None:
        self._hybrid = hybrid
        self._k = k

    def invoke(self, query: str, **kwargs: Any) -> list[Document]:
        return self._hybrid.retrieve(query, k=self._k)

    def get_relevant_documents(self, query: str) -> list[Document]:
        return self._hybrid.retrieve(query, k=self._k)

    # LangChain BaseRetriever interface
    async def ainvoke(self, query: str, **kwargs: Any) -> list[Document]:
        return self._hybrid.retrieve(query, k=self._k)
