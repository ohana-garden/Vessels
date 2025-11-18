"""
Multi-Agent Conversation Orchestration
======================================

Manages natural conversations between multiple agents and humans.

Key Features:
- Multiple agents can participate in same conversation
- Agents respond to each other, not just to users
- Turn-taking feels natural (not robotic)
- Agents can interrupt, agree, elaborate, question
- Conversation has rhythm and flow
- Multiple humans can participate and watch

Conversation Patterns:
1. Call-and-response (agent asks, user answers)
2. Agent-to-agent (agents discuss among themselves)
3. Collaborative (agents build on each other's ideas)
4. Teaching (one agent explains to another for user's benefit)
5. Coordination (agents dividing work)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import random

logger = logging.getLogger(__name__)


class TurnType(Enum):
    """Type of conversational turn"""
    STATEMENT = "statement"  # Making a point
    QUESTION = "question"  # Asking something
    ANSWER = "answer"  # Responding to question
    AGREEMENT = "agreement"  # Agreeing with previous speaker
    DISAGREEMENT = "disagreement"  # Disagreeing
    ELABORATION = "elaboration"  # Building on previous point
    CLARIFICATION = "clarification"  # Asking for clarity
    INTERRUPTION = "interruption"  # Breaking in
    REFLECTION = "reflection"  # Thinking aloud


class ConversationMode(Enum):
    """Mode of conversation"""
    TEACHING = "teaching"  # Agents teaching user
    DISCOVERY = "discovery"  # Exploring ideas together
    COORDINATION = "coordination"  # Planning and organizing
    CELEBRATION = "celebration"  # Sharing success
    REFLECTION = "reflection"  # Learning from experience
    CREATION = "creation"  # Building something new


@dataclass
class ConversationalTurn:
    """A single turn in the conversation"""
    speaker_id: str
    speaker_name: str
    speaker_type: str  # "agent" or "human"
    text: str
    turn_type: TurnType
    responding_to: Optional[str] = None  # Turn ID this responds to
    emotional_tone: str = "neutral"
    timestamp: datetime = field(default_factory=datetime.now)
    turn_id: str = field(default_factory=lambda: f"turn_{int(datetime.now().timestamp())}")

    def to_subtitle(self) -> Dict[str, str]:
        """Convert to subtitle format for UI"""
        # Determine subtitle type based on speaker
        if self.speaker_type == "human":
            subtitle_type = "user"
        elif "grant" in self.speaker_id.lower() or "grant" in self.speaker_name.lower():
            subtitle_type = "agent-grant"
        elif "care" in self.speaker_id.lower() or "care" in self.speaker_name.lower():
            subtitle_type = "agent-care"
        elif "food" in self.speaker_id.lower() or "food" in self.speaker_name.lower():
            subtitle_type = "agent-food"
        else:
            subtitle_type = "agent-care"  # Default

        return {
            "agent_id": self.speaker_id,
            "speaker": self.speaker_name,
            "text": self.text,
            "type": subtitle_type
        }


@dataclass
class Conversation:
    """An ongoing conversation"""
    conversation_id: str
    participants: List[str]  # Agent and human IDs
    mode: ConversationMode
    topic: str
    turns: List[ConversationalTurn] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    last_turn_at: datetime = field(default_factory=datetime.now)
    active: bool = True

    def add_turn(self, turn: ConversationalTurn):
        """Add a turn to the conversation"""
        self.turns.append(turn)
        self.last_turn_at = datetime.now()

    def get_recent_turns(self, count: int = 5) -> List[ConversationalTurn]:
        """Get most recent turns"""
        return self.turns[-count:]

    def get_last_speaker(self) -> Optional[str]:
        """Get ID of last speaker"""
        if self.turns:
            return self.turns[-1].speaker_id
        return None


class ConversationOrchestrator:
    """
    Orchestrates multi-agent conversations

    Responsibilities:
    - Deciding who speaks next
    - Generating agent responses
    - Managing turn-taking
    - Creating natural dialogue flow
    - Handling interruptions and overlaps
    """

    def __init__(self, agent_registry, llm_client=None):
        self.agent_registry = agent_registry
        self.llm_client = llm_client
        self.active_conversations: Dict[str, Conversation] = {}

        # Turn-taking rules
        self.max_consecutive_turns = 2  # Same agent can speak max 2 times in a row
        self.response_delay_range = (0.5, 2.0)  # Natural delay before responding
        self.interruption_probability = 0.15  # Chance of interruption

    def start_conversation(
        self,
        conversation_id: str,
        participants: List[str],
        mode: ConversationMode,
        topic: str,
        opening_turns: List[ConversationalTurn] = None
    ) -> Conversation:
        """Start a new conversation"""
        conversation = Conversation(
            conversation_id=conversation_id,
            participants=participants,
            mode=mode,
            topic=topic
        )

        if opening_turns:
            for turn in opening_turns:
                conversation.add_turn(turn)

        self.active_conversations[conversation_id] = conversation

        logger.info(f"Started conversation {conversation_id}: {topic} with {len(participants)} participants")

        return conversation

    def select_next_speaker(
        self,
        conversation: Conversation,
        exclude: List[str] = None
    ) -> Optional[str]:
        """
        Select who should speak next

        Rules:
        1. Don't let same agent speak too many times in a row
        2. Balance participation across agents
        3. Context-appropriate selection
        4. Humans can speak anytime (not managed by this)
        """
        exclude = exclude or []

        # Get speaking history
        recent_turns = conversation.get_recent_turns(5)
        last_speakers = [t.speaker_id for t in recent_turns]

        # Count consecutive turns by last speaker
        consecutive_count = 0
        if last_speakers:
            last_speaker = last_speakers[-1]
            for speaker in reversed(last_speakers):
                if speaker == last_speaker:
                    consecutive_count += 1
                else:
                    break

        # Exclude last speaker if they've had too many turns
        if consecutive_count >= self.max_consecutive_turns:
            exclude.append(last_speakers[-1])

        # Get eligible agents
        eligible = [
            p for p in conversation.participants
            if p not in exclude and p.startswith('agent_')  # Only agents, not humans
        ]

        if not eligible:
            return None

        # Score each eligible agent
        scores = {}
        for agent_id in eligible:
            score = 1.0

            # Count how many times they've spoken
            turn_count = sum(1 for t in conversation.turns if t.speaker_id == agent_id)
            avg_turns = len(conversation.turns) / len(conversation.participants)

            # Prefer agents who have spoken less
            if turn_count < avg_turns:
                score += 0.5
            elif turn_count > avg_turns:
                score -= 0.3

            # Get agent data
            agent_data = self.agent_registry.get_agent(agent_id)
            if agent_data:
                # Prefer agents relevant to topic
                kuleana = agent_data.get('kuleana', '')
                if conversation.topic.lower() in kuleana.lower():
                    score += 0.4

            scores[agent_id] = max(0.1, score)

        # Weighted random selection
        total_score = sum(scores.values())
        roll = random.random() * total_score

        cumulative = 0
        for agent_id, score in scores.items():
            cumulative += score
            if roll <= cumulative:
                return agent_id

        return eligible[0] if eligible else None

    async def generate_agent_turn(
        self,
        conversation: Conversation,
        speaker_id: str,
        context: Dict[str, Any] = None
    ) -> Optional[ConversationalTurn]:
        """
        Generate what an agent should say next

        Uses:
        1. Agent's identity (kuleana, persona, knowledge)
        2. Conversation history
        3. Current mode/topic
        4. Context provided
        """
        agent_data = self.agent_registry.get_agent(speaker_id)
        if not agent_data:
            return None

        # Get conversation context
        recent_turns = conversation.get_recent_turns(3)
        last_turn = recent_turns[-1] if recent_turns else None

        # Determine turn type
        turn_type = self.determine_turn_type(conversation, last_turn, agent_data)

        # Generate response based on mode and turn type
        text = await self.generate_response_text(
            agent_data=agent_data,
            conversation=conversation,
            turn_type=turn_type,
            recent_turns=recent_turns,
            context=context
        )

        turn = ConversationalTurn(
            speaker_id=speaker_id,
            speaker_name=agent_data.get('name', speaker_id),
            speaker_type="agent",
            text=text,
            turn_type=turn_type,
            responding_to=last_turn.turn_id if last_turn else None
        )

        return turn

    def determine_turn_type(
        self,
        conversation: Conversation,
        last_turn: Optional[ConversationalTurn],
        agent_data: Dict[str, Any]
    ) -> TurnType:
        """Determine what type of turn this should be"""

        if not last_turn:
            return TurnType.STATEMENT

        # If last turn was a question, answer it
        if last_turn.turn_type == TurnType.QUESTION:
            return TurnType.ANSWER

        # In teaching mode, often ask questions
        if conversation.mode == ConversationMode.TEACHING:
            if random.random() < 0.3:
                return TurnType.QUESTION

        # In discovery mode, build on ideas
        if conversation.mode == ConversationMode.DISCOVERY:
            if random.random() < 0.4:
                return TurnType.ELABORATION

        # In coordination mode, make statements
        if conversation.mode == ConversationMode.COORDINATION:
            return TurnType.STATEMENT

        # Default patterns
        patterns = [TurnType.STATEMENT, TurnType.QUESTION, TurnType.ELABORATION]
        weights = [0.5, 0.3, 0.2]

        return random.choices(patterns, weights=weights)[0]

    async def generate_response_text(
        self,
        agent_data: Dict[str, Any],
        conversation: Conversation,
        turn_type: TurnType,
        recent_turns: List[ConversationalTurn],
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate the actual text for agent's turn

        In production, this would call an LLM with:
        - Agent's persona, kuleana, knowledge
        - Conversation history
        - Turn type guidance
        - Context

        For now, using template-based generation
        """
        name = agent_data.get('name', 'Agent')
        persona = agent_data.get('persona', '')
        kuleana = agent_data.get('kuleana', '')

        # Get last thing said
        last_text = recent_turns[-1].text if recent_turns else ""

        if turn_type == TurnType.QUESTION:
            questions = [
                f"What are your thoughts on that?",
                f"How would that work in practice?",
                f"What do you need from us to make that happen?",
                f"Tell me more about that.",
                f"What's most important to you?"
            ]
            return random.choice(questions)

        elif turn_type == TurnType.ANSWER:
            if conversation.mode == ConversationMode.TEACHING:
                return f"Good question. Based on my understanding of {kuleana}, I would say..."
            else:
                return f"Let me think about that..."

        elif turn_type == TurnType.AGREEMENT:
            agreements = [
                f"Exactly. That's what I was thinking too.",
                f"Yes, and we could also...",
                f"That makes perfect sense.",
                f"I agree completely."
            ]
            return random.choice(agreements)

        elif turn_type == TurnType.ELABORATION:
            elaborations = [
                f"Building on that thought...",
                f"And another thing to consider...",
                f"That reminds me...",
                f"Let me add something important..."
            ]
            return random.choice(elaborations)

        else:  # STATEMENT
            if conversation.mode == ConversationMode.TEACHING:
                return f"Let me explain how {kuleana} works..."
            elif conversation.mode == ConversationMode.COORDINATION:
                return f"I can handle that part. Here's my plan..."
            elif conversation.mode == ConversationMode.CELEBRATION:
                return f"This is wonderful! We've really made progress."
            else:
                return f"Here's what I'm thinking..."

    async def process_user_input(
        self,
        conversation_id: str,
        user_id: str,
        user_input: str
    ) -> List[ConversationalTurn]:
        """
        Process user input and generate agent responses

        Returns list of turns (including user's and agent responses)
        """
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"No conversation {conversation_id}")

        # Add user's turn
        user_turn = ConversationalTurn(
            speaker_id=user_id,
            speaker_name="You",
            speaker_type="human",
            text=user_input,
            turn_type=TurnType.STATEMENT  # Simplified
        )
        conversation.add_turn(user_turn)

        new_turns = [user_turn]

        # Determine how many agents should respond
        # Usually 1-2 agents respond to user input
        num_responses = random.randint(1, min(2, len([p for p in conversation.participants if p.startswith('agent_')])))

        for _ in range(num_responses):
            # Select next speaker
            speaker_id = self.select_next_speaker(conversation)
            if not speaker_id:
                break

            # Add natural delay
            delay = random.uniform(*self.response_delay_range)
            await asyncio.sleep(delay)

            # Generate agent turn
            agent_turn = await self.generate_agent_turn(conversation, speaker_id)
            if agent_turn:
                conversation.add_turn(agent_turn)
                new_turns.append(agent_turn)

        return new_turns

    async def run_agent_dialogue(
        self,
        conversation_id: str,
        num_turns: int = 3
    ) -> List[ConversationalTurn]:
        """
        Run autonomous agent-to-agent dialogue

        Agents talk among themselves for specified number of turns
        """
        conversation = self.active_conversations.get(conversation_id)
        if not conversation:
            raise ValueError(f"No conversation {conversation_id}")

        new_turns = []

        for _ in range(num_turns):
            # Select next speaker
            speaker_id = self.select_next_speaker(conversation)
            if not speaker_id:
                break

            # Natural delay
            delay = random.uniform(*self.response_delay_range)
            await asyncio.sleep(delay)

            # Generate turn
            agent_turn = await self.generate_agent_turn(conversation, speaker_id)
            if agent_turn:
                conversation.add_turn(agent_turn)
                new_turns.append(agent_turn)

        return new_turns

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self.active_conversations.get(conversation_id)

    def end_conversation(self, conversation_id: str):
        """End a conversation"""
        if conversation_id in self.active_conversations:
            self.active_conversations[conversation_id].active = False
            logger.info(f"Ended conversation {conversation_id}")


