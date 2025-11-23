"""
Vector Clock implementation for causality tracking in distributed systems.

Vector clocks provide partial ordering of events in distributed systems,
enabling detection of concurrent vs. causally-ordered events.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime
import uuid


@dataclass(frozen=True)
class Timestamp:
    """
    Hybrid timestamp combining vector clock and wall-clock time.

    Provides total ordering even for concurrent events by using
    wall-clock time as tiebreaker.
    """
    vector_clock: Dict[str, int]
    wall_clock: datetime
    node_id: str

    def __lt__(self, other: 'Timestamp') -> bool:
        """
        Compare timestamps for ordering.

        Rules:
        1. If A causally precedes B (A's vector clock ≤ B's), then A < B
        2. If concurrent (neither precedes), use wall-clock time
        3. If wall-clock times equal, use node_id as tiebreaker
        """
        if not isinstance(other, Timestamp):
            return NotImplemented

        # Check causal precedence
        a_precedes_b = all(
            self.vector_clock.get(node, 0) <= other.vector_clock.get(node, 0)
            for node in set(self.vector_clock) | set(other.vector_clock)
        )
        b_precedes_a = all(
            other.vector_clock.get(node, 0) <= self.vector_clock.get(node, 0)
            for node in set(self.vector_clock) | set(other.vector_clock)
        )

        if a_precedes_b and not b_precedes_a:
            return True  # A causally precedes B
        elif b_precedes_a and not a_precedes_b:
            return False  # B causally precedes A
        else:
            # Concurrent events - use wall-clock time
            if self.wall_clock != other.wall_clock:
                return self.wall_clock < other.wall_clock
            else:
                # Same wall-clock time - use node_id as tiebreaker
                return self.node_id < other.node_id

    def __le__(self, other: 'Timestamp') -> bool:
        return self == other or self < other

    def __gt__(self, other: 'Timestamp') -> bool:
        return other < self

    def __ge__(self, other: 'Timestamp') -> bool:
        return other <= self


class VectorClock:
    """
    Vector clock for tracking causality in distributed systems.

    Each node maintains a vector of logical clocks, one per node.
    When an event occurs:
    - Local clock increments
    - On message send: include current vector
    - On message receive: merge vectors + increment local

    This enables detection of:
    - Causal ordering: event A happened before event B
    - Concurrent events: neither A nor B preceded the other
    """

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize vector clock.

        Args:
            node_id: Unique identifier for this node (UUID if not provided)
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.clock: Dict[str, int] = {self.node_id: 0}

    def increment(self) -> None:
        """Increment local clock on local event."""
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1

    def update(self, other_clock: Dict[str, int]) -> None:
        """
        Update vector clock on message receive.

        Merge rule: take max of each component, then increment local.

        Args:
            other_clock: Vector clock from received message
        """
        # Merge: take max of each component
        all_nodes = set(self.clock.keys()) | set(other_clock.keys())
        for node in all_nodes:
            self.clock[node] = max(
                self.clock.get(node, 0),
                other_clock.get(node, 0)
            )

        # Increment local clock
        self.increment()

    def get_timestamp(self) -> Timestamp:
        """
        Get current timestamp (vector clock + wall-clock time).

        Returns:
            Timestamp object for total ordering
        """
        return Timestamp(
            vector_clock=self.clock.copy(),
            wall_clock=datetime.utcnow(),
            node_id=self.node_id
        )

    def happens_before(self, other: 'VectorClock') -> bool:
        """
        Check if this clock causally precedes another.

        A happens-before B if:
        - All components of A ≤ corresponding components of B
        - At least one component of A < corresponding component of B

        Args:
            other: Other vector clock to compare

        Returns:
            True if self causally precedes other
        """
        all_nodes = set(self.clock.keys()) | set(other.clock.keys())

        all_leq = all(
            self.clock.get(node, 0) <= other.clock.get(node, 0)
            for node in all_nodes
        )

        some_less = any(
            self.clock.get(node, 0) < other.clock.get(node, 0)
            for node in all_nodes
        )

        return all_leq and some_less

    def concurrent_with(self, other: 'VectorClock') -> bool:
        """
        Check if this clock is concurrent with another.

        Two events are concurrent if neither happens-before the other.

        Args:
            other: Other vector clock to compare

        Returns:
            True if events are concurrent
        """
        return not self.happens_before(other) and not other.happens_before(self)

    def copy(self) -> 'VectorClock':
        """Create a deep copy of this vector clock."""
        vc = VectorClock(self.node_id)
        vc.clock = self.clock.copy()
        return vc

    def to_dict(self) -> Dict[str, int]:
        """Export vector clock as dictionary."""
        return self.clock.copy()

    @classmethod
    def from_dict(cls, clock_dict: Dict[str, int], node_id: str) -> 'VectorClock':
        """
        Create vector clock from dictionary.

        Args:
            clock_dict: Clock state as dictionary
            node_id: This node's ID

        Returns:
            VectorClock instance
        """
        vc = cls(node_id)
        vc.clock = clock_dict.copy()
        return vc

    def __repr__(self) -> str:
        return f"VectorClock(node={self.node_id}, clock={self.clock})"
