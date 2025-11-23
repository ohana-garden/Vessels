"""
CRDT backend for Community Memory.

Provides conflict-free, offline-first memory storage using
Last-Write-Wins Element Set CRDT.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from vessels.crdt.memory import CRDTMemory, CRDTElement
from vessels.crdt.sync import SyncManager

logger = logging.getLogger(__name__)


class CRDTMemoryBackend:
    """
    CRDT-backed memory storage for community memories.

    Provides offline-first, eventually-consistent memory storage
    that can sync across distributed Vessels nodes.
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize CRDT memory backend.

        Args:
            node_id: Unique identifier for this Vessels node
        """
        self.crdt_memory = CRDTMemory(node_id=node_id)
        self.sync_manager = SyncManager(node_id=node_id or self.crdt_memory.lww_set.node_id)
        logger.info(f"Initialized CRDT memory backend (node={self.crdt_memory.lww_set.node_id})")

    def store_memory(self, memory_entry) -> None:
        """
        Store a memory entry.

        Args:
            memory_entry: MemoryEntry object from community_memory.py
        """
        # Convert MemoryEntry to dict for CRDT storage
        memory_data = {
            "id": memory_entry.id,
            "type": memory_entry.type.value,
            "content": memory_entry.content,
            "agent_id": memory_entry.agent_id,
            "timestamp": memory_entry.timestamp.isoformat(),
            "tags": memory_entry.tags,
            "relationships": memory_entry.relationships,
            "confidence": memory_entry.confidence,
            "access_count": memory_entry.access_count
        }

        self.crdt_memory.store_memory(memory_entry.id, memory_data)
        self.sync_manager.protocol.increment_version("memory")

        logger.debug(f"Stored memory in CRDT: {memory_entry.id}")

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory data dict or None if not found
        """
        return self.crdt_memory.get_memory(memory_id)

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Get all non-deleted memories."""
        return self.crdt_memory.all_memories()

    def delete_memory(self, memory_id: str) -> None:
        """
        Delete a memory (tombstone).

        Args:
            memory_id: Memory identifier
        """
        self.crdt_memory.delete_memory(memory_id)
        self.sync_manager.protocol.increment_version("memory")

    def merge_with_peer(self, peer_memory_backend: 'CRDTMemoryBackend') -> None:
        """
        Merge memory state with another CRDT memory backend.

        Args:
            peer_memory_backend: Another CRDT memory backend to merge with
        """
        self.crdt_memory = self.crdt_memory.merge_with(peer_memory_backend.crdt_memory)
        logger.info(f"Merged with peer (total memories: {len(self.crdt_memory)})")

    def generate_sync_delta(self, target_node_id: str) -> Optional[Any]:
        """
        Generate delta for synchronization with target node.

        Args:
            target_node_id: Node to sync with

        Returns:
            Delta object or None if already synced
        """
        return self.sync_manager.protocol.generate_delta(
            target_node_id=target_node_id,
            data_type="memory",
            full_state=self.crdt_memory.to_dict()
        )

    def apply_sync_delta(self, delta) -> None:
        """
        Apply sync delta from peer.

        Args:
            delta: Delta object from peer
        """
        def merge_memory_states(current_state, delta_data):
            # Deserialize delta data to CRDT memory
            delta_memory = CRDTMemory.from_dict(delta_data)
            # Merge with current state
            return current_state.merge_with(delta_memory)

        self.crdt_memory = self.sync_manager.protocol.apply_delta(
            delta=delta,
            current_state=self.crdt_memory,
            merge_function=merge_memory_states
        )

        logger.info(f"Applied sync delta from {delta.source_node_id}")

    def export_state(self) -> Dict[str, Any]:
        """Export CRDT state for persistence."""
        return self.crdt_memory.to_dict()

    def import_state(self, state: Dict[str, Any]) -> None:
        """Import CRDT state from persistence."""
        self.crdt_memory = CRDTMemory.from_dict(state)
        logger.info(f"Imported CRDT state ({len(self.crdt_memory)} memories)")

    def get_stats(self) -> Dict[str, Any]:
        """Get CRDT backend statistics."""
        return {
            "node_id": self.crdt_memory.lww_set.node_id,
            "memory_count": len(self.crdt_memory),
            "vector_clock": self.crdt_memory.lww_set.vector_clock.to_dict(),
            "sync_peers": len(self.sync_manager.sync_peers),
            "local_version": self.sync_manager.protocol.local_version
        }

    def __repr__(self) -> str:
        return (
            f"CRDTMemoryBackend(node={self.crdt_memory.lww_set.node_id}, "
            f"memories={len(self.crdt_memory)})"
        )
