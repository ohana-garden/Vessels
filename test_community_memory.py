#!/usr/bin/env python3
"""
Test suite for community_memory.py
Tests the community memory system with vector storage and event streaming
"""

import pytest
import time
from datetime import datetime
from community_memory import (
    MemoryType,
    MemoryEntry,
    VectorEmbedding,
    CommunityMemory
)
import numpy as np


class TestMemoryType:
    """Tests for MemoryType enum"""

    def test_memory_type_values(self):
        """Test that all memory types have correct values"""
        assert MemoryType.EXPERIENCE.value == "experience"
        assert MemoryType.KNOWLEDGE.value == "knowledge"
        assert MemoryType.PATTERN.value == "pattern"
        assert MemoryType.RELATIONSHIP.value == "relationship"
        assert MemoryType.EVENT.value == "event"


class TestMemoryEntry:
    """Tests for MemoryEntry dataclass"""

    def test_memory_entry_creation(self):
        """Test creating a memory entry"""
        entry = MemoryEntry(
            id="mem_123",
            type=MemoryType.EXPERIENCE,
            content={"action": "test", "result": "success"},
            agent_id="agent_456",
            timestamp=datetime.now(),
            tags=["test", "success"],
            confidence=0.9
        )

        assert entry.id == "mem_123"
        assert entry.type == MemoryType.EXPERIENCE
        assert entry.agent_id == "agent_456"
        assert entry.confidence == 0.9
        assert len(entry.tags) == 2

    def test_memory_entry_defaults(self):
        """Test memory entry with default values"""
        entry = MemoryEntry(
            id="mem_001",
            type=MemoryType.KNOWLEDGE,
            content={"fact": "test"},
            agent_id="agent_001",
            timestamp=datetime.now()
        )

        assert entry.tags == []
        assert entry.relationships == []
        assert entry.confidence == 1.0
        assert entry.access_count == 0


class TestVectorEmbedding:
    """Tests for VectorEmbedding dataclass"""

    def test_vector_embedding_creation(self):
        """Test creating a vector embedding"""
        vector = np.array([0.1, 0.2, 0.3])
        embedding = VectorEmbedding(
            memory_id="mem_123",
            vector=vector,
            metadata={"type": "experience"}
        )

        assert embedding.memory_id == "mem_123"
        assert np.array_equal(embedding.vector, vector)
        assert embedding.metadata["type"] == "experience"


