"""
Last-Write-Wins Element Set (LWW-Element-Set) CRDT for memory storage.

Provides conflict-free replication of community memories across
distributed Vessels nodes.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Set, List
from datetime import datetime
import uuid
import json

from vessels.crdt.vector_clock import VectorClock, Timestamp


@dataclass
class CRDTElement:
    """
    Element in LWW-Element-Set with timestamp and node origin.

    Each element is immutable and carries:
    - value: The actual data
    - timestamp: Hybrid timestamp for total ordering
    - deleted: Tombstone flag for removals
    """
    key: str
    value: Any
    timestamp: Timestamp
    deleted: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize element to dictionary."""
        return {
            "key": self.key,
            "value": self.value,
            "timestamp": {
                "vector_clock": self.timestamp.vector_clock,
                "wall_clock": self.timestamp.wall_clock.isoformat(),
                "node_id": self.timestamp.node_id
            },
            "deleted": self.deleted
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CRDTElement':
        """Deserialize element from dictionary."""
        timestamp_data = data["timestamp"]
        timestamp = Timestamp(
            vector_clock=timestamp_data["vector_clock"],
            wall_clock=datetime.fromisoformat(timestamp_data["wall_clock"]),
            node_id=timestamp_data["node_id"]
        )

        return cls(
            key=data["key"],
            value=data["value"],
            timestamp=timestamp,
            deleted=data.get("deleted", False)
        )


class LWWElementSet:
    """
    Last-Write-Wins Element Set CRDT.

    State-based CRDT that resolves conflicts using timestamps.
    When two writes conflict, the one with the later timestamp wins.

    Properties:
    - Commutative: merge(A, B) = merge(B, A)
    - Associative: merge(merge(A, B), C) = merge(A, merge(B, C))
    - Idempotent: merge(A, A) = A

    Deletion is handled with tombstones to ensure deleted elements
    stay deleted even if merged with older versions.
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize LWW-Element-Set.

        Args:
            node_id: Unique identifier for this node
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.vector_clock = VectorClock(self.node_id)
        self.elements: Dict[str, CRDTElement] = {}

    def add(self, key: str, value: Any) -> None:
        """
        Add or update an element.

        Args:
            key: Element identifier
            value: Element data (must be JSON-serializable)
        """
        # Increment vector clock for local event
        self.vector_clock.increment()

        # Create element with current timestamp
        element = CRDTElement(
            key=key,
            value=value,
            timestamp=self.vector_clock.get_timestamp(),
            deleted=False
        )

        # Only update if newer than existing (or doesn't exist)
        if key not in self.elements or element.timestamp > self.elements[key].timestamp:
            self.elements[key] = element

    def remove(self, key: str) -> None:
        """
        Remove an element (tombstone).

        Args:
            key: Element identifier to remove
        """
        # Increment vector clock
        self.vector_clock.increment()

        # Create tombstone
        tombstone = CRDTElement(
            key=key,
            value=None,  # Tombstone has no value
            timestamp=self.vector_clock.get_timestamp(),
            deleted=True
        )

        # Only update if newer than existing (or doesn't exist)
        if key not in self.elements or tombstone.timestamp > self.elements[key].timestamp:
            self.elements[key] = tombstone

    def get(self, key: str) -> Optional[Any]:
        """
        Get element value.

        Args:
            key: Element identifier

        Returns:
            Element value or None if not exists/deleted
        """
        element = self.elements.get(key)
        if element and not element.deleted:
            return element.value
        return None

    def contains(self, key: str) -> bool:
        """
        Check if element exists and is not deleted.

        Args:
            key: Element identifier

        Returns:
            True if element exists and not deleted
        """
        element = self.elements.get(key)
        return element is not None and not element.deleted

    def keys(self) -> Set[str]:
        """Get all non-deleted element keys."""
        return {
            key for key, element in self.elements.items()
            if not element.deleted
        }

    def values(self) -> List[Any]:
        """Get all non-deleted element values."""
        return [
            element.value for element in self.elements.values()
            if not element.deleted
        ]

    def items(self) -> List[tuple]:
        """Get all non-deleted (key, value) pairs."""
        return [
            (key, element.value) for key, element in self.elements.items()
            if not element.deleted
        ]

    def merge(self, other: 'LWWElementSet') -> 'LWWElementSet':
        """
        Merge with another LWW-Element-Set.

        Merge rule: For each element, take the version with
        the latest timestamp.

        Args:
            other: Other LWW-Element-Set to merge

        Returns:
            New merged LWW-Element-Set
        """
        # Create new instance for merged result
        merged = LWWElementSet(self.node_id)

        # Merge vector clocks
        merged.vector_clock.update(other.vector_clock.to_dict())

        # Merge elements: take max timestamp for each key
        all_keys = set(self.elements.keys()) | set(other.elements.keys())

        for key in all_keys:
            self_element = self.elements.get(key)
            other_element = other.elements.get(key)

            if self_element and other_element:
                # Both have element - take newer
                if other_element.timestamp > self_element.timestamp:
                    merged.elements[key] = other_element
                else:
                    merged.elements[key] = self_element
            elif self_element:
                # Only self has element
                merged.elements[key] = self_element
            else:
                # Only other has element
                merged.elements[key] = other_element

        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "node_id": self.node_id,
            "vector_clock": self.vector_clock.to_dict(),
            "elements": {
                key: element.to_dict()
                for key, element in self.elements.items()
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LWWElementSet':
        """Deserialize from dictionary."""
        lww = cls(data["node_id"])
        lww.vector_clock = VectorClock.from_dict(
            data["vector_clock"],
            data["node_id"]
        )
        lww.elements = {
            key: CRDTElement.from_dict(elem_data)
            for key, elem_data in data["elements"].items()
        }
        return lww

    def __len__(self) -> int:
        """Count non-deleted elements."""
        return sum(1 for element in self.elements.values() if not element.deleted)

    def __repr__(self) -> str:
        return f"LWWElementSet(node={self.node_id}, size={len(self)})"


class CRDTMemory:
    """
    CRDT-backed memory storage for community memories.

    Wrapper around LWW-Element-Set that provides a convenient
    interface for memory operations compatible with existing
    CommunityMemory API.
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize CRDT memory store.

        Args:
            node_id: Unique identifier for this Vessels node
        """
        self.lww_set = LWWElementSet(node_id)

    def store_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> None:
        """
        Store a memory.

        Args:
            memory_id: Unique memory identifier
            memory_data: Memory data (must be JSON-serializable)
        """
        self.lww_set.add(memory_id, memory_data)

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory data or None if not found
        """
        return self.lww_set.get(memory_id)

    def delete_memory(self, memory_id: str) -> None:
        """
        Delete a memory (tombstone).

        Args:
            memory_id: Memory identifier
        """
        self.lww_set.remove(memory_id)

    def all_memories(self) -> List[Dict[str, Any]]:
        """Get all non-deleted memories."""
        return self.lww_set.values()

    def memory_ids(self) -> Set[str]:
        """Get all non-deleted memory IDs."""
        return self.lww_set.keys()

    def merge_with(self, other: 'CRDTMemory') -> 'CRDTMemory':
        """
        Merge with another CRDT memory store.

        Args:
            other: Other CRDT memory store

        Returns:
            New merged CRDT memory store
        """
        merged = CRDTMemory(self.lww_set.node_id)
        merged.lww_set = self.lww_set.merge(other.lww_set)
        return merged

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return self.lww_set.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CRDTMemory':
        """Deserialize from dictionary."""
        memory = cls()
        memory.lww_set = LWWElementSet.from_dict(data)
        return memory

    def __len__(self) -> int:
        """Count memories."""
        return len(self.lww_set)

    def __repr__(self) -> str:
        return f"CRDTMemory(node={self.lww_set.node_id}, memories={len(self)})"
