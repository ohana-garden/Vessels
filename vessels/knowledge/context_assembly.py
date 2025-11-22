"""
Context Assembly Pipeline

Fast multi-source context retrieval for servant agents.

Target latency: <100ms total
- Project vectors: ~10ms
- Graph traversal: ~20ms
- Shared vectors: ~30ms (if needed)
- Ranking: ~10ms

Architecture:
1. Query project-specific vector store (FAST)
2. Extract entities and query graph (MEDIUM)
3. Fallback to shared store if insufficient (SLOW)
4. Rank and combine by relevance + recency + centrality
"""

from typing import Dict, List, Any, Optional
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ContextAssembler:
    """
    Assembles context for servant tasks within <100ms latency budget.
    
    Multi-source context assembly:
    - Project-specific knowledge (vector store)
    - Graph-based relationships (Graphiti)
    - Shared community knowledge (shared vector store)
    
    Context is ranked by:
    - Semantic relevance (50%)
    - Recency (30%)
    - Graph centrality (20%)
    """
    
    def __init__(
        self,
        project: 'ServantProject',
        shared_store: Optional['SharedVectorStore'] = None
    ):
        """
        Initialize context assembler.
        
        Args:
            project: ServantProject instance
            shared_store: Optional shared community knowledge store
        """
        self.project = project
        self.shared_store = shared_store
        
        # Initialize subsystems
        self.project_store = project.load_vector_store()
        self.graphiti = project.get_graphiti_client()
        
        # Performance tracking
        self.assembly_times: List[float] = []
    
    async def assemble_context(
        self,
        task: str,
        max_results: int = 10,
        include_shared: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble context from multiple sources.
        
        Args:
            task: Task description
            max_results: Maximum number of context items
            include_shared: Whether to query shared store
        
        Returns:
            Assembled context with timing information
        """
        start_time = time.time()
        
        # Step 1: Query project vector store (~10ms)
        step1_start = time.time()
        project_docs = await self._query_project_vectors(task)
        step1_duration = (time.time() - step1_start) * 1000
        
        # Step 2: Get graph context (~20ms)
        step2_start = time.time()
        graph_context = await self._get_graph_context(project_docs, task)
        step2_duration = (time.time() - step2_start) * 1000
        
        # Step 3: Query shared store if needed (~30ms)
        step3_start = time.time()
        shared_docs = []
        if include_shared and len(project_docs) < 3 and self.shared_store:
            shared_docs = await self._query_shared_vectors(task)
        step3_duration = (time.time() - step3_start) * 1000
        
        # Step 4: Rank and combine (~10ms)
        step4_start = time.time()
        combined = self._rank_by_relevance(project_docs, graph_context, shared_docs)
        combined = combined[:max_results]
        step4_duration = (time.time() - step4_start) * 1000
        
        # Total elapsed time
        total_duration = (time.time() - start_time) * 1000
        
        # Track performance
        self.assembly_times.append(total_duration)
        
        # Log performance
        if total_duration > 100:
            logger.warning(f"Context assembly exceeded target: {total_duration:.1f}ms")
        else:
            logger.info(f"Context assembled in {total_duration:.1f}ms")
        
        return {
            "task": task,
            "project_knowledge": project_docs,
            "graph_context": graph_context,
            "shared_knowledge": shared_docs,
            "combined_context": combined,
            "assembly_time_ms": total_duration,
            "timing_breakdown": {
                "project_vectors_ms": step1_duration,
                "graph_traversal_ms": step2_duration,
                "shared_vectors_ms": step3_duration,
                "ranking_ms": step4_duration,
            },
            "performance_target_met": total_duration < 100
        }
    
    async def _query_project_vectors(self, task: str) -> List[Dict]:
        """
        Query project vector store.
        
        Target: <10ms
        """
        try:
            results = self.project_store.query(task, top_k=5)
            logger.debug(f"Found {len(results)} docs in project store")
            return results
        except Exception as e:
            logger.error(f"Error querying project vectors: {e}")
            return []
    
    async def _get_graph_context(
        self,
        docs: List[Dict],
        task: str
    ) -> Dict[str, Any]:
        """
        Query graph for related entities and relationships.
        
        Target: <20ms
        """
        try:
            # Extract entities mentioned in task or retrieved docs
            entities = self._extract_entities(task, docs)
            
            if not entities:
                return {}
            
            # Query graph for relationships
            context = {}
            for entity in entities[:5]:  # Limit to 5 entities for performance
                try:
                    # Get neighbors from graph
                    neighbors = await self._get_neighbors(entity, max_depth=2)
                    if neighbors:
                        context[entity] = neighbors
                except Exception as e:
                    logger.debug(f"Could not get neighbors for {entity}: {e}")
            
            logger.debug(f"Found graph context for {len(context)} entities")
            return context
        
        except Exception as e:
            logger.error(f"Error getting graph context: {e}")
            return {}
    
    async def _get_neighbors(self, entity: str, max_depth: int = 2) -> List[Dict]:
        """Get neighbors from graph (async wrapper)"""
        try:
            # Note: This would use async Graphiti API in production
            # For now, wrapping synchronous call
            neighbors = self.graphiti.get_neighbors(
                node_id=entity,
                max_depth=max_depth
            )
            return neighbors if neighbors else []
        except:
            return []
    
    async def _query_shared_vectors(self, task: str) -> List[Dict]:
        """
        Query shared community knowledge.
        
        Target: <30ms
        """
        if not self.shared_store:
            return []
        
        try:
            results = self.shared_store.query(task, top_k=3)
            logger.debug(f"Found {len(results)} docs in shared store")
            return results
        except Exception as e:
            logger.error(f"Error querying shared vectors: {e}")
            return []
    
    def _extract_entities(self, task: str, docs: List[Dict]) -> List[str]:
        """
        Extract entity mentions from task and documents.
        
        Note: This is a simple keyword-based extraction.
        In production, use NER (Named Entity Recognition).
        """
        entities = []
        
        # Extract from task
        words = task.lower().split()
        
        # Look for common entity patterns
        # In production, this would use NER models
        entity_keywords = [
            "kupuna", "elder", "transport", "meal", "appointment",
            "driver", "cook", "volunteer", "community"
        ]
        
        for word in words:
            if word in entity_keywords:
                entities.append(word)
        
        # Extract from doc metadata
        for doc in docs:
            metadata = doc.get("metadata", {})
            if "entity" in metadata:
                entities.append(metadata["entity"])
        
        # Return unique entities
        return list(set(entities))
    
    def _rank_by_relevance(
        self,
        project_docs: List[Dict],
        graph_context: Dict[str, Any],
        shared_docs: List[Dict]
    ) -> List[Dict]:
        """
        Rank and combine context from all sources.
        
        Scoring formula:
        - 0.5 * semantic_similarity (from vector search)
        - 0.3 * recency (newer is better)
        - 0.2 * graph_centrality (more connected is better)
        
        Target: <10ms
        """
        all_items = []
        
        # Add project docs
        for doc in project_docs:
            all_items.append({
                "text": doc.get("text", ""),
                "source": "project",
                "metadata": doc.get("metadata", {}),
                "semantic_score": doc.get("score", 0.5),
                "recency_score": self._compute_recency_score(doc),
                "centrality_score": self._compute_centrality_score(doc, graph_context),
            })
        
        # Add graph context items
        for entity, neighbors in graph_context.items():
            for neighbor in neighbors[:3]:  # Limit neighbors
                all_items.append({
                    "text": f"Related to {entity}: {neighbor.get('type', 'unknown')}",
                    "source": "graph",
                    "metadata": neighbor,
                    "semantic_score": 0.5,  # Default score
                    "recency_score": self._compute_recency_score(neighbor),
                    "centrality_score": 0.8,  # High centrality for graph items
                })
        
        # Add shared docs
        for doc in shared_docs:
            all_items.append({
                "text": doc.get("text", ""),
                "source": "shared",
                "metadata": doc.get("metadata", {}),
                "semantic_score": doc.get("score", 0.3),
                "recency_score": self._compute_recency_score(doc),
                "centrality_score": 0.3,  # Lower centrality for shared
            })
        
        # Compute final scores
        for item in all_items:
            item["final_score"] = (
                0.5 * item["semantic_score"] +
                0.3 * item["recency_score"] +
                0.2 * item["centrality_score"]
            )
        
        # Sort by final score
        all_items.sort(key=lambda x: x["final_score"], reverse=True)
        
        return all_items
    
    def _compute_recency_score(self, item: Dict) -> float:
        """Compute recency score (0-1, newer is higher)"""
        # Simple placeholder - in production, use actual timestamps
        metadata = item.get("metadata", {})
        
        if "timestamp" in metadata:
            # Would compute age-based score here
            return 0.7
        
        return 0.5  # Default recency
    
    def _compute_centrality_score(
        self,
        item: Dict,
        graph_context: Dict[str, Any]
    ) -> float:
        """Compute graph centrality score (0-1, more central is higher)"""
        # Simple placeholder - in production, use PageRank or degree centrality
        metadata = item.get("metadata", {})
        
        if "entity" in metadata:
            entity = metadata["entity"]
            if entity in graph_context:
                neighbor_count = len(graph_context[entity])
                # Normalize by max expected neighbors
                return min(neighbor_count / 10.0, 1.0)
        
        return 0.3  # Default centrality
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get context assembly performance statistics"""
        if not self.assembly_times:
            return {
                "total_assemblies": 0,
                "avg_time_ms": 0,
                "min_time_ms": 0,
                "max_time_ms": 0,
                "target_met_pct": 0
            }
        
        target_met = sum(1 for t in self.assembly_times if t < 100)
        
        return {
            "total_assemblies": len(self.assembly_times),
            "avg_time_ms": sum(self.assembly_times) / len(self.assembly_times),
            "min_time_ms": min(self.assembly_times),
            "max_time_ms": max(self.assembly_times),
            "target_met_pct": (target_met / len(self.assembly_times)) * 100
        }
