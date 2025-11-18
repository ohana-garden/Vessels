"""
Choreography Engine - Cinematic Timing & Pacing
===============================================

The screen changes like a TV show or movie:
- Different "shots" every few seconds
- Pacing is contextual (slow for important moments, fast for routine)
- Visual transitions match emotional beats
- Timing creates dramatic effect

Key Principles:
- Average shot duration: 3-5 seconds (like TV)
- Important moments: Slow down to 7-10 seconds
- Routine updates: Speed up to 1-2 seconds
- Transitions feel natural and purposeful
- Multiple agents create rhythm through alternating dialogue
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
import time
import logging
import asyncio

logger = logging.getLogger(__name__)


class ShotType(Enum):
    """Types of visual shots"""
    ESTABLISHING = "establishing"  # Set the scene
    CLOSE_UP = "close_up"  # Focus on one agent
    TWO_SHOT = "two_shot"  # Two agents in conversation
    WIDE = "wide"  # Multiple agents/full context
    DETAIL = "detail"  # Specific content (grant card, protocol step)
    TRANSITION = "transition"  # Moving between contexts


class Pace(Enum):
    """Pacing of the scene"""
    VERY_SLOW = 10.0  # Dramatic, emotional moments
    SLOW = 7.0  # Important information
    NORMAL = 4.0  # Standard conversation
    QUICK = 2.5  # Routine updates
    RAPID = 1.5  # Excitement, urgency


class EmotionalBeat(Enum):
    """Emotional tone of a moment"""
    WELCOMING = "welcoming"
    TEACHING = "teaching"
    DISCOVERING = "discovering"
    CELEBRATING = "celebrating"
    REFLECTING = "reflecting"
    URGENT = "urgent"
    PLAYFUL = "playful"
    SOLEMN = "solemn"
    HOPEFUL = "hopeful"
    CONCERNED = "concerned"


@dataclass
class Shot:
    """A single visual moment"""
    shot_id: str
    shot_type: ShotType
    duration: float  # seconds
    visual_state: str  # What's displayed
    agents_visible: List[str]  # Which agents are "on screen"
    dialogue: Optional[Dict[str, str]] = None  # What's being said
    emotional_beat: EmotionalBeat = EmotionalBeat.TEACHING
    transition_in: str = "fade"  # How to enter this shot
    transition_out: str = "fade"  # How to exit
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Check if this shot's duration has elapsed"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed >= self.duration


@dataclass
class Scene:
    """A sequence of shots that form a coherent narrative unit"""
    scene_id: str
    title: str
    shots: List[Shot] = field(default_factory=list)
    current_shot_index: int = 0
    started_at: Optional[datetime] = None
    emotional_arc: List[EmotionalBeat] = field(default_factory=list)

    def current_shot(self) -> Optional[Shot]:
        """Get current shot"""
        if 0 <= self.current_shot_index < len(self.shots):
            return self.shots[self.current_shot_index]
        return None

    def advance(self) -> Optional[Shot]:
        """Move to next shot"""
        self.current_shot_index += 1
        return self.current_shot()

    def is_complete(self) -> bool:
        """Check if scene is finished"""
        return self.current_shot_index >= len(self.shots)


class ChoreographyEngine:
    """
    The Choreography Engine - Director of the visual experience

    Manages:
    - Shot timing and pacing
    - Visual transitions
    - Emotional beats
    - Multi-agent dialogue rhythm
    - Screen state changes
    """

    def __init__(self):
        self.active_scenes: Dict[str, Scene] = {}
        self.current_pace = Pace.NORMAL
        self.callbacks: Dict[str, Callable] = {}

        # Timing adjustments based on context
        self.pace_modifiers = {
            "first_time_user": 1.5,  # 50% slower for new users
            "elder": 1.8,  # 80% slower for elders
            "crisis": 0.6,  # 40% faster during crisis
            "celebration": 1.2,  # 20% slower for celebrations
            "routine": 0.8  # 20% faster for routine
        }

    def create_arrival_scene(
        self,
        conversation_state: Any,  # ConversationState from context_engine
        user_context: Any  # UserContext from context_engine
    ) -> Scene:
        """
        Create the opening scene when user arrives

        Choreographs the first 15-30 seconds of experience
        """
        scene_id = f"arrival_{conversation_state.conversation_id}"

        # Determine base pace
        pace = self.determine_pace(conversation_state, user_context)

        scene = Scene(
            scene_id=scene_id,
            title=f"Arrival: {conversation_state.topic}",
            started_at=datetime.now()
        )

        # Shot 1: Establishing shot - Show the visual state
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_establishing",
            shot_type=ShotType.ESTABLISHING,
            duration=pace.value * 1.2,  # Slightly longer for establishing
            visual_state=conversation_state.visual_state,
            agents_visible=conversation_state.participants[:2],
            emotional_beat=self.determine_emotional_beat(conversation_state.topic)
        ))

        # Shots 2-N: Dialogue between agents
        for i, dialogue_entry in enumerate(conversation_state.dialogue):
            # Determine shot type based on dialogue position
            if i == 0:
                shot_type = ShotType.CLOSE_UP  # Focus on first speaker
            elif i == len(conversation_state.dialogue) - 1:
                shot_type = ShotType.TWO_SHOT  # Open to user at end
            else:
                shot_type = ShotType.CLOSE_UP if i % 2 == 0 else ShotType.TWO_SHOT

            # Adjust duration based on dialogue length
            text_length = len(dialogue_entry.get("text", ""))
            base_duration = pace.value
            reading_time = text_length / 15  # ~15 chars per second reading speed
            duration = max(base_duration, reading_time + 1.0)  # At least 1 sec after reading

            scene.shots.append(Shot(
                shot_id=f"{scene_id}_dialogue_{i}",
                shot_type=shot_type,
                duration=duration,
                visual_state=conversation_state.visual_state,
                agents_visible=[dialogue_entry.get("agent_id")],
                dialogue=dialogue_entry,
                emotional_beat=self.determine_emotional_beat(conversation_state.topic)
            ))

            scene.emotional_arc.append(
                self.determine_emotional_beat(conversation_state.topic)
            )

        # Final shot: Wide shot showing all agents, inviting user to join
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_wide",
            shot_type=ShotType.WIDE,
            duration=pace.value,
            visual_state=conversation_state.visual_state,
            agents_visible=conversation_state.participants,
            emotional_beat=EmotionalBeat.WELCOMING
        ))

        self.active_scenes[scene_id] = scene

        logger.info(f"Created arrival scene: {scene_id} with {len(scene.shots)} shots")

        return scene

    def create_agent_creation_scene(
        self,
        creation_conversation: Any,  # CreationConversation
        phase_name: str
    ) -> Scene:
        """
        Create scene for agent creation conversation

        Each phase gets its own choreography showing agent "taking shape"
        """
        scene_id = f"creation_{creation_conversation.creation_id}_{phase_name}"

        scene = Scene(
            scene_id=scene_id,
            title=f"Creating Agent: {phase_name}",
            started_at=datetime.now()
        )

        # Pace is slower for creation (intimate, important)
        pace = Pace.SLOW

        # Establishing shot: Show creation canvas
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_canvas",
            shot_type=ShotType.ESTABLISHING,
            duration=pace.value,
            visual_state=creation_conversation.visual_state,
            agents_visible=creation_conversation.facilitators,
            emotional_beat=EmotionalBeat.DISCOVERING
        ))

        # Dialogue shots
        recent_dialogue = creation_conversation.conversation_history[-5:]  # Last 5 exchanges
        for i, dialogue_entry in enumerate(recent_dialogue):
            is_user = dialogue_entry.get("agent_id") == "user"

            # User responses get close-up
            shot_type = ShotType.CLOSE_UP if is_user else ShotType.TWO_SHOT

            # Calculate duration
            text_length = len(dialogue_entry.get("text", ""))
            reading_time = text_length / 15
            duration = max(pace.value, reading_time + 1.5)

            # Emotional beat for creation
            if phase_name == "discovery":
                beat = EmotionalBeat.DISCOVERING
            elif phase_name == "character":
                beat = EmotionalBeat.PLAYFUL
            elif phase_name == "birth":
                beat = EmotionalBeat.CELEBRATING
            else:
                beat = EmotionalBeat.TEACHING

            scene.shots.append(Shot(
                shot_id=f"{scene_id}_dialogue_{i}",
                shot_type=shot_type,
                duration=duration,
                visual_state=creation_conversation.visual_state,
                agents_visible=[dialogue_entry.get("agent_id")],
                dialogue=dialogue_entry,
                emotional_beat=beat
            ))

        # Detail shot: Show agent identity forming
        completeness = creation_conversation.identity.completeness()
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_detail",
            shot_type=ShotType.DETAIL,
            duration=pace.value * 1.5,
            visual_state=f"creation_progress_{int(completeness * 100)}",
            agents_visible=creation_conversation.facilitators,
            emotional_beat=EmotionalBeat.HOPEFUL
        ))

        self.active_scenes[scene_id] = scene

        return scene

    def create_multi_agent_coordination_scene(
        self,
        agents: List[str],
        topic: str,
        visual_state: str,
        urgency: float
    ) -> Scene:
        """
        Create scene for multiple agents coordinating

        Fast-paced, rhythmic, showing collaboration
        """
        scene_id = f"coordination_{int(time.time())}"

        # Pace based on urgency
        if urgency > 0.8:
            pace = Pace.RAPID
        elif urgency > 0.6:
            pace = Pace.QUICK
        else:
            pace = Pace.NORMAL

        scene = Scene(
            scene_id=scene_id,
            title=f"Coordination: {topic}",
            started_at=datetime.now()
        )

        # Wide shot: All agents
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_wide",
            shot_type=ShotType.WIDE,
            duration=pace.value,
            visual_state=visual_state,
            agents_visible=agents,
            emotional_beat=EmotionalBeat.URGENT if urgency > 0.7 else EmotionalBeat.TEACHING
        ))

        # Rapid cuts between agents (showing parallel work)
        for i, agent_id in enumerate(agents[:4]):  # Max 4 agents
            scene.shots.append(Shot(
                shot_id=f"{scene_id}_agent_{i}",
                shot_type=ShotType.CLOSE_UP,
                duration=pace.value * 0.8,  # Quick cuts
                visual_state=visual_state,
                agents_visible=[agent_id],
                emotional_beat=EmotionalBeat.URGENT if urgency > 0.7 else EmotionalBeat.TEACHING
            ))

        # Back to wide: Show result
        scene.shots.append(Shot(
            shot_id=f"{scene_id}_result",
            shot_type=ShotType.WIDE,
            duration=pace.value * 1.2,
            visual_state=visual_state,
            agents_visible=agents,
            emotional_beat=EmotionalBeat.HOPEFUL
        ))

        self.active_scenes[scene_id] = scene

        return scene

    def determine_pace(
        self,
        conversation_state: Any,
        user_context: Any
    ) -> Pace:
        """
        Determine appropriate pacing based on context
        """
        base_pace = Pace.NORMAL

        # Adjust for urgency
        if conversation_state.urgency > 0.8:
            base_pace = Pace.RAPID
        elif conversation_state.urgency > 0.6:
            base_pace = Pace.QUICK
        elif conversation_state.urgency < 0.3:
            base_pace = Pace.SLOW

        # Adjust for user type
        if hasattr(user_context, 'user_type'):
            user_type = user_context.user_type.value if hasattr(user_context.user_type, 'value') else str(user_context.user_type)

            if user_type == "first_time" or user_type == "elder":
                # Slow down for new users and elders
                if base_pace == Pace.RAPID:
                    base_pace = Pace.QUICK
                elif base_pace == Pace.QUICK:
                    base_pace = Pace.NORMAL
                elif base_pace == Pace.NORMAL:
                    base_pace = Pace.SLOW

        return base_pace

    def determine_emotional_beat(self, topic: str) -> EmotionalBeat:
        """Determine emotional tone from topic"""
        topic_lower = topic.lower()

        if "introducing" in topic_lower or "welcome" in topic_lower:
            return EmotionalBeat.WELCOMING
        elif "celebrating" in topic_lower or "success" in topic_lower:
            return EmotionalBeat.CELEBRATING
        elif "learning" in topic_lower or "challenges" in topic_lower:
            return EmotionalBeat.REFLECTING
        elif "crisis" in topic_lower or "urgent" in topic_lower:
            return EmotionalBeat.URGENT
        elif "preparing" in topic_lower:
            return EmotionalBeat.CONCERNED
        else:
            return EmotionalBeat.TEACHING

    async def play_scene(
        self,
        scene: Scene,
        shot_callback: Optional[Callable] = None
    ):
        """
        Play a scene, calling callback for each shot

        This is the runtime that advances through shots at appropriate timing
        """
        scene.started_at = datetime.now()

        logger.info(f"Starting scene: {scene.title} with {len(scene.shots)} shots")

        while not scene.is_complete():
            current_shot = scene.current_shot()

            if current_shot:
                # Call callback with current shot
                if shot_callback:
                    try:
                        await shot_callback(current_shot)
                    except Exception as e:
                        logger.error(f"Error in shot callback: {e}")

                # Wait for shot duration
                await asyncio.sleep(current_shot.duration)

            # Advance to next shot
            scene.advance()

        logger.info(f"Scene complete: {scene.title}")

    def register_callback(self, event_type: str, callback: Callable):
        """Register callback for specific events"""
        self.callbacks[event_type] = callback

    def get_current_shot(self, scene_id: str) -> Optional[Shot]:
        """Get current shot for a scene"""
        if scene_id in self.active_scenes:
            return self.active_scenes[scene_id].current_shot()
        return None

    def advance_shot(self, scene_id: str) -> Optional[Shot]:
        """Manually advance to next shot"""
        if scene_id in self.active_scenes:
            return self.active_scenes[scene_id].advance()
        return None


class TransitionDirector:
    """
    Manages transitions between shots

    Handles visual effects, timing, and emotional continuity
    """

    TRANSITIONS = {
        "fade": {"duration": 0.3, "effect": "opacity"},
        "slide": {"duration": 0.4, "effect": "transform"},
        "zoom": {"duration": 0.5, "effect": "scale"},
        "dissolve": {"duration": 0.6, "effect": "opacity-blur"},
        "cut": {"duration": 0.0, "effect": "instant"}
    }

    @staticmethod
    def select_transition(
        from_shot: Optional[Shot],
        to_shot: Shot
    ) -> str:
        """
        Select appropriate transition between shots
        """
        # No previous shot = fade in
        if not from_shot:
            return "fade"

        # Same visual state = cut (fast)
        if from_shot.visual_state == to_shot.visual_state:
            return "cut"

        # Different emotional beats = dissolve (smooth)
        if from_shot.emotional_beat != to_shot.emotional_beat:
            return "dissolve"

        # Urgency = cut or slide (fast)
        if to_shot.emotional_beat == EmotionalBeat.URGENT:
            return "slide"

        # Default = fade
        return "fade"

    @staticmethod
    def get_transition_duration(transition_type: str) -> float:
        """Get duration of a transition"""
        return TransitionDirector.TRANSITIONS.get(
            transition_type,
            TransitionDirector.TRANSITIONS["fade"]
        )["duration"]
