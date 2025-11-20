"""
Vessels Vector Embeddings

Provides semantic embeddings using sentence-transformers for:
- Project-specific knowledge
- Community-wide knowledge
- Semantic search and similarity

Replaces the hash-based vector approach with learned embeddings.
"""

import numpy as np
from typing import List, Union, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VesselsEmbedder:
    """
    Semantic embedding generator using sentence-transformers

    Uses all-MiniLM-L6-v2 model:
    - 384 dimensions
    - 80MB model size
    - Fast inference (~10ms per sentence)
    - Good balance of speed and quality for off-grid deployment
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", cache_dir: Optional[Path] = None):
        """
        Initialize embedder with specified model

        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
            cache_dir: Directory to cache model weights
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None

    @property
    def model(self):
        """Lazy-load model on first use"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(
                    self.model_name,
                    cache_folder=str(self.cache_dir) if self.cache_dir else None
                )
                logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
            except ImportError:
                logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
                raise
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                raise

        return self._model

    @property
    def embedding_dim(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed

        Returns:
            NumPy array of shape (embedding_dim,)
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim, dtype=np.float32)

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Error embedding text: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for multiple texts (batched for efficiency)

        Args:
            texts: List of input texts
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            NumPy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.zeros((0, self.embedding_dim), dtype=np.float32)

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Error embedding batch: {e}")
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity in range [-1, 1]
        """
        return cosine_similarity(embedding1, embedding2)

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and multiple embeddings

        Args:
            query_embedding: Query vector of shape (embedding_dim,)
            embeddings: Matrix of shape (n_docs, embedding_dim)

        Returns:
            Array of similarities of shape (n_docs,)
        """
        return batch_cosine_similarity(query_embedding, embeddings)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity in range [-1, 1]
    """
    # Normalize vectors
    vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-10)
    vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-10)

    # Dot product of normalized vectors
    return float(np.dot(vec1_norm, vec2_norm))


def batch_cosine_similarity(query: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query and multiple embeddings (vectorized)

    Args:
        query: Query vector of shape (embedding_dim,)
        embeddings: Matrix of shape (n_docs, embedding_dim)

    Returns:
        Array of similarities of shape (n_docs,)
    """
    # Normalize query
    query_norm = query / (np.linalg.norm(query) + 1e-10)

    # Normalize embeddings (per row)
    embeddings_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-10)

    # Dot product (matrix-vector multiplication)
    similarities = embeddings_norm @ query_norm

    return similarities


# Global embedder instance (lazy-loaded)
_global_embedder: Optional[VesselsEmbedder] = None


def get_embedder() -> VesselsEmbedder:
    """Get global embedder instance (singleton pattern)"""
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = VesselsEmbedder()
    return _global_embedder
