"""
Gardener agent for automated memory hygiene.

The Gardener runs as a background agent, continuously maintaining
memory quality through pruning, synthesis, and fact-checking.

Now also handles conversation pruning for the ConversationStore.
"""

import logging
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, time as dt_time

from vessels.memory.pruning import (
    MemoryPruner,
    PruningCriteria,
    ConversationPruner,
    ConversationPruningCriteria,
)
from vessels.memory.synthesis import MemorySynthesizer, WisdomNode
from vessels.memory.fact_checking import FactChecker, Contradiction

logger = logging.getLogger(__name__)


@dataclass
class GardenerStats:
    """Statistics for Gardener agent operations."""
    # Memory stats
    memories_pruned: int = 0
    memories_synthesized: int = 0
    wisdom_nodes_created: int = 0
    contradictions_found: int = 0

    # Conversation stats
    conversations_archived: int = 0
    conversations_summarized: int = 0
    conversations_preserved: int = 0

    # Overall
    cycles_completed: int = 0
    last_run: Optional[datetime] = None
    cpu_budget_used: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memories_pruned": self.memories_pruned,
            "memories_synthesized": self.memories_synthesized,
            "wisdom_nodes_created": self.wisdom_nodes_created,
            "contradictions_found": self.contradictions_found,
            "conversations_archived": self.conversations_archived,
            "conversations_summarized": self.conversations_summarized,
            "conversations_preserved": self.conversations_preserved,
            "cycles_completed": self.cycles_completed,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "cpu_budget_used": self.cpu_budget_used
        }


