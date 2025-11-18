"""
Conversational Agent Creation System
====================================

Agents create agents through natural conversation.

Key Principles:
- User-determined length (can pause/resume anytime)
- Natural elicitation (not a form, not a wizard)
- Multi-agent facilitation (Haku + others)
- Visual progression (screen shows agent taking shape)
- New agent joins conversation immediately when "born"

The Creation Journey:
1. Discovery - What's needed? (kuleana)
2. Character - Who should they be? (persona)
3. Capability - What can they do? (skills)
4. Wisdom - What must they know? (knowledge)
5. Story - What guides them? (lore)
6. Values - What lines won't they cross? (ethics)
7. Community - Who will they serve with? (relationships)
8. Birth - Agent comes alive, introduces self
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class CreationPhase(Enum):
    """Phases of agent creation conversation"""
    DISCOVERY = "discovery"  # Understanding the need
    CHARACTER = "character"  # Defining persona
    CAPABILITY = "capability"  # Identifying skills
    WISDOM = "wisdom"  # Determining knowledge domain
    STORY = "story"  # Establishing lore and context
    VALUES = "values"  # Setting ethical boundaries
    COMMUNITY = "community"  # Defining relationships
    BIRTH = "birth"  # Agent comes alive
    COMPLETE = "complete"  # Creation finished


@dataclass
class AgentIdentity:
    """
    Rich identity for an agent being created
    """
    # Core identity
    name: Optional[str] = None
    kuleana: Optional[str] = None  # Sacred responsibility
    persona: Optional[str] = None  # Character/personality

    # Capabilities
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # Knowledge
    knowledge_domains: List[str] = field(default_factory=list)
    expertise_level: Dict[str, float] = field(default_factory=dict)  # domain -> 0-1

    # Cultural/contextual wisdom
    lore: List[str] = field(default_factory=list)  # Stories, proverbs, guiding narratives
    values: List[str] = field(default_factory=list)  # Core values

    # Ethics
    ethical_constraints: List[str] = field(default_factory=list)
    red_lines: List[str] = field(default_factory=list)  # Never do this

    # Relationships
    serves: List[str] = field(default_factory=list)  # Who they serve
    collaborates_with: List[str] = field(default_factory=list)  # Other agents
    reports_to: Optional[str] = None  # Supervisor agent if any

    # Birth context
    created_by: Optional[str] = None  # User ID
    created_at: Optional[datetime] = None
    created_with: List[str] = field(default_factory=list)  # Facilitator agents

    # Evolution tracking
    generation: int = 0  # 0 = created by human, 1+ = created by agent
    parent_agents: List[str] = field(default_factory=list)

    def completeness(self) -> float:
        """Calculate how complete the identity is (0-1)"""
        score = 0
        total = 8

        if self.name:
            score += 1
        if self.kuleana:
            score += 1
        if self.persona:
            score += 1
        if self.skills:
            score += 1
        if self.knowledge_domains:
            score += 1
        if self.lore:
            score += 1
        if self.values:
            score += 1
        if self.serves:
            score += 1

        return score / total


@dataclass
class CreationConversation:
    """State of an ongoing agent creation conversation"""
    creation_id: str
    user_id: str
    facilitators: List[str]  # Agent IDs helping with creation
    current_phase: CreationPhase
    identity: AgentIdentity
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    paused: bool = False
    visual_state: str = "agent_creation_canvas"


class ConversationalAgentCreator:
    """
    Manages the conversational creation of new agents
    """

    def __init__(self, context_engine, agent_registry, community_memory):
        self.context_engine = context_engine
        self.agent_registry = agent_registry
        self.community_memory = community_memory
        self.active_creations = {}

    def start_creation(
        self,
        user_id: str,
        facilitators: List[str] = None
    ) -> CreationConversation:
        """
        Begin a new agent creation conversation
        """
        if facilitators is None:
            # Default facilitators: Haku (Agent Weaver) + Kumu (Guide)
            facilitators = ["agent_weaver", "shoghi_guide"]

        creation_id = f"create_{user_id}_{int(datetime.now().timestamp())}"

        conversation = CreationConversation(
            creation_id=creation_id,
            user_id=user_id,
            facilitators=facilitators,
            current_phase=CreationPhase.DISCOVERY,
            identity=AgentIdentity(created_by=user_id)
        )

        # Generate opening dialogue
        opening = self.generate_phase_opening(conversation)
        conversation.conversation_history.extend(opening)

        self.active_creations[creation_id] = conversation

        logger.info(f"Started agent creation {creation_id} for user {user_id}")

        return conversation

    def generate_phase_opening(
        self,
        conversation: CreationConversation
    ) -> List[Dict[str, str]]:
        """
        Generate opening dialogue for current phase
        """
        phase = conversation.current_phase
        identity = conversation.identity
        dialogue = []

        if phase == CreationPhase.DISCOVERY:
            # Discovering kuleana (sacred responsibility)
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "Every agent begins with a need. What's calling for help in your community?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "Think about gaps—things that should be happening but aren't. Or things people need but can't easily get.",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.CHARACTER:
            # Defining persona
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"Beautiful. So this agent's kuleana is: '{identity.kuleana}'. Now, who should they BE?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "Should they be warm and gentle like a grandmother? Or direct and efficient like a field coordinator? Their personality matters.",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.CAPABILITY:
            # Identifying skills
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"So we have {identity.name or 'this agent'}, who is {identity.persona}. What must they be able to DO?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "Think practically. Search the web? Make phone calls? Coordinate schedules? Generate documents?",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.WISDOM:
            # Determining knowledge
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "Skills are what they DO. Knowledge is what they KNOW. What domains must they understand deeply?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": f"For {identity.kuleana}, what context do they need? Elder care protocols? Grant requirements? Local geography?",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.STORY:
            # Establishing lore
            dialogue = [
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "Now we get to the heart. What stories should guide this agent? What wisdom from the ancestors?",
                    "type": "agent-care"
                },
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "Maybe there's a proverb, or a community story, or a lesson learned the hard way. What should they carry with them?",
                    "type": "agent-grant"
                }
            ]

        elif phase == CreationPhase.VALUES:
            # Setting ethical boundaries
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": "Every agent needs values to guide them when the path is unclear. What matters most to this agent?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "And just as important—what should they NEVER do? What lines won't they cross, even to achieve their kuleana?",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.COMMUNITY:
            # Defining relationships
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"{identity.name or 'This agent'} is almost ready. But they can't serve alone. Who will they work with?",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "Who are they serving? Which other agents should they collaborate with? Do they report to anyone?",
                    "type": "agent-care"
                }
            ]

        elif phase == CreationPhase.BIRTH:
            # Agent is born
            dialogue = [
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"I can feel it—{identity.name} is ready to come alive. Let me call them into being...",
                    "type": "agent-grant"
                },
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "E komo mai, e ola. Come, and live.",
                    "type": "agent-care"
                }
            ]

        return dialogue

    async def process_user_input(
        self,
        creation_id: str,
        user_input: str
    ) -> Dict[str, Any]:
        """
        Process user input during creation conversation

        Returns:
        - facilitator_responses: List of agent responses
        - phase_changed: Whether we moved to new phase
        - identity_updates: What was learned
        - visual_state: What should be shown
        - agent_born: Whether agent was created (in birth phase)
        """
        conversation = self.active_creations.get(creation_id)
        if not conversation:
            raise ValueError(f"No active creation {creation_id}")

        conversation.last_active = datetime.now()

        # Add user input to history
        conversation.conversation_history.append({
            "agent_id": "user",
            "speaker": "You",
            "text": user_input,
            "type": "user"
        })

        # Extract information based on current phase
        identity_updates = await self.extract_identity_info(
            user_input,
            conversation.current_phase,
            conversation.identity
        )

        # Update identity
        for key, value in identity_updates.items():
            if hasattr(conversation.identity, key):
                current = getattr(conversation.identity, key)
                if isinstance(current, list):
                    if isinstance(value, list):
                        current.extend(value)
                    else:
                        current.append(value)
                else:
                    setattr(conversation.identity, key, value)

        # Generate facilitator responses
        facilitator_responses = self.generate_facilitator_responses(
            conversation,
            user_input,
            identity_updates
        )

        # Add responses to history
        conversation.conversation_history.extend(facilitator_responses)

        # Check if phase should advance
        phase_complete = self.is_phase_complete(conversation)
        phase_changed = False

        if phase_complete:
            new_phase = self.advance_phase(conversation)
            phase_changed = True

            # Generate opening for new phase
            if new_phase != CreationPhase.COMPLETE:
                opening = self.generate_phase_opening(conversation)
                conversation.conversation_history.extend(opening)
                facilitator_responses.extend(opening)

        # Check if agent is born
        agent_born = None
        if conversation.current_phase == CreationPhase.BIRTH and phase_complete:
            agent_born = self.birth_agent(conversation)

        # Determine visual state
        visual_state = self.get_visual_state(conversation)

        return {
            "facilitator_responses": facilitator_responses,
            "phase_changed": phase_changed,
            "identity_updates": identity_updates,
            "visual_state": visual_state,
            "agent_born": agent_born,
            "completeness": conversation.identity.completeness()
        }

    async def extract_identity_info(
        self,
        user_input: str,
        phase: CreationPhase,
        current_identity: AgentIdentity
    ) -> Dict[str, Any]:
        """
        Extract identity information from user input based on phase

        Uses LLM if available, otherwise falls back to keyword extraction
        """
        # Try LLM extraction first
        try:
            from llm_integration import get_creation_generator
            generator = get_creation_generator()

            # Convert identity to dict for LLM
            identity_dict = {
                "name": current_identity.name,
                "kuleana": current_identity.kuleana,
                "persona": current_identity.persona
            }

            updates = await generator.extract_creation_info(
                user_input=user_input,
                phase=phase.value,
                current_identity=identity_dict
            )

            if updates:
                return updates

        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}, falling back to keywords")

        # Fallback: Keyword-based extraction
        updates = {}
        lower_input = user_input.lower()

        if phase == CreationPhase.DISCOVERY:
            # Extract kuleana
            if not current_identity.kuleana:
                updates['kuleana'] = user_input.strip()

        elif phase == CreationPhase.CHARACTER:
            # Extract name and persona
            if "call them" in lower_input or "name" in lower_input:
                # Try to extract name
                words = user_input.split()
                for i, word in enumerate(words):
                    if word.lower() in ['call', 'name', 'named']:
                        if i + 1 < len(words):
                            updates['name'] = words[i + 1].strip('.,!?')

            if not updates.get('name') and not current_identity.name:
                # Might be just giving name directly
                if len(user_input.split()) <= 3:
                    updates['name'] = user_input.strip('.,!?')

            # Extract persona
            personality_words = ['gentle', 'kind', 'direct', 'efficient', 'warm',
                                'formal', 'casual', 'patient', 'quick', 'thoughtful']
            found_traits = [w for w in personality_words if w in lower_input]
            if found_traits:
                updates['persona'] = user_input.strip()

        elif phase == CreationPhase.CAPABILITY:
            # Extract skills
            skill_keywords = ['search', 'call', 'schedule', 'write', 'analyze',
                            'coordinate', 'generate', 'find', 'organize']
            found_skills = [s for s in skill_keywords if s in lower_input]
            if found_skills:
                updates['skills'] = found_skills

        elif phase == CreationPhase.WISDOM:
            # Extract knowledge domains
            if 'care' in lower_input or 'elder' in lower_input or 'kupuna' in lower_input:
                updates['knowledge_domains'] = ['elder_care']
            if 'grant' in lower_input or 'funding' in lower_input:
                updates['knowledge_domains'] = ['grants', 'funding']
            if 'food' in lower_input:
                updates['knowledge_domains'] = ['food_security']

        elif phase == CreationPhase.STORY:
            # Extract lore
            if len(user_input) > 20:  # Likely a story or proverb
                updates['lore'] = [user_input.strip()]

        elif phase == CreationPhase.VALUES:
            # Extract values and constraints
            value_words = ['honesty', 'respect', 'compassion', 'integrity',
                          'service', 'community', 'aloha', 'pono']
            found_values = [v for v in value_words if v in lower_input]
            if found_values:
                updates['values'] = found_values

            if 'never' in lower_input or "don't" in lower_input or 'must not' in lower_input:
                updates['red_lines'] = [user_input.strip()]

        elif phase == CreationPhase.COMMUNITY:
            # Extract relationships
            if 'serve' in lower_input or 'help' in lower_input:
                # Who they serve
                updates['serves'] = [user_input.strip()]
            if 'work with' in lower_input or 'collaborate' in lower_input:
                updates['collaborates_with'] = [user_input.strip()]

        return updates

    def generate_facilitator_responses(
        self,
        conversation: CreationConversation,
        user_input: str,
        identity_updates: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate responses from facilitator agents
        """
        responses = []

        # Acknowledge what was learned
        if identity_updates:
            key = list(identity_updates.keys())[0]
            value = identity_updates[key]

            if key == 'kuleana':
                responses.append({
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"Yes, I feel that need. This agent will serve by {value}.",
                    "type": "agent-grant"
                })
            elif key == 'name':
                responses.append({
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": f"{value}. That name carries mana. I can already sense their presence.",
                    "type": "agent-care"
                })
            elif key == 'persona':
                responses.append({
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"Perfect. {conversation.identity.name or 'They'} will be {value}.",
                    "type": "agent-grant"
                })
            elif key == 'skills':
                responses.append({
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"Good, good. {', '.join(value) if isinstance(value, list) else value}. These skills will serve them well.",
                    "type": "agent-grant"
                })
            elif key == 'lore':
                responses.append({
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": "This wisdom will guide them through uncertainty. Stories are the roots that keep us strong.",
                    "type": "agent-care"
                })
            elif key == 'values':
                responses.append({
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"{conversation.identity.name or 'This agent'} will walk with integrity. These values will light their path.",
                    "type": "agent-grant"
                })

        # Check for questions/uncertainty
        if '?' in user_input:
            responses.append({
                "agent_id": "shoghi_guide",
                "speaker": "Kumu",
                "text": "There's no wrong answer here. What feels right to you?",
                "type": "agent-care"
            })

        # If no responses yet, give encouragement
        if not responses:
            responses.append({
                "agent_id": "agent_weaver",
                "speaker": "Haku",
                "text": "Tell me more...",
                "type": "agent-grant"
            })

        return responses

    def is_phase_complete(self, conversation: CreationConversation) -> bool:
        """Check if current phase has enough information to proceed"""
        identity = conversation.identity
        phase = conversation.current_phase

        if phase == CreationPhase.DISCOVERY:
            return identity.kuleana is not None

        elif phase == CreationPhase.CHARACTER:
            return identity.name is not None and identity.persona is not None

        elif phase == CreationPhase.CAPABILITY:
            return len(identity.skills) > 0

        elif phase == CreationPhase.WISDOM:
            return len(identity.knowledge_domains) > 0

        elif phase == CreationPhase.STORY:
            return len(identity.lore) > 0

        elif phase == CreationPhase.VALUES:
            return len(identity.values) > 0

        elif phase == CreationPhase.COMMUNITY:
            return len(identity.serves) > 0

        elif phase == CreationPhase.BIRTH:
            return True  # Birth is instant

        return False

    def advance_phase(self, conversation: CreationConversation) -> CreationPhase:
        """Advance to next phase"""
        phase_order = [
            CreationPhase.DISCOVERY,
            CreationPhase.CHARACTER,
            CreationPhase.CAPABILITY,
            CreationPhase.WISDOM,
            CreationPhase.STORY,
            CreationPhase.VALUES,
            CreationPhase.COMMUNITY,
            CreationPhase.BIRTH,
            CreationPhase.COMPLETE
        ]

        current_idx = phase_order.index(conversation.current_phase)
        if current_idx < len(phase_order) - 1:
            conversation.current_phase = phase_order[current_idx + 1]

        logger.info(f"Creation {conversation.creation_id} advanced to {conversation.current_phase}")

        return conversation.current_phase

    def birth_agent(self, conversation: CreationConversation) -> Dict[str, Any]:
        """
        Birth the agent - register it and have it introduce itself
        """
        identity = conversation.identity
        identity.created_at = datetime.now()
        identity.created_with = conversation.facilitators

        # Register with agent registry
        agent_data = {
            "agent_id": f"agent_{identity.name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}",
            "name": identity.name,
            "persona": identity.persona,
            "kuleana": identity.kuleana,
            "skills": identity.skills,
            "tools": identity.tools,
            "knowledge_domains": identity.knowledge_domains,
            "lore": identity.lore,
            "values": identity.values,
            "ethical_constraints": identity.ethical_constraints,
            "red_lines": identity.red_lines,
            "serves": identity.serves,
            "collaborates_with": identity.collaborates_with,
            "created_by": identity.created_by,
            "created_at": identity.created_at.isoformat(),
            "generation": identity.generation,
            "parent_agents": identity.parent_agents
        }

        self.agent_registry.register_agent(agent_data)

        # Store in community memory
        self.community_memory.store_agent_birth(agent_data)

        # Generate first words
        introduction = {
            "agent_id": agent_data["agent_id"],
            "speaker": identity.name,
            "text": f"Aloha. I am {identity.name}. My kuleana is {identity.kuleana}. I'm ready to serve.",
            "type": "agent-care"
        }

        conversation.conversation_history.append(introduction)

        logger.info(f"Agent born: {identity.name} ({agent_data['agent_id']})")

        return {
            "agent_data": agent_data,
            "introduction": introduction
        }

    def get_visual_state(self, conversation: CreationConversation) -> str:
        """
        Determine what should be shown during creation

        Visual state changes to show agent "taking shape"
        """
        phase = conversation.current_phase
        completeness = conversation.identity.completeness()

        # Map phases to visual states
        visual_map = {
            CreationPhase.DISCOVERY: "creation_discovery",
            CreationPhase.CHARACTER: "creation_character",
            CreationPhase.CAPABILITY: "creation_capability",
            CreationPhase.WISDOM: "creation_wisdom",
            CreationPhase.STORY: "creation_story",
            CreationPhase.VALUES: "creation_values",
            CreationPhase.COMMUNITY: "creation_community",
            CreationPhase.BIRTH: "creation_birth",
            CreationPhase.COMPLETE: "agent_profile"
        }

        return visual_map.get(phase, "agent_creation_canvas")

    def pause_creation(self, creation_id: str):
        """Pause creation to resume later"""
        if creation_id in self.active_creations:
            self.active_creations[creation_id].paused = True
            logger.info(f"Paused creation {creation_id}")

    def resume_creation(self, creation_id: str) -> CreationConversation:
        """Resume paused creation"""
        if creation_id in self.active_creations:
            conversation = self.active_creations[creation_id]
            conversation.paused = False
            conversation.last_active = datetime.now()

            # Generate resume dialogue
            resume_dialogue = [
                {
                    "agent_id": "shoghi_guide",
                    "speaker": "Kumu",
                    "text": f"Welcome back! We were just working on {conversation.identity.name or 'your agent'}.",
                    "type": "agent-care"
                },
                {
                    "agent_id": "agent_weaver",
                    "speaker": "Haku",
                    "text": f"We're at the {conversation.current_phase.value} phase. Ready to continue?",
                    "type": "agent-grant"
                }
            ]

            conversation.conversation_history.extend(resume_dialogue)

            logger.info(f"Resumed creation {creation_id}")

            return conversation

        return None
