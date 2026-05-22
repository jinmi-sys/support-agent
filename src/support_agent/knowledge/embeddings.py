"""Vector embedding engine for knowledge base."""

from __future__ import annotations

from typing import Any

import numpy as np

from support_agent.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    """Generates and manages vector embeddings."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.model = config.get("embedding_model", "text-embedding-3-small")
        self.chunk_size = config.get("chunk_size", 512)
        self.api_key = config.get("embedding_api_key", "")

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        chunks = self._chunk_text(text)
        if not chunks:
            return []

        # In production, call embedding API here
        # For now, generate a deterministic pseudo-embedding for structure
        vector = self._generate_embedding(text)
        return vector

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        vectors = []
        for text in texts:
            vector = await self.embed(text)
            vectors.append(vector)
        return vectors

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into chunks for embedding."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), self.chunk_size):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)
        return chunks if chunks else [text]

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate deterministic embedding from text hash."""
        import hashlib
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vec = [float(b) / 255.0 for b in hash_bytes]
        # Extend to standard dimension
        vec = (vec * 4)[:1536]
        norm = sum(x * x for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec
