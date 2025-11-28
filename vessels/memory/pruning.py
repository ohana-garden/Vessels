"""
Memory and Conversation pruning logic for the Gardener agent.

Identifies and archives low-utility memories and stale conversations
to maintain memory quality over time.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PruneAction(str, Enum):
    """Actions that can be taken on prunable items."""
    ARCHIVE = "archive"
    SUMMARIZE = "summarize"  # Keep summary, discard turns
    DELETE = "delete"


@dataclass
class PruningCriteria:
    """Criteria for determining if a memory should be pruned."""
    min_access_count: int = 3
    max_age_days: int = 90
    min_kala_value: float = 0.1
    preserve_high_kala: bool = True
    high_kala_threshold: float = 1.0


class MemoryPruner:
    """
    Prunes low-utility memories from community memory.

    Strategy:
    - Archive memories with low access and low value
    - Preserve memories with high Kala value (community-important)
    - Conservative thresholds to avoid over-pruning
    """

    def __init__(self, criteria: Optional[PruningCriteria] = None):
        """
        Initialize memory pruner.

        Args:
            criteria: Pruning criteria (uses defaults if not provided)
        """
        self.criteria = criteria or PruningCriteria()
        self.pruned_count = 0
        self.preserved_count = 0

    def should_prune(self, memory: Dict[str, Any]) -> bool:
        """
        Determine if a memory should be pruned.

        Args:
            memory: Memory dictionary with metadata

        Returns:
            True if memory should be pruned
        """
        # Extract metadata
        access_count = memory.get("access_count", 0)
        created_at_str = memory.get("timestamp") or memory.get("created_at")

        if not created_at_str:
            logger.warning("Memory has no timestamp, cannot prune")
            return False

        # Parse timestamp
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str)
        elif isinstance(created_at_str, datetime):
            created_at = created_at_str
        else:
            logger.warning(f"Invalid timestamp type: {type(created_at_str)}")
            return False

        age = datetime.now() - created_at
        kala_value = memory.get("kala_value", 0.0)

        # Preserve high-kala memories regardless of access
        if self.criteria.preserve_high_kala and kala_value >= self.criteria.high_kala_threshold:
            self.preserved_count += 1
            return False

        # Prune if:
        # 1. Low access count
        # 2. Old enough
        # 3. Low kala value
        should_prune = (
            access_count < self.criteria.min_access_count and
            age > timedelta(days=self.criteria.max_age_days) and
            kala_value < self.criteria.min_kala_value
        )

        if should_prune:
            self.pruned_count += 1

        return should_prune

    def prune_memories(
        self,
        memories: List[Dict[str, Any]],
        archive_callback: callable
    ) -> Dict[str, Any]:
        """
        Prune low-utility memories.

        Args:
            memories: List of memory dictionaries
            archive_callback: Function to call for each memory to archive

        Returns:
            Pruning statistics
        """
        self.pruned_count = 0
        self.preserved_count = 0
        archived_memories = []

        for memory in memories:
            if self.should_prune(memory):
                # Archive the memory
                archive_callback(memory)
                archived_memories.append(memory["id"] if "id" in memory else memory.get("memory_id"))

        logger.info(
            f"Pruning complete: {self.pruned_count} archived, "
            f"{self.preserved_count} preserved"
        )

        return {
            "pruned_count": self.pruned_count,
            "preserved_count": self.preserved_count,
            "archived_ids": archived_memories
        }

    def get_pruning_candidates(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Get list of memories that would be pruned (without actually pruning).

        Useful for review before actual pruning.

        Args:
            memories: List of memory dictionaries

        Returns:
            List of memories that would be pruned
        """
        candidates = []

        for memory in memories:
            if self.should_prune(memory):
                candidates.append(memory)

        return candidates


# =============================================================================
# Conversation Pruning
# =============================================================================

@dataclass
class ConversationPruningCriteria:
    """Criteria for determining if a conversation should be pruned."""
    # Age-based criteria
    max_inactive_days: int = 30        # Prune ended conversations older than this
    max_active_days: int = 90          # Force-end and prune very old conversations

    # Turn-based criteria
    min_turns_to_keep: int = 3         # Keep conversations with few turns (likely important)
    max_turns_to_keep: int = 100       # Summarize conversations with many turns

    # Status-based
    prune_ended_only: bool = True      # Only prune ended conversations
    archive_before_delete: bool = True  # Archive to cold storage before deleting

    # Privacy-aware
    respect_project_retention: bool = True  # Check project-level retention policies


