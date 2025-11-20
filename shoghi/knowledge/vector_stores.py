"""
Shoghi Vector Stores

Provides project-specific and shared vector stores for semantic search:
- ProjectVectorStore: Per-servant task-specific knowledge (fast, isolated)
- SharedVectorStore: Community-wide knowledge (shared, deduplicated)

Uses NumPy for lightweight storage suitable for off-grid deployment.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

from .embeddings import get_embedder, batch_cosine_similarity

logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """A document in the vector store"""
    id: str
    text: str
    metadata: Dict[str, Any]
    created_at: str


class ProjectVectorStore:
    """
    Lightweight NumPy-based vector store for project-specific knowledge

    Fast, isolated, and suitable for servant-specific task knowledge.
    Stores embeddings as .npz files (compressed NumPy arrays).

    Target: <10ms query latency
    """

    def __init__(self, project_dir: Path):
        """
        Initialize vector store for a project

        Args:
            project_dir: Path to project directory (e.g., work_dir/projects/community/servant/)
        """
        self.project_dir = Path(project_dir)
        self.vectors_dir = self.project_dir / "vectors"
        self.vectors_file = self.vectors_dir / "embeddings.npz"
        self.metadata_file = self.vectors_dir / "metadata.json"

        self.embedder = get_embedder()

        # In-memory cache
        self._embeddings: Optional[np.ndarray] = None
        self._documents: Optional[List[VectorDocument]] = None

        # Create directories
        self.vectors_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load()

    def _load(self):
        """Load embeddings and metadata from disk"""
        if self.vectors_file.exists() and self.metadata_file.exists():
            try:
                # Load embeddings
                data = np.load(self.vectors_file)
                self._embeddings = data["embeddings"]

                # Load metadata
                with open(self.metadata_file, "r") as f:
                    metadata_list = json.load(f)
                    self._documents = [VectorDocument(**doc) for doc in metadata_list]

                logger.info(f"Loaded {len(self._documents)} documents from {self.project_dir.name}")
            except Exception as e:
                logger.error(f"Error loading vector store: {e}")
                self._embeddings = np.zeros((0, self.embedder.embedding_dim), dtype=np.float32)
                self._documents = []
        else:
            # Initialize empty
            self._embeddings = np.zeros((0, self.embedder.embedding_dim), dtype=np.float32)
            self._documents = []

    def _save(self):
        """Save embeddings and metadata to disk"""
        try:
            # Save embeddings (compressed)
            np.savez_compressed(self.vectors_file, embeddings=self._embeddings)

            # Save metadata
            with open(self.metadata_file, "w") as f:
                json.dump([asdict(doc) for doc in self._documents], f, indent=2)

            logger.debug(f"Saved {len(self._documents)} documents to {self.project_dir.name}")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def add(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ):
        """
        Add documents to the vector store

        Args:
            texts: List of text strings to add
            metadata: Optional list of metadata dicts (same length as texts)
            ids: Optional list of document IDs (generated if not provided)
        """
        if not texts:
            return

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{len(self._documents) + i}_{datetime.utcnow().timestamp()}" for i in range(len(texts))]

        # Default metadata
        if metadata is None:
            metadata = [{} for _ in texts]

        # Generate embeddings
        new_embeddings = self.embedder.embed_batch(texts, show_progress=False)

        # Create documents
        created_at = datetime.utcnow().isoformat()
        new_documents = [
            VectorDocument(
                id=doc_id,
                text=text,
                metadata=meta,
                created_at=created_at
            )
            for doc_id, text, meta in zip(ids, texts, metadata)
        ]

        # Append to existing
        if self._embeddings.size > 0:
            self._embeddings = np.vstack([self._embeddings, new_embeddings])
        else:
            self._embeddings = new_embeddings

        self._documents.extend(new_documents)

        # Save to disk
        self._save()

        logger.info(f"Added {len(texts)} documents to {self.project_dir.name}")

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents

        Args:
            query_text: Query string
            top_k: Number of top results to return
            min_similarity: Minimum similarity threshold

        Returns:
            List of dicts with keys: id, text, metadata, similarity
        """
        if not self._documents or self._embeddings.size == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedder.embed(query_text)

        # Compute similarities (vectorized)
        similarities = batch_cosine_similarity(query_embedding, self._embeddings)

        # Filter by minimum similarity
        valid_indices = np.where(similarities >= min_similarity)[0]

        if len(valid_indices) == 0:
            return []

        # Sort by similarity (descending)
        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]

        # Take top_k
        top_indices = sorted_indices[:top_k]

        # Build results
        results = []
        for idx in top_indices:
            doc = self._documents[idx]
            results.append({
                "id": doc.id,
                "text": doc.text,
                "metadata": doc.metadata,
                "similarity": float(similarities[idx]),
                "created_at": doc.created_at
            })

        return results

    def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        for i, doc in enumerate(self._documents):
            if doc.id == doc_id:
                return {
                    "id": doc.id,
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "created_at": doc.created_at,
                    "embedding": self._embeddings[i]
                }
        return None

    def delete(self, doc_id: str) -> bool:
        """Delete document by ID"""
        for i, doc in enumerate(self._documents):
            if doc.id == doc_id:
                # Remove from lists
                self._documents.pop(i)
                self._embeddings = np.delete(self._embeddings, i, axis=0)
                self._save()
                logger.info(f"Deleted document {doc_id} from {self.project_dir.name}")
                return True
        return False

    def count(self) -> int:
        """Get number of documents in store"""
        return len(self._documents)

    def clear(self):
        """Clear all documents"""
        self._embeddings = np.zeros((0, self.embedder.embedding_dim), dtype=np.float32)
        self._documents = []
        self._save()
        logger.info(f"Cleared all documents from {self.project_dir.name}")


