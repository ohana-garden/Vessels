"""
Memory management modules for Vessels platform.

Includes:
- ConversationStore: Unified persistence for ALL conversations (core feature)
- Gardener agent for memory hygiene
- Pruning logic for low-utility memories and stale conversations
- Synthesis for duplicate merging
- Fact-checking for contradiction detection
"""

from vessels.memory.conversation_store import (
    ConversationStore,
    Conversation,
    Turn,
    ImageContext,
    ConversationType,
    SpeakerType,
    ConversationStatus,
)
from vessels.memory.gardener import GardenerAgent, GardenerStats
from vessels.memory.pruning import (
    MemoryPruner,
    PruningCriteria,
    ConversationPruner,
    ConversationPruningCriteria,
    PruneAction,
)
from vessels.memory.synthesis import MemorySynthesizer, WisdomNode
from vessels.memory.fact_checking import FactChecker, Contradiction

__all__ = [
    # Conversation Store (CORE)
    "ConversationStore",
    "Conversation",
    "Turn",
    "ImageContext",
    "ConversationType",
    "SpeakerType",
    "ConversationStatus",
    # Memory Management
    "GardenerAgent",
    "GardenerStats",
    # Pruning
    "MemoryPruner",
    "PruningCriteria",
    "ConversationPruner",
    "ConversationPruningCriteria",
    "PruneAction",
    # Synthesis & Fact-checking
    "MemorySynthesizer",
    "WisdomNode",
    "FactChecker",
    "Contradiction",
]