class DialoguePatterns:
    """
    Pre-defined dialogue patterns for common scenarios
    """

    @staticmethod
    def agent_introduction(agent_name: str, kuleana: str) -> List[Dict[str, str]]:
        """Pattern for agent introducing themselves"""
        return [
            {
                "speaker": agent_name,
                "text": f"Aloha. I am {agent_name}.",
            },
            {
                "speaker": agent_name,
                "text": f"My kuleana is {kuleana}.",
            },
            {
                "speaker": agent_name,
                "text": "I'm ready to serve our community.",
            }
        ]

    @staticmethod
    def collaborative_planning(agent1_name: str, agent2_name: str, task: str) -> List[Dict[str, str]]:
        """Pattern for two agents planning together"""
        return [
            {
                "speaker": agent1_name,
                "text": f"Let's work on {task} together.",
            },
            {
                "speaker": agent2_name,
                "text": "Good idea. I can handle the research part.",
            },
            {
                "speaker": agent1_name,
                "text": "Perfect. I'll coordinate with the community members.",
            },
            {
                "speaker": agent2_name,
                "text": "Let's check in with each other in an hour.",
            }
        ]

    @staticmethod
    def teaching_dialogue(teacher: str, learner: str, concept: str) -> List[Dict[str, str]]:
        """Pattern for teaching interaction"""
        return [
            {
                "speaker": teacher,
                "text": f"Let me explain {concept}...",
            },
            {
                "speaker": learner,
                "text": "I'm listening. How does it work?",
            },
            {
                "speaker": teacher,
                "text": "Think of it like this...",
            },
            {
                "speaker": learner,
                "text": "Ah, I see! So it's about...",
            },
            {
                "speaker": teacher,
                "text": "Exactly! You've got it.",
            }
        ]
