"""Knowledge base module for RAG-based retrieval."""

from support_agent.knowledge.retriever import KnowledgeRetriever
from support_agent.knowledge.embeddings import EmbeddingEngine

__all__ = ["KnowledgeRetriever", "EmbeddingEngine"]
