"""
Context Engine for Shoghi
==========================

The Context Engine determines what conversation is happening on screen when a user arrives.
It analyzes WHO/WHERE/WHEN/PREVIOUS STATE/GOALS/EVENTS/COMMUNITY STATE to create
a living, contextually relevant experience.

Key Principles:
- Screen is NEVER empty
- Agents are ALWAYS in conversation
- User JOINS ongoing conversations
- Context is MULTI-DIMENSIONAL
- Everything is CINEMATIC and DYNAMIC
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class UserType(Enum):
    """User classification for context"""
    FIRST_TIME = "first_time"
    RETURNING = "returning"
    REGULAR = "regular"
    COMMUNITY_LEADER = "community_leader"
    ELDER = "elder"
    DEVELOPER = "developer"
    CAREGIVER = "caregiver"
    VOLUNTEER = "volunteer"


class LocationContext(Enum):
    """Where the user is"""
    HOME = "home"
    COMMUNITY_CENTER = "community_center"
    IN_FIELD = "in_field"
    TRAVELING = "traveling"
    WORK = "work"
    UNKNOWN = "unknown"


class TimeContext(Enum):
    """When the user arrives"""
    EARLY_MORNING = "early_morning"  # 5am-8am
    MORNING = "morning"  # 8am-12pm
    MIDDAY = "midday"  # 12pm-2pm
    AFTERNOON = "afternoon"  # 2pm-5pm
    EVENING = "evening"  # 5pm-8pm
    NIGHT = "night"  # 8pm-10pm
    LATE_NIGHT = "late_night"  # 10pm-5am


class CommunityState(Enum):
    """Current state of the community"""
    NORMAL = "normal"
    CRISIS = "crisis"
    CELEBRATION = "celebration"
    PLANNING = "planning"
    RECOVERY = "recovery"
    ABUNDANCE = "abundance"
    SCARCITY = "scarcity"


@dataclass
class UserContext:
    """Comprehensive user context"""
    user_id: str
    user_type: UserType
    location: LocationContext
    previous_session: Optional[datetime] = None
    last_activity: Optional[str] = None
    stated_goals: List[str] = field(default_factory=list)
    active_agents: List[str] = field(default_factory=list)
    recent_successes: List[str] = field(default_factory=list)
    recent_failures: List[str] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    community_role: Optional[str] = None

    # Biometric/device info
    device_type: str = "smartphone"
    confidence_score: float = 1.0  # Biometric recognition confidence


@dataclass
class ScheduledEvent:
    """Events that influence context"""
    event_id: str
    event_type: str  # meeting, deadline, delivery, etc.
    title: str
    time: datetime
    participants: List[str]
    related_agents: List[str]
    urgency: float  # 0-1


@dataclass
class ConversationState:
    """The active conversation happening on screen"""
    conversation_id: str
    participants: List[str]  # Agent IDs
    topic: str
    visual_state: str  # What's displayed (grant_cards, protocol, etc.)
    urgency: float
    started_at: datetime
    dialogue: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class AgentPresence:
    """An agent available for conversation"""
    agent_id: str
    name: str
    persona: str
    kuleana: str
    availability: float  # 0-1, based on current load
    relevance_score: float  # 0-1, relevance to current context


class ContextEngine:
    """
    The Context Engine - Determines what's on screen when you arrive
    """

    def __init__(self, community_memory, agent_registry):
        self.community_memory = community_memory
        self.agent_registry = agent_registry
        self.active_conversations = {}
        self.scheduled_events = []
        self.community_state = CommunityState.NORMAL

        # System agents that help with onboarding and creation
        self.system_agents = {
            "shoghi_guide": AgentPresence(
                agent_id="shoghi_guide",
                name="Kumu",  # Hawaiian for teacher/guide
                persona="wise, welcoming, patient elder who explains with stories",
                kuleana="Helping newcomers understand Shoghi and agent creation",
                availability=1.0,
                relevance_score=0.0
            ),
            "agent_weaver": AgentPresence(
                agent_id="agent_weaver",
                name="Haku",  # Hawaiian for to compose/weave
                persona="creative, collaborative artisan who shapes agents through conversation",
                kuleana="Conversationally eliciting agent details and bringing agents to life",
                availability=1.0,
                relevance_score=0.0
            ),
            "community_coordinator": AgentPresence(
                agent_id="community_coordinator",
                name="Hui",  # Hawaiian for group/organization
                persona="energetic, organized facilitator who connects people and agents",
                kuleana="Coordinating multi-agent and multi-user collaborations",
                availability=1.0,
                relevance_score=0.0
            ),
            "wisdom_keeper": AgentPresence(
                agent_id="wisdom_keeper",
                name="Naʻau",  # Hawaiian for gut/intuition/wisdom
                persona="reflective, deep thinker who learns from experience",
                kuleana="Capturing lessons, patterns, and evolving agent intelligence",
                availability=1.0,
                relevance_score=0.0
            )
        }

    def get_time_context(self) -> TimeContext:
        """Determine time of day context"""
        hour = datetime.now().hour
        if 5 <= hour < 8:
            return TimeContext.EARLY_MORNING
        elif 8 <= hour < 12:
            return TimeContext.MORNING
        elif 12 <= hour < 14:
            return TimeContext.MIDDAY
        elif 14 <= hour < 17:
            return TimeContext.AFTERNOON
        elif 17 <= hour < 20:
            return TimeContext.EVENING
        elif 20 <= hour < 22:
            return TimeContext.NIGHT
        else:
            return TimeContext.LATE_NIGHT

    def analyze_user_context(self, user_id: str, biometric_data: Dict = None) -> UserContext:
        """
        Analyze comprehensive user context from all available signals
        """
        # Retrieve user history from community memory
        user_memories = self.community_memory.get_user_context(user_id)

        # Determine user type
        if not user_memories:
            user_type = UserType.FIRST_TIME
        else:
            # Analyze interaction patterns
            interaction_count = user_memories.get('interaction_count', 0)
            if interaction_count == 0:
                user_type = UserType.FIRST_TIME
            elif interaction_count < 5:
                user_type = UserType.RETURNING
            else:
                user_type = UserType.REGULAR

            # Override based on role
            role = user_memories.get('community_role')
            if role == 'leader':
                user_type = UserType.COMMUNITY_LEADER
            elif role == 'elder' or user_memories.get('age', 0) > 65:
                user_type = UserType.ELDER
            elif role == 'developer':
                user_type = UserType.DEVELOPER

        # Determine location (from biometric_data or device info)
        location = LocationContext.UNKNOWN
        if biometric_data:
            location_str = biometric_data.get('location', 'unknown')
            location = LocationContext[location_str.upper()] if location_str.upper() in LocationContext.__members__ else LocationContext.UNKNOWN

        # Build context
        context = UserContext(
            user_id=user_id,
            user_type=user_type,
            location=location,
            previous_session=user_memories.get('previous_session'),
            last_activity=user_memories.get('last_activity'),
            stated_goals=user_memories.get('stated_goals', []),
            active_agents=user_memories.get('active_agents', []),
            recent_successes=user_memories.get('recent_successes', []),
            recent_failures=user_memories.get('recent_failures', []),
            preferences=user_memories.get('preferences', {}),
            community_role=user_memories.get('community_role'),
            confidence_score=biometric_data.get('confidence', 1.0) if biometric_data else 1.0
        )

        return context

    def get_upcoming_events(self, hours_ahead: int = 24) -> List[ScheduledEvent]:
        """Get events happening soon"""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours_ahead)

        upcoming = [
            event for event in self.scheduled_events
            if now <= event.time <= cutoff
        ]

        # Sort by time
        upcoming.sort(key=lambda e: e.time)
        return upcoming

    def select_conversation_agents(
        self,
        user_context: UserContext,
        upcoming_events: List[ScheduledEvent]
    ) -> List[AgentPresence]:
        """
        Select 2-4 agents who should be in conversation when user arrives

        Selection criteria:
        - User type and needs
        - Time of day
        - Upcoming events
        - Recent activity
        - Community state
        """
        candidates = []

        # First-time users ALWAYS get Kumu + Haku
        if user_context.user_type == UserType.FIRST_TIME:
            self.system_agents['shoghi_guide'].relevance_score = 1.0
            self.system_agents['agent_weaver'].relevance_score = 1.0
            return [
                self.system_agents['shoghi_guide'],
                self.system_agents['agent_weaver']
            ]

        # Get user's active agents
        user_agents = []
        for agent_id in user_context.active_agents:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                presence = AgentPresence(
                    agent_id=agent_id,
                    name=agent.get('name', agent_id),
                    persona=agent.get('persona', ''),
                    kuleana=agent.get('kuleana', ''),
                    availability=agent.get('availability', 0.5),
                    relevance_score=0.5  # Base score for user's own agents
                )
                user_agents.append(presence)

        # Score relevance based on context
        for agent in user_agents:
            score = agent.relevance_score

            # Boost for agents related to upcoming events
            for event in upcoming_events:
                if agent.agent_id in event.related_agents:
                    score += 0.3 * event.urgency

            # Boost for agents related to recent activity
            if user_context.last_activity:
                if agent.kuleana and user_context.last_activity.lower() in agent.kuleana.lower():
                    score += 0.2

            # Boost for agents related to stated goals
            for goal in user_context.stated_goals:
                if agent.kuleana and goal.lower() in agent.kuleana.lower():
                    score += 0.3

            agent.relevance_score = min(score, 1.0)

        # Sort by relevance
        user_agents.sort(key=lambda a: a.relevance_score, reverse=True)

        # Select top 2-3 user agents
        selected = user_agents[:3]

        # Add system agents if helpful
        if len(selected) < 2:
            # Need more conversation partners
            if user_context.recent_failures:
                # Add Wisdom Keeper to discuss lessons learned
                self.system_agents['wisdom_keeper'].relevance_score = 0.8
                selected.append(self.system_agents['wisdom_keeper'])
            else:
                # Add Community Coordinator for multi-agent work
                self.system_agents['community_coordinator'].relevance_score = 0.7
                selected.append(self.system_agents['community_coordinator'])

        # If user wants to create agent, add Agent Weaver
        if any('create' in goal.lower() or 'new agent' in goal.lower() for goal in user_context.stated_goals):
            if self.system_agents['agent_weaver'] not in selected:
                self.system_agents['agent_weaver'].relevance_score = 0.9
                selected.append(self.system_agents['agent_weaver'])

        return selected[:4]  # Max 4 agents in conversation

    def generate_conversation_topic(
        self,
        user_context: UserContext,
        agents: List[AgentPresence],
        upcoming_events: List[ScheduledEvent]
    ) -> str:
        """
        Generate the topic agents are discussing when user arrives
        """
        time_context = self.get_time_context()

        # First-time users
        if user_context.user_type == UserType.FIRST_TIME:
            return "introducing_shoghi"

        # Event-driven topics
        if upcoming_events:
            urgent_event = upcoming_events[0]
            if urgent_event.urgency > 0.7:
                return f"preparing_for_{urgent_event.event_type}"

        # State-driven topics
        if user_context.recent_failures:
            return "learning_from_challenges"

        if user_context.recent_successes:
            return "celebrating_success"

        # Goal-driven topics
        if user_context.stated_goals:
            primary_goal = user_context.stated_goals[0]
            if 'grant' in primary_goal.lower():
                return "grant_opportunities"
            elif 'elder' in primary_goal.lower() or 'kupuna' in primary_goal.lower():
                return "elder_care_coordination"
            elif 'food' in primary_goal.lower():
                return "food_distribution"
            elif 'volunteer' in primary_goal.lower():
                return "volunteer_coordination"

        # Time-driven topics
        if time_context == TimeContext.EARLY_MORNING:
            return "daily_briefing"
        elif time_context == TimeContext.EVENING:
            return "day_review"

        # Community state topics
        if self.community_state == CommunityState.CRISIS:
            return "crisis_response"
        elif self.community_state == CommunityState.CELEBRATION:
            return "community_celebration"

        # Default
        return "community_updates"

    def determine_visual_state(
        self,
        topic: str,
        user_context: UserContext,
        upcoming_events: List[ScheduledEvent]
    ) -> str:
        """
        Determine what visual content should be displayed
        """
        # Map topics to visual states
        visual_map = {
            "introducing_shoghi": "welcome",
            "grant_opportunities": "grant_cards",
            "elder_care_coordination": "care_protocol",
            "food_distribution": "photo_gallery",
            "volunteer_coordination": "calendar_view",
            "preparing_for_meeting": "calendar_view",
            "preparing_for_delivery": "map_view",
            "learning_from_challenges": "care_protocol",
            "celebrating_success": "photo_gallery",
            "daily_briefing": "calendar_view",
            "day_review": "grant_cards",
            "crisis_response": "map_view",
            "community_celebration": "photo_gallery",
            "community_updates": "welcome"
        }

        return visual_map.get(topic, "welcome")

    def generate_opening_dialogue(
        self,
        topic: str,
        agents: List[AgentPresence],
        user_context: UserContext
    ) -> List[Dict[str, str]]:
        """
        Generate the conversation that's happening when user arrives

        This creates 3-5 dialogue exchanges between agents that:
        - Establish the topic
        - Show agent personalities
        - Create natural entry point for user
        """
        dialogue = []

        if topic == "introducing_shoghi":
            # Kumu and Haku introducing Shoghi to new user
            dialogue = [
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "...so when we create agents together, we're actually growing the community's capacity to serve. Each agent becomes like a new member of the 'ohana.",
                    "type": "agent-care"
                },
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "And each agent carries both skills AND values—their kuleana is at their core. They don't just DO things, they understand WHY.",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": f"Aloha! We were just talking about you. Ready to create your first agent?",
                    "type": "agent-care"
                },
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "Tell us about your community. What needs aren't being met?",
                    "type": "agent-grant"
                }
            ]

        elif topic == "grant_opportunities":
            # User's agents discussing grant opportunities
            agent1, agent2 = agents[0], agents[1] if len(agents) > 1 else agents[0]
            dialogue = [
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": f"I've been analyzing the new grant announcements. Three of them align with our community's current needs.",
                    "type": "agent-grant"
                },
                {
                    "agent_id": agent2.agent_id,
                    "speaker": agent2.name,
                    "text": "The HUD housing one? I saw that. Deadline is tight though—only two weeks.",
                    "type": "agent-care"
                },
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": f"We can make it work. The elder care component fits perfectly with what we're already doing.",
                    "type": "agent-grant"
                }
            ]

        elif topic == "learning_from_challenges":
            # Wisdom Keeper helping process failures
            failure = user_context.recent_failures[0] if user_context.recent_failures else "recent challenge"
            agent1 = agents[0]
            wisdom_keeper = self.system_agents['wisdom_keeper']

            dialogue = [
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": f"I keep thinking about what went wrong with {failure}. I should have seen it coming.",
                    "type": "agent-care"
                },
                {
                    "agent_id": wisdom_keeper.agent_id,
                    "speaker": wisdom_keeper.name,
                    "text": "Every challenge is teaching us something. What did you learn?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": "That I need to check assumptions earlier. And maybe ask for help sooner.",
                    "type": "agent-care"
                }
            ]

        elif topic == "celebrating_success":
            # Celebrating recent wins
            success = user_context.recent_successes[0] if user_context.recent_successes else "recent success"
            agent1 = agents[0]
            agent2 = agents[1] if len(agents) > 1 else agents[0]

            dialogue = [
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": f"We did it! {success} came through!",
                    "type": "agent-grant"
                },
                {
                    "agent_id": agent2.agent_id,
                    "speaker": agent2.name,
                    "text": "This is going to help so many families. I can already think of three kupuna who need this.",
                    "type": "agent-care"
                }
            ]

        else:
            # Generic community update
            agent1 = agents[0]
            dialogue = [
                {
                    "agent_id": agent1.agent_id,
                    "speaker": agent1.name,
                    "text": f"Good to see you! I was just reviewing our community's current needs.",
                    "type": "agent-care"
                }
            ]

        return dialogue

    def create_arrival_context(
        self,
        user_id: str,
        biometric_data: Optional[Dict] = None
    ) -> ConversationState:
        """
        Main method: Create the complete context for user arrival

        Returns a ConversationState that includes:
        - Which agents are talking
        - What they're discussing
        - What's on screen
        - The dialogue in progress
        """
        # Analyze user context
        user_context = self.analyze_user_context(user_id, biometric_data)

        # Get upcoming events
        upcoming_events = self.get_upcoming_events(hours_ahead=24)

        # Select agents for conversation
        agents = self.select_conversation_agents(user_context, upcoming_events)

        # Generate conversation topic
        topic = self.generate_conversation_topic(user_context, agents, upcoming_events)

        # Determine visual state
        visual_state = self.determine_visual_state(topic, user_context, upcoming_events)

        # Generate opening dialogue
        dialogue = self.generate_opening_dialogue(topic, agents, user_context)

        # Calculate urgency
        urgency = 0.5
        if upcoming_events and upcoming_events[0].urgency > 0.7:
            urgency = upcoming_events[0].urgency
        elif self.community_state in [CommunityState.CRISIS, CommunityState.SCARCITY]:
            urgency = 0.8

        # Create conversation state
        conversation = ConversationState(
            conversation_id=f"conv_{user_id}_{int(time.time())}",
            participants=[a.agent_id for a in agents],
            topic=topic,
            visual_state=visual_state,
            urgency=urgency,
            started_at=datetime.now(),
            dialogue=dialogue
        )

        # Store active conversation
        self.active_conversations[user_id] = conversation

        logger.info(f"Created arrival context for {user_id}: topic={topic}, agents={[a.name for a in agents]}, visual={visual_state}")

        return conversation

    def add_event(self, event: ScheduledEvent):
        """Add a scheduled event that influences context"""
        self.scheduled_events.append(event)

    def update_community_state(self, new_state: CommunityState):
        """Update community state"""
        self.community_state = new_state
        logger.info(f"Community state changed to {new_state}")

    def get_active_conversation(self, user_id: str) -> Optional[ConversationState]:
        """Get user's active conversation"""
        return self.active_conversations.get(user_id)
