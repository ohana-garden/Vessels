"""
Graphiti Memory Backend

Provides Graphiti-backed storage for CommunityMemory system.
Replaces in-memory + SQLite storage with knowledge graph + vector search.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from .graphiti_client import VesselsGraphitiClient
from .schema import NodeType, RelationType, PropertyName

# Import from root community_memory module
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from community_memory import MemoryType, MemoryEntry

logger = logging.getLogger(__name__)


# Memory type → Graph node type mapping
MEMORY_TYPE_TO_NODE = {
    MemoryType.EXPERIENCE: NodeType.EXPERIENCE,
    MemoryType.KNOWLEDGE: NodeType.FACT,
    MemoryType.PATTERN: NodeType.PATTERN,
    MemoryType.RELATIONSHIP: NodeType.FACT,  # Relationships stored as facts
    MemoryType.EVENT: NodeType.EVENT,
    MemoryType.CONTRIBUTION: NodeType.CONTRIBUTION,
}


class GraphitiMemoryBackend:
    """
    Graphiti-backed storage for community memory.

    Replaces in-memory + SQLite with FalkorDB knowledge graph.
    Provides same interface as original CommunityMemory but with:
    - Persistent graph storage
    - Better semantic search via Graphiti
    - Automatic entity extraction
    - Relationship discovery
    """

    def __init__(
        self,
        graphiti_client: VesselsGraphitiClient,
        enable_semantic_search: bool = True
    ):
        """
        Initialize Graphiti memory backend.

        Args:
            graphiti_client: VesselsGraphitiClient instance
            enable_semantic_search: Use Graphiti's semantic search (requires embeddings)
        """
        self.graphiti = graphiti_client
        self.enable_semantic_search = enable_semantic_search
        logger.info(
            f"Initialized GraphitiMemoryBackend for community: {graphiti_client.community_id}"
        )

    def store_memory(self, memory: MemoryEntry) -> str:
        """
        Store a memory in the graph.

        Args:
            memory: MemoryEntry to store

        Returns:
            Memory node ID
        """
        # Map memory type to node type
        node_type = MEMORY_TYPE_TO_NODE.get(memory.type, NodeType.EXPERIENCE)

        # Prepare node properties
        properties = {
            PropertyName.NAME: memory.id,
            PropertyName.COMMUNITY_ID: self.graphiti.community_id,
            PropertyName.CREATED_AT: memory.timestamp.isoformat(),
            PropertyName.TYPE: memory.type.value,
            "confidence": memory.confidence,
            "access_count": memory.access_count,
            "tags": ",".join(memory.tags),
            "content": str(memory.content),  # Store as string for now
        }

        # Add temporal validity for temporal nodes
        if node_type in [NodeType.EXPERIENCE, NodeType.EVENT, NodeType.FACT]:
            properties[PropertyName.VALID_AT] = memory.timestamp.isoformat()

        try:
            # Create node in graph
            node_id = self.graphiti.create_node(
                node_type=node_type,
                properties=properties,
                node_id=memory.id
            )

            # Create relationship to agent (if we have agent entities)
            # For now, we'll store agent_id as a property
            # In full implementation, we'd link to an agent node

            # Store relationships to other memories
            for related_id in memory.relationships:
                try:
                    self.graphiti.create_relationship(
                        source_id=memory.id,
                        rel_type=RelationType.RELATES_TO,
                        target_id=related_id,
                        properties={"created_at": datetime.utcnow().isoformat()}
                    )
                except Exception as e:
                    logger.warning(f"Could not create relationship to {related_id}: {e}")

            # Add episodic memory for semantic search
            if self.enable_semantic_search:
                episode_text = self._format_episode(memory)
                self.graphiti.add_episode(
                    text=episode_text,
                    metadata={
                        "memory_id": memory.id,
                        "memory_type": memory.type.value,
                        "agent_id": memory.agent_id,
                        "tags": memory.tags,
                    }
                )

            logger.debug(f"Stored {memory.type.value} memory: {memory.id}")
            return node_id

        except Exception as e:
            logger.error(f"Error storing memory in Graphiti: {e}")
            raise

    def query_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        agent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Query memories using semantic search and filters.

        Args:
            query: Search query text
            memory_type: Filter by memory type
            agent_id: Filter by agent ID
            tags: Filter by tags
            limit: Maximum results to return

        Returns:
            List of MemoryEntry objects
        """
        try:
            # Use Graphiti semantic search if enabled
            if self.enable_semantic_search:
                results = self.graphiti.search_semantic(query, top_k=limit * 2)
            else:
                # Fallback to Cypher query
                results = self._query_by_cypher(query, memory_type, agent_id, tags, limit)

            # Convert to MemoryEntry objects
            memories = []
            for result in results[:limit]:
                try:
                    memory = self._result_to_memory(result)

                    # Apply filters
                    if memory_type and memory.type != memory_type:
                        continue
                    if agent_id and memory.agent_id != agent_id:
                        continue
                    if tags and not any(tag in memory.tags for tag in tags):
                        continue

                    memories.append(memory)
                except Exception as e:
                    logger.warning(f"Could not convert result to memory: {e}")
                    continue

            return memories[:limit]

        except Exception as e:
            logger.error(f"Error querying memories: {e}")
            return []

    def get_agent_memories(
        self,
        agent_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[MemoryEntry]:
        """
        Get all memories for a specific agent.

        Args:
            agent_id: Agent ID
            memory_type: Optional memory type filter
            limit: Maximum results

        Returns:
            List of MemoryEntry objects
        """
        try:
            # Build Cypher query
            node_type_filter = ""
            if memory_type:
                node_type = MEMORY_TYPE_TO_NODE.get(memory_type, NodeType.EXPERIENCE)
                node_type_filter = f":{node_type.value}"

            cypher = f"""
            MATCH (m{node_type_filter})
            WHERE m.created_by = $agent_id OR m.content CONTAINS $agent_id
            RETURN m
            ORDER BY m.created_at DESC
            LIMIT $limit
            """

            results = self.graphiti.query(
                cypher,
                agent_id=agent_id,
                limit=limit
            )

            memories = []
            for record in results:
                try:
                    memory = self._result_to_memory(record.get("m", {}))
                    memories.append(memory)
                except Exception as e:
                    logger.warning(f"Could not convert result to memory: {e}")
                    continue

            return memories

        except Exception as e:
            logger.error(f"Error getting agent memories: {e}")
            return []

    def get_related_memories(
        self,
        memory_id: str,
        max_depth: int = 2,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Get memories related to a given memory via graph traversal.

        Args:
            memory_id: Source memory ID
            max_depth: Maximum traversal depth
            limit: Maximum results

        Returns:
            List of related MemoryEntry objects
        """
        try:
            # Use Graphiti neighbor query
            neighbors_dict = self.graphiti.get_neighbors(
                node_id=memory_id,
                rel_types=[RelationType.RELATES_TO],
                max_depth=max_depth
            )

            # Flatten neighbors from all relationship types
            all_neighbors = []
            for rel_type, neighbors in neighbors_dict.items():
                all_neighbors.extend(neighbors)

            # Convert to MemoryEntry objects
            memories = []
            for neighbor in all_neighbors[:limit]:
                try:
                    memory = self._result_to_memory(neighbor)
                    memories.append(memory)
                except Exception as e:
                    logger.warning(f"Could not convert neighbor to memory: {e}")
                    continue

            return memories[:limit]

        except Exception as e:
            logger.error(f"Error getting related memories: {e}")
            return []

    def update_access_count(self, memory_id: str):
        """
        Increment access count for a memory.

        Args:
            memory_id: Memory ID
        """
        try:
            cypher = """
            MATCH (m {id: $memory_id})
            SET m.access_count = COALESCE(m.access_count, 0) + 1
            RETURN m.access_count as new_count
            """

            results = self.graphiti.query(cypher, memory_id=memory_id)
            if results:
                new_count = results[0].get("new_count", 0)
                logger.debug(f"Updated access count for {memory_id}: {new_count}")

        except Exception as e:
            logger.error(f"Error updating access count: {e}")

    def _format_episode(self, memory: MemoryEntry) -> str:
        """
        Format memory as episode text for Graphiti.

        Args:
            memory: MemoryEntry

        Returns:
            Formatted episode text
        """
        content_str = str(memory.content)
        tags_str = ", ".join(memory.tags) if memory.tags else "none"

        episode = (
            f"Agent {memory.agent_id} recorded {memory.type.value} memory:\n"
            f"{content_str}\n"
            f"Tags: {tags_str}\n"
            f"Confidence: {memory.confidence}"
        )

        return episode

    def _query_by_cypher(
        self,
        query: str,
        memory_type: Optional[MemoryType],
        agent_id: Optional[str],
        tags: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Query memories using Cypher (fallback when semantic search unavailable).

        Args:
            query: Search query
            memory_type: Optional memory type filter
            agent_id: Optional agent filter
            tags: Optional tag filters
            limit: Result limit

        Returns:
            List of query results
        """
        # Build filters
        filters = ["m.content CONTAINS $query"]

        if memory_type:
            node_type = MEMORY_TYPE_TO_NODE.get(memory_type, NodeType.EXPERIENCE)
            filters.append(f"m.type = '{memory_type.value}'")

        if agent_id:
            filters.append("m.created_by = $agent_id")

        if tags:
            tag_filters = " OR ".join([f"m.tags CONTAINS '{tag}'" for tag in tags])
            filters.append(f"({tag_filters})")

        where_clause = " AND ".join(filters)

        cypher = f"""
        MATCH (m)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.created_at DESC
        LIMIT $limit
        """

        results = self.graphiti.query(
            cypher,
            query=query,
            agent_id=agent_id,
            limit=limit
        )

        return results

    def _result_to_memory(self, result: Dict[str, Any]) -> MemoryEntry:
        """
        Convert graph query result to MemoryEntry.

        Args:
            result: Graph query result

        Returns:
            MemoryEntry object
        """
        # Handle different result formats
        if "properties" in result:
            props = result["properties"]
        else:
            props = result

        # Extract fields
        memory_id = props.get("id") or props.get(PropertyName.NAME, "")
        memory_type_str = props.get(PropertyName.TYPE, "experience")

        try:
            memory_type = MemoryType(memory_type_str)
        except ValueError:
            memory_type = MemoryType.EXPERIENCE

        # Parse timestamp
        timestamp_str = props.get(PropertyName.CREATED_AT, datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.utcnow()

        # Parse tags
        tags_str = props.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        # Parse relationships
        relationships_str = props.get("relationships", "")
        if isinstance(relationships_str, list):
            relationships = relationships_str
        elif isinstance(relationships_str, str) and relationships_str:
            relationships = [r.strip() for r in relationships_str.split(",") if r.strip()]
        else:
            relationships = []

        # Create MemoryEntry
        memory = MemoryEntry(
            id=memory_id,
            type=memory_type,
            content={"text": props.get("content", "")},
            agent_id=props.get(PropertyName.CREATED_BY, "unknown"),
            timestamp=timestamp,
            tags=tags,
            relationships=relationships,
            confidence=float(props.get("confidence", 1.0)),
            access_count=int(props.get("access_count", 0))
        )

        return memory
