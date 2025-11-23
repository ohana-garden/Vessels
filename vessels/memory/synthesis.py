"""
Memory synthesis logic for the Gardener agent.

Merges duplicate or similar memories into higher-order "wisdom" nodes
to reduce redundancy and improve memory quality.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WisdomNode:
    """
    Higher-order knowledge synthesized from multiple memories.

    Represents a pattern or insight derived from merging similar memories.
    """
    id: str
    type: str = "wisdom"
    synthesized_from: List[str] = field(default_factory=list)  # Memory IDs
    pattern: str = ""
    confidence: float = 0.0
    evidence_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "synthesized_from": self.synthesized_from,
            "pattern": self.pattern,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags
        }


class MemorySynthesizer:
    """
    Synthesizes wisdom nodes from similar memories.

    Strategy:
    - Find semantic clusters using vector similarity
    - Merge similar memories into wisdom nodes
    - Preserve original memories in archive
    - Track synthesis lineage
    """

    def __init__(self, similarity_threshold: float = 0.95):
        """
        Initialize memory synthesizer.

        Args:
            similarity_threshold: Cosine similarity threshold for clustering
        """
        self.similarity_threshold = similarity_threshold
        self.synthesized_count = 0

    def find_semantic_clusters(
        self,
        memories: List[Dict[str, Any]],
        embeddings: Optional[Dict[str, np.ndarray]] = None
    ) -> List[List[Dict[str, Any]]]:
        """
        Find clusters of semantically similar memories.

        Args:
            memories: List of memory dictionaries
            embeddings: Optional dict of memory_id -> embedding vector

        Returns:
            List of memory clusters (each cluster is a list of memories)
        """
        if not embeddings:
            logger.warning("No embeddings provided, cannot cluster")
            return []

        if len(memories) < 2:
            return []

        # Extract memory IDs and their embeddings
        memory_ids = []
        embedding_vectors = []

        for memory in memories:
            memory_id = memory.get("id") or memory.get("memory_id")
            if memory_id in embeddings:
                memory_ids.append(memory_id)
                embedding_vectors.append(embeddings[memory_id])

        if len(embedding_vectors) < 2:
            return []

        # Use DBSCAN clustering based on cosine similarity
        try:
            from sklearn.cluster import DBSCAN

            # Convert to numpy array
            X = np.array(embedding_vectors)

            # DBSCAN with cosine metric
            # eps = 1 - similarity_threshold (cosine distance)
            eps = 1.0 - self.similarity_threshold
            clustering = DBSCAN(eps=eps, min_samples=2, metric='cosine').fit(X)

            # Group memories by cluster
            clusters = {}
            for idx, label in enumerate(clustering.labels_):
                if label == -1:  # Noise point
                    continue

                if label not in clusters:
                    clusters[label] = []

                # Find the memory corresponding to this index
                memory_id = memory_ids[idx]
                memory = next((m for m in memories if m.get("id") == memory_id or m.get("memory_id") == memory_id), None)
                if memory:
                    clusters[label].append(memory)

            return list(clusters.values())

        except ImportError:
            logger.warning("scikit-learn not available, using simple similarity")
            return self._simple_clustering(memories, memory_ids, embedding_vectors)

    def _simple_clustering(
        self,
        memories: List[Dict[str, Any]],
        memory_ids: List[str],
        embeddings: List[np.ndarray]
    ) -> List[List[Dict[str, Any]]]:
        """Fallback: simple pairwise similarity clustering."""
        clusters = []
        used = set()

        for i in range(len(embeddings)):
            if memory_ids[i] in used:
                continue

            cluster = [memories[i]]
            used.add(memory_ids[i])

            # Find similar memories
            for j in range(i + 1, len(embeddings)):
                if memory_ids[j] in used:
                    continue

                # Cosine similarity
                similarity = np.dot(embeddings[i], embeddings[j]) / (
                    np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[j])
                )

                if similarity >= self.similarity_threshold:
                    cluster.append(memories[j])
                    used.add(memory_ids[j])

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    def create_wisdom_node(
        self,
        cluster: List[Dict[str, Any]]
    ) -> WisdomNode:
        """
        Create a wisdom node from a cluster of similar memories.

        Args:
            cluster: List of similar memories

        Returns:
            WisdomNode synthesized from cluster
        """
        memory_ids = [m.get("id") or m.get("memory_id") for m in cluster]

        # Extract common patterns
        contents = [m.get("content", {}) for m in cluster]

        # Synthesize pattern (simple heuristic: most common content)
        # In production, could use LLM to generate summary
        pattern = self._extract_common_pattern(contents)

        # Aggregate tags
        all_tags = set()
        for memory in cluster:
            all_tags.update(memory.get("tags", []))

        # Calculate confidence based on cluster size
        confidence = min(len(cluster) / 10.0, 1.0)  # Max out at 10 memories

        wisdom = WisdomNode(
            id=str(uuid.uuid4()),
            synthesized_from=memory_ids,
            pattern=pattern,
            confidence=confidence,
            evidence_count=len(cluster),
            tags=list(all_tags)
        )

        self.synthesized_count += 1

        logger.info(f"Created wisdom node from {len(cluster)} memories: {pattern[:100]}")

        return wisdom

    def _extract_common_pattern(self, contents: List[Dict[str, Any]]) -> str:
        """
        Extract common pattern from memory contents.

        Simple heuristic: return most common content string.
        In production, use LLM to generate intelligent summary.
        """
        if not contents:
            return ""

        # If contents have "content" field, extract it
        content_strings = []
        for content in contents:
            if isinstance(content, dict):
                content_str = content.get("content", str(content))
            else:
                content_str = str(content)
            content_strings.append(content_str)

        # Return first one as representative (simple heuristic)
        # TODO: Use LLM to generate synthesis
        return content_strings[0] if content_strings else "Synthesized pattern"

    def synthesize_memories(
        self,
        memories: List[Dict[str, Any]],
        embeddings: Optional[Dict[str, np.ndarray]] = None,
        store_wisdom_callback: callable = None
    ) -> List[WisdomNode]:
        """
        Synthesize wisdom nodes from memories.

        Args:
            memories: List of memory dictionaries
            embeddings: Dict of memory_id -> embedding vector
            store_wisdom_callback: Optional callback to store wisdom nodes

        Returns:
            List of created wisdom nodes
        """
        self.synthesized_count = 0

        # Find clusters
        clusters = self.find_semantic_clusters(memories, embeddings)

        # Create wisdom nodes
        wisdom_nodes = []
        for cluster in clusters:
            wisdom = self.create_wisdom_node(cluster)
            wisdom_nodes.append(wisdom)

            if store_wisdom_callback:
                store_wisdom_callback(wisdom)

        logger.info(f"Synthesized {len(wisdom_nodes)} wisdom nodes from {len(memories)} memories")

        return wisdom_nodes
