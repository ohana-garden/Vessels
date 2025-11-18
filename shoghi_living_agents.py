"""
Shoghi Living Agents - Integration Module
=========================================

This module ties together all the ethical agents framework components
into a cohesive, easy-to-use system.

Usage:
    from shoghi_living_agents import ShoghiLivingAgents

    # Initialize
    shoghi = ShoghiLivingAgents()

    # User arrives
    arrival_context = await shoghi.user_arrives(user_id="user123")

    # User creates an agent
    creation = shoghi.start_agent_creation(user_id="user123")

    # Process user input during creation
    result = await shoghi.process_creation_input(
        creation_id=creation.creation_id,
        user_input="We need help with elder care"
    )

    # Multi-user session
    session = await shoghi.create_multi_user_session(
        host_id="user123",
        title="Community Planning",
        session_type="coordination"
    )
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

# Import all framework components
from context_engine import (
    ContextEngine,
    UserContext,
    ConversationState,
    ScheduledEvent,
    CommunityState
)
from conversational_agent_creation import (
    ConversationalAgentCreator,
    CreationConversation,
    CreationPhase
)
from rich_agent_identity import RichAgentIdentity
from choreography_engine import (
    ChoreographyEngine,
    Scene,
    Shot,
    Pace,
    EmotionalBeat
)
from conversation_orchestrator import (
    ConversationOrchestrator,
    Conversation,
    ConversationMode,
    ConversationalTurn
)
from agent_evolution import (
    AgentEvolutionEngine,
    AgentReproductionEngine,
    EvolutionTrigger,
    ReproductionReason
)
from multi_user_coordination import (
    MultiUserCoordinator,
    MultiUserSession,
    SessionType,
    Participant
)

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Simple agent registry for demo purposes
    In production, this would be backed by database
    """

    def __init__(self):
        self.agents: Dict[str, Any] = {}

    def register_agent(self, agent_data: Dict[str, Any]):
        """Register a new agent"""
        agent_id = agent_data.get('agent_id')
        if agent_id:
            self.agents[agent_id] = agent_data
            logger.info(f"Registered agent: {agent_data.get('name', agent_id)}")

    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents"""
        return list(self.agents.values())

    def get_agents_by_creator(self, user_id: str) -> List[Dict[str, Any]]:
        """Get agents created by a user"""
        return [
            agent for agent in self.agents.values()
            if agent.get('created_by') == user_id
        ]


class SimpleCommunityMemory:
    """
    Simple community memory for demo purposes
    In production, this would integrate with full community_memory.py
    """

    def __init__(self):
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
        self.events: List[Any] = []

    def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Get user context"""
        return self.user_contexts.get(user_id, {})

    def update_user_context(self, user_id: str, updates: Dict[str, Any]):
        """Update user context"""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {}
        self.user_contexts[user_id].update(updates)

    def store_agent_birth(self, agent_data: Dict[str, Any]):
        """Store agent birth event"""
        self.events.append({
            'type': 'agent_birth',
            'data': agent_data,
            'timestamp': datetime.now()
        })

    def store_evolution_event(self, event: Any):
        """Store evolution event"""
        self.events.append({
            'type': 'evolution',
            'data': event,
            'timestamp': datetime.now()
        })

    def store_reproduction_event(self, event: Any):
        """Store reproduction event"""
        self.events.append({
            'type': 'reproduction',
            'data': event,
            'timestamp': datetime.now()
        })


