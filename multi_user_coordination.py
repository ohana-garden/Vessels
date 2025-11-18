"""
Multi-User/Multi-Agent Coordination
===================================

Multiple humans can join the same conversation and watch their agents
coordinate with each other.

Use Cases:
1. Community meeting - Multiple people, their agents discuss together
2. Collaborative planning - Agents coordinate while humans observe
3. Teaching moments - Humans learn by watching agent collaboration
4. Decision making - Agents present options, humans discuss
5. Celebration - Community shares success, agents report

Key Principles:
- Humans can join/leave conversations
- Each human has their own agents
- Agents know who they serve
- Conversation visible to all participants
- Humans can interject anytime
- Agents can address specific humans or each other
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class ParticipantRole(Enum):
    """Role in multi-user session"""
    HOST = "host"  # Started the session
    PARTICIPANT = "participant"  # Invited participant
    OBSERVER = "observer"  # Watching only
    AGENT = "agent"  # AI agent


class SessionType(Enum):
    """Type of multi-user session"""
    COMMUNITY_MEETING = "community_meeting"
    COLLABORATIVE_PLANNING = "collaborative_planning"
    TEACHING_SESSION = "teaching_session"
    DECISION_MAKING = "decision_making"
    CELEBRATION = "celebration"
    COORDINATION = "coordination"
    EMERGENCY_RESPONSE = "emergency_response"


@dataclass
class Participant:
    """A participant in multi-user session"""
    participant_id: str
    participant_type: str  # "human" or "agent"
    name: str
    role: ParticipantRole
    owned_agents: List[str] = field(default_factory=list)  # If human, their agents
    serves: Optional[str] = None  # If agent, who they serve
    joined_at: datetime = field(default_factory=datetime.now)
    active: bool = True
    last_spoke: Optional[datetime] = None


@dataclass
class MultiUserSession:
    """A session with multiple humans and their agents"""
    session_id: str
    session_type: SessionType
    title: str
    host_id: str
    participants: Dict[str, Participant] = field(default_factory=dict)
    conversation_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    active: bool = True

    def add_participant(self, participant: Participant):
        """Add participant to session"""
        self.participants[participant.participant_id] = participant
        logger.info(f"Added {participant.name} to session {self.session_id}")

    def remove_participant(self, participant_id: str):
        """Remove participant from session"""
        if participant_id in self.participants:
            self.participants[participant_id].active = False
            logger.info(f"Removed {participant_id} from session {self.session_id}")

    def get_humans(self) -> List[Participant]:
        """Get all human participants"""
        return [
            p for p in self.participants.values()
            if p.participant_type == "human" and p.active
        ]

    def get_agents(self) -> List[Participant]:
        """Get all agent participants"""
        return [
            p for p in self.participants.values()
            if p.participant_type == "agent" and p.active
        ]

    def get_agents_for_human(self, human_id: str) -> List[Participant]:
        """Get all agents belonging to a human"""
        human = self.participants.get(human_id)
        if not human or human.participant_type != "human":
            return []

        return [
            p for p in self.participants.values()
            if p.participant_type == "agent" and p.serves == human_id and p.active
        ]


class MultiUserCoordinator:
    """
    Coordinates multi-user sessions

    Manages:
    - Session creation and lifecycle
    - Participant joining/leaving
    - Agent-to-agent coordination while humans watch
    - Human interjections
    - Fair speaking distribution
    - Context for all participants
    """

    def __init__(
        self,
        conversation_orchestrator,
        choreography_engine,
        agent_registry,
        context_engine
    ):
        self.conversation_orchestrator = conversation_orchestrator
        self.choreography_engine = choreography_engine
        self.agent_registry = agent_registry
        self.context_engine = context_engine
        self.active_sessions: Dict[str, MultiUserSession] = {}

    async def create_session(
        self,
        host_id: str,
        session_type: SessionType,
        title: str,
        initial_participants: List[str] = None
    ) -> MultiUserSession:
        """
        Create a new multi-user session

        Args:
            host_id: Human who hosts the session
            session_type: Type of session
            title: Session title/topic
            initial_participants: Initial participant IDs to invite
        """
        session_id = f"session_{int(datetime.now().timestamp())}"

        session = MultiUserSession(
            session_id=session_id,
            session_type=session_type,
            title=title,
            host_id=host_id
        )

        # Add host
        host_participant = Participant(
            participant_id=host_id,
            participant_type="human",
            name=await self.get_participant_name(host_id),
            role=ParticipantRole.HOST
        )
        session.add_participant(host_participant)

        # Add host's agents
        host_agents = await self.get_user_agents(host_id)
        for agent_id in host_agents:
            agent_data = self.agent_registry.get_agent(agent_id)
            if agent_data:
                agent_participant = Participant(
                    participant_id=agent_id,
                    participant_type="agent",
                    name=agent_data.get('name', agent_id),
                    role=ParticipantRole.AGENT,
                    serves=host_id
                )
                session.add_participant(agent_participant)
                host_participant.owned_agents.append(agent_id)

        # Invite initial participants
        if initial_participants:
            for participant_id in initial_participants:
                await self.invite_participant(session_id, participant_id, host_id)

        # Create conversation for session
        all_participants = [p.participant_id for p in session.participants.values()]
        conversation = self.conversation_orchestrator.start_conversation(
            conversation_id=f"conv_{session_id}",
            participants=all_participants,
            mode=self.get_conversation_mode(session_type),
            topic=title
        )
        session.conversation_id = conversation.conversation_id

        self.active_sessions[session_id] = session

        logger.info(f"Created multi-user session: {title} ({session_type.value})")

        return session

    async def invite_participant(
        self,
        session_id: str,
        participant_id: str,
        invited_by: str
    ):
        """
        Invite a participant to join session

        Participant brings their agents with them
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Add participant
        participant = Participant(
            participant_id=participant_id,
            participant_type="human",
            name=await self.get_participant_name(participant_id),
            role=ParticipantRole.PARTICIPANT
        )
        session.add_participant(participant)

        # Add their agents
        participant_agents = await self.get_user_agents(participant_id)
        for agent_id in participant_agents:
            agent_data = self.agent_registry.get_agent(agent_id)
            if agent_data:
                agent_participant = Participant(
                    participant_id=agent_id,
                    participant_type="agent",
                    name=agent_data.get('name', agent_id),
                    role=ParticipantRole.AGENT,
                    serves=participant_id
                )
                session.add_participant(agent_participant)
                participant.owned_agents.append(agent_id)

        # Update conversation participants
        if session.conversation_id:
            conversation = self.conversation_orchestrator.get_conversation(session.conversation_id)
            if conversation:
                conversation.participants.extend([participant_id] + participant_agents)

        # Announce arrival
        await self.announce_participant_arrival(session, participant)

        logger.info(f"{participant.name} joined session {session_id}")

    async def announce_participant_arrival(
        self,
        session: MultiUserSession,
        participant: Participant
    ):
        """Announce when someone joins the session"""
        # Get one of the host's agents to welcome
        host_agents = session.get_agents_for_human(session.host_id)
        if host_agents:
            welcomer = host_agents[0]

            from conversation_orchestrator import ConversationalTurn, TurnType

            welcome_turn = ConversationalTurn(
                speaker_id=welcomer.participant_id,
                speaker_name=welcomer.name,
                speaker_type="agent",
                text=f"Aloha {participant.name}! Welcome to our {session.session_type.value.replace('_', ' ')}. We're discussing {session.title}.",
                turn_type=TurnType.STATEMENT
            )

            conversation = self.conversation_orchestrator.get_conversation(session.conversation_id)
            if conversation:
                conversation.add_turn(welcome_turn)

    async def run_agent_coordination(
        self,
        session_id: str,
        task: str,
        duration_minutes: int = 5
    ) -> List[Any]:
        """
        Run agent-to-agent coordination while humans watch

        Agents discuss and coordinate on a task while humans observe
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        agents = session.get_agents()
        if len(agents) < 2:
            logger.warning(f"Session {session_id} needs at least 2 agents for coordination")
            return []

        logger.info(f"Starting agent coordination in session {session_id}: {task}")

        # Create coordination scene
        scene = self.choreography_engine.create_multi_agent_coordination_scene(
            agents=[a.participant_id for a in agents],
            topic=task,
            visual_state="coordination_view",
            urgency=0.7
        )

        # Run agent dialogue
        turns = []
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        while datetime.now() < end_time:
            # Let agents coordinate
            new_turns = await self.conversation_orchestrator.run_agent_dialogue(
                session.conversation_id,
                num_turns=2
            )
            turns.extend(new_turns)

            # Short pause between exchanges
            await asyncio.sleep(2)

        logger.info(f"Agent coordination complete: {len(turns)} turns")

        return turns

    async def human_interjects(
        self,
        session_id: str,
        human_id: str,
        interjection: str
    ) -> List[Any]:
        """
        Human interjects in conversation

        Agents respond to human input
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        participant = session.participants.get(human_id)
        if not participant or participant.participant_type != "human":
            raise ValueError(f"Invalid human participant {human_id}")

        logger.info(f"{participant.name} interjects in session {session_id}")

        # Process through conversation orchestrator
        turns = await self.conversation_orchestrator.process_user_input(
            conversation_id=session.conversation_id,
            user_id=human_id,
            user_input=interjection
        )

        participant.last_spoke = datetime.now()

        return turns

    def get_session_state(self, session_id: str) -> Dict[str, Any]:
        """Get complete state of a session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        conversation = self.conversation_orchestrator.get_conversation(session.conversation_id)

        return {
            "session_id": session.session_id,
            "title": session.title,
            "type": session.session_type.value,
            "started_at": session.started_at.isoformat(),
            "active": session.active,
            "participants": {
                "humans": [
                    {
                        "id": p.participant_id,
                        "name": p.name,
                        "role": p.role.value,
                        "agents": len(p.owned_agents)
                    }
                    for p in session.get_humans()
                ],
                "agents": [
                    {
                        "id": p.participant_id,
                        "name": p.name,
                        "serves": p.serves
                    }
                    for p in session.get_agents()
                ]
            },
            "conversation": {
                "turn_count": len(conversation.turns) if conversation else 0,
                "recent_turns": [
                    t.to_subtitle() for t in conversation.get_recent_turns(5)
                ] if conversation else []
            }
        }

    async def end_session(self, session_id: str):
        """End a multi-user session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        session.active = False
        session.ended_at = datetime.now()

        # End conversation
        if session.conversation_id:
            self.conversation_orchestrator.end_conversation(session.conversation_id)

        logger.info(f"Ended session {session_id}: {session.title}")

    # Helper methods

    async def get_participant_name(self, participant_id: str) -> str:
        """Get name for participant"""
        # In production, would query user database
        return f"User_{participant_id[-8:]}"

    async def get_user_agents(self, user_id: str) -> List[str]:
        """Get list of agent IDs for a user"""
        # Query agent registry for agents created by this user
        all_agents = self.agent_registry.list_agents()
        user_agents = [
            agent['agent_id']
            for agent in all_agents
            if agent.get('created_by') == user_id
        ]
        return user_agents

    def get_conversation_mode(self, session_type: SessionType):
        """Map session type to conversation mode"""
        from conversation_orchestrator import ConversationMode

        mapping = {
            SessionType.COMMUNITY_MEETING: ConversationMode.COORDINATION,
            SessionType.COLLABORATIVE_PLANNING: ConversationMode.COORDINATION,
            SessionType.TEACHING_SESSION: ConversationMode.TEACHING,
            SessionType.DECISION_MAKING: ConversationMode.DISCOVERY,
            SessionType.CELEBRATION: ConversationMode.CELEBRATION,
            SessionType.COORDINATION: ConversationMode.COORDINATION,
            SessionType.EMERGENCY_RESPONSE: ConversationMode.COORDINATION
        }

        return mapping.get(session_type, ConversationMode.COORDINATION)


from datetime import timedelta
