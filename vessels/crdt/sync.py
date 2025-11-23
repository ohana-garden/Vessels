"""
Synchronization protocol for CRDT state exchange.

Provides efficient delta-state synchronization for CRDT memories
and Kala accounts across distributed Vessels nodes.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Set
from enum import Enum
import json
import hashlib


class SyncState(Enum):
    """State of synchronization between nodes."""
    UNSYNCED = "unsynced"
    IN_PROGRESS = "in_progress"
    SYNCED = "synced"
    ERROR = "error"


@dataclass
class Delta:
    """
    Delta state for efficient synchronization.

    Instead of sending entire CRDT state, only send changes (delta)
    since last sync. This reduces bandwidth usage significantly.
    """
    source_node_id: str
    target_node_id: str
    delta_type: str  # "memory", "kala", "full"
    data: Dict[str, Any]
    version: int  # For tracking delta sequence

    def to_json(self) -> str:
        """Serialize delta to JSON."""
        return json.dumps({
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "delta_type": self.delta_type,
            "data": self.data,
            "version": self.version
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'Delta':
        """Deserialize delta from JSON."""
        data = json.loads(json_str)
        return cls(**data)

    def checksum(self) -> str:
        """
        Calculate checksum for integrity verification.

        Returns:
            SHA-256 hash of delta data
        """
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class SyncProtocol:
    """
    CRDT synchronization protocol.

    Implements efficient delta-state synchronization:
    1. Nodes maintain version vectors (last known state from each node)
    2. On sync request, generate delta containing only new changes
    3. Send delta to target node
    4. Target node merges delta and updates version vector

    This approach minimizes network traffic compared to sending
    full state every time.
    """

    def __init__(self, node_id: str):
        """
        Initialize sync protocol.

        Args:
            node_id: This Vessels node's unique identifier
        """
        self.node_id = node_id
        # Version vectors: track last known state from each node
        # Format: {node_id: {data_type: version}}
        self.version_vectors: Dict[str, Dict[str, int]] = {}
        # Local version counter
        self.local_version: Dict[str, int] = {
            "memory": 0,
            "kala": 0
        }

    def generate_delta(
        self,
        target_node_id: str,
        data_type: str,
        full_state: Dict[str, Any]
    ) -> Optional[Delta]:
        """
        Generate delta for synchronization.

        Args:
            target_node_id: Node to sync with
            data_type: Type of data ("memory" or "kala")
            full_state: Current full CRDT state

        Returns:
            Delta containing changes since last sync, or None if already synced
        """
        # Get last known version for target node
        if target_node_id not in self.version_vectors:
            self.version_vectors[target_node_id] = {}

        last_version = self.version_vectors[target_node_id].get(data_type, 0)
        current_version = self.local_version[data_type]

        if current_version <= last_version:
            # No new changes
            return None

        # Create delta (for state-based CRDTs, delta = full state)
        # For more efficient delta-state CRDTs, could extract only changed elements
        delta = Delta(
            source_node_id=self.node_id,
            target_node_id=target_node_id,
            delta_type=data_type,
            data=full_state,
            version=current_version
        )

        return delta

    def apply_delta(
        self,
        delta: Delta,
        current_state: Any,
        merge_function: callable
    ) -> Any:
        """
        Apply delta to current state.

        Args:
            delta: Delta to apply
            current_state: Current CRDT state
            merge_function: Function to merge delta with current state

        Returns:
            New merged state
        """
        # Verify delta is for this node
        if delta.target_node_id != self.node_id:
            raise ValueError(
                f"Delta target mismatch: expected {self.node_id}, "
                f"got {delta.target_node_id}"
            )

        # Merge delta into current state using provided merge function
        # For LWW-Element-Set: current_state.merge(delta_state)
        # For G-Counter: current_state.merge(delta_state)
        new_state = merge_function(current_state, delta.data)

        # Update version vector
        if delta.source_node_id not in self.version_vectors:
            self.version_vectors[delta.source_node_id] = {}

        self.version_vectors[delta.source_node_id][delta.delta_type] = delta.version

        return new_state

    def increment_version(self, data_type: str) -> None:
        """
        Increment local version on state change.

        Args:
            data_type: Type of data that changed
        """
        self.local_version[data_type] += 1

    def get_sync_state(self, target_node_id: str, data_type: str) -> SyncState:
        """
        Get synchronization state with target node.

        Args:
            target_node_id: Node to check sync state with
            data_type: Type of data

        Returns:
            Current sync state
        """
        if target_node_id not in self.version_vectors:
            return SyncState.UNSYNCED

        last_version = self.version_vectors[target_node_id].get(data_type, 0)
        current_version = self.local_version[data_type]

        if current_version == last_version:
            return SyncState.SYNCED
        else:
            return SyncState.UNSYNCED

    def full_sync_required(self, target_node_id: str) -> bool:
        """
        Check if full sync is required with target node.

        Full sync required if we've never synced before or if
        version vectors are too far apart.

        Args:
            target_node_id: Node to check

        Returns:
            True if full sync needed
        """
        if target_node_id not in self.version_vectors:
            return True

        # Check if version gap is too large (>100 versions)
        for data_type in ["memory", "kala"]:
            last_version = self.version_vectors[target_node_id].get(data_type, 0)
            current_version = self.local_version[data_type]

            if current_version - last_version > 100:
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize sync protocol state."""
        return {
            "node_id": self.node_id,
            "version_vectors": self.version_vectors,
            "local_version": self.local_version
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncProtocol':
        """Deserialize sync protocol state."""
        protocol = cls(data["node_id"])
        protocol.version_vectors = data["version_vectors"]
        protocol.local_version = data["local_version"]
        return protocol

    def __repr__(self) -> str:
        return (
            f"SyncProtocol(node={self.node_id}, "
            f"memory_v={self.local_version['memory']}, "
            f"kala_v={self.local_version['kala']}, "
            f"peers={len(self.version_vectors)})"
        )


class SyncManager:
    """
    High-level sync manager for orchestrating CRDT synchronization.

    Manages periodic syncs, handles network failures, and coordinates
    multiple data types (memory, Kala).
    """

    def __init__(self, node_id: str):
        """
        Initialize sync manager.

        Args:
            node_id: This Vessels node's identifier
        """
        self.node_id = node_id
        self.protocol = SyncProtocol(node_id)
        self.sync_peers: Set[str] = set()  # Known peers to sync with
        self.sync_interval_seconds = 60  # Default: sync every minute

    def add_peer(self, peer_node_id: str) -> None:
        """Add peer node for synchronization."""
        self.sync_peers.add(peer_node_id)

    def remove_peer(self, peer_node_id: str) -> None:
        """Remove peer node from synchronization."""
        self.sync_peers.discard(peer_node_id)

    def sync_with_peer(
        self,
        peer_node_id: str,
        memory_state: Any,
        kala_state: Any,
        send_delta_callback: callable,
        merge_memory_callback: callable,
        merge_kala_callback: callable
    ) -> Dict[str, SyncState]:
        """
        Synchronize with a peer node.

        Args:
            peer_node_id: Peer to sync with
            memory_state: Current memory CRDT state
            kala_state: Current Kala CRDT state
            send_delta_callback: Function to send delta to peer (delta) -> None
            merge_memory_callback: Function to merge memory states
            merge_kala_callback: Function to merge Kala states

        Returns:
            Dictionary of sync states for each data type
        """
        results = {}

        # Sync memory
        memory_delta = self.protocol.generate_delta(
            peer_node_id,
            "memory",
            memory_state.to_dict() if hasattr(memory_state, 'to_dict') else memory_state
        )

        if memory_delta:
            send_delta_callback(memory_delta)
            results["memory"] = SyncState.IN_PROGRESS
        else:
            results["memory"] = SyncState.SYNCED

        # Sync Kala
        kala_delta = self.protocol.generate_delta(
            peer_node_id,
            "kala",
            kala_state.to_dict() if hasattr(kala_state, 'to_dict') else kala_state
        )

        if kala_delta:
            send_delta_callback(kala_delta)
            results["kala"] = SyncState.IN_PROGRESS
        else:
            results["kala"] = SyncState.SYNCED

        return results

    def receive_delta(
        self,
        delta: Delta,
        memory_state: Any,
        kala_state: Any,
        merge_memory_callback: callable,
        merge_kala_callback: callable
    ) -> Any:
        """
        Receive and apply delta from peer.

        Args:
            delta: Received delta
            memory_state: Current memory state
            kala_state: Current Kala state
            merge_memory_callback: Memory merge function
            merge_kala_callback: Kala merge function

        Returns:
            Updated state (memory or Kala depending on delta type)
        """
        if delta.delta_type == "memory":
            return self.protocol.apply_delta(
                delta,
                memory_state,
                merge_memory_callback
            )
        elif delta.delta_type == "kala":
            return self.protocol.apply_delta(
                delta,
                kala_state,
                merge_kala_callback
            )
        else:
            raise ValueError(f"Unknown delta type: {delta.delta_type}")

    def __repr__(self) -> str:
        return (
            f"SyncManager(node={self.node_id}, "
            f"peers={len(self.sync_peers)}, "
            f"interval={self.sync_interval_seconds}s)"
        )
