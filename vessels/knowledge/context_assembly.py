"""
Context Assembly Pipeline

Fast multi-source context retrieval for servant tasks:
1. Project vector store (task-specific, ~10ms)
2. Graph traversal (relational context, ~20ms)
3. Shared vector store (general knowledge, ~30ms if needed)
4. Ranking and combination (~10ms)

Target: <100ms total
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .graphiti_client import VesselsGraphitiClient
from .vector_stores import ProjectVectorStore, SharedVectorStore

logger = logging.getLogger(__name__)


@dataclass
class ContextSource:
    """A single piece of context from a source"""
    text: str
    source: str  # "project_vectors", "graph", "shared_vectors"
    similarity: float
    metadata: Dict[str, Any]
    score: float = 0.0  # Combined score after ranking


class ContextAssembler:
    """
    Assembles context for servant tasks within <100ms budget

    Multi-source retrieval with intelligent ranking:
    - Project vectors: High relevance, task-specific
    - Graph context: Relationship awareness, entity connections
    - Shared vectors: General knowledge fallback
    """

    def __init__(
        self,
        project_vector_store: ProjectVectorStore,
        graphiti_client: VesselsGraphitiClient,
        shared_vector_store: Optional[SharedVectorStore] = None
    ):
        """
        Initialize context assembler

        Args:
            project_vector_store: Project-specific vector store
            graphiti_client: Graphiti client for graph queries
            shared_vector_store: Optional shared knowledge store
        """
        self.project_store = project_vector_store
        self.graphiti = graphiti_client
        self.shared_store = shared_vector_store

        self.stats = {
            "total_assemblies": 0,
            "avg_time_ms": 0.0,
            "source_usage": {
                "project_vectors": 0,
                "graph": 0,
                "shared_vectors": 0
            }
        }

    async def assemble_context(self, task: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Assemble context for a task (async for parallel queries)

        Args:
            task: Task description / query
            max_results: Maximum number of context pieces

        Returns:
            Dict with assembled context and timing info
        """
        start_time = time.time()

        # Step 1: Query project vector store (FAST - ~10ms)
        project_docs = await self._query_project_vectors(task)

        # Step 2: Get related entities from graph (MEDIUM - ~20ms)
        graph_context = await self._get_graph_context(task, project_docs)

        # Step 3: Query shared store if insufficient results (SLOW - ~30ms)
        shared_docs = []
        if len(project_docs) < 3 and self.shared_store:
            shared_docs = await self._query_shared_vectors(task)

        # Step 4: Rank and combine (FAST - ~10ms)
        combined = self._rank_by_relevance(project_docs, graph_context, shared_docs)
        combined = combined[:max_results]

        elapsed_ms = (time.time() - start_time) * 1000

        # Update stats
        self._update_stats(elapsed_ms, len(project_docs), len(graph_context), len(shared_docs))

        return {
            "task": task,
            "context": [c.text for c in combined],
            "sources": [
                {
                    "text": c.text,
                    "source": c.source,
                    "similarity": c.similarity,
                    "score": c.score,
                    "metadata": c.metadata
                }
                for c in combined
            ],
            "assembly_time_ms": elapsed_ms,
            "source_counts": {
                "project": len(project_docs),
                "graph": len(graph_context),
                "shared": len(shared_docs)
            }
        }

    def assemble_context_sync(self, task: str, max_results: int = 10) -> Dict[str, Any]:
        """Synchronous version of assemble_context (for non-async code)"""
        start_time = time.time()

        # Step 1: Query project vector store
        project_docs = self._query_project_vectors_sync(task)

        # Step 2: Get graph context
        graph_context = self._get_graph_context_sync(task, project_docs)

        # Step 3: Query shared store if needed
        shared_docs = []
        if len(project_docs) < 3 and self.shared_store:
            shared_docs = self._query_shared_vectors_sync(task)

        # Step 4: Rank and combine
        combined = self._rank_by_relevance(project_docs, graph_context, shared_docs)
        combined = combined[:max_results]

        elapsed_ms = (time.time() - start_time) * 1000

        self._update_stats(elapsed_ms, len(project_docs), len(graph_context), len(shared_docs))

        return {
            "task": task,
            "context": [c.text for c in combined],
            "sources": [
                {
                    "text": c.text,
                    "source": c.source,
                    "similarity": c.similarity,
                    "score": c.score,
                    "metadata": c.metadata
                }
                for c in combined
            ],
            "assembly_time_ms": elapsed_ms,
            "source_counts": {
                "project": len(project_docs),
                "graph": len(graph_context),
                "shared": len(shared_docs)
            }
        }

    async def _query_project_vectors(self, query: str) -> List[ContextSource]:
        """Query project vector store"""
        results = self.project_store.query(query, top_k=5)
        return [
            ContextSource(
                text=r["text"],
                source="project_vectors",
                similarity=r["similarity"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]

    def _query_project_vectors_sync(self, query: str) -> List[ContextSource]:
        """Sync version of project vector query"""
        results = self.project_store.query(query, top_k=5)
        return [
            ContextSource(
                text=r["text"],
                source="project_vectors",
                similarity=r["similarity"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]

    async def _get_graph_context(self, query: str, docs: List[ContextSource]) -> List[ContextSource]:
        """Get related entities from graph"""
        # Extract entities mentioned in retrieved docs
        entities = self._extract_entities(docs)

        context_items = []

        for entity in entities[:5]:  # Limit to 5 entities
            try:
                # Query graph for neighbors
                neighbors = self.graphiti.get_neighbors(entity, max_depth=1)

                # Convert to context sources
                for rel_type, neighbor_list in neighbors.items():
                    for neighbor in neighbor_list[:2]:  # Max 2 per relationship type
                        text = self._format_graph_context(entity, rel_type, neighbor)
                        context_items.append(
                            ContextSource(
                                text=text,
                                source="graph",
                                similarity=0.8,  # High relevance for graph connections
                                metadata={
                                    "entity": entity,
                                    "relation": rel_type,
                                    "neighbor": neighbor
                                }
                            )
                        )

            except Exception as e:
                logger.error(f"Error querying graph for entity {entity}: {e}")

        return context_items

    def _get_graph_context_sync(self, query: str, docs: List[ContextSource]) -> List[ContextSource]:
        """Sync version of graph context retrieval"""
        entities = self._extract_entities(docs)
        context_items = []

        for entity in entities[:5]:
            try:
                neighbors = self.graphiti.get_neighbors(entity, max_depth=1)

                for rel_type, neighbor_list in neighbors.items():
                    for neighbor in neighbor_list[:2]:
                        text = self._format_graph_context(entity, rel_type, neighbor)
                        context_items.append(
                            ContextSource(
                                text=text,
                                source="graph",
                                similarity=0.8,
                                metadata={
                                    "entity": entity,
                                    "relation": rel_type,
                                    "neighbor": neighbor
                                }
                            )
                        )

            except Exception as e:
                logger.error(f"Error querying graph: {e}")

        return context_items

    async def _query_shared_vectors(self, query: str) -> List[ContextSource]:
        """Query shared vector store"""
        if not self.shared_store:
            return []

        results = self.shared_store.query(query, top_k=3)
        return [
            ContextSource(
                text=r["text"],
                source="shared_vectors",
                similarity=r["similarity"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]

    def _query_shared_vectors_sync(self, query: str) -> List[ContextSource]:
        """Sync version of shared vector query"""
        if not self.shared_store:
            return []

        results = self.shared_store.query(query, top_k=3)
        return [
            ContextSource(
                text=r["text"],
                source="shared_vectors",
                similarity=r["similarity"],
                metadata=r.get("metadata", {})
            )
            for r in results
        ]

    def _rank_by_relevance(self, *source_lists) -> List[ContextSource]:
        """
        Rank and combine context from multiple sources

        Scoring:
        - 0.5 * semantic_similarity
        - 0.3 * source_priority (project > graph > shared)
        - 0.2 * recency
        """
        all_sources = []
        for source_list in source_lists:
            all_sources.extend(source_list)

        # Source priority weights
        source_weights = {
            "project_vectors": 1.0,
            "graph": 0.9,
            "shared_vectors": 0.7
        }

        # Score each source
        for source in all_sources:
            source_weight = source_weights.get(source.source, 0.5)
            recency_weight = 1.0  # Could incorporate timestamp from metadata

            source.score = (
                0.5 * source.similarity +
                0.3 * source_weight +
                0.2 * recency_weight
            )

        # Sort by score
        all_sources.sort(key=lambda x: x.score, reverse=True)

        # Deduplicate (remove very similar texts)
        deduped = []
        seen_texts = set()

        for source in all_sources:
            # Simple deduplication by first 100 chars
            text_key = source.text[:100].lower()
            if text_key not in seen_texts:
                deduped.append(source)
                seen_texts.add(text_key)

        return deduped

    def _extract_entities(self, docs: List[ContextSource]) -> List[str]:
        """Extract entity mentions from documents"""
        entities = []

        for doc in docs:
            # Simple entity extraction from metadata
            if "entities" in doc.metadata:
                entities.extend(doc.metadata["entities"])

            # Could add NER here for more sophisticated extraction

        return list(set(entities))  # Deduplicate

    def _format_graph_context(self, entity: str, relation: str, neighbor: Any) -> str:
        """Format graph relationship as text"""
        # Simplified formatting - could be more sophisticated
        if isinstance(neighbor, dict):
            neighbor_str = neighbor.get("name", str(neighbor))
        else:
            neighbor_str = str(neighbor)

        return f"{entity} {relation} {neighbor_str}"

    def _update_stats(self, elapsed_ms: float, project_count: int, graph_count: int, shared_count: int):
        """Update performance statistics"""
        self.stats["total_assemblies"] += 1

        # Update average time (running average)
        n = self.stats["total_assemblies"]
        old_avg = self.stats["avg_time_ms"]
        self.stats["avg_time_ms"] = (old_avg * (n - 1) + elapsed_ms) / n

        # Update source usage
        if project_count > 0:
            self.stats["source_usage"]["project_vectors"] += 1
        if graph_count > 0:
            self.stats["source_usage"]["graph"] += 1
        if shared_count > 0:
            self.stats["source_usage"]["shared_vectors"] += 1

        # Log warning if too slow
        if elapsed_ms > 100:
            logger.warning(
                f"Slow context assembly: {elapsed_ms:.1f}ms "
                f"(project={project_count}, graph={graph_count}, shared={shared_count})"
            )
        else:
            logger.debug(f"Context assembled in {elapsed_ms:.1f}ms")

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.stats.copy()
