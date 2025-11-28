"""
Conversation Store - Unified Persistence for ALL Conversations

This is a CORE feature of Vessels. Every interaction is persisted to the
knowledge graph for:
- Full conversation history
- Semantic search over past interactions
- Cross-vessel context sharing
- Analytics and insights
- Memory continuity

All paths through the system (user-vessel, vessel-vessel, user-ambassador)
flow through this store.
"""

import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Conversation Types
# =============================================================================

class ConversationType(str, Enum):
    """Types of conversations in the system."""
    USER_VESSEL = "user_vessel"           # User talking to a vessel
    VESSEL_VESSEL = "vessel_vessel"       # A2A vessel-to-vessel
    USER_AMBASSADOR = "user_ambassador"   # User talking to MCP ambassador
    VESSEL_AMBASSADOR = "vessel_ambassador"  # Vessel consulting ambassador
    USER_A0 = "user_a0"                   # User talking to Agent Zero directly
    SYSTEM = "system"                     # System-initiated conversations


class SpeakerType(str, Enum):
    """Types of speakers in a conversation."""
    USER = "user"
    VESSEL = "vessel"
    AMBASSADOR = "ambassador"
    AGENT = "agent"
    A0 = "a0"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Status of a conversation."""
    ACTIVE = "active"
    ENDED = "ended"
    ARCHIVED = "archived"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Turn:
    """A single turn in a conversation."""
    turn_id: str
    conversation_id: str
    sequence_number: int
    speaker_id: str
    speaker_type: SpeakerType
    message: str
    response: Optional[str] = None
    intent: Optional[str] = None
    entities: Optional[List[str]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    sentiment: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    response_at: Optional[datetime] = None
    latency_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "conversation_id": self.conversation_id,
            "sequence_number": self.sequence_number,
            "speaker_id": self.speaker_id,
            "speaker_type": self.speaker_type.value,
            "message": self.message,
            "response": self.response,
            "intent": self.intent,
            "entities": self.entities,
            "tool_calls": self.tool_calls,
            "sentiment": self.sentiment,
            "created_at": self.created_at.isoformat(),
            "response_at": self.response_at.isoformat() if self.response_at else None,
            "latency_ms": self.latency_ms,
        }


@dataclass
class Conversation:
    """A conversation session."""
    conversation_id: str
    participant_ids: List[str]
    conversation_type: ConversationType
    vessel_id: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    topic: Optional[str] = None
    summary: Optional[str] = None
    turn_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    last_activity_at: datetime = field(default_factory=datetime.utcnow)
    status: ConversationStatus = ConversationStatus.ACTIVE
    turns: List[Turn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "participant_ids": self.participant_ids,
            "conversation_type": self.conversation_type.value,
            "vessel_id": self.vessel_id,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "topic": self.topic,
            "summary": self.summary,
            "turn_count": self.turn_count,
            "started_at": self.started_at.isoformat(),
            "last_activity_at": self.last_activity_at.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
        }


# =============================================================================
# Conversation Store
# =============================================================================

class ConversationStore:
    """
    Unified conversation persistence layer.

    All conversations flow through this store, ensuring nothing is lost.
    Provides both in-memory caching for performance and graph persistence
    for durability.

    Features:
    - Structured node persistence (Conversation, Turn nodes)
    - Episodic memory via add_episode() for automatic entity extraction
    - Privacy scoping (user/vessel/project isolation)
    - In-memory caching with LRU eviction

    Usage:
        store = ConversationStore(graphiti_client)

        # Start a conversation
        conv = store.start_conversation(
            user_id="user-123",
            vessel_id="vessel-456",
            conversation_type=ConversationType.USER_VESSEL
        )

        # Record a turn
        turn = store.add_turn(
            conversation_id=conv.conversation_id,
            speaker_id="user-123",
            speaker_type=SpeakerType.USER,
            message="Hello, how are you?"
        )

        # Record response
        store.add_response(
            turn_id=turn.turn_id,
            response="I'm doing well, thank you!"
        )

        # Search conversations
        results = store.search("grant writing")
    """

    def __init__(
        self,
        graphiti_client: Optional[Any] = None,
        enable_caching: bool = True,
        max_cache_size: int = 1000,
        enable_entity_extraction: bool = True,
    ):
        """
        Initialize conversation store.

        Args:
            graphiti_client: VesselsGraphitiClient or GraphitiMemoryBackend
            enable_caching: Keep recent conversations in memory
            max_cache_size: Max conversations to cache
            enable_entity_extraction: Use add_episode() for automatic entity extraction
        """
        self.graphiti = graphiti_client
        self.enable_caching = enable_caching
        self.max_cache_size = max_cache_size
        self.enable_entity_extraction = enable_entity_extraction

        # In-memory cache for active conversations
        self._conversations: Dict[str, Conversation] = {}
        self._turns: Dict[str, Turn] = {}

        # Index by participant
        self._by_user: Dict[str, List[str]] = {}      # user_id -> [conversation_ids]
        self._by_vessel: Dict[str, List[str]] = {}    # vessel_id -> [conversation_ids]
        self._by_project: Dict[str, List[str]] = {}   # project_id -> [conversation_ids]

        logger.info(
            f"ConversationStore initialized "
            f"(entity_extraction={'enabled' if enable_entity_extraction else 'disabled'})"
        )

    # =========================================================================
    # Graph Client Helper
    # =========================================================================

    def _get_client(self) -> Optional[Any]:
        """Get the underlying Graphiti client."""
        if not self.graphiti:
            return None
        # Direct VesselsGraphitiClient
        if hasattr(self.graphiti, 'create_node'):
            return self.graphiti
        # Wrapped in GraphitiMemoryBackend
        if hasattr(self.graphiti, 'graphiti') and hasattr(self.graphiti.graphiti, 'create_node'):
            return self.graphiti.graphiti
        return None

    # =========================================================================
    # Entity Extraction via Graphiti Episodes
    # =========================================================================

    def _format_turn_as_episode(
        self,
        turn: Turn,
        conversation: Optional[Conversation] = None,
    ) -> str:
        """
        Format a turn as narrative text for Graphiti entity extraction.

        Creates natural language that Graphiti can parse to extract:
        - Named entities (people, places, concepts)
        - Relationships between entities
        - Topics and themes
        - Temporal information

        Args:
            turn: The turn to format
            conversation: Optional conversation context

        Returns:
            Narrative text suitable for add_episode()
        """
        parts = []

        # Add speaker context
        speaker_label = self._get_speaker_label(turn.speaker_id, turn.speaker_type)

        # Format the message
        parts.append(f"{speaker_label} said: \"{turn.message}\"")

        # Add response if present
        if turn.response:
            responder_label = self._get_responder_label(turn, conversation)
            parts.append(f"{responder_label} responded: \"{turn.response}\"")

        # Add detected intent if available
        if turn.intent:
            parts.append(f"The intent was: {turn.intent}")

        # Add topic context if available
        if conversation and conversation.topic:
            parts.append(f"This was part of a conversation about: {conversation.topic}")

        return " ".join(parts)

    def _get_speaker_label(self, speaker_id: str, speaker_type: SpeakerType) -> str:
        """Get a human-readable label for a speaker."""
        if speaker_type == SpeakerType.USER:
            return f"User ({speaker_id})"
        elif speaker_type == SpeakerType.VESSEL:
            return f"Vessel ({speaker_id})"
        elif speaker_type == SpeakerType.AMBASSADOR:
            return f"Ambassador ({speaker_id})"
        elif speaker_type == SpeakerType.A0:
            return "Agent Zero"
        else:
            return f"{speaker_type.value.title()} ({speaker_id})"

    def _get_responder_label(
        self,
        turn: Turn,
        conversation: Optional[Conversation],
    ) -> str:
        """Determine who responded to a turn."""
        # User messages are typically responded to by vessels/agents
        if turn.speaker_type == SpeakerType.USER:
            if conversation and conversation.vessel_id:
                return f"Vessel ({conversation.vessel_id})"
            return "The vessel"
        # Vessel/agent messages are responded to by users or other agents
        elif turn.speaker_type in (SpeakerType.VESSEL, SpeakerType.AMBASSADOR, SpeakerType.A0):
            if conversation and conversation.user_id:
                return f"User ({conversation.user_id})"
            return "The user"
        return "The responder"

    def _build_episode_metadata(
        self,
        turn: Turn,
        conversation: Optional[Conversation] = None,
    ) -> Dict[str, Any]:
        """
        Build metadata for an episode.

        Includes privacy scoping information for isolation.
        """
        metadata = {
            "turn_id": turn.turn_id,
            "conversation_id": turn.conversation_id,
            "speaker_id": turn.speaker_id,
            "speaker_type": turn.speaker_type.value,
            "sequence": turn.sequence_number,
            "timestamp": turn.created_at.isoformat(),
            "source": "conversation_store",
        }

        # Privacy scoping - critical for isolation
        if conversation:
            if conversation.user_id:
                metadata["user_id"] = conversation.user_id
            if conversation.vessel_id:
                metadata["vessel_id"] = conversation.vessel_id
            if conversation.project_id:
                metadata["project_id"] = conversation.project_id
            metadata["conversation_type"] = conversation.conversation_type.value

        # Add entities if detected
        if turn.entities:
            metadata["pre_extracted_entities"] = turn.entities

        return metadata

    def _extract_entities_from_turn(
        self,
        turn: Turn,
        conversation: Optional[Conversation] = None,
    ) -> None:
        """
        Use Graphiti's add_episode() for automatic entity extraction.

        This sends the turn as narrative text to Graphiti, which will:
        1. Parse the text for named entities
        2. Extract relationships between entities
        3. Build/update the knowledge graph
        4. Create searchable embeddings
        """
        if not self.enable_entity_extraction:
            return

        client = self._get_client()
        if not client or not hasattr(client, 'add_episode'):
            return

        try:
            # Format turn as narrative
            episode_text = self._format_turn_as_episode(turn, conversation)

            # Build metadata with privacy scoping
            metadata = self._build_episode_metadata(turn, conversation)

            # Send to Graphiti for entity extraction
            client.add_episode(text=episode_text, metadata=metadata)

            logger.debug(
                f"Entity extraction complete for turn {turn.turn_id[:8]}... "
                f"(text: {len(episode_text)} chars)"
            )

        except Exception as e:
            # Don't fail the turn if entity extraction fails
            logger.warning(f"Entity extraction failed for turn {turn.turn_id}: {e}")

    def generate_image_prompt(
        self,
        turn: Turn,
        conversation: Optional[Conversation] = None,
        style: str = "warm, Hawaiian, community-focused",
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an image prompt based on extracted entities from a turn.

        This is the first practical use of entity extraction - creating
        contextual visual content for the conversation.

        Args:
            turn: The turn to generate a prompt for
            conversation: Optional conversation context
            style: Visual style guidance

        Returns:
            Dict with prompt, entities used, and metadata, or None if no visual content needed
        """
        # Collect entities from the turn
        entities = turn.entities or []

        # Also extract key nouns/concepts from message if no entities provided
        if not entities:
            entities = self._extract_visual_concepts(turn.message)

        if not entities:
            return None  # Nothing visual to generate

        # Categorize entities for better prompts
        places = []
        people_types = []
        objects = []
        concepts = []

        # Simple categorization (in production, use NLP)
        place_keywords = ['valley', 'center', 'garden', 'farm', 'beach', 'mountain', 'village', 'hawaii', 'kailua', 'waipio']
        people_keywords = ['kupuna', 'elder', 'farmer', 'family', 'community', 'neighbor', 'ohana']
        object_keywords = ['taro', 'food', 'meal', 'grant', 'program', 'building']

        for entity in entities:
            entity_lower = entity.lower()
            if any(kw in entity_lower for kw in place_keywords):
                places.append(entity)
            elif any(kw in entity_lower for kw in people_keywords):
                people_types.append(entity)
            elif any(kw in entity_lower for kw in object_keywords):
                objects.append(entity)
            else:
                concepts.append(entity)

        # Build the image prompt
        prompt_parts = []

        # Scene setting
        if places:
            prompt_parts.append(f"Scene in {', '.join(places)}")
        else:
            prompt_parts.append("A warm Hawaiian community scene")

        # People
        if people_types:
            prompt_parts.append(f"featuring {', '.join(people_types)}")

        # Objects/activities
        if objects:
            prompt_parts.append(f"with {', '.join(objects)}")

        # Add style
        prompt_parts.append(f"Style: {style}")

        # Add conversation topic context
        if conversation and conversation.topic:
            prompt_parts.append(f"Theme: {conversation.topic}")

        image_prompt = ". ".join(prompt_parts)

        return {
            "prompt": image_prompt,
            "entities_used": entities,
            "places": places,
            "people_types": people_types,
            "objects": objects,
            "concepts": concepts,
            "turn_id": turn.turn_id,
            "conversation_id": turn.conversation_id,
            "style": style,
        }

    def _extract_visual_concepts(self, text: str) -> List[str]:
        """
        Extract visual concepts from text when no entities are provided.

        Simple keyword extraction for visual elements.
        """
        # Visual keywords to look for
        visual_keywords = [
            # Places
            'garden', 'farm', 'valley', 'beach', 'mountain', 'center', 'home',
            'village', 'community', 'building', 'office',
            # Hawaiian places
            'kailua', 'waipio', 'maui', 'oahu', 'hawaii', 'honolulu',
            # People
            'kupuna', 'elder', 'family', 'children', 'farmer', 'community',
            # Things
            'taro', 'food', 'meal', 'plant', 'water', 'ocean',
            # Activities
            'farming', 'cooking', 'gathering', 'meeting', 'caring',
        ]

        text_lower = text.lower()
        found = []

        for keyword in visual_keywords:
            if keyword in text_lower:
                found.append(keyword)

        return found[:5]  # Limit to 5 most relevant

    # =========================================================================
    # Conversation Lifecycle
    # =========================================================================

    def start_conversation(
        self,
        conversation_type: ConversationType,
        participant_ids: List[str],
        vessel_id: Optional[str] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        topic: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """
        Start a new conversation.

        Args:
            conversation_type: Type of conversation
            participant_ids: List of participant IDs
            vessel_id: Primary vessel ID (if applicable)
            user_id: User ID (if applicable)
            project_id: Project context
            topic: Initial topic
            metadata: Additional metadata

        Returns:
            Created Conversation
        """
        conversation_id = str(uuid.uuid4())

        conversation = Conversation(
            conversation_id=conversation_id,
            participant_ids=participant_ids,
            conversation_type=conversation_type,
            vessel_id=vessel_id,
            user_id=user_id,
            project_id=project_id,
            topic=topic,
            metadata=metadata or {},
        )

        # Cache
        if self.enable_caching:
            self._conversations[conversation_id] = conversation
            self._evict_if_needed()

            # Index by user/vessel/project for privacy scoping
            if user_id:
                if user_id not in self._by_user:
                    self._by_user[user_id] = []
                self._by_user[user_id].append(conversation_id)

            if vessel_id:
                if vessel_id not in self._by_vessel:
                    self._by_vessel[vessel_id] = []
                self._by_vessel[vessel_id].append(conversation_id)

            if project_id:
                if project_id not in self._by_project:
                    self._by_project[project_id] = []
                self._by_project[project_id].append(conversation_id)

        # Persist to graph
        self._persist_conversation(conversation)

        logger.info(f"Started conversation {conversation_id[:8]}... ({conversation_type.value})")
        return conversation

    def get_or_create_conversation(
        self,
        user_id: str,
        vessel_id: str,
        conversation_type: ConversationType = ConversationType.USER_VESSEL,
        project_id: Optional[str] = None,
    ) -> Conversation:
        """
        Get existing active conversation or create new one.

        Useful for continuing conversations without explicit session management.
        """
        # Check cache for active conversation
        if user_id in self._by_user:
            for conv_id in reversed(self._by_user[user_id]):  # Most recent first
                conv = self._conversations.get(conv_id)
                if (conv and
                    conv.vessel_id == vessel_id and
                    conv.status == ConversationStatus.ACTIVE):
                    return conv

        # Create new
        return self.start_conversation(
            conversation_type=conversation_type,
            participant_ids=[user_id, vessel_id],
            vessel_id=vessel_id,
            user_id=user_id,
            project_id=project_id,
        )

    def end_conversation(self, conversation_id: str, summary: Optional[str] = None) -> bool:
        """End a conversation."""
        conversation = self._conversations.get(conversation_id)
        if not conversation:
            return False

        conversation.status = ConversationStatus.ENDED
        conversation.last_activity_at = datetime.utcnow()
        if summary:
            conversation.summary = summary

        self._persist_conversation(conversation)
        logger.info(f"Ended conversation {conversation_id[:8]}...")
        return True

    # =========================================================================
    # Turn Management
    # =========================================================================

    def add_turn(
        self,
        conversation_id: str,
        speaker_id: str,
        speaker_type: SpeakerType,
        message: str,
        intent: Optional[str] = None,
        entities: Optional[List[str]] = None,
    ) -> Turn:
        """
        Add a turn (message) to a conversation.

        Args:
            conversation_id: Conversation to add to
            speaker_id: Who is speaking
            speaker_type: Type of speaker
            message: The message content
            intent: Detected intent (optional)
            entities: Extracted entities (optional)

        Returns:
            Created Turn
        """
        turn_id = str(uuid.uuid4())

        # Get conversation to determine sequence
        conversation = self._conversations.get(conversation_id)
        sequence = conversation.turn_count if conversation else 0

        turn = Turn(
            turn_id=turn_id,
            conversation_id=conversation_id,
            sequence_number=sequence,
            speaker_id=speaker_id,
            speaker_type=speaker_type,
            message=message,
            intent=intent,
            entities=entities,
        )

        # Update conversation
        if conversation:
            conversation.turns.append(turn)
            conversation.turn_count += 1
            conversation.last_activity_at = datetime.utcnow()

        # Cache turn
        self._turns[turn_id] = turn

        # Persist
        self._persist_turn(turn)

        logger.debug(f"Added turn {turn_id[:8]}... to conversation {conversation_id[:8]}...")
        return turn

    def add_response(
        self,
        turn_id: str,
        response: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        sentiment: Optional[str] = None,
    ) -> Optional[Turn]:
        """
        Add a response to an existing turn.

        Args:
            turn_id: Turn to respond to
            response: Response content
            tool_calls: Tools that were called
            sentiment: Detected sentiment

        Returns:
            Updated Turn or None
        """
        turn = self._turns.get(turn_id)
        if not turn:
            logger.warning(f"Turn {turn_id} not found")
            return None

        turn.response = response
        turn.response_at = datetime.utcnow()
        turn.tool_calls = tool_calls
        turn.sentiment = sentiment

        # Calculate latency
        if turn.created_at:
            delta = turn.response_at - turn.created_at
            turn.latency_ms = int(delta.total_seconds() * 1000)

        # Persist update
        self._persist_turn(turn)

        # Get conversation for entity extraction context
        conversation = self._conversations.get(turn.conversation_id)

        # Extract entities now that we have the complete turn (message + response)
        self._extract_entities_from_turn(turn, conversation)

        return turn

    def record_complete_turn(
        self,
        conversation_id: str,
        speaker_id: str,
        speaker_type: SpeakerType,
        message: str,
        response: str,
        responder_id: Optional[str] = None,
        intent: Optional[str] = None,
        entities: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> Turn:
        """
        Record a complete turn (message + response) in one call.

        Convenience method for when you have both parts at once.
        """
        turn = self.add_turn(
            conversation_id=conversation_id,
            speaker_id=speaker_id,
            speaker_type=speaker_type,
            message=message,
            intent=intent,
            entities=entities,
        )

        self.add_response(
            turn_id=turn.turn_id,
            response=response,
            tool_calls=tool_calls,
        )

        return turn

    # =========================================================================
    # Retrieval
    # =========================================================================

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        # Check cache
        if conversation_id in self._conversations:
            return self._conversations[conversation_id]

        # Try to load from graph
        return self._load_conversation_from_graph(conversation_id)

    def get_turn(self, turn_id: str) -> Optional[Turn]:
        """Get a turn by ID."""
        return self._turns.get(turn_id)

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        include_ended: bool = False,
    ) -> List[Conversation]:
        """Get conversations for a user."""
        conv_ids = self._by_user.get(user_id, [])
        conversations = []

        for conv_id in reversed(conv_ids):  # Most recent first
            conv = self._conversations.get(conv_id)
            if conv:
                if include_ended or conv.status == ConversationStatus.ACTIVE:
                    conversations.append(conv)
                if len(conversations) >= limit:
                    break

        return conversations

    def get_vessel_conversations(
        self,
        vessel_id: str,
        limit: int = 20,
        include_ended: bool = False,
    ) -> List[Conversation]:
        """Get conversations for a vessel."""
        conv_ids = self._by_vessel.get(vessel_id, [])
        conversations = []

        for conv_id in reversed(conv_ids):
            conv = self._conversations.get(conv_id)
            if conv:
                if include_ended or conv.status == ConversationStatus.ACTIVE:
                    conversations.append(conv)
                if len(conversations) >= limit:
                    break

        return conversations

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50,
    ) -> List[Dict[str, str]]:
        """
        Get conversation history in simple format.

        Returns list of {"role": "user/assistant", "content": "..."}
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []

        history = []
        for turn in conversation.turns[-limit:]:
            # Message
            role = "user" if turn.speaker_type in (SpeakerType.USER,) else "assistant"
            history.append({"role": role, "content": turn.message})

            # Response (if present)
            if turn.response:
                history.append({"role": "assistant", "content": turn.response})

        return history

    # =========================================================================
    # Privacy Scoping
    # =========================================================================

    def get_project_conversations(
        self,
        project_id: str,
        limit: int = 20,
        include_ended: bool = False,
    ) -> List[Conversation]:
        """Get conversations for a project."""
        conv_ids = self._by_project.get(project_id, [])
        conversations = []

        for conv_id in reversed(conv_ids):  # Most recent first
            conv = self._conversations.get(conv_id)
            if conv:
                if include_ended or conv.status == ConversationStatus.ACTIVE:
                    conversations.append(conv)
                if len(conversations) >= limit:
                    break

        return conversations

    def check_access(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> bool:
        """
        Check if an entity has access to a conversation.

        Privacy rules:
        - A user can access their own conversations
        - A vessel can access conversations it participates in
        - Project members can access project conversations
        - Admins can access all (not implemented here, handled at API layer)
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False

        # User access: must be a participant
        if user_id:
            if conversation.user_id == user_id:
                return True
            if user_id in conversation.participant_ids:
                return True

        # Vessel access: must be a participant
        if vessel_id:
            if conversation.vessel_id == vessel_id:
                return True
            if vessel_id in conversation.participant_ids:
                return True

        # Project access: must match project
        if project_id:
            if conversation.project_id == project_id:
                return True

        return False

    def get_accessible_conversations(
        self,
        user_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Conversation]:
        """
        Get all conversations accessible within a privacy scope.

        Returns conversations where the caller is authorized to access.
        """
        accessible_ids: set = set()

        if user_id and user_id in self._by_user:
            accessible_ids.update(self._by_user[user_id])

        if vessel_id and vessel_id in self._by_vessel:
            accessible_ids.update(self._by_vessel[vessel_id])

        if project_id and project_id in self._by_project:
            accessible_ids.update(self._by_project[project_id])

        # Sort by last activity and return
        conversations = []
        for conv_id in accessible_ids:
            conv = self._conversations.get(conv_id)
            if conv:
                conversations.append(conv)

        conversations.sort(key=lambda c: c.last_activity_at, reverse=True)
        return conversations[:limit]

    def scoped_search(
        self,
        query: str,
        user_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search within a privacy scope.

        Only returns results from conversations the caller can access.
        """
        # Get accessible conversations
        accessible = self.get_accessible_conversations(
            user_id=user_id,
            vessel_id=vessel_id,
            project_id=project_id,
            limit=1000,  # Get all accessible for filtering
        )
        accessible_ids = {c.conversation_id for c in accessible}

        # Search and filter
        all_results = self.search(query, limit=limit * 2)  # Get more to filter

        filtered_results = []
        for result in all_results:
            if result.get("conversation_id") in accessible_ids:
                filtered_results.append(result)
                if len(filtered_results) >= limit:
                    break

        return filtered_results

    # =========================================================================
    # Search
    # =========================================================================

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        vessel_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Search conversations and turns.

        Uses graph search if available, falls back to in-memory.
        """
        client = self._get_client()

        # Try graph search
        if client and hasattr(client, 'search'):
            try:
                results = client.search(query, limit=limit)
                return results
            except Exception as e:
                logger.warning(f"Graph search failed: {e}")

        # Fallback to in-memory search
        results = []
        query_lower = query.lower()

        for conv in self._conversations.values():
            # Filter by user/vessel
            if user_id and conv.user_id != user_id:
                continue
            if vessel_id and conv.vessel_id != vessel_id:
                continue

            # Search in turns
            for turn in conv.turns:
                if query_lower in turn.message.lower():
                    results.append({
                        "type": "turn",
                        "conversation_id": conv.conversation_id,
                        "turn_id": turn.turn_id,
                        "message": turn.message,
                        "response": turn.response,
                        "created_at": turn.created_at.isoformat(),
                    })

                if len(results) >= limit:
                    break

            if len(results) >= limit:
                break

        return results

    # =========================================================================
    # Persistence
    # =========================================================================

    def _persist_conversation(self, conversation: Conversation) -> None:
        """Persist conversation to graph."""
        client = self._get_client()
        if not client:
            return

        try:
            from vessels.knowledge.schema import NodeType, PropertyName

            client.create_node(
                node_type=NodeType.CONVERSATION,
                properties={
                    "conversation_id": conversation.conversation_id,
                    "participant_ids": json.dumps(conversation.participant_ids),
                    "participant_type": conversation.conversation_type.value,
                    "vessel_id": conversation.vessel_id,
                    "user_id": conversation.user_id,
                    "project_id": conversation.project_id,
                    "topic": conversation.topic,
                    "summary": conversation.summary,
                    "turn_count": conversation.turn_count,
                    "started_at": conversation.started_at.isoformat(),
                    "last_activity_at": conversation.last_activity_at.isoformat(),
                    PropertyName.STATUS: conversation.status.value,
                },
                node_id=conversation.conversation_id,
            )
        except Exception as e:
            logger.error(f"Failed to persist conversation: {e}")

    def _persist_turn(self, turn: Turn) -> None:
        """Persist turn to graph."""
        client = self._get_client()
        if not client:
            return

        try:
            from vessels.knowledge.schema import NodeType, PropertyName

            client.create_node(
                node_type=NodeType.TURN,
                properties={
                    "turn_id": turn.turn_id,
                    "conversation_id": turn.conversation_id,
                    "sequence_number": turn.sequence_number,
                    "speaker_id": turn.speaker_id,
                    "speaker_type": turn.speaker_type.value,
                    "message": turn.message,
                    "response": turn.response,
                    "intent": turn.intent,
                    "entities": json.dumps(turn.entities) if turn.entities else None,
                    "tool_calls": json.dumps(turn.tool_calls) if turn.tool_calls else None,
                    "sentiment": turn.sentiment,
                    PropertyName.CREATED_AT: turn.created_at.isoformat(),
                    "response_at": turn.response_at.isoformat() if turn.response_at else None,
                    "latency_ms": turn.latency_ms,
                },
                node_id=turn.turn_id,
            )

            # Create relationship to conversation
            if hasattr(client, 'create_relationship'):
                from vessels.knowledge.schema import RelationType
                client.create_relationship(
                    source_id=turn.conversation_id,
                    rel_type=RelationType.HAS_TURN,
                    target_id=turn.turn_id,
                    properties={"sequence": turn.sequence_number},
                )

        except Exception as e:
            logger.error(f"Failed to persist turn: {e}")

    def _load_conversation_from_graph(self, conversation_id: str) -> Optional[Conversation]:
        """Load conversation from graph."""
        client = self._get_client()
        if not client or not hasattr(client, 'query'):
            return None

        try:
            result = client.query(
                f"MATCH (c:Conversation {{conversation_id: '{conversation_id}'}}) RETURN c"
            )
            if result:
                # Parse and return
                # (Implementation depends on graph response format)
                pass
        except Exception as e:
            logger.error(f"Failed to load conversation from graph: {e}")

        return None

    # =========================================================================
    # Cache Management
    # =========================================================================

    def _evict_if_needed(self) -> None:
        """Evict old conversations if cache is full."""
        if len(self._conversations) <= self.max_cache_size:
            return

        # Sort by last activity, evict oldest ended conversations first
        sorted_convs = sorted(
            self._conversations.items(),
            key=lambda x: (
                x[1].status != ConversationStatus.ENDED,
                x[1].last_activity_at,
            )
        )

        # Evict 10%
        to_evict = len(self._conversations) - int(self.max_cache_size * 0.9)
        for conv_id, _ in sorted_convs[:to_evict]:
            del self._conversations[conv_id]

        logger.debug(f"Evicted {to_evict} conversations from cache")

    # =========================================================================
    # Stats
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        active = sum(1 for c in self._conversations.values()
                    if c.status == ConversationStatus.ACTIVE)
        total_turns = sum(c.turn_count for c in self._conversations.values())

        return {
            "cached_conversations": len(self._conversations),
            "active_conversations": active,
            "cached_turns": len(self._turns),
            "total_turns": total_turns,
            "users_tracked": len(self._by_user),
            "vessels_tracked": len(self._by_vessel),
            "graph_connected": self._get_client() is not None,
        }
