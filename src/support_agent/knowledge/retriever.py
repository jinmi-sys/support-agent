"""RAG-based knowledge retrieval engine."""

from __future__ import annotations

from typing import Any

from support_agent.knowledge.embeddings import EmbeddingEngine
from support_agent.utils.logger import get_logger

logger = get_logger(__name__)


class KnowledgeRetriever:
    """Retrieves relevant knowledge base articles using semantic search."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.embeddings = EmbeddingEngine(config)
        self.top_k = config.get("top_k", 5)
        self._documents: list[dict[str, Any]] = []
        self._vectors: list[list[float]] = []

    async def load_documents(self, documents: list[dict[str, Any]]) -> None:
        """Load and index knowledge base documents."""
        self._documents = documents
        texts = [f"{doc.get('title', '')} {doc.get('content', '')}" for doc in documents]
        self._vectors = await self.embeddings.embed_batch(texts)
        logger.info("knowledge_loaded", count=len(documents))

    async def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        """Retrieve top-k relevant documents for a query."""
        k = top_k or self.top_k

        if not self._documents:
            logger.info("knowledge_empty", query=query[:50])
            return []

        query_vector = await self.embeddings.embed(query)
        scores = self._compute_similarity(query_vector)

        ranked = sorted(
            zip(self._documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )[:k]

        results = []
        for doc, score in ranked:
            results.append({
                **doc,
                "relevance_score": score,
            })

        logger.info(
            "knowledge_retrieved",
            query=query[:50],
            results=len(results),
            top_score=results[0]["relevance_score"] if results else 0,
        )
        return results

    def _compute_similarity(self, query_vector: list[float]) -> list[float]:
        """Compute cosine similarity between query and all documents."""
        scores = []
        for doc_vector in self._vectors:
            score = self._cosine_similarity(query_vector, doc_vector)
            scores.append(score)
        return scores

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