class SharedVectorStore:
    """
    Shared vector store for community-wide knowledge

    Stores knowledge that is common across multiple servants:
    - Cultural protocols
    - Universal contacts
    - General procedures

    Backed by the same NumPy format as ProjectVectorStore, but located
    in a shared directory accessible to all servants.

    Target: <30ms query latency (slightly slower due to larger size)
    """

    def __init__(self, shared_dir: Path = Path("work_dir/shared")):
        """
        Initialize shared vector store

        Args:
            shared_dir: Path to shared directory
        """
        self.shared_dir = Path(shared_dir)
        self.vectors_dir = self.shared_dir / "vectors"
        self.vectors_file = self.vectors_dir / "shared_embeddings.npz"
        self.metadata_file = self.vectors_dir / "shared_metadata.json"

        self.embedder = get_embedder()

        # In-memory cache
        self._embeddings: Optional[np.ndarray] = None
        self._documents: Optional[List[VectorDocument]] = None

        # Create directories
        self.vectors_dir.mkdir(parents=True, exist_ok=True)

        # Load existing data
        self._load()

    def _load(self):
        """Load embeddings and metadata from disk"""
        if self.vectors_file.exists() and self.metadata_file.exists():
            try:
                # Load embeddings
                data = np.load(self.vectors_file)
                self._embeddings = data["embeddings"]

                # Load metadata
                with open(self.metadata_file, "r") as f:
                    metadata_list = json.load(f)
                    self._documents = [VectorDocument(**doc) for doc in metadata_list]

                logger.info(f"Loaded {len(self._documents)} documents from shared store")
            except Exception as e:
                logger.error(f"Error loading shared vector store: {e}")
                self._embeddings = np.zeros((0, self.embedder.embedding_dim), dtype=np.float32)
                self._documents = []
        else:
            # Initialize empty
            self._embeddings = np.zeros((0, self.embedder.embedding_dim), dtype=np.float32)
            self._documents = []

    def _save(self):
        """Save embeddings and metadata to disk"""
        try:
            # Save embeddings (compressed)
            np.savez_compressed(self.vectors_file, embeddings=self._embeddings)

            # Save metadata
            with open(self.metadata_file, "w") as f:
                json.dump([asdict(doc) for doc in self._documents], f, indent=2)

            logger.debug(f"Saved {len(self._documents)} documents to shared store")
        except Exception as e:
            logger.error(f"Error saving shared vector store: {e}")

    # Same methods as ProjectVectorStore
    def add(self, texts: List[str], metadata: Optional[List[Dict[str, Any]]] = None, ids: Optional[List[str]] = None):
        """Add documents to shared store"""
        if not texts:
            return

        if ids is None:
            ids = [f"shared_{len(self._documents) + i}_{datetime.utcnow().timestamp()}" for i in range(len(texts))]

        if metadata is None:
            metadata = [{} for _ in texts]

        new_embeddings = self.embedder.embed_batch(texts, show_progress=False)

        created_at = datetime.utcnow().isoformat()
        new_documents = [
            VectorDocument(id=doc_id, text=text, metadata=meta, created_at=created_at)
            for doc_id, text, meta in zip(ids, texts, metadata)
        ]

        if self._embeddings.size > 0:
            self._embeddings = np.vstack([self._embeddings, new_embeddings])
        else:
            self._embeddings = new_embeddings

        self._documents.extend(new_documents)
        self._save()

        logger.info(f"Added {len(texts)} documents to shared store")

    def query(self, query_text: str, top_k: int = 3, min_similarity: float = 0.0) -> List[Dict[str, Any]]:
        """Query shared store"""
        if not self._documents or self._embeddings.size == 0:
            return []

        query_embedding = self.embedder.embed(query_text)
        similarities = batch_cosine_similarity(query_embedding, self._embeddings)

        valid_indices = np.where(similarities >= min_similarity)[0]
        if len(valid_indices) == 0:
            return []

        sorted_indices = valid_indices[np.argsort(similarities[valid_indices])[::-1]]
        top_indices = sorted_indices[:top_k]

        results = []
        for idx in top_indices:
            doc = self._documents[idx]
            results.append({
                "id": doc.id,
                "text": doc.text,
                "metadata": doc.metadata,
                "similarity": float(similarities[idx]),
                "created_at": doc.created_at
            })

        return results

    def count(self) -> int:
        """Get number of documents"""
        return len(self._documents)
