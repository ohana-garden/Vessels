"""
FalkorDB Community Memory System

Graph-native implementation of community memory with:
- Semantic relationship types between memories
- Agent-memory associations with confidence scores
- Temporal event sequences
- Pattern discovery and knowledge accumulation
- Cross-community memory access control
"""
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """Types of memory entries."""
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    PATTERN = "pattern"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    CONTRIBUTION = "contribution"


class RelationshipType(Enum):
    """Types of relationships between memories."""
    CAUSATION = "causation"           # A caused B
    SIMILARITY = "similarity"         # A is similar to B
    TEMPORAL_SEQUENCE = "temporal"    # A happened before B
    CONTRADICTION = "contradiction"   # A contradicts B
    GENERALIZATION = "generalization" # B generalizes A
    SOLUTION = "solution"             # B solves problem A


class FalkorDBCommunityMemory:
    """
    Graph-native community memory system.

    Graph structure:
        (servant:Servant) -[REMEMBERS {confidence: 0.8}]-> (memory:MemoryEntry)
        (memory1:MemoryEntry) -[RELATES_TO {type: "causation"}]-> (memory2:MemoryEntry)
        (memory:MemoryEntry) -[FOR_PERSON]-> (person:Person)
        (memory:MemoryEntry) -[IN_COMMUNITY]-> (community:Community)
        (memory:MemoryEntry) -[TAGGED_WITH]-> (tag:Tag)
    """

    def __init__(self, falkor_client, graph_name: str = "vessels_memory"):
        """
        Initialize FalkorDB community memory.

        Args:
            falkor_client: FalkorDBClient instance
            graph_name: Graph namespace for memory data
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        logger.info(f"Using FalkorDB Community Memory with graph '{graph_name}'")

    def store_memory(
        self,
        memory_id: str,
        memory_type: MemoryType,
        content: Dict[str, Any],
        agent_id: str,
        person_id: Optional[str] = None,
        community_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        confidence: float = 1.0
    ) -> bool:
        """
        Store a new memory in the graph.

        Args:
            memory_id: Unique memory identifier
            memory_type: Type of memory (EXPERIENCE, KNOWLEDGE, etc.)
            content: Memory content as dictionary
            agent_id: Agent that created/observed this memory
            person_id: Optional person this memory is about
            community_id: Optional community context
            tags: Optional tags for categorization
            confidence: Confidence score (0-1)

        Returns:
            True if successful
        """
        try:
            memory_props = {
                "memory_id": memory_id,
                "type": memory_type.value,
                "content": json.dumps(content),
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": confidence,
                "access_count": 0
            }

            # Build query based on optional relationships
            query_parts = []
            params = {
                "memory_props": memory_props,
                "agent_id": agent_id
            }

            # Core memory creation
            query_parts.append("""
                MERGE (agent:Servant {agent_id: $agent_id})
                CREATE (memory:MemoryEntry $memory_props)
                CREATE (agent)-[:REMEMBERS {confidence: $confidence, recorded_at: $timestamp}]->(memory)
            """)

            # Add person relationship if provided
            if person_id:
                query_parts.append("""
                    MERGE (person:Person {person_id: $person_id})
                    CREATE (memory)-[:FOR_PERSON]->(person)
                """)
                params["person_id"] = person_id

            # Add community relationship if provided
            if community_id:
                query_parts.append("""
                    MERGE (community:Community {community_id: $community_id})
                    CREATE (memory)-[:IN_COMMUNITY]->(community)
                """)
                params["community_id"] = community_id

            # Add tags
            if tags:
                for i, tag in enumerate(tags):
                    query_parts.append(f"""
                        MERGE (tag{i}:Tag {{name: $tag{i}}})
                        CREATE (memory)-[:TAGGED_WITH]->(tag{i})
                    """)
                    params[f"tag{i}"] = tag

            query_parts.append("RETURN memory")

            query = "\n".join(query_parts)
            result = self.graph.query(query, params)

            logger.debug(f"Stored memory {memory_id} (type={memory_type.value}, agent={agent_id})")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to store memory {memory_id}: {e}")
            return False

    def link_memories(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        strength: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a semantic relationship between two memories.

        Args:
            from_memory_id: Source memory ID
            to_memory_id: Target memory ID
            relationship_type: Type of relationship
            strength: Relationship strength (0-1)
            metadata: Optional relationship metadata

        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (m1:MemoryEntry {memory_id: $from_id})
            MATCH (m2:MemoryEntry {memory_id: $to_id})
            CREATE (m1)-[r:RELATES_TO {
                type: $rel_type,
                strength: $strength,
                created_at: $timestamp,
                metadata: $metadata
            }]->(m2)
            RETURN r
            """

            params = {
                "from_id": from_memory_id,
                "to_id": to_memory_id,
                "rel_type": relationship_type.value,
                "strength": strength,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": json.dumps(metadata or {})
            }

            result = self.graph.query(query, params)
            logger.debug(f"Linked memories: {from_memory_id} -> {to_memory_id} ({relationship_type.value})")
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to link memories: {e}")
            return False

    def recall_memories(
        self,
        person_id: Optional[str] = None,
        community_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recall memories based on filters.

        Args:
            person_id: Filter by person
            community_id: Filter by community
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            agent_id: Filter by agent
            limit: Maximum results

        Returns:
            List of memory dictionaries
        """
        try:
            # Build dynamic query based on filters
            match_clauses = ["MATCH (memory:MemoryEntry)"]
            where_clauses = []
            params = {"limit": limit}

            if person_id:
                match_clauses.append("MATCH (memory)-[:FOR_PERSON]->(person:Person {person_id: $person_id})")
                params["person_id"] = person_id

            if community_id:
                match_clauses.append("MATCH (memory)-[:IN_COMMUNITY]->(community:Community {community_id: $community_id})")
                params["community_id"] = community_id

            if agent_id:
                match_clauses.append("MATCH (agent:Servant {agent_id: $agent_id})-[:REMEMBERS]->(memory)")
                params["agent_id"] = agent_id

            if memory_type:
                where_clauses.append("memory.type = $memory_type")
                params["memory_type"] = memory_type.value

            if tags:
                for i, tag in enumerate(tags):
                    match_clauses.append(f"MATCH (memory)-[:TAGGED_WITH]->(tag{i}:Tag {{name: $tag{i}}})")
                    params[f"tag{i}"] = tag

            # Construct full query
            query_parts = match_clauses
            if where_clauses:
                query_parts.append("WHERE " + " AND ".join(where_clauses))

            query_parts.append("""
                RETURN memory.memory_id as memory_id,
                       memory.type as type,
                       memory.content as content,
                       memory.timestamp as timestamp,
                       memory.confidence as confidence,
                       memory.access_count as access_count
                ORDER BY datetime(memory.timestamp) DESC
                LIMIT $limit
            """)

            query = "\n".join(query_parts)
            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            memories = []
            for row in result.result_set:
                memories.append({
                    "memory_id": row[0],
                    "type": row[1],
                    "content": json.loads(row[2]),
                    "timestamp": row[3],
                    "confidence": row[4],
                    "access_count": row[5]
                })

            logger.debug(f"Recalled {len(memories)} memories")
            return memories

        except Exception as e:
            logger.error(f"Failed to recall memories: {e}")
            return []

    def find_related_memories(
        self,
        memory_id: str,
        relationship_types: Optional[List[RelationshipType]] = None,
        max_depth: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find memories related to a given memory.

        Traverses the relationship graph to find connected memories.

        Args:
            memory_id: Starting memory ID
            relationship_types: Filter by relationship types (None = all)
            max_depth: Maximum traversal depth
            limit: Maximum results

        Returns:
            List of related memories with relationship paths
        """
        try:
            if relationship_types:
                # Filter by specific relationship types
                type_filter = " OR ".join([f"r.type = '{rt.value}'" for rt in relationship_types])
                where_clause = f"WHERE {type_filter}"
            else:
                where_clause = ""

            query = f"""
            MATCH path = (start:MemoryEntry {{memory_id: $memory_id}})-[r:RELATES_TO*1..{max_depth}]->(related:MemoryEntry)
            {where_clause}
            RETURN related.memory_id as memory_id,
                   related.type as type,
                   related.content as content,
                   [rel IN relationships(path) | rel.type] as relationship_path,
                   length(path) as distance
            ORDER BY distance ASC
            LIMIT $limit
            """

            params = {
                "memory_id": memory_id,
                "limit": limit
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            related = []
            for row in result.result_set:
                related.append({
                    "memory_id": row[0],
                    "type": row[1],
                    "content": json.loads(row[2]),
                    "relationship_path": row[3],
                    "distance": row[4]
                })

            logger.debug(f"Found {len(related)} related memories for {memory_id}")
            return related

        except Exception as e:
            logger.error(f"Failed to find related memories: {e}")
            return []

    def find_patterns(
        self,
        community_id: Optional[str] = None,
        min_occurrences: int = 3,
        lookback_days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Find recurring patterns in community memory.

        Identifies sequences of memories that occur frequently.

        Args:
            community_id: Optional community filter
            min_occurrences: Minimum pattern occurrences
            lookback_days: How far back to analyze

        Returns:
            List of discovered patterns
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            community_filter = ""
            params = {
                "since": since.isoformat(),
                "min_count": min_occurrences
            }

            if community_id:
                community_filter = """
                MATCH (pattern)-[:IN_COMMUNITY]->(c:Community {community_id: $community_id})
                MATCH (next)-[:IN_COMMUNITY]->(c)
                """
                params["community_id"] = community_id

            query = f"""
            MATCH (pattern:MemoryEntry {{type: 'pattern'}})-[r:RELATES_TO {{type: 'temporal'}}]->(next:MemoryEntry)
            WHERE datetime(pattern.timestamp) > datetime($since)
            {community_filter}
            WITH pattern, next, COUNT(*) as occurrences
            WHERE occurrences >= $min_count
            RETURN pattern.memory_id as pattern_id,
                   pattern.content as pattern_content,
                   next.memory_id as next_id,
                   next.content as next_content,
                   occurrences
            ORDER BY occurrences DESC
            """

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return []

            patterns = []
            for row in result.result_set:
                patterns.append({
                    "pattern_id": row[0],
                    "pattern_content": json.loads(row[1]),
                    "next_id": row[2],
                    "next_content": json.loads(row[3]),
                    "occurrences": row[4]
                })

            logger.info(f"Found {len(patterns)} recurring patterns")
            return patterns

        except Exception as e:
            logger.error(f"Failed to find patterns: {e}")
            return []

    def get_agent_knowledge(
        self,
        agent_id: str,
        min_confidence: float = 0.5,
        lookback_days: int = 30
    ) -> Dict[str, int]:
        """
        Get what an agent has learned over time.

        Args:
            agent_id: Agent identifier
            min_confidence: Minimum confidence threshold
            lookback_days: How far back to analyze

        Returns:
            Dictionary of memory types and counts
        """
        try:
            since = datetime.utcnow() - timedelta(days=lookback_days)

            query = """
            MATCH (agent:Servant {agent_id: $agent_id})-[r:REMEMBERS]->(memory:MemoryEntry)
            WHERE datetime(memory.timestamp) > datetime($since)
            AND r.confidence >= $min_confidence
            WITH memory.type as mem_type, COUNT(*) as count
            RETURN mem_type, count
            ORDER BY count DESC
            """

            params = {
                "agent_id": agent_id,
                "since": since.isoformat(),
                "min_confidence": min_confidence
            }

            result = self.graph.query(query, params)

            if not result or not result.result_set:
                return {}

            knowledge = {}
            for row in result.result_set:
                knowledge[row[0]] = row[1]

            logger.debug(f"Agent {agent_id} has {sum(knowledge.values())} memories across {len(knowledge)} types")
            return knowledge

        except Exception as e:
            logger.error(f"Failed to get agent knowledge: {e}")
            return {}

    def increment_access_count(self, memory_id: str) -> bool:
        """
        Increment access count for a memory.

        Tracks which memories are frequently accessed.

        Args:
            memory_id: Memory identifier

        Returns:
            True if successful
        """
        try:
            query = """
            MATCH (memory:MemoryEntry {memory_id: $memory_id})
            SET memory.access_count = memory.access_count + 1
            RETURN memory.access_count
            """

            result = self.graph.query(query, {"memory_id": memory_id})
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to increment access count for {memory_id}: {e}")
            return False
