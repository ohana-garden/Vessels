"""
Memory management modules for Vessels platform.

Includes:
- ConversationStore: Unified persistence for ALL conversations (core feature)
- Gardener agent for memory hygiene
- Pruning logic for low-utility memories
- Synthesis for duplicate merging
- Fact-checking for contradiction detection
"""

from vessels.memory.conversation_store import (
    ConversationStore,
    Conversation,
    Turn,
    ConversationType,
    SpeakerType,
    ConversationStatus,
)
from vessels.memory.gardener import GardenerAgent, GardenerStats
from vessels.memory.pruning import MemoryPruner, PruningCriteria
from vessels.memory.synthesis import MemorySynthesizer, WisdomNode
from vessels.memory.fact_checking import FactChecker, Contradiction

__all__ = [
    # Conversation Store (CORE)
    "ConversationStore",
    "Conversation",
    "Turn",
    "ConversationType",
    "SpeakerType",
    "ConversationStatus",
    # Memory Management
    "GardenerAgent",
    "GardenerStats",
    "MemoryPruner",
    "PruningCriteria",
    "MemorySynthesizer",
    "WisdomNode",
    "FactChecker",
    "Contradiction",
]
