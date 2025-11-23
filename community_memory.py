#!/usr/bin/env python3
"""
COMMUNITY MEMORY SYSTEM
Vector store + graph database + event streaming
Agents share context, learn from each other, build on previous work

Now includes Kala contribution tracking for valuing community contributions.
"""

import json
import logging
import sqlite3
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    PATTERN = "pattern"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    CONTRIBUTION = "contribution"  # Kala-valued contributions

@dataclass
class MemoryEntry:
    """Single memory entry in the system"""
    id: str
    type: MemoryType
    content: Dict[str, Any]
    agent_id: str
    timestamp: datetime
    tags: List[str] = field(default_factory=list)
    relationships: List[str] = field(default_factory=list)
    confidence: float = 1.0
    access_count: int = 0
    
@dataclass
class VectorEmbedding:
    """Vector embedding for semantic search"""
    memory_id: str
    vector: np.ndarray
    metadata: Dict[str, Any]

class CommunityMemory:
    """Distributed memory system for agent coordination"""

    def __init__(
        self,
        db_path: Optional[str] = None,
        backend: str = "sqlite",
        graphiti_client=None,
        community_id: Optional[str] = None,
        node_id: Optional[str] = None
    ):
        """
        Initialize Community Memory system.

        Args:
            db_path: Path to SQLite database (for sqlite backend)
            backend: Backend type: "sqlite", "graphiti", "hybrid", or "crdt"
            graphiti_client: VesselsGraphitiClient instance (for graphiti/hybrid backends)
            community_id: Community ID (for graphiti backend)
            node_id: Node ID (for CRDT backend)
        """
        self.backend_type = backend
        self.graphiti_backend = None
        self.crdt_backend = None
        self.community_id = community_id
        self.node_id = node_id

        # Initialize CRDT backend if requested
        if backend == "crdt":
            try:
                from vessels.knowledge.crdt_backend import CRDTMemoryBackend
                self.crdt_backend = CRDTMemoryBackend(node_id=node_id)
                logger.info(f"Initialized CRDT memory backend (node: {self.crdt_backend.crdt_memory.lww_set.node_id})")
            except Exception as e:
                logger.error(f"Could not initialize CRDT backend: {e}")
                raise

        # Initialize Graphiti backend if requested
        if backend in ["graphiti", "hybrid"]:
            if graphiti_client is None and community_id:
                # Lazy-load graphiti client
                try:
                    from vessels.knowledge.graphiti_client import VesselsGraphitiClient
                    graphiti_client = VesselsGraphitiClient(
                        community_id=community_id,
                        allow_mock=True  # Allow mock for testing
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize Graphiti client: {e}")
                    if backend == "graphiti":
                        raise
                    # Fall back to SQLite for hybrid mode
                    self.backend_type = "sqlite"

            if graphiti_client:
                try:
                    from vessels.knowledge.memory_backend import GraphitiMemoryBackend
                    self.graphiti_backend = GraphitiMemoryBackend(graphiti_client)
                    logger.info(f"Initialized Graphiti memory backend (mode: {backend})")
                except Exception as e:
                    logger.warning(f"Could not initialize Graphiti backend: {e}")
                    if backend == "graphiti":
                        raise
                    # Fall back to SQLite for hybrid mode
                    self.backend_type = "sqlite"

        # Always initialize in-memory structures (used by all backends)
        self.memories: Dict[str, MemoryEntry] = {}
        self.agent_memories: Dict[str, List[str]] = defaultdict(list)
        self.vector_embeddings: Dict[str, VectorEmbedding] = {}
        self.relationship_graph: Dict[str, List[str]] = defaultdict(list)
        self.event_stream = deque(maxlen=10000)
        self.memory_db = None
        self.db_path = db_path or self._resolve_db_path()
        self.running = False
        self.memory_thread = None
        self.vector_dimension = 384  # Standard embedding size
        self.embedding_model = None

        # Kala system integration
        self.kala_system = None
        self._init_kala_system()

        # Optional embedding model
        self._load_embedding_model()

        # Initialize in-memory vector storage
        self.initialize_memory_system()

    def _resolve_db_path(self) -> str:
        """Choose a durable on-disk database by default."""
        import os

        return os.environ.get("COMMUNITY_MEMORY_DB_PATH", "community_memory.db")

    def _init_kala_system(self):
        """Initialize kala value tracking system"""
        try:
            from kala import kala_system
            self.kala_system = kala_system
            logger.info("Kala system integrated with Community Memory")
        except ImportError:
            logger.warning("Kala system not available - contribution tracking disabled")

    def _load_embedding_model(self) -> None:
        """Attempt to load a proper embedding model with graceful fallback."""
        try:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.vector_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info("SentenceTransformer embedding model loaded")
        except Exception as exc:  # noqa: BLE001
            # Keep the lightweight hash-based embedding if model is unavailable
            self.embedding_model = None
            logger.warning("Falling back to hash embeddings: %s", exc)
        
    def initialize_memory_system(self):
        """Initialize the memory system"""
        self.running = True
        self.memory_thread = threading.Thread(target=self._memory_maintenance_loop)
        self.memory_thread.daemon = True
        self.memory_thread.start()
        
        # Initialize SQLite for persistent storage (defaults to on-disk)
        self.memory_db = sqlite3.connect(self.db_path, check_same_thread=False)
        self._configure_database(self.memory_db)

        logger.info("Community Memory System initialized")

    def _configure_database(self, connection: sqlite3.Connection) -> None:
        """Configure SQLite for safer durability and concurrency."""
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        self._create_memory_tables()
        connection.commit()
    
    def _create_memory_tables(self):
        """Create database tables for memory storage"""
        cursor = self.memory_db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tags TEXT,
                relationships TEXT,
                confidence REAL,
                access_count INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source_agent TEXT,
                target_agents TEXT
            )
        ''')
        
        self.memory_db.commit()
    
    def store_experience(self, agent_id: str, experience: Dict[str, Any]) -> str:
        """Store agent experience in community memory"""
        memory_id = str(uuid.uuid4())

        memory_entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.EXPERIENCE,
            content=experience,
            agent_id=agent_id,
            timestamp=datetime.now(),
            tags=experience.get("tags", []),
            relationships=experience.get("relationships", []),
            confidence=experience.get("confidence", 1.0)
        )

        # Store in CRDT backend if enabled
        if self.backend_type == "crdt" and self.crdt_backend:
            try:
                self.crdt_backend.store_memory(memory_entry)
                logger.debug(f"Stored experience in CRDT: {memory_id}")
                # For CRDT backend, we still maintain in-memory structures for fast access
                self.memories[memory_id] = memory_entry
                self.agent_memories[agent_id].append(memory_id)
                return memory_id
            except Exception as e:
                logger.error(f"Failed to store in CRDT: {e}")
                raise

        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_backend:
            try:
                self.graphiti_backend.store_memory(memory_entry)
                logger.debug(f"Stored experience in Graphiti: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to store in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend (always for hybrid, or if graphiti failed)
        if self.backend_type in ["sqlite", "hybrid"]:
            # Store in memory
            self.memories[memory_id] = memory_entry
            self.agent_memories[agent_id].append(memory_id)

            # Generate vector embedding
            vector = self._generate_embedding(experience)
            self.vector_embeddings[memory_id] = VectorEmbedding(
                memory_id=memory_id,
                vector=vector,
                metadata={"type": "experience", "agent_id": agent_id}
            )

            # Update relationships
            self._update_relationships(memory_id, experience)

            # Store event
            self._store_event({
                "type": "memory_stored",
                "memory_id": memory_id,
                "agent_id": agent_id,
                "experience_type": experience.get("type", "unknown")
            })

            # Persist to database
            self._persist_memory(memory_entry)

        logger.info(f"Stored experience for agent {agent_id}: {memory_id}")
        return memory_id
    
    def store_knowledge(self, agent_id: str, knowledge: Dict[str, Any]) -> str:
        """Store community knowledge"""
        memory_id = str(uuid.uuid4())

        memory_entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.KNOWLEDGE,
            content=knowledge,
            agent_id=agent_id,
            timestamp=datetime.now(),
            tags=knowledge.get("tags", []),
            relationships=knowledge.get("relationships", []),
            confidence=knowledge.get("confidence", 0.8)
        )

        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_backend:
            try:
                self.graphiti_backend.store_memory(memory_entry)
                logger.debug(f"Stored knowledge in Graphiti: {memory_id}")
            except Exception as e:
                logger.error(f"Failed to store in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend (always for hybrid, or if graphiti failed)
        if self.backend_type in ["sqlite", "hybrid"]:
            self.memories[memory_id] = memory_entry
            self.agent_memories[agent_id].append(memory_id)

            # Generate vector embedding
            vector = self._generate_embedding(knowledge)
            self.vector_embeddings[memory_id] = VectorEmbedding(
                memory_id=memory_id,
                vector=vector,
                metadata={"type": "knowledge", "agent_id": agent_id}
            )

            self._update_relationships(memory_id, knowledge)
            self._store_event({
                "type": "knowledge_stored",
                "memory_id": memory_id,
                "agent_id": agent_id,
                "knowledge_domain": knowledge.get("domain", "general")
            })

            self._persist_memory(memory_entry)

        logger.info(f"Stored knowledge from agent {agent_id}: {memory_id}")
        return memory_id
    
    def find_similar_memories(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories similar to query using vector search"""
        
        # Generate query vector
        query_vector = self._generate_embedding(query)
        
        # Calculate similarities
        similarities = []
        for memory_id, embedding in self.vector_embeddings.items():
            similarity = self._cosine_similarity(query_vector, embedding.vector)
            similarities.append((memory_id, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for memory_id, similarity in similarities[:limit]:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                memory.access_count += 1
                results.append({
                    "memory": memory,
                    "similarity": similarity,
                    "relevance_score": self._calculate_relevance_score(memory, query)
                })
        
        return results

    def dynamic_find_similar(self, query: Dict[str, Any], agent_id: str = None,
                              tags: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories similar to query with dynamic weighting and proximity considerations.

        This method augments the standard vector similarity search with additional
        heuristics to exploit both homogeneity (similar agents or tags) and
        heterogeneity (diverse agents with related domains).  It first
        calculates cosine similarity between the query and all memory
        embeddings, then adjusts the score based on tag overlap, recency and
        whether the memory comes from the same agent.  Memories sharing more
        tags or originating from the same agent receive a higher weight,
        encouraging local reuse, while still allowing relevant knowledge
        from other agents to surface when no local results exist.

        Parameters
        ----------
        query : Dict[str, Any]
            Dictionary representing the content to search for.  Can include
            arbitrary keys but will be converted into an embedding for
            similarity and can include a "tags" field for tag-based weighting.
        agent_id : str, optional
            Identifier of the querying agent.  If provided, memories from
            this agent are preferentially ranked higher to exploit local
            homogeneity.  If None, agent-specific weighting is skipped.
        tags : List[str], optional
            Additional tags to consider for proximity.  When provided,
            memories containing overlapping tags get a boost in relevance.
        limit : int
            Maximum number of results to return.

        Returns
        -------
        List[Dict[str, Any]]
            A list of dictionaries containing the memory entry, the raw
            similarity score and the combined dynamic score.
        """
        # Generate query vector
        query_vector = self._generate_embedding(query)
        query_tags = set(tags or query.get("tags", []))

        similarities = []
        for memory_id, embedding in self.vector_embeddings.items():
            # Base cosine similarity
            base_sim = self._cosine_similarity(query_vector, embedding.vector)

            # Retrieve memory entry
            if memory_id not in self.memories:
                continue
            memory = self.memories[memory_id]

            # Tag overlap factor: number of overlapping tags / total query tags
            mem_tags = set(memory.tags)
            tag_overlap = len(query_tags.intersection(mem_tags))
            tag_factor = 0.0
            if query_tags:
                tag_factor = tag_overlap / len(query_tags)

            # Recency factor (same as _calculate_relevance_score)
            time_diff = (datetime.now() - memory.timestamp).total_seconds()
            recency_factor = 1.0 / (1.0 + time_diff / 86400)

            # Agent factor: give a small boost to memories from the same agent
            agent_factor = 0.0
            if agent_id is not None and memory.agent_id == agent_id:
                agent_factor = 0.1

            # Combine factors with weights
            # Weights chosen empirically: similarity (0.6), tag factor (0.2), recency (0.1), agent factor (0.1)
            combined_score = (
                base_sim * 0.6 +
                tag_factor * 0.2 +
                recency_factor * 0.1 +
                agent_factor * 0.1
            )

            similarities.append((memory_id, base_sim, combined_score))

        # Sort by combined score first, then base similarity
        similarities.sort(key=lambda x: (x[2], x[1]), reverse=True)

        results = []
        for memory_id, base_sim, combined_score in similarities[:limit]:
            memory = self.memories[memory_id]
            memory.access_count += 1
            results.append({
                "memory": memory,
                "similarity": base_sim,
                "dynamic_score": combined_score
            })
        return results
    
    def search_memories(self, query: str, filters: Dict[str, Any] = None) -> List[MemoryEntry]:
        """Search memories using text query and filters"""
        results = []
        
        for memory in self.memories.values():
            # Apply filters
            if filters:
                if filters.get("type") and memory.type.value != filters["type"]:
                    continue
                if filters.get("agent_id") and memory.agent_id != filters["agent_id"]:
                    continue
                if filters.get("tags"):
                    if not any(tag in memory.tags for tag in filters["tags"]):
                        continue
            
            # Text search in content
            if query.lower() in json.dumps(memory.content).lower():
                memory.access_count += 1
                results.append(memory)
        
        # Sort by relevance (access count and recency)
        results.sort(key=lambda m: (m.access_count, m.timestamp), reverse=True)
        
        return results
    
    def get_agent_memories(self, agent_id: str, memory_type: MemoryType = None) -> List[MemoryEntry]:
        """Get all memories for specific agent"""
        memories = []
        
        memory_ids = self.agent_memories.get(agent_id, [])
        for memory_id in memory_ids:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                if memory_type is None or memory.type == memory_type:
                    memories.append(memory)
        
        return sorted(memories, key=lambda m: m.timestamp, reverse=True)
    
    def get_community_knowledge(self, domain: str = None) -> List[Dict[str, Any]]:
        """Get community knowledge, optionally filtered by domain"""
        knowledge = []
        
        for memory in self.memories.values():
            if memory.type == MemoryType.KNOWLEDGE:
                if domain is None or domain in memory.tags:
                    knowledge.append({
                        "id": memory.id,
                        "content": memory.content,
                        "agent_id": memory.agent_id,
                        "timestamp": memory.timestamp,
                        "confidence": memory.confidence,
                        "access_count": memory.access_count
                    })
        
        return sorted(knowledge, key=lambda k: (k["confidence"], k["access_count"]), reverse=True)
    
    def store_contribution(self, agent_id: str, contribution_data: Dict[str, Any]) -> Optional[str]:
        """
        Store a community contribution with kala valuation.

        Args:
            agent_id: ID of agent/person making contribution
            contribution_data: Dict containing:
                - type: ContributionType name (e.g., "TIME", "CARE", "FOOD")
                - description: Human-readable description
                - kala_value: Value in kala (or omit to auto-calculate)
                - hours: For time contributions
                - skill_level: For time contributions
                - market_value_usd: For resource contributions
                - recipient_id: Optional recipient
                - tags: Optional tags
                - metadata: Optional additional data

        Returns:
            Contribution ID if successful, None otherwise
        """
        if not self.kala_system:
            logger.warning("Kala system not available - cannot store contribution")
            return None

        try:
            from kala import ContributionType

            # Extract contribution details
            contribution_type_str = contribution_data.get("type", "OTHER")
            contribution_type = ContributionType[contribution_type_str.upper()]
            description = contribution_data.get("description", "")
            recipient_id = contribution_data.get("recipient_id")
            tags = contribution_data.get("tags", [])
            metadata = contribution_data.get("metadata", {})

            # Calculate kala value
            if "kala_value" in contribution_data:
                kala_value = contribution_data["kala_value"]
            elif contribution_type == ContributionType.TIME:
                hours = contribution_data.get("hours", 1.0)
                skill_level = contribution_data.get("skill_level", "general")
                kala_value = self.kala_system.value_time_contribution(hours, skill_level)
            elif "market_value_usd" in contribution_data:
                kala_value = self.kala_system.value_resource_contribution(
                    description,
                    market_value_usd=contribution_data["market_value_usd"]
                )
            else:
                logger.error("Cannot calculate kala value - insufficient data")
                return None

            # Record in kala system
            contribution = self.kala_system.record_contribution(
                contributor_id=agent_id,
                contribution_type=contribution_type,
                description=description,
                kala_value=kala_value,
                recipient_id=recipient_id,
                metadata=metadata,
                tags=tags
            )

            # Store in memory system
            memory_id = str(uuid.uuid4())
            memory_entry = MemoryEntry(
                id=memory_id,
                type=MemoryType.CONTRIBUTION,
                content={
                    "contribution_id": contribution.id,
                    "type": contribution_type.value,
                    "description": description,
                    "kala_value": kala_value,
                    "usd_equivalent": contribution.usd_equivalent,
                    "recipient_id": recipient_id,
                    **metadata
                },
                agent_id=agent_id,
                timestamp=datetime.now(),
                tags=tags + ["contribution", "kala"],
                confidence=1.0
            )

            self.memories[memory_id] = memory_entry
            self.agent_memories[agent_id].append(memory_id)
            self._persist_memory(memory_entry)

            # Log event
            self._store_event({
                "type": "contribution_recorded",
                "agent_id": agent_id,
                "contribution_id": contribution.id,
                "kala_value": kala_value,
                "contribution_type": contribution_type.value
            })

            logger.info(
                f"Stored contribution: {agent_id} contributed {kala_value} kala "
                f"({contribution_type.value})"
            )

            return contribution.id

        except Exception as e:
            logger.error(f"Error storing contribution: {e}")
            return None

    def get_contribution_summary(
        self,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get summary of contributions (kala-valued).

        Args:
            agent_id: Specific agent (None = community-wide)
            start_date: Start of period
            end_date: End of period

        Returns:
            Summary of contributions in kala
        """
        if not self.kala_system:
            return {"error": "Kala system not available"}

        return self.kala_system.generate_report(agent_id, start_date, end_date)

    def share_learning(self, source_agent_id: str, target_agent_ids: List[str],
                      learning_type: str) -> bool:
        """Share learning between agents"""
        try:
            # Get relevant memories from source agent
            source_memories = self.get_agent_memories(source_agent_id)

            # Filter by learning type
            relevant_memories = [
                m for m in source_memories
                if learning_type in m.tags or learning_type in m.content.get("type", "")
            ]

            # Share with target agents
            for target_agent_id in target_agent_ids:
                for memory in relevant_memories:
                    # Create shared memory entry
                    shared_memory = MemoryEntry(
                        id=str(uuid.uuid4()),
                        type=MemoryType.KNOWLEDGE,
                        content=memory.content,
                        agent_id=target_agent_id,
                        timestamp=datetime.now(),
                        tags=memory.tags + ["shared_learning"],
                        relationships=[memory.id],
                        confidence=memory.confidence * 0.9  # Slightly reduce confidence for shared knowledge
                    )

                    self.memories[shared_memory.id] = shared_memory
                    self.agent_memories[target_agent_id].append(shared_memory.id)

            # Log sharing event
            self._store_event({
                "type": "learning_shared",
                "source_agent": source_agent_id,
                "target_agents": target_agent_ids,
                "learning_type": learning_type,
                "memories_shared": len(relevant_memories)
            })

            logger.info(f"Shared {len(relevant_memories)} memories from {source_agent_id} to {len(target_agent_ids)} agents")
            return True

        except Exception as e:
            logger.error(f"Error sharing learning: {e}")
            return False
    
    def get_relationship_graph(self) -> Dict[str, List[str]]:
        """Get the relationship graph between memories"""
        return dict(self.relationship_graph)
    
    def get_memory_insights(self, agent_id: str = None) -> Dict[str, Any]:
        """Get insights from memory system"""
        insights = {
            "total_memories": len(self.memories),
            "memory_types": {},
            "agent_contributions": {},
            "popular_tags": {},
            "recent_activity": [],
            "learning_patterns": []
        }
        
        # Count memory types
        for memory in self.memories.values():
            memory_type = memory.type.value
            insights["memory_types"][memory_type] = insights["memory_types"].get(memory_type, 0) + 1
            
            # Count agent contributions
            agent = memory.agent_id
            insights["agent_contributions"][agent] = insights["agent_contributions"].get(agent, 0) + 1
            
            # Count tags
            for tag in memory.tags:
                insights["popular_tags"][tag] = insights["popular_tags"].get(tag, 0) + 1
        
        # Get recent activity
        recent_memories = sorted(
            self.memories.values(), 
            key=lambda m: m.timestamp, 
            reverse=True
        )[:10]
        
        for memory in recent_memories:
            insights["recent_activity"].append({
                "id": memory.id,
                "type": memory.type.value,
                "agent_id": memory.agent_id,
                "timestamp": memory.timestamp.isoformat(),
                "tags": memory.tags[:3]  # Top 3 tags
            })
        
        # Analyze learning patterns
        insights["learning_patterns"] = self._analyze_learning_patterns()
        
        return insights
    
    def _generate_embedding(self, content: Dict[str, Any]) -> np.ndarray:
        """Generate vector embedding for content with model-first fallback."""
        content_str = json.dumps(content, sort_keys=True)

        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode(content_str)
                return np.asarray(embedding, dtype=float)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Embedding model failed, using hash fallback: %s", exc)

        # Deterministic hash-based embedding as a lightweight fallback
        import hashlib

        hash_obj = hashlib.md5(content_str.encode())
        hash_hex = hash_obj.hexdigest()

        vector = np.zeros(self.vector_dimension)
        for i in range(min(len(hash_hex) // 2, self.vector_dimension)):
            vector[i] = int(hash_hex[i * 2 : (i + 1) * 2], 16) / 255.0

        return vector
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _calculate_relevance_score(self, memory: MemoryEntry, query: Dict[str, Any]) -> float:
        """Calculate relevance score based on multiple factors"""
        score = 0.0
        
        # Recency factor (more recent = higher score)
        time_diff = (datetime.now() - memory.timestamp).total_seconds()
        recency_score = 1.0 / (1.0 + time_diff / 86400)  # Decay over 24 hours
        score += recency_score * 0.3
        
        # Access frequency factor
        access_score = min(memory.access_count / 10.0, 1.0)
        score += access_score * 0.2
        
        # Confidence factor
        score += memory.confidence * 0.3
        
        # Tag matching factor
        query_tags = query.get("tags", [])
        if query_tags:
            tag_matches = len(set(query_tags) & set(memory.tags))
            tag_score = tag_matches / len(query_tags)
            score += tag_score * 0.2
        
        return min(score, 1.0)
    
    def _update_relationships(self, memory_id: str, content: Dict[str, Any]):
        """Update relationship graph based on content"""
        # Extract related memory IDs from content
        related_ids = content.get("related_memories", [])
        
        for related_id in related_ids:
            if related_id in self.memories:
                self.relationship_graph[memory_id].append(related_id)
                self.relationship_graph[related_id].append(memory_id)
    
    def _store_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store system event"""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(),
            **event_data
        }
        
        self.event_stream.append(event)
        
        # Persist to database
        cursor = self.memory_db.cursor()
        cursor.execute('''
            INSERT INTO events (id, type, data, timestamp, source_agent, target_agents)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            event["id"],
            event["type"],
            json.dumps(event_data),
            event["timestamp"].isoformat(),
            event_data.get("source_agent", ""),
            json.dumps(event_data.get("target_agents", []))
        ))
        self.memory_db.commit()

        return event

    def record_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        source_agent: str | None = None,
        target_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Public helper for recording events into the shared stream."""

        payload = {
            "type": event_type,
            "data": data,
            "source_agent": source_agent or "",
            "target_agents": target_agents or [],
        }

        return self._store_event(payload)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent events from the in-memory stream."""

        if limit <= 0:
            return []

        return list(self.event_stream)[-limit:]
    
    def _persist_memory(self, memory: MemoryEntry):
        """Persist memory to database"""
        cursor = self.memory_db.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO memories 
            (id, type, content, agent_id, timestamp, tags, relationships, confidence, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            memory.id,
            memory.type.value,
            json.dumps(memory.content),
            memory.agent_id,
            memory.timestamp.isoformat(),
            json.dumps(memory.tags),
            json.dumps(memory.relationships),
            memory.confidence,
            memory.access_count
        ))
        self.memory_db.commit()
    
    def _analyze_learning_patterns(self) -> List[Dict[str, Any]]:
        """Analyze patterns in agent learning"""
        patterns = []
        
        # Analyze memory types by agent
        for agent_id in self.agent_memories:
            agent_memories = self.get_agent_memories(agent_id)
            
            type_counts = {}
            for memory in agent_memories:
                type_counts[memory.type.value] = type_counts.get(memory.type.value, 0) + 1
            
            patterns.append({
                "agent_id": agent_id,
                "learning_focus": max(type_counts.items(), key=lambda x: x[1])[0],
                "total_memories": len(agent_memories),
                "memory_distribution": type_counts
            })
        
        return patterns
    
    def _memory_maintenance_loop(self):
        """Background maintenance loop for memory system"""
        while self.running:
            try:
                # Clean up old, low-confidence memories
                self._cleanup_memories()
                
                # Optimize vector embeddings
                self._optimize_embeddings()
                
                # Update relationship strengths
                self._update_relationship_strengths()
                
            except Exception as e:
                logger.error(f"Memory maintenance error: {e}")
            
            time.sleep(300)  # Run every 5 minutes
    
    def _cleanup_memories(self):
        """Clean up old, low-confidence memories"""
        current_time = datetime.now()
        memories_to_remove = []
        
        for memory_id, memory in self.memories.items():
            # Remove memories older than 30 days with low confidence and access
            time_diff = (current_time - memory.timestamp).total_seconds()
            if (time_diff > 30 * 86400 and 
                memory.confidence < 0.5 and 
                memory.access_count < 3):
                memories_to_remove.append(memory_id)
        
        for memory_id in memories_to_remove:
            self._remove_memory(memory_id)
        
        if memories_to_remove:
            logger.info(f"Cleaned up {len(memories_to_remove)} old memories")
    
    def _optimize_embeddings(self):
        """Optimize vector embeddings for better search performance"""
        # In a real implementation, this would use proper optimization techniques
        pass
    
    def _update_relationship_strengths(self):
        """
        Update relationship strengths based on access patterns.

        Memories that are frequently accessed together become more strongly related.
        This creates emergent knowledge clusters.
        """
        # Track co-access patterns: which memories are retrieved together
        # For simplicity, we'll look at temporal proximity of access

        recent_accesses = []
        time_window = 300  # 5 minutes
        current_time = time.time()

        # Get memories accessed in the recent time window
        for memory_id, memory in self.memories.items():
            if hasattr(memory, 'last_accessed') and memory.last_accessed:
                if current_time - memory.last_accessed < time_window:
                    recent_accesses.append(memory_id)

        # If we have at least 2 recent accesses, strengthen relationships between them
        if len(recent_accesses) >= 2:
            for i in range(len(recent_accesses)):
                for j in range(i + 1, len(recent_accesses)):
                    mem_id_1 = recent_accesses[i]
                    mem_id_2 = recent_accesses[j]

                    # Add bidirectional relationship if not already present
                    if mem_id_2 not in self.relationship_graph[mem_id_1]:
                        self.relationship_graph[mem_id_1].append(mem_id_2)
                        logger.debug(f"Strengthened relationship: {mem_id_1} <-> {mem_id_2}")

                    if mem_id_1 not in self.relationship_graph[mem_id_2]:
                        self.relationship_graph[mem_id_2].append(mem_id_1)
    
    def _remove_memory(self, memory_id: str):
        """Remove memory from system"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            
            # Remove from agent memory list
            if memory.agent_id in self.agent_memories:
                if memory_id in self.agent_memories[memory.agent_id]:
                    self.agent_memories[memory.agent_id].remove(memory_id)
            
            # Remove from main memory
            del self.memories[memory_id]
            
            # Remove vector embedding
            if memory_id in self.vector_embeddings:
                del self.vector_embeddings[memory_id]
            
            # Remove from relationship graph
            if memory_id in self.relationship_graph:
                del self.relationship_graph[memory_id]
    
    def shutdown(self):
        """Shutdown the memory system"""
        self.running = False
        if self.memory_thread:
            self.memory_thread.join(timeout=10)
        
        if self.memory_db:
            self.memory_db.close()
        
        logger.info("Community Memory System shutdown complete")

# Global memory instance
community_memory = CommunityMemory()
