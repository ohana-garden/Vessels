"""
Memory pruning logic for the Gardener agent.

Identifies and archives low-utility memories to maintain
memory quality over time.
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