class ShoghiLivingAgents:
    """
    Main integration class for Shoghi Living Agents framework

    This provides a unified API for:
    - User arrivals with contextual greetings
    - Conversational agent creation
    - Agent evolution and reproduction
    - Multi-agent conversations
    - Multi-user coordination
    - Cinematic choreography
    """

    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        community_memory: Optional[SimpleCommunityMemory] = None
    ):
        # Initialize registries
        self.agent_registry = agent_registry or AgentRegistry()
        self.community_memory = community_memory or SimpleCommunityMemory()

        # Initialize core engines
        self.context_engine = ContextEngine(
            self.community_memory,
            self.agent_registry
        )

        self.choreography_engine = ChoreographyEngine()

        self.conversation_orchestrator = ConversationOrchestrator(
            self.agent_registry,
            llm_client=None  # TODO: Add LLM client
        )

        self.conversational_creator = ConversationalAgentCreator(
            self.context_engine,
            self.agent_registry,
            self.community_memory
        )

        self.evolution_engine = AgentEvolutionEngine(
            self.agent_registry,
            self.community_memory
        )

        self.reproduction_engine = AgentReproductionEngine(
            self.agent_registry,
            self.community_memory,
            self.conversational_creator
        )

        self.multi_user_coordinator = MultiUserCoordinator(
            self.conversation_orchestrator,
            self.choreography_engine,
            self.agent_registry,
            self.context_engine
        )

        # Agent identity cache
        self.agent_identities: Dict[str, RichAgentIdentity] = {}

        logger.info("Shoghi Living Agents initialized")

    # ==================== User Arrivals ====================

    async def user_arrives(
        self,
        user_id: str,
        biometric_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Handle user arrival with biometric recognition

        Returns complete context including:
        - Conversation already in progress
        - Agents involved
        - Visual state
        - Dialogue to display
        - Choreographed scene
        """
        logger.info(f"User arrives: {user_id}")

        # Create arrival context
        conversation_state = self.context_engine.create_arrival_context(
            user_id,
            biometric_data
        )

        # Get user context for pacing
        user_context = self.context_engine.analyze_user_context(user_id, biometric_data)

        # Create cinematic scene
        scene = self.choreography_engine.create_arrival_scene(
            conversation_state,
            user_context
        )

        return {
            'conversation_state': conversation_state,
            'user_context': user_context,
            'scene': scene,
            'visual_state': conversation_state.visual_state,
            'dialogue': conversation_state.dialogue
        }

    # ==================== Agent Creation ====================

    def start_agent_creation(
        self,
        user_id: str,
        facilitators: Optional[List[str]] = None
    ) -> CreationConversation:
        """
        Start conversational agent creation

        Returns creation conversation with opening dialogue
        """
        logger.info(f"Starting agent creation for {user_id}")

        creation = self.conversational_creator.start_creation(
            user_id,
            facilitators
        )

        return creation

    async def process_creation_input(
        self,
        creation_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Process user input during agent creation

        Returns:
        - Facilitator responses
        - Updated identity
        - Visual state changes
        - Whether agent was born
        """
        logger.info(f"Processing creation input for {creation_id}")

        result = self.conversational_creator.process_user_input(
            creation_id,
            user_input
        )

        # If agent was born, create rich identity and register
        if result.get('agent_born'):
            agent_data = result['agent_born']['agent_data']
            rich_identity = self.create_rich_identity_from_data(agent_data)
            self.agent_identities[agent_data['agent_id']] = rich_identity

        return result

    def create_rich_identity_from_data(self, agent_data: Dict[str, Any]) -> RichAgentIdentity:
        """Create RichAgentIdentity from agent data"""
        identity = RichAgentIdentity(
            agent_id=agent_data['agent_id'],
            name=agent_data['name'],
            kuleana=agent_data['kuleana'],
            persona=agent_data['persona'],
            created_by=agent_data['created_by'],
            generation=agent_data.get('generation', 0)
        )

        # Add skills
        for skill in agent_data.get('skills', []):
            identity.add_skill(skill, proficiency=0.5)

        # Add knowledge
        for domain in agent_data.get('knowledge_domains', []):
            identity.add_knowledge_domain(domain, expertise_level=0.4)

        # Add lore
        for lore_text in agent_data.get('lore', []):
            identity.add_lore(lore_text, source='creation')

        # Add values
        identity.values = agent_data.get('values', [])

        # Add ethics
        for constraint in agent_data.get('ethical_constraints', []):
            identity.add_ethical_constraint(
                constraint.get('description', ''),
                constraint.get('constraint_type', 'should_do'),
                constraint.get('strength', 0.8)
            )

        identity.red_lines = agent_data.get('red_lines', [])

        return identity

    # ==================== Agent Conversations ====================

    async def start_conversation(
        self,
        user_id: str,
        agent_ids: List[str],
        topic: str,
        mode: str = "teaching"
    ) -> Conversation:
        """Start a conversation with specific agents"""
        from conversation_orchestrator import ConversationMode

        mode_map = {
            "teaching": ConversationMode.TEACHING,
            "discovery": ConversationMode.DISCOVERY,
            "coordination": ConversationMode.COORDINATION,
            "celebration": ConversationMode.CELEBRATION,
            "reflection": ConversationMode.REFLECTION,
            "creation": ConversationMode.CREATION
        }

        conversation_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
        participants = [user_id] + agent_ids

        conversation = self.conversation_orchestrator.start_conversation(
            conversation_id=conversation_id,
            participants=participants,
            mode=mode_map.get(mode, ConversationMode.TEACHING),
            topic=topic
        )

        return conversation

    async def process_user_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str
    ) -> List[ConversationalTurn]:
        """Process user message in conversation"""
        return await self.conversation_orchestrator.process_user_input(
            conversation_id,
            user_id,
            message
        )

    # ==================== Agent Evolution ====================

    async def check_and_evolve_agents(self) -> List[Any]:
        """
        Check all agents for evolution triggers and evolve if needed

        This should be called periodically (e.g., every hour)
        """
        evolved_agents = []

        for agent_id, identity in self.agent_identities.items():
            # Check triggers
            triggers = self.evolution_engine.check_evolution_triggers(identity)

            # Evolve if triggers fired
            for trigger in triggers:
                event = await self.evolution_engine.evolve_agent(identity, trigger)
                evolved_agents.append({
                    'agent_id': agent_id,
                    'agent_name': identity.name,
                    'event': event
                })

        return evolved_agents

    # ==================== Agent Reproduction ====================

    async def check_reproduction_needs(self) -> List[Any]:
        """
        Check all agents for reproduction needs

        Returns list of agents that should reproduce
        """
        reproduction_needs = []

        for agent_id, identity in self.agent_identities.items():
            need = self.reproduction_engine.check_reproduction_need(identity)
            if need:
                reason, context = need
                reproduction_needs.append({
                    'agent_id': agent_id,
                    'agent_name': identity.name,
                    'reason': reason,
                    'context': context
                })

        return reproduction_needs

    async def reproduce_agent(
        self,
        parent_agent_id: str,
        reason: str,
        specialization: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reproduce an agent"""
        parent_identity = self.agent_identities.get(parent_agent_id)
        if not parent_identity:
            raise ValueError(f"Agent {parent_agent_id} not found")

        # Map reason string to enum
        reason_map = {
            'specialization': ReproductionReason.SPECIALIZATION,
            'delegation': ReproductionReason.DELEGATION,
            'discovery': ReproductionReason.DISCOVERY,
            'collaboration': ReproductionReason.COLLABORATION,
            'succession': ReproductionReason.SUCCESSION,
            'innovation': ReproductionReason.INNOVATION
        }

        reason_enum = reason_map.get(reason, ReproductionReason.SPECIALIZATION)

        # Reproduce
        result = await self.reproduction_engine.reproduce_agent(
            parent_identity,
            reason_enum,
            specialization
        )

        # Store child identity
        child_identity = result['child_identity']
        self.agent_identities[child_identity.agent_id] = child_identity

        return result

    # ==================== Multi-User Sessions ====================

    async def create_multi_user_session(
        self,
        host_id: str,
        title: str,
        session_type: str,
        invitees: Optional[List[str]] = None
    ) -> MultiUserSession:
        """Create a multi-user session"""
        # Map session type string to enum
        type_map = {
            'community_meeting': SessionType.COMMUNITY_MEETING,
            'collaborative_planning': SessionType.COLLABORATIVE_PLANNING,
            'teaching_session': SessionType.TEACHING_SESSION,
            'decision_making': SessionType.DECISION_MAKING,
            'celebration': SessionType.CELEBRATION,
            'coordination': SessionType.COORDINATION,
            'emergency_response': SessionType.EMERGENCY_RESPONSE
        }

        session_type_enum = type_map.get(session_type, SessionType.COORDINATION)

        session = await self.multi_user_coordinator.create_session(
            host_id,
            session_type_enum,
            title,
            invitees
        )

        return session

    async def invite_to_session(
        self,
        session_id: str,
        participant_id: str,
        invited_by: str
    ):
        """Invite participant to session"""
        await self.multi_user_coordinator.invite_participant(
            session_id,
            participant_id,
            invited_by
        )

    async def run_agent_coordination(
        self,
        session_id: str,
        task: str,
        duration_minutes: int = 5
    ) -> List[Any]:
        """Run agent-to-agent coordination in session"""
        return await self.multi_user_coordinator.run_agent_coordination(
            session_id,
            task,
            duration_minutes
        )

    # ==================== Utility Methods ====================

    def get_agent_identity(self, agent_id: str) -> Optional[RichAgentIdentity]:
        """Get rich agent identity"""
        return self.agent_identities.get(agent_id)

    def get_user_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all agents created by user"""
        return self.agent_registry.get_agents_by_creator(user_id)

    def get_active_conversations(self) -> List[Conversation]:
        """Get all active conversations"""
        return [
            conv for conv in self.conversation_orchestrator.active_conversations.values()
            if conv.active
        ]

    def get_active_sessions(self) -> List[MultiUserSession]:
        """Get all active multi-user sessions"""
        return [
            session for session in self.multi_user_coordinator.active_sessions.values()
            if session.active
        ]

    # ==================== Event Scheduling ====================

    def add_scheduled_event(
        self,
        event_type: str,
        title: str,
        time: datetime,
        participants: List[str],
        related_agents: List[str],
        urgency: float = 0.5
    ):
        """Add a scheduled event that affects context"""
        event = ScheduledEvent(
            event_id=f"event_{int(datetime.now().timestamp())}",
            event_type=event_type,
            title=title,
            time=time,
            participants=participants,
            related_agents=related_agents,
            urgency=urgency
        )

        self.context_engine.add_event(event)

    def update_community_state(self, state: str):
        """Update community state"""
        state_map = {
            'normal': CommunityState.NORMAL,
            'crisis': CommunityState.CRISIS,
            'celebration': CommunityState.CELEBRATION,
            'planning': CommunityState.PLANNING,
            'recovery': CommunityState.RECOVERY,
            'abundance': CommunityState.ABUNDANCE,
            'scarcity': CommunityState.SCARCITY
        }

        state_enum = state_map.get(state, CommunityState.NORMAL)
        self.context_engine.update_community_state(state_enum)


# ==================== Example Usage ====================

async def example_usage():
    """
    Example of using the Shoghi Living Agents framework
    """
    # Initialize
    shoghi = ShoghiLivingAgents()

    # Scenario 1: New user arrives
    print("\n=== User Arrival ===")
    arrival = await shoghi.user_arrives(user_id="user_123")
    print(f"Topic: {arrival['conversation_state'].topic}")
    print(f"Visual: {arrival['conversation_state'].visual_state}")
    print(f"Agents: {arrival['conversation_state'].participants}")

    for dialogue in arrival['conversation_state'].dialogue:
        print(f"[{dialogue['speaker']}]: {dialogue['text']}")

    # Scenario 2: User creates an agent
    print("\n=== Agent Creation ===")
    creation = shoghi.start_agent_creation(user_id="user_123")

    # Simulate creation conversation
    inputs = [
        "We need help caring for our elders",
        "Call them Tutu Care",
        "They should be warm and patient like a grandmother",
        "They need to make phone calls and detect problems",
        "Elder care protocols and Hawaiian customs",
        "My tutu always said 'Nana i ke kumu' - look to the source",
        "Never lie to an elder. Never make them feel like a burden.",
        "They'll work with family members"
    ]

    for user_input in inputs:
        result = await shoghi.process_creation_input(creation.creation_id, user_input)
        print(f"\nUser: {user_input}")
        if result.get('facilitator_responses'):
            for response in result['facilitator_responses']:
                print(f"[{response['speaker']}]: {response['text']}")

        if result.get('agent_born'):
            print(f"\n🎉 Agent Born: {result['agent_born']['agent_data']['name']}")
            break

    # Scenario 3: Multi-user session
    print("\n=== Multi-User Session ===")
    session = await shoghi.create_multi_user_session(
        host_id="user_123",
        title="Community Food Distribution Planning",
        session_type="coordination",
        invitees=["user_456", "user_789"]
    )

    print(f"Session created: {session.title}")
    print(f"Participants: {len(session.participants)}")

    # Run agent coordination
    print("\n=== Agent Coordination ===")
    await shoghi.run_agent_coordination(
        session.session_id,
        task="Optimize food delivery routes for this week",
        duration_minutes=1  # Short demo
    )


if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
