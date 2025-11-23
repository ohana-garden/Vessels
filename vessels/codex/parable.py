"""
Parable system for storing moral learnings.

A parable is a teachable moment - a story about a tension,
how the village deliberated, and what was learned.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class Parable:
    """
    A parable: a story of tension, deliberation, and learning.

    Parables are stored in community memory so all Vessels can
    learn from past decisions.
    """
    id: str
    title: str
    situation: str  # What was the context?
    tension: str  # What values collided or what was unclear?
    deliberation: str  # How did the village discuss it?
    decision: str  # What did the village decide?
    lesson: str  # What was learned?

    agent_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Metadata for retrieval
    tags: List[str] = field(default_factory=list)
    involved_virtues: List[str] = field(default_factory=list)

    # Context
    original_state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert parable to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'situation': self.situation,
            'tension': self.tension,
            'deliberation': self.deliberation,
            'decision': self.decision,
            'lesson': self.lesson,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'involved_virtues': self.involved_virtues,
            'original_state': self.original_state,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Parable':
        """Create parable from dictionary."""
        data = data.copy()
        if isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def to_narrative(self) -> str:
        """Convert parable to narrative form for display."""
        narrative = f"""
# The Parable: {self.title}

## The Situation
{self.situation}

## The Tension
{self.tension}

## The Deliberation
{self.deliberation}

## The Decision
{self.decision}

## The Lesson
{self.lesson}

---
*Recorded by {self.agent_id} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return narrative.strip()


class ParableStorage:
    """
    Storage system for parables.

    Integrates with CommunityMemory to store parables as
    special memory entries with semantic search.
    """

    def __init__(self, community_memory=None):
        """
        Initialize parable storage.

        Args:
            community_memory: CommunityMemory instance for storage
        """
        self.community_memory = community_memory
        self.parables: Dict[str, Parable] = {}

    def store(self, parable: Parable) -> str:
        """
        Store a parable.

        Args:
            parable: Parable to store

        Returns:
            Parable ID
        """
        self.parables[parable.id] = parable

        # Store in community memory if available
        if self.community_memory:
            try:
                self.community_memory.store_experience(
                    agent_id=parable.agent_id,
                    experience={
                        'type': 'parable',
                        'title': parable.title,
                        'situation': parable.situation,
                        'tension': parable.tension,
                        'deliberation': parable.deliberation,
                        'decision': parable.decision,
                        'lesson': parable.lesson,
                        'tags': ['parable', 'codex', 'learning'] + parable.tags,
                        'involved_virtues': parable.involved_virtues,
                        'metadata': parable.metadata,
                    }
                )
                logger.info(f"Stored parable '{parable.title}' in community memory")
            except Exception as e:
                logger.warning(f"Failed to store parable in community memory: {e}")

        return parable.id

    def retrieve(self, parable_id: str) -> Optional[Parable]:
        """Retrieve a parable by ID."""
        return self.parables.get(parable_id)

    def find_similar(
        self,
        situation: str,
        limit: int = 5
    ) -> List[Parable]:
        """
        Find parables about similar situations.

        Args:
            situation: Description of current situation
            limit: Maximum number to return

        Returns:
            List of relevant parables
        """
        if not self.community_memory:
            # Fallback: return all parables
            return list(self.parables.values())[:limit]

        try:
            # Search community memory for similar parables
            memories = self.community_memory.find_similar_memories(
                query={'situation': situation, 'type': 'parable'},
                limit=limit
            )

            # Convert memories back to parables
            similar_parables = []
            for mem in memories:
                content = mem['memory'].content
                if content.get('type') == 'parable':
                    # Reconstruct parable (simplified)
                    parable = Parable(
                        id=str(mem['memory'].id),
                        title=content.get('title', 'Untitled'),
                        situation=content.get('situation', ''),
                        tension=content.get('tension', ''),
                        deliberation=content.get('deliberation', ''),
                        decision=content.get('decision', ''),
                        lesson=content.get('lesson', ''),
                        agent_id=mem['memory'].agent_id,
                        timestamp=mem['memory'].created_at,
                        tags=content.get('tags', []),
                        involved_virtues=content.get('involved_virtues', []),
                        metadata=content.get('metadata', {}),
                    )
                    similar_parables.append(parable)

            return similar_parables
        except Exception as e:
            logger.warning(f"Failed to search parables: {e}")
            return []

    def get_all(self) -> List[Parable]:
        """Get all stored parables."""
        return list(self.parables.values())

    def get_by_virtue(self, virtue: str) -> List[Parable]:
        """Get parables involving a specific virtue."""
        return [
            p for p in self.parables.values()
            if virtue in p.involved_virtues
        ]
