"""Shared Hive Mind abstraction that all servants read from and write to."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional, Sequence

from community_memory import CommunityMemory, community_memory


class HiveMind:
    """Coordinated shared memory that every servant can tap into."""

    def __init__(self, memory: Optional[CommunityMemory] = None) -> None:
        self.memory = memory or community_memory
        self._lock = threading.RLock()

    def store_experience(self, agent_id: str, experience: Dict[str, Any]) -> str:
        """Record an experience into the shared memory (agent-agnostic)."""
        with self._lock:
            return self.memory.store_experience(agent_id, experience)

    def search(self, query: str, *, filters: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Search across all servants' contributions."""
        with self._lock:
            return self.memory.search_memories(query, filters)

    def share_learning(self, source_agent_id: str, target_agent_ids: Sequence[str], learning_type: str) -> bool:
        """Delegate to the CommunityMemory sharing mechanism."""
        with self._lock:
            return self.memory.share_learning(source_agent_id, list(target_agent_ids), learning_type)

    def record_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        source_agent: Optional[str] = None,
        target_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Capture coordination events in the hive stream."""
        with self._lock:
            return self.memory.record_event(
                event_type,
                data,
                source_agent=source_agent,
                target_agents=target_agents,
            )

    def recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Access the latest cross-agent events."""
        with self._lock:
            return self.memory.get_recent_events(limit)

    def collective_insights(self) -> Dict[str, Any]:
        """Summarize the hive mind's activity across all servants."""
        with self._lock:
            return self.memory.get_memory_insights()


hive_mind = HiveMind()
