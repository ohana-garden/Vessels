"""
Parable System: Moral Precedent Memory

A Parable is a structured 'teachable moment' that encodes moral precedents
for resolving conflicts between competing values/dimensions.

Unlike raw logs, Parables tell stories of conflicting values and how they
were resolved, allowing agents to learn from past wisdom and apply it to
new situations.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid

from vessels.measurement.state import Dimension

# Import MemoryEntry and MemoryType from root community_memory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from community_memory import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


@dataclass
class Parable:
    """
    A structured 'teachable moment' that encodes a moral precedent.

    Unlike a raw log, a Parable tells a story of conflicting values and
    how those conflicts were resolved through human guidance or community wisdom.

    Attributes:
        id: Unique identifier for this parable
        title: Short descriptive title
        agent_id: ID of the agent that encountered this conflict
        conflict_pair: The two dimensions in tension (e.g., [TRUTHFULNESS, UNITY])
        situation_summary: Description of the situation that created the conflict
        council_guidance: The wisdom/guidance provided by humans or the council
        resolution_principle: The general rule derived from this case
        winning_dimension: Which value took precedence, if any (None if balanced)
        timestamp: When this parable was recorded
        tags: Additional tags for categorization and retrieval
        context: Additional contextual information
    """
    id: str
    title: str
    agent_id: str
    conflict_pair: List[Dimension]
    situation_summary: str
    council_guidance: str
    resolution_principle: str
    winning_dimension: Optional[Dimension] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)
    context: Dict[str, any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate parable structure."""
        if len(self.conflict_pair) != 2:
            raise ValueError(
                f"conflict_pair must contain exactly 2 dimensions, got {len(self.conflict_pair)}"
            )
        if not all(isinstance(d, Dimension) for d in self.conflict_pair):
            raise ValueError("conflict_pair must contain Dimension enum values")

    @classmethod
    def create(
        cls,
        title: str,
        agent_id: str,
        conflict_pair: List[Dimension],
        situation_summary: str,
        council_guidance: str,
        resolution_principle: str,
        winning_dimension: Optional[Dimension] = None,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, any]] = None,
    ) -> 'Parable':
        """
        Create a new Parable with auto-generated ID.

        Args:
            title: Short descriptive title
            agent_id: ID of the agent
            conflict_pair: Two dimensions in conflict
            situation_summary: Description of the situation
            council_guidance: Wisdom provided
            resolution_principle: General rule derived
            winning_dimension: Which dimension took precedence (optional)
            tags: Additional tags (optional)
            context: Additional context (optional)

        Returns:
            New Parable instance
        """
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            agent_id=agent_id,
            conflict_pair=conflict_pair,
            situation_summary=situation_summary,
            council_guidance=council_guidance,
            resolution_principle=resolution_principle,
            winning_dimension=winning_dimension,
            tags=tags or [],
            context=context or {},
        )

    def to_dict(self) -> Dict:
        """
        Serialize Parable to dictionary.

        Returns:
            Dictionary representation suitable for storage
        """
        return {
            "id": self.id,
            "title": self.title,
            "agent_id": self.agent_id,
            "conflict_pair": [d.value for d in self.conflict_pair],
            "situation": self.situation_summary,
            "guidance": self.council_guidance,
            "principle": self.resolution_principle,
            "winner": self.winning_dimension.value if self.winning_dimension else None,
            "timestamp": self.timestamp.isoformat(),
            "tags": self.tags,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Parable':
        """
        Deserialize Parable from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Parable instance
        """
        # Parse conflict pair
        conflict_pair = [Dimension(d) for d in data.get("conflict_pair", [])]

        # Parse winning dimension
        winner_value = data.get("winner")
        winning_dimension = Dimension(winner_value) if winner_value else None

        # Parse timestamp
        timestamp_str = data.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_str)
            if timestamp_str
            else datetime.utcnow()
        )

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            title=data.get("title", "Untitled Parable"),
            agent_id=data.get("agent_id", "unknown"),
            conflict_pair=conflict_pair,
            situation_summary=data.get("situation", ""),
            council_guidance=data.get("guidance", ""),
            resolution_principle=data.get("principle", ""),
            winning_dimension=winning_dimension,
            timestamp=timestamp,
            tags=data.get("tags", []),
            context=data.get("context", {}),
        )

    def to_memory_entry(self) -> MemoryEntry:
        """
        Convert Parable to MemoryEntry for storage in memory backend.

        Returns:
            MemoryEntry instance
        """
        # Add conflict tag for easy filtering
        sorted_pair = sorted([d.value for d in self.conflict_pair])
        conflict_tag = f"conflict:{sorted_pair[0]}_vs_{sorted_pair[1]}"

        all_tags = list(self.tags)
        if conflict_tag not in all_tags:
            all_tags.append(conflict_tag)
        if "parable" not in all_tags:
            all_tags.append("parable")

        return MemoryEntry(
            id=self.id,
            type=MemoryType.PATTERN,  # Parables are patterns/wisdom
            content=self.to_dict(),
            agent_id=self.agent_id,
            timestamp=self.timestamp,
            tags=all_tags,
            relationships=[],
            confidence=1.0,
            access_count=0,
        )

    @classmethod
    def from_memory_entry(cls, entry: MemoryEntry) -> 'Parable':
        """
        Reconstruct Parable from MemoryEntry.

        Args:
            entry: MemoryEntry containing parable data

        Returns:
            Parable instance
        """
        if not isinstance(entry.content, dict):
            raise ValueError(f"Expected dict content, got {type(entry.content)}")

        data = entry.content.copy()
        # Ensure ID and timestamp match the entry
        data["id"] = entry.id
        data["timestamp"] = entry.timestamp.isoformat()

        return cls.from_dict(data)


