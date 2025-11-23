"""
Conflict-Free Replicated Data Types (CRDTs) for Vessels Platform

This module implements CRDTs to enable offline-first, eventually-consistent
data synchronization across distributed Vessels nodes.

Key Components:
- LWWElementSet: Last-Write-Wins Element Set for memory storage
- GCounter: Grow-only Counter for Kala contributions
- VectorClock: Causality tracking for distributed events
- SyncProtocol: Delta-state synchronization

CRDTs provide strong eventual consistency guarantees:
- Commutative: merge(A, B) = merge(B, A)
- Associative: merge(merge(A, B), C) = merge(A, merge(B, C))
- Idempotent: merge(A, A) = A

This allows offline operation with seamless conflict-free merging
when nodes reconnect.
"""

from vessels.crdt.vector_clock import VectorClock, Timestamp
from vessels.crdt.memory import LWWElementSet, CRDTElement, CRDTMemory
from vessels.crdt.kala import GCounter, CRDTKalaAccount
from vessels.crdt.sync import SyncProtocol, Delta, SyncState

__all__ = [
    "VectorClock",
    "Timestamp",
    "LWWElementSet",
    "CRDTElement",
    "CRDTMemory",
    "GCounter",
    "CRDTKalaAccount",
    "SyncProtocol",
    "Delta",
    "SyncState",
]

__version__ = "1.0.0"
