#!/usr/bin/env python3
"""
COMMUNITY MEMORY SYSTEM
In-memory storage for agent coordination.
All data stored in memory, managed through AgentZeroCore.
"""

import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    PATTERN = "pattern"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    CONTRIBUTION = "contribution"


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


class CommunityMemory:
    """In-memory storage for agent coordination."""

    def __init__(self):
        """Initialize in-memory Community Memory system."""
        # In-memory storage
        self.memory_store: Dict[str, MemoryEntry] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self.agent_memories: Dict[str, List[str]] = defaultdict(list)
        self.events: List[Dict[str, Any]] = []
        self.relationships: Dict[str, List[str]] = defaultdict(list)

        self._lock = threading.RLock()

        # Initialize Kala integration
        self._init_kala_system()

        # Simple hash-based embeddings
        self._load_embedding_model()

        logger.info("Community Memory System initialized")

    def _init_kala_system(self):
        """Initialize Kala value system integration."""
        try:
            from kala import kala_system
            self.kala_system = kala_system
            logger.info("Kala system integrated with Community Memory")
        except Exception as e:
            logger.warning(f"Kala system not available: {e}")
            self.kala_system = None

    def _load_embedding_model(self):
        """Load embedding model (falls back to hash)."""
        self.embedding_model = None
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            logger.warning("Falling back to hash embeddings: No module named 'sentence_transformers'")

    def store_experience(self, agent_id: str, experience: Dict[str, Any]) -> str:
        """Store an experience memory."""
        memory_id = str(uuid.uuid4())

        entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.EXPERIENCE,
            content=experience,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            tags=experience.get("tags", []),
            confidence=experience.get("confidence", 1.0)
        )

        with self._lock:
            self.memory_store[memory_id] = entry
            self.agent_memories[agent_id].append(memory_id)

            # Generate embedding
            self.embeddings[memory_id] = self._generate_embedding(experience)

        logger.info(f"Stored experience for agent {agent_id}: {memory_id}")
        return memory_id

    def store_knowledge(self, agent_id: str, knowledge: Dict[str, Any]) -> str:
        """Store a knowledge memory."""
        memory_id = str(uuid.uuid4())

        entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.KNOWLEDGE,
            content=knowledge,
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            tags=knowledge.get("tags", []),
            confidence=knowledge.get("confidence", 1.0)
        )

        with self._lock:
            self.memory_store[memory_id] = entry
            self.agent_memories[agent_id].append(memory_id)
            self.embeddings[memory_id] = self._generate_embedding(knowledge)

        logger.info(f"Stored knowledge for agent {agent_id}: {memory_id}")
        return memory_id

    def find_similar_memories(self, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Find memories similar to query."""
        query_embedding = self._generate_embedding(query)

        similarities = []
        with self._lock:
            for memory_id, embedding in self.embeddings.items():
                similarity = self._cosine_similarity(query_embedding, embedding)
                similarities.append((memory_id, similarity))

        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for memory_id, score in similarities[:limit]:
            if memory_id in self.memory_store:
                entry = self.memory_store[memory_id]
                results.append({
                    "id": entry.id,
                    "type": entry.type.value,
                    "content": entry.content,
                    "agent_id": entry.agent_id,
                    "similarity": score
                })

        return results

    def get_agent_memories(self, agent_id: str, memory_type: MemoryType = None) -> List[MemoryEntry]:
        """Get all memories for an agent."""
        with self._lock:
            memory_ids = self.agent_memories.get(agent_id, [])
            memories = [self.memory_store[mid] for mid in memory_ids if mid in self.memory_store]

            if memory_type:
                memories = [m for m in memories if m.type == memory_type]

            return memories

    def record_event(self, event_type: str, agent_id: str, data: Dict[str, Any]) -> str:
        """Record an event."""
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "type": event_type,
            "agent_id": agent_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        with self._lock:
            self.events.append(event)

        return event_id

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent events."""
        with self._lock:
            return self.events[-limit:]

    def store_contribution(self, agent_id: str, contribution_data: Dict[str, Any]) -> Optional[str]:
        """Store a Kala-valued contribution."""
        if not self.kala_system:
            logger.warning("Kala system not available for contribution tracking")
            return None

        memory_id = str(uuid.uuid4())

        entry = MemoryEntry(
            id=memory_id,
            type=MemoryType.CONTRIBUTION,
            content=contribution_data,
            agent_id=agent_id,
            timestamp=datetime.utcnow()
        )

        with self._lock:
            self.memory_store[memory_id] = entry
            self.agent_memories[agent_id].append(memory_id)

        return memory_id

    def _generate_embedding(self, content: Dict[str, Any]) -> np.ndarray:
        """Generate embedding for content."""
        text = str(content)

        if self.embedding_model:
            return self.embedding_model.encode(text)

        # Fallback: simple hash-based embedding
        hash_val = hash(text)
        np.random.seed(abs(hash_val) % (2**32))
        return np.random.randn(384)

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between vectors."""
        if vec1 is None or vec2 is None:
            return 0.0
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def get_memory_insights(self, agent_id: str = None) -> Dict[str, Any]:
        """Get memory system insights."""
        with self._lock:
            total = len(self.memory_store)
            by_type = defaultdict(int)
            for entry in self.memory_store.values():
                by_type[entry.type.value] += 1

            return {
                "total_memories": total,
                "by_type": dict(by_type),
                "total_agents": len(self.agent_memories),
                "total_events": len(self.events)
            }


# Global instance
community_memory = CommunityMemory()