class ParableLibrary:
    """
    Manages the storage and retrieval of moral precedents.

    Allows agents to ask: 'Has the village solved a conflict between X and Y before?'
    Uses the memory backend for persistent storage and semantic search.
    """

    def __init__(self, memory_backend):
        """
        Initialize ParableLibrary.

        Args:
            memory_backend: GraphitiMemoryBackend or CommunityMemory instance
        """
        self.memory = memory_backend
        logger.info("Initialized ParableLibrary")

    def store_parable(self, parable: Parable) -> str:
        """
        Store a new parable with optimized tags for retrieval.

        Args:
            parable: Parable instance to store

        Returns:
            Memory ID of stored parable

        Raises:
            Exception: If storage fails
        """
        try:
            memory_entry = parable.to_memory_entry()
            memory_id = self.memory.store_memory(memory_entry)
            logger.info(f"Stored parable '{parable.title}' with ID {memory_id}")
            return memory_id
        except Exception as e:
            logger.error(f"Failed to store parable '{parable.title}': {e}")
            raise

    def find_precedents(
        self,
        conflict_pair: List[Dimension],
        limit: int = 3,
    ) -> List[Parable]:
        """
        Find parables matching a specific dimensional conflict.

        Args:
            conflict_pair: Two dimensions in conflict
            limit: Maximum number of precedents to return

        Returns:
            List of matching Parable instances, ordered by relevance/recency
        """
        if len(conflict_pair) != 2:
            raise ValueError(f"conflict_pair must contain exactly 2 dimensions")

        # Sort for consistent key generation (Unity-Truth vs Truth-Unity)
        sorted_pair = sorted([d.value for d in conflict_pair])
        conflict_tag = f"conflict:{sorted_pair[0]}_vs_{sorted_pair[1]}"

        try:
            # Query by tags
            results = self.memory.query_memories(
                query=conflict_tag,
                memory_type=MemoryType.PATTERN,
                tags=["parable", conflict_tag],
                limit=limit,
            )

            # Convert to Parable objects
            parables = []
            for entry in results:
                try:
                    parable = Parable.from_memory_entry(entry)
                    parables.append(parable)
                except Exception as e:
                    logger.warning(f"Failed to convert memory entry to parable: {e}")
                    continue

            logger.debug(
                f"Found {len(parables)} precedents for conflict {conflict_tag}"
            )
            return parables

        except Exception as e:
            logger.error(f"Error finding precedents for {conflict_tag}: {e}")
            return []

    def find_by_dimension(
        self,
        dimension: Dimension,
        limit: int = 10,
    ) -> List[Parable]:
        """
        Find all parables involving a specific dimension.

        Args:
            dimension: The dimension to search for
            limit: Maximum number of parables to return

        Returns:
            List of Parable instances involving this dimension
        """
        try:
            # Query for parables mentioning this dimension
            query = f"conflict:{dimension.value}"

            results = self.memory.query_memories(
                query=query,
                memory_type=MemoryType.PATTERN,
                tags=["parable"],
                limit=limit,
            )

            # Convert and filter
            parables = []
            for entry in results:
                try:
                    parable = Parable.from_memory_entry(entry)
                    # Verify dimension is actually in conflict pair
                    if dimension in parable.conflict_pair:
                        parables.append(parable)
                except Exception as e:
                    logger.warning(f"Failed to convert memory entry: {e}")
                    continue

            logger.debug(
                f"Found {len(parables)} parables for dimension {dimension.value}"
            )
            return parables

        except Exception as e:
            logger.error(f"Error finding parables for dimension {dimension.value}: {e}")
            return []

    def get_by_id(self, parable_id: str) -> Optional[Parable]:
        """
        Retrieve a specific parable by ID.

        Args:
            parable_id: The parable's unique identifier

        Returns:
            Parable instance if found, None otherwise
        """
        try:
            # Query for this specific ID
            results = self.memory.query_memories(
                query=parable_id,
                memory_type=MemoryType.PATTERN,
                tags=["parable"],
                limit=1,
            )

            if results:
                return Parable.from_memory_entry(results[0])
            return None

        except Exception as e:
            logger.error(f"Error retrieving parable {parable_id}: {e}")
            return None

    def get_agent_parables(
        self,
        agent_id: str,
        limit: int = 20,
    ) -> List[Parable]:
        """
        Get all parables created by a specific agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of parables to return

        Returns:
            List of Parable instances from this agent
        """
        try:
            results = self.memory.get_agent_memories(
                agent_id=agent_id,
                memory_type=MemoryType.PATTERN,
                limit=limit,
            )

            # Filter to only parables and convert
            parables = []
            for entry in results:
                if "parable" in entry.tags:
                    try:
                        parable = Parable.from_memory_entry(entry)
                        parables.append(parable)
                    except Exception as e:
                        logger.warning(f"Failed to convert memory entry: {e}")
                        continue

            logger.debug(f"Found {len(parables)} parables for agent {agent_id}")
            return parables

        except Exception as e:
            logger.error(f"Error getting parables for agent {agent_id}: {e}")
            return []

    def search_semantic(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Parable]:
        """
        Perform semantic search across all parables.

        Args:
            query: Natural language query
            limit: Maximum number of results

        Returns:
            List of relevant Parable instances
        """
        try:
            results = self.memory.query_memories(
                query=query,
                memory_type=MemoryType.PATTERN,
                tags=["parable"],
                limit=limit,
            )

            parables = []
            for entry in results:
                try:
                    parable = Parable.from_memory_entry(entry)
                    parables.append(parable)
                except Exception as e:
                    logger.warning(f"Failed to convert memory entry: {e}")
                    continue

            logger.debug(f"Semantic search found {len(parables)} parables for: {query}")
            return parables

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