class GardenerAgent:
    """
    Background agent for automated memory hygiene.

    Responsibilities:
    1. **Pruning**: Archive low-utility memories and stale conversations
    2. **Synthesis**: Merge duplicates into wisdom nodes
    3. **Fact-Checking**: Flag contradictions for review
    4. **Optimization**: Maintain optimal memory graph structure

    Runs continuously with low priority, during off-peak hours.
    """

    def __init__(
        self,
        memory_store,
        conversation_store=None,
        pruning_criteria: Optional[PruningCriteria] = None,
        conversation_pruning_criteria: Optional[ConversationPruningCriteria] = None,
        synthesis_threshold: float = 0.95,
        schedule: str = "nightly",
        cpu_budget_percent: float = 5.0
    ):
        """
        Initialize Gardener agent.

        Args:
            memory_store: CommunityMemory instance to maintain
            conversation_store: ConversationStore instance (optional)
            pruning_criteria: Criteria for memory pruning
            conversation_pruning_criteria: Criteria for conversation pruning
            synthesis_threshold: Similarity threshold for synthesis
            schedule: When to run ("continuous", "nightly", "weekly")
            cpu_budget_percent: Max CPU usage percentage (default 5%)
        """
        self.memory_store = memory_store
        self.conversation_store = conversation_store
        self.pruner = MemoryPruner(criteria=pruning_criteria)
        self.conversation_pruner = ConversationPruner(criteria=conversation_pruning_criteria)
        self.synthesizer = MemorySynthesizer(similarity_threshold=synthesis_threshold)
        self.fact_checker = FactChecker()
        self.schedule = schedule
        self.cpu_budget_percent = cpu_budget_percent
        self.stats = GardenerStats()

        self.running = False
        self.thread: Optional[threading.Thread] = None

        store_types = []
        if memory_store:
            store_types.append("memory")
        if conversation_store:
            store_types.append("conversation")

        logger.info(
            f"Gardener agent initialized "
            f"(stores: {', '.join(store_types)}, schedule: {schedule}, CPU budget: {cpu_budget_percent}%)"
        )

    def start(self) -> None:
        """Start the Gardener agent in background thread."""
        if self.running:
            logger.warning("Gardener already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        logger.info("Gardener agent started")

    def stop(self) -> None:
        """Stop the Gardener agent."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)

        logger.info("Gardener agent stopped")

    def _should_run_now(self) -> bool:
        """
        Determine if Gardener should run based on schedule.

        Returns:
            True if should run now
        """
        if self.schedule == "continuous":
            return True

        now = datetime.now()

        if self.schedule == "nightly":
            # Run between 2 AM and 5 AM
            return dt_time(2, 0) <= now.time() <= dt_time(5, 0)

        elif self.schedule == "weekly":
            # Run on Sundays at 3 AM
            return now.weekday() == 6 and dt_time(3, 0) <= now.time() <= dt_time(4, 0)

        return False

    def _run_loop(self) -> None:
        """Main loop for Gardener agent."""
        while self.running:
            if self._should_run_now():
                try:
                    self.run_maintenance_cycle()
                except Exception as e:
                    logger.error(f"Gardener cycle failed: {e}", exc_info=True)

            # Sleep for 1 hour between checks
            time.sleep(3600)

    def run_maintenance_cycle(self) -> GardenerStats:
        """
        Run a full maintenance cycle.

        Returns:
            Updated statistics
        """
        logger.info("🌱 Gardener: Starting maintenance cycle...")

        start_time = time.time()

        # 1. Prune low-utility memories
        self._prune_memories()

        # 2. Prune stale conversations
        self._prune_conversations()

        # 3. Synthesize duplicates
        self._synthesize_memories()

        # 4. Check for contradictions
        self._check_contradictions()

        # 5. Optimize graph structure (if applicable)
        self._optimize_graph()

        # Update statistics
        elapsed_time = time.time() - start_time
        self.stats.cycles_completed += 1
        self.stats.last_run = datetime.now()
        self.stats.cpu_budget_used = elapsed_time / 3600.0 * 100  # Rough estimate

        logger.info(
            f"🌱 Gardener: Cycle complete "
            f"(memories_pruned: {self.pruner.pruned_count}, "
            f"convs_archived: {self.conversation_pruner.pruned_count}, "
            f"convs_summarized: {self.conversation_pruner.summarized_count}, "
            f"synthesized: {self.synthesizer.synthesized_count}, "
            f"contradictions: {len(self.fact_checker.contradictions_found)}, "
            f"time: {elapsed_time:.1f}s)"
        )

        return self.stats

    def _prune_memories(self) -> None:
        """Prune low-utility memories."""
        logger.info("🌱 Gardener: Pruning low-utility memories...")

        # Get all memories
        all_memories = self.memory_store.memories.values()

        # Convert to dicts
        memory_dicts = [
            {
                "id": m.id,
                "type": m.type.value,
                "content": m.content,
                "timestamp": m.timestamp,
                "access_count": m.access_count,
                "kala_value": 0.0  # TODO: Extract kala value if tracked
            }
            for m in all_memories
        ]

        # Prune
        def archive_callback(memory):
            # Move to archive (simple approach: just log)
            # In production, move to cold storage
            logger.debug(f"Archiving memory: {memory['id']}")

        result = self.pruner.prune_memories(memory_dicts, archive_callback)

        self.stats.memories_pruned += result["pruned_count"]

    def _prune_conversations(self) -> None:
        """Prune stale conversations."""
        if not self.conversation_store:
            logger.debug("No conversation store configured, skipping conversation pruning")
            return

        logger.info("🌱 Gardener: Pruning stale conversations...")

        # Get all conversations from cache
        all_conversations = list(self.conversation_store._conversations.values())

        if not all_conversations:
            logger.info("No conversations to prune")
            return

        # Convert to dicts
        conv_dicts = [conv.to_dict() for conv in all_conversations]

        # Archive callback
        def archive_callback(conv: dict):
            conv_id = conv.get("conversation_id")
            logger.debug(f"Archiving conversation: {conv_id}")

            # Update status in store
            original_conv = self.conversation_store._conversations.get(conv_id)
            if original_conv:
                from vessels.memory.conversation_store import ConversationStatus
                original_conv.status = ConversationStatus.ARCHIVED

                # Remove from active indices (but keep in cache for now)
                user_id = original_conv.user_id
                vessel_id = original_conv.vessel_id
                project_id = original_conv.project_id

                if user_id and user_id in self.conversation_store._by_user:
                    if conv_id in self.conversation_store._by_user[user_id]:
                        self.conversation_store._by_user[user_id].remove(conv_id)

                if vessel_id and vessel_id in self.conversation_store._by_vessel:
                    if conv_id in self.conversation_store._by_vessel[vessel_id]:
                        self.conversation_store._by_vessel[vessel_id].remove(conv_id)

                if project_id and project_id in self.conversation_store._by_project:
                    if conv_id in self.conversation_store._by_project[project_id]:
                        self.conversation_store._by_project[project_id].remove(conv_id)

        # Summarize callback
        def summarize_callback(conv: dict) -> str:
            conv_id = conv.get("conversation_id")
            logger.debug(f"Summarizing conversation: {conv_id}")

            # Generate a simple summary from turn messages
            original_conv = self.conversation_store._conversations.get(conv_id)
            if original_conv and original_conv.turns:
                # Take first and last few messages
                turns = original_conv.turns
                summary_parts = []

                if turns:
                    summary_parts.append(f"Started: {turns[0].message[:100]}...")
                if len(turns) > 1:
                    summary_parts.append(f"Ended: {turns[-1].message[:100]}...")

                summary = f"Conversation with {conv.get('turn_count', 0)} turns. " + " ".join(summary_parts)

                # Update the conversation
                original_conv.summary = summary

                # Clear turns to save memory (keep only summary)
                original_conv.turns = []

                return summary

            return f"Conversation with {conv.get('turn_count', 0)} turns (no details available)"

        # Run pruning
        result = self.conversation_pruner.prune_conversations(
            conv_dicts,
            archive_callback,
            summarize_callback,
        )

        self.stats.conversations_archived += result["pruned_count"]
        self.stats.conversations_summarized += result["summarized_count"]
        self.stats.conversations_preserved += result["preserved_count"]

    def _synthesize_memories(self) -> None:
        """Synthesize wisdom nodes from similar memories."""
        logger.info("🌱 Gardener: Synthesizing wisdom from duplicates...")

        # Get all memories
        all_memories = list(self.memory_store.memories.values())

        if len(all_memories) < 2:
            logger.info("Not enough memories to synthesize")
            return

        # Get embeddings
        embeddings = {}
        for memory_id, embedding_obj in self.memory_store.vector_embeddings.items():
            embeddings[memory_id] = embedding_obj.vector

        # Convert to dicts
        memory_dicts = [
            {
                "id": m.id,
                "content": m.content,
                "tags": m.tags
            }
            for m in all_memories
        ]

        # Store wisdom callback
        def store_wisdom_callback(wisdom: WisdomNode):
            logger.info(f"Created wisdom node: {wisdom.pattern[:100]}")
            # TODO: Store wisdom node in memory system

        # Synthesize
        wisdom_nodes = self.synthesizer.synthesize_memories(
            memory_dicts,
            embeddings,
            store_wisdom_callback
        )

        self.stats.wisdom_nodes_created += len(wisdom_nodes)
        self.stats.memories_synthesized += sum(w.evidence_count for w in wisdom_nodes)

    def _check_contradictions(self) -> None:
        """Check for contradictions in memories."""
        logger.info("🌱 Gardener: Checking for contradictions...")

        # Get all memories
        all_memories = list(self.memory_store.memories.values())

        if len(all_memories) < 2:
            return

        # Convert to dicts
        memory_dicts = [
            {
                "id": m.id,
                "content": m.content
            }
            for m in all_memories
        ]

        # Find contradictions
        contradictions = self.fact_checker.find_contradictions(memory_dicts)

        # Flag for review
        for contradiction in contradictions:
            self.fact_checker.flag_for_review(contradiction)

        self.stats.contradictions_found += len(contradictions)

    def _optimize_graph(self) -> None:
        """Optimize memory graph structure (if using graph backend)."""
        logger.info("🌱 Gardener: Optimizing graph structure...")

        # If using Graphiti backend, could optimize graph here
        # For now, this is a placeholder

        # TODO: Implement graph optimization
        # - Densify frequently-accessed subgraphs
        # - Reorganize for faster retrieval
        # - Update indices

        pass

    def get_stats(self) -> GardenerStats:
        """Get current statistics."""
        return self.stats

    def force_run(self) -> GardenerStats:
        """
        Force a maintenance cycle to run immediately.

        Useful for testing or manual triggering.

        Returns:
            Updated statistics
        """
        logger.info("🌱 Gardener: Forced run triggered")
        return self.run_maintenance_cycle()