class ConversationPruner:
    """
    Prunes stale conversations from the conversation store.

    Strategy:
    - Archive ended conversations after inactivity threshold
    - Summarize very long conversations (keep summary, discard turns)
    - Preserve recent and active conversations
    - Respect privacy scoping (project retention policies)
    """

    def __init__(self, criteria: Optional[ConversationPruningCriteria] = None):
        """
        Initialize conversation pruner.

        Args:
            criteria: Pruning criteria (uses defaults if not provided)
        """
        self.criteria = criteria or ConversationPruningCriteria()
        self.pruned_count = 0
        self.summarized_count = 0
        self.preserved_count = 0

    def should_prune(self, conversation: Dict[str, Any]) -> PruneAction:
        """
        Determine what action to take on a conversation.

        Args:
            conversation: Conversation dictionary with metadata

        Returns:
            PruneAction indicating what to do
        """
        # Extract metadata
        status = conversation.get("status", "active")
        turn_count = conversation.get("turn_count", 0)
        last_activity_str = conversation.get("last_activity_at")
        started_at_str = conversation.get("started_at")

        # Parse timestamps
        last_activity = self._parse_timestamp(last_activity_str)
        started_at = self._parse_timestamp(started_at_str)

        if not last_activity:
            logger.warning("Conversation has no last_activity_at, cannot prune")
            self.preserved_count += 1
            return None

        age = datetime.now() - last_activity

        # Status check
        is_ended = status in ("ended", "archived")
        if self.criteria.prune_ended_only and not is_ended:
            # Check if should force-end very old active conversations
            if age > timedelta(days=self.criteria.max_active_days):
                logger.info(f"Force-ending stale active conversation (age: {age.days} days)")
                # Return summarize action to preserve context
                return PruneAction.SUMMARIZE
            self.preserved_count += 1
            return None

        # Turn count checks
        if turn_count <= self.criteria.min_turns_to_keep:
            # Short conversations might be important single interactions
            self.preserved_count += 1
            return None

        # Very long conversations should be summarized, not deleted
        if turn_count > self.criteria.max_turns_to_keep:
            self.summarized_count += 1
            return PruneAction.SUMMARIZE

        # Age check for ended conversations
        if is_ended and age > timedelta(days=self.criteria.max_inactive_days):
            self.pruned_count += 1
            return PruneAction.ARCHIVE

        self.preserved_count += 1
        return None

    def _parse_timestamp(self, ts) -> Optional[datetime]:
        """Parse a timestamp from various formats."""
        if not ts:
            return None
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    def prune_conversations(
        self,
        conversations: List[Dict[str, Any]],
        archive_callback: Callable[[Dict[str, Any]], None],
        summarize_callback: Callable[[Dict[str, Any]], str],
    ) -> Dict[str, Any]:
        """
        Prune conversations based on criteria.

        Args:
            conversations: List of conversation dictionaries
            archive_callback: Called for conversations to archive
            summarize_callback: Called for conversations to summarize, returns summary

        Returns:
            Pruning statistics
        """
        self.pruned_count = 0
        self.summarized_count = 0
        self.preserved_count = 0

        archived_ids = []
        summarized_ids = []

        for conv in conversations:
            action = self.should_prune(conv)

            if action == PruneAction.ARCHIVE:
                archive_callback(conv)
                archived_ids.append(conv.get("conversation_id"))

            elif action == PruneAction.SUMMARIZE:
                summary = summarize_callback(conv)
                conv["summary"] = summary
                summarized_ids.append(conv.get("conversation_id"))

        logger.info(
            f"Conversation pruning complete: {self.pruned_count} archived, "
            f"{self.summarized_count} summarized, {self.preserved_count} preserved"
        )

        return {
            "pruned_count": self.pruned_count,
            "summarized_count": self.summarized_count,
            "preserved_count": self.preserved_count,
            "archived_ids": archived_ids,
            "summarized_ids": summarized_ids,
        }

    def get_pruning_candidates(
        self,
        conversations: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get candidates for each pruning action without actually pruning.

        Args:
            conversations: List of conversation dictionaries

        Returns:
            Dict mapping action type to list of candidates
        """
        candidates = {
            "archive": [],
            "summarize": [],
        }

        for conv in conversations:
            action = self.should_prune(conv)
            if action == PruneAction.ARCHIVE:
                candidates["archive"].append(conv)
            elif action == PruneAction.SUMMARIZE:
                candidates["summarize"].append(conv)

        return candidates