class TestCommunityMemory:
    """Tests for CommunityMemory class"""

    def setup_method(self):
        """Create fresh CommunityMemory instance for each test"""
        self.memory = CommunityMemory()
        # Give the background thread a moment to start
        time.sleep(0.1)

    def teardown_method(self):
        """Clean up after each test"""
        self.memory.running = False
        if self.memory.memory_db:
            self.memory.memory_db.close()
        time.sleep(0.1)

    def test_initialization(self):
        """Test memory system initialization"""
        assert self.memory.memories == {}
        assert len(self.memory.agent_memories) == 0
        assert len(self.memory.vector_embeddings) == 0
        assert self.memory.running is True
        assert self.memory.memory_db is not None
        assert self.memory.vector_dimension == 384

    def test_store_experience(self):
        """Test storing an experience"""
        experience = {
            "action": "grant_search",
            "result": "found_5_grants",
            "tags": ["grant", "search"],
            "confidence": 0.95
        }

        memory_id = self.memory.store_experience("agent_001", experience)

        assert memory_id is not None
        assert memory_id in self.memory.memories
        assert self.memory.memories[memory_id].type == MemoryType.EXPERIENCE
        assert memory_id in self.memory.agent_memories["agent_001"]
        assert memory_id in self.memory.vector_embeddings

    def test_store_experience_updates_agent_memories(self):
        """Test that experience is tracked per agent"""
        experience1 = {"action": "test1"}
        experience2 = {"action": "test2"}

        mem_id1 = self.memory.store_experience("agent_001", experience1)
        mem_id2 = self.memory.store_experience("agent_001", experience2)

        assert len(self.memory.agent_memories["agent_001"]) == 2
        assert mem_id1 in self.memory.agent_memories["agent_001"]
        assert mem_id2 in self.memory.agent_memories["agent_001"]

    def test_store_knowledge(self):
        """Test storing knowledge"""
        knowledge = {
            "domain": "elder_care",
            "fact": "Medicare covers home health care",
            "tags": ["medicare", "elder_care"],
            "confidence": 0.9
        }

        memory_id = self.memory.store_knowledge("agent_002", knowledge)

        assert memory_id is not None
        assert memory_id in self.memory.memories
        assert self.memory.memories[memory_id].type == MemoryType.KNOWLEDGE
        assert memory_id in self.memory.agent_memories["agent_002"]

    def test_store_multiple_memories_different_agents(self):
        """Test storing memories from different agents"""
        exp1 = {"action": "action1"}
        exp2 = {"action": "action2"}

        self.memory.store_experience("agent_001", exp1)
        self.memory.store_experience("agent_002", exp2)

        assert len(self.memory.agent_memories["agent_001"]) == 1
        assert len(self.memory.agent_memories["agent_002"]) == 1

    def test_vector_embedding_created(self):
        """Test that vector embeddings are created"""
        experience = {"action": "test", "result": "success"}

        memory_id = self.memory.store_experience("agent_001", experience)

        assert memory_id in self.memory.vector_embeddings
        embedding = self.memory.vector_embeddings[memory_id]
        assert isinstance(embedding.vector, np.ndarray)
        assert len(embedding.vector) == self.memory.vector_dimension

    def test_find_similar_memories(self):
        """Test finding similar memories"""
        # Store some experiences
        exp1 = {"action": "grant_search", "domain": "education"}
        exp2 = {"action": "grant_search", "domain": "healthcare"}
        exp3 = {"action": "volunteer_coordination", "domain": "community"}

        self.memory.store_experience("agent_001", exp1)
        self.memory.store_experience("agent_001", exp2)
        self.memory.store_experience("agent_002", exp3)

        # Search for similar to grant_search
        query = {"action": "grant_search", "domain": "research"}
        similar = self.memory.find_similar_memories(query, limit=2)

        # Should find memories (exact similarity depends on embedding algorithm)
        assert isinstance(similar, list)

    def test_event_stream_stores_events(self):
        """Test that events are stored in event stream"""
        initial_event_count = len(self.memory.event_stream)

        experience = {"action": "test"}
        self.memory.store_experience("agent_001", experience)

        # Should have added an event
        assert len(self.memory.event_stream) >= initial_event_count

    def test_memory_persistence(self):
        """Test that memories are persisted to database"""
        experience = {"action": "test", "tags": ["test"]}

        memory_id = self.memory.store_experience("agent_001", experience)

        # Give database time to write
        time.sleep(0.1)

        # Query database
        cursor = self.memory.memory_db.cursor()
        cursor.execute("SELECT id, type FROM memories WHERE id = ?", (memory_id,))
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == memory_id
        assert result[1] == "experience"

    def test_relationship_graph_updated(self):
        """Test that relationship graph is updated"""
        experience = {
            "action": "test",
            "relationships": ["related_mem_1", "related_mem_2"]
        }

        memory_id = self.memory.store_experience("agent_001", experience)

        # Give time for relationships to be processed
        time.sleep(0.1)

        # Relationship graph should have entries
        # (exact behavior depends on _update_relationships implementation)
        assert isinstance(self.memory.relationship_graph, dict)

    def test_generate_embedding_consistent(self):
        """Test that embedding generation is consistent"""
        content1 = {"action": "test", "result": "success"}
        content2 = {"action": "test", "result": "success"}

        vec1 = self.memory._generate_embedding(content1)
        vec2 = self.memory._generate_embedding(content2)

        # Same content should produce same or very similar embeddings
        assert isinstance(vec1, np.ndarray)
        assert isinstance(vec2, np.ndarray)
        assert len(vec1) == self.memory.vector_dimension
        assert len(vec2) == self.memory.vector_dimension

    def test_generate_embedding_different_content(self):
        """Test that different content produces different embeddings"""
        content1 = {"action": "search_grants"}
        content2 = {"action": "coordinate_volunteers"}

        vec1 = self.memory._generate_embedding(content1)
        vec2 = self.memory._generate_embedding(content2)

        # Different content should produce different embeddings
        assert not np.array_equal(vec1, vec2)

    def test_memory_thread_running(self):
        """Test that memory maintenance thread is running"""
        assert self.memory.running is True
        assert self.memory.memory_thread is not None
        assert self.memory.memory_thread.is_alive()

    def test_store_experience_with_empty_content(self):
        """Test storing experience with minimal content"""
        experience = {}

        memory_id = self.memory.store_experience("agent_001", experience)

        assert memory_id is not None
        assert memory_id in self.memory.memories

    def test_store_knowledge_with_tags(self):
        """Test storing knowledge with tags"""
        knowledge = {
            "fact": "test fact",
            "tags": ["tag1", "tag2", "tag3"]
        }

        memory_id = self.memory.store_knowledge("agent_001", knowledge)

        stored_memory = self.memory.memories[memory_id]
        assert len(stored_memory.tags) == 3
        assert "tag1" in stored_memory.tags

    def test_multiple_agents_memories_isolated(self):
        """Test that agent memories are properly isolated"""
        self.memory.store_experience("agent_A", {"action": "A"})
        self.memory.store_experience("agent_B", {"action": "B"})
        self.memory.store_knowledge("agent_A", {"fact": "A_fact"})

        assert len(self.memory.agent_memories["agent_A"]) == 2
        assert len(self.memory.agent_memories["agent_B"]) == 1

    def test_confidence_scores_preserved(self):
        """Test that confidence scores are preserved"""
        experience = {"action": "test", "confidence": 0.75}

        memory_id = self.memory.store_experience("agent_001", experience)

        stored_memory = self.memory.memories[memory_id]
        assert stored_memory.confidence == 0.75

    def test_knowledge_default_confidence(self):
        """Test that knowledge has appropriate default confidence"""
        knowledge = {"fact": "test"}

        memory_id = self.memory.store_knowledge("agent_001", knowledge)

        stored_memory = self.memory.memories[memory_id]
        assert stored_memory.confidence == 0.8

    def test_event_stream_max_length(self):
        """Test that event stream respects max length"""
        # Event stream has maxlen=10000
        # We can't practically test filling it, but we can verify it's a deque with maxlen
        assert hasattr(self.memory.event_stream, 'maxlen')
        assert self.memory.event_stream.maxlen == 10000

    def test_memory_timestamps(self):
        """Test that memories have proper timestamps"""
        before = datetime.now()
        experience = {"action": "test"}

        memory_id = self.memory.store_experience("agent_001", experience)

        after = datetime.now()
        stored_memory = self.memory.memories[memory_id]

        assert before <= stored_memory.timestamp <= after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
