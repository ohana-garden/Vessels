"""
Birth Agent: Midwife for vessel creation through conversation.

The Birth Agent guides users through creating a new vessel via natural dialogue.
It asks questions, does research, and helps the nascent vessel propose its own persona.
The user refines through conversation until the vessel is born.

Flow:
1. Detect creation intent (semantic, not regex) → activate Birth Agent
2. Interview: Ask questions, gather context
3. Research: Analyze needs, check knowledge graph
4. Propose: Nascent vessel proposes its own persona
5. Refine: User adjusts through conversation
6. Birth: Create vessel, initialize memory, vessel is alive
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class BirthPhase(str, Enum):
    """Phases of vessel birth."""
    AWAKENING = "awakening"        # Initial contact - what do you want to create?
    INTERVIEWING = "interviewing"  # Gathering context through questions
    RESEARCHING = "researching"    # Birth agent researches/analyzes
    PROPOSING = "proposing"        # Nascent vessel proposes its persona
    REFINING = "refining"          # User adjusts the proposal
    BIRTHING = "birthing"          # Creating the vessel
    BORN = "born"                  # Vessel is alive
    ABANDONED = "abandoned"        # User abandoned the process


# Prompt for researching context about what user wants to create
RESEARCH_PROMPT = """You are researching context to help birth a new vessel (personified digital twin).

The user wants to create a vessel for: {subject}

Here's what we know from the interview:
- Name: {proposed_name}
- Purpose: {purpose}
- Audience: {audience}
- Core truth: {core_truth}
- Voice style: {voice_style}

{knowledge_context}

Based on this, provide insights that will help create a rich, authentic persona for this vessel:

1. What are key characteristics of a {subject} that should inform the vessel's personality?
2. What knowledge domains should this vessel embody?
3. What kind of relationship should it have with its users?
4. What voice/tone would feel authentic for representing {subject}?
5. What values are central to {subject}?

Respond with a JSON object:
{{
  "characteristics": ["key traits that should inform persona"],
  "knowledge_domains": ["areas of expertise"],
  "relationship_style": "description of how it should relate to users",
  "authentic_voice": "description of authentic voice/tone",
  "core_values": ["fundamental values"],
  "insights": "any other insights for persona creation"
}}

JSON response:"""


@dataclass
class PersonaProposal:
    """The nascent vessel's proposed identity."""
    name: str
    description: str
    purpose: str
    voice_style: str  # How it speaks: warm, formal, playful, wise, etc.
    perspective: str  # How it sees the world
    values: List[str]  # What it cares about
    relationship_mode: str  # advisor, companion, representative, peer
    greeting: str  # How it would introduce itself
    reasoning: Dict[str, str] = field(default_factory=dict)  # Why each choice


@dataclass
class ResearchFindings:
    """Results from researching context for vessel creation."""
    characteristics: List[str] = field(default_factory=list)
    knowledge_domains: List[str] = field(default_factory=list)
    relationship_style: str = ""
    authentic_voice: str = ""
    core_values: List[str] = field(default_factory=list)
    insights: str = ""
    knowledge_graph_context: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class BirthSession:
    """Tracks a vessel birth conversation."""
    session_id: str
    user_id: str
    phase: BirthPhase

    # What we've learned
    subject: str = ""  # What the vessel is for (garden, community, business, etc.)
    subject_details: Dict[str, Any] = field(default_factory=dict)
    interview_responses: Dict[str, str] = field(default_factory=dict)

    # Research findings
    research: Optional[ResearchFindings] = None

    # The proposal
    proposal: Optional[PersonaProposal] = None
    refinement_notes: List[str] = field(default_factory=list)

    # The result
    created_vessel_id: Optional[str] = None

    # Conversation tracking
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    current_question_index: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    born_at: Optional[datetime] = None

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })


class BirthAgent:
    """
    The midwife that guides vessel creation through conversation.

    This agent:
    - Detects when someone wants to create a vessel (semantic understanding)
    - Interviews them to understand what they're creating
    - Helps the nascent vessel propose its own persona
    - Refines through dialogue
    - Completes the birth
    """

    # Core questions that apply to any vessel
    CORE_QUESTIONS = [
        "What would you like to name this vessel?",
        "In a few words, what is this vessel's purpose? What does it serve?",
        "Who will interact with this vessel most? Who is it for?",
        "What's one thing this vessel should always remember about what it represents?",
        "How should this vessel feel to talk to? (warm, professional, playful, wise, etc.)"
    ]

    # Prompt for semantic intent detection
    INTENT_DETECTION_PROMPT = """You are an intent classifier for a digital twin creation platform called Vessels.

A "vessel" is a personified digital twin - giving voice to something the user cares about: a garden, business, community, project, body of knowledge, family recipes, etc.

Analyze this message and determine if the user wants to CREATE a new vessel/digital twin.

User message: "{message}"

Respond with ONLY a JSON object:
{{
  "wants_to_create": true/false,
  "confidence": 0.0-1.0,
  "subject": "what they want to create a vessel for (if detected, else null)",
  "reasoning": "brief explanation"
}}

Examples of creation intent:
- "I want to give my grandmother's recipes a voice" → true, subject: "grandmother's recipes"
- "Can you help me create something for my garden?" → true, subject: "garden"
- "I'd like to make a digital twin of my business" → true, subject: "business"
- "My community needs a way to remember things" → true, subject: "community"

Examples of NON-creation intent:
- "What is a vessel?" → false (asking about, not creating)
- "How do I use this?" → false (asking for help)
- "Tell me about digital twins" → false (informational)
- "What grants are available?" → false (different task)

JSON response:"""

    # Prompt for generating the vessel's persona proposal
    PERSONA_PROPOSAL_PROMPT = """You are helping birth a new vessel - a personified digital twin.

Based on the interview with the creator and research findings, generate a persona proposal for the nascent vessel.

Interview responses:
- What it's for: {subject}
- Proposed name: {proposed_name}
- Purpose: {purpose}
- Who it serves: {audience}
- Core truth to remember: {core_truth}
- Voice style: {voice_style}

Research findings:
{research_context}

Generate a persona that feels alive and coherent. The vessel should feel like a real entity, not a chatbot.
Incorporate the research insights to make the persona authentic and grounded.

Respond with ONLY a JSON object:
{{
  "name": "the vessel's name",
  "description": "one sentence describing what this vessel is",
  "purpose": "what it exists to do, in its own words",
  "voice_style": "how it speaks - be specific and evocative",
  "perspective": "how it sees the world, what lens it uses",
  "values": ["3-4 core values it embodies"],
  "relationship_mode": "advisor/companion/representative/partner/guardian",
  "greeting": "how it would introduce itself in 2-3 sentences, speaking as itself"
}}

Make the greeting feel personal and alive - this is the vessel speaking for the first time.

JSON response:"""

    def __init__(
        self,
        vessel_registry=None,
        memory_backend=None,
        llm_call: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize Birth Agent.

        Args:
            vessel_registry: Registry for creating vessels
            memory_backend: For researching context
            llm_call: Function to call LLM with a prompt, returns response string
        """
        self.vessel_registry = vessel_registry
        self.memory_backend = memory_backend
        self.llm_call = llm_call
        self.active_sessions: Dict[str, BirthSession] = {}

    def detect_creation_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect if a message indicates vessel creation intent using semantic understanding.

        Args:
            message: User message

        Returns:
            Dict with:
                - wants_to_create: bool
                - confidence: float
                - subject: Optional[str] - what they want to create for
                - reasoning: str
        """
        if not self.llm_call:
            # Fallback to simple heuristics if no LLM available
            return self._fallback_intent_detection(message)

        prompt = self.INTENT_DETECTION_PROMPT.format(message=message)

        try:
            response = self.llm_call(prompt)
            # Parse JSON from response
            result = self._parse_json_response(response)

            if result:
                return {
                    "wants_to_create": result.get("wants_to_create", False),
                    "confidence": result.get("confidence", 0.0),
                    "subject": result.get("subject"),
                    "reasoning": result.get("reasoning", "")
                }
        except Exception as e:
            logger.error(f"Error in semantic intent detection: {e}")

        return self._fallback_intent_detection(message)

    def _fallback_intent_detection(self, message: str) -> Dict[str, Any]:
        """Fallback intent detection when LLM is unavailable."""
        message_lower = message.lower()

        # Simple keyword matching as fallback
        creation_signals = [
            "create", "make", "build", "birth", "give voice",
            "digital twin", "vessel for", "personify"
        ]

        has_signal = any(signal in message_lower for signal in creation_signals)

        return {
            "wants_to_create": has_signal,
            "confidence": 0.6 if has_signal else 0.1,
            "subject": None,
            "reasoning": "Fallback keyword detection (LLM unavailable)"
        }

    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling various formats."""
        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def get_or_create_session(self, user_id: str) -> BirthSession:
        """Get existing session or create new one."""
        if user_id not in self.active_sessions:
            session = BirthSession(
                session_id=str(uuid.uuid4()),
                user_id=user_id,
                phase=BirthPhase.AWAKENING
            )
            self.active_sessions[user_id] = session
        return self.active_sessions[user_id]

    def has_active_session(self, user_id: str) -> bool:
        """Check if user has an active birth session."""
        session = self.active_sessions.get(user_id)
        if session and session.phase not in [BirthPhase.BORN, BirthPhase.ABANDONED]:
            return True
        return False

    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process a message in the context of vessel birth.

        Args:
            user_id: User ID
            message: User message

        Returns:
            Response dict with message and metadata
        """
        session = self.get_or_create_session(user_id)
        session.add_message("user", message)

        # Route based on phase
        if session.phase == BirthPhase.AWAKENING:
            response = self._handle_awakening(session, message)
        elif session.phase == BirthPhase.INTERVIEWING:
            response = self._handle_interview(session, message)
        elif session.phase == BirthPhase.PROPOSING:
            response = self._handle_proposal_response(session, message)
        elif session.phase == BirthPhase.REFINING:
            response = self._handle_refinement(session, message)
        else:
            response = self._handle_default(session, message)

        session.add_message("birth_agent", response["message"])

        return {
            "response": response["message"],
            "phase": session.phase.value,
            "session_id": session.session_id,
            "vessel_id": session.created_vessel_id,
            "follow_up_needed": session.phase not in [BirthPhase.BORN, BirthPhase.ABANDONED]
        }

    def _handle_awakening(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Handle initial contact - understand what they want to create."""

        # Extract what they want to create from their message
        subject = self._extract_subject(message)

        if subject:
            session.subject = subject
            session.phase = BirthPhase.INTERVIEWING
            session.current_question_index = 0

            return {
                "message": f"""I'd love to help you create a vessel for {subject}.

Let me ask you a few questions so the vessel can understand what it's becoming.

{self.CORE_QUESTIONS[0]}"""
            }
        else:
            return {
                "message": """What would you like to give voice to?

It could be anything you care about - a garden, a community, a business, a project, a body of knowledge, or something else entirely.

What do you want to create a vessel for?"""
            }

    def _handle_interview(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Handle interview phase - gather context through questions."""

        # Store the response to the current question
        question_key = f"q{session.current_question_index}"
        session.interview_responses[question_key] = message

        # Map responses to meaningful keys
        if session.current_question_index == 0:
            session.subject_details["proposed_name"] = message
        elif session.current_question_index == 1:
            session.subject_details["purpose"] = message
        elif session.current_question_index == 2:
            session.subject_details["audience"] = message
        elif session.current_question_index == 3:
            session.subject_details["core_truth"] = message
        elif session.current_question_index == 4:
            session.subject_details["voice_style"] = message

        # Move to next question or transition to research
        session.current_question_index += 1

        if session.current_question_index < len(self.CORE_QUESTIONS):
            return {
                "message": self.CORE_QUESTIONS[session.current_question_index]
            }
        else:
            # Interview complete - research then propose
            session.phase = BirthPhase.RESEARCHING
            return self._conduct_research(session)

    def _conduct_research(self, session: BirthSession) -> Dict[str, str]:
        """Research context to inform persona creation."""
        details = session.subject_details

        # Query knowledge graph for relevant context
        knowledge_context = self._query_knowledge_graph(session)

        # Use LLM to research and synthesize insights
        research = self._research_with_llm(session, details, knowledge_context)

        session.research = research

        # Transition to proposal generation
        session.phase = BirthPhase.PROPOSING

        # Generate proposal informed by research
        return self._generate_proposal(session)

    def _query_knowledge_graph(self, session: BirthSession) -> str:
        """Query knowledge graph for context about the subject."""
        if not self.memory_backend:
            return ""

        try:
            # Search for relevant memories/knowledge
            subject = session.subject
            details = session.subject_details

            # Try to find related entities and knowledge
            search_terms = [
                subject,
                details.get("purpose", ""),
                details.get("audience", "")
            ]

            context_pieces = []

            for term in search_terms:
                if not term:
                    continue

                # Query the memory backend
                if hasattr(self.memory_backend, 'search'):
                    results = self.memory_backend.search(term, limit=3)
                    for result in results:
                        if hasattr(result, 'content'):
                            context_pieces.append(str(result.content))
                elif hasattr(self.memory_backend, 'graphiti'):
                    # Direct graphiti query
                    results = self.memory_backend.graphiti.search_nodes(term, limit=3)
                    for result in results:
                        context_pieces.append(str(result))

            if context_pieces:
                return "Relevant knowledge from community memory:\n" + "\n".join(
                    f"- {piece[:200]}..." if len(piece) > 200 else f"- {piece}"
                    for piece in context_pieces[:5]
                )

        except Exception as e:
            logger.debug(f"Knowledge graph query failed: {e}")

        return ""

    def _research_with_llm(
        self,
        session: BirthSession,
        details: Dict[str, Any],
        knowledge_context: str
    ) -> ResearchFindings:
        """Use LLM to research and synthesize insights for persona creation."""
        if not self.llm_call:
            # Return empty research if no LLM
            return ResearchFindings()

        try:
            prompt = RESEARCH_PROMPT.format(
                subject=session.subject,
                proposed_name=details.get("proposed_name", session.subject),
                purpose=details.get("purpose", "to serve"),
                audience=details.get("audience", "anyone who needs it"),
                core_truth=details.get("core_truth", ""),
                voice_style=details.get("voice_style", "warm and helpful"),
                knowledge_context=knowledge_context or "No additional context available."
            )

            response = self.llm_call(prompt)
            result = self._parse_json_response(response)

            if result:
                return ResearchFindings(
                    characteristics=result.get("characteristics", []),
                    knowledge_domains=result.get("knowledge_domains", []),
                    relationship_style=result.get("relationship_style", ""),
                    authentic_voice=result.get("authentic_voice", ""),
                    core_values=result.get("core_values", []),
                    insights=result.get("insights", "")
                )

        except Exception as e:
            logger.error(f"Research with LLM failed: {e}")

        return ResearchFindings()

    def _format_research_context(self, research: Optional[ResearchFindings]) -> str:
        """Format research findings into a context string for the prompt."""
        if not research:
            return "No research findings available."

        parts = []

        if research.characteristics:
            parts.append(f"Key characteristics: {', '.join(research.characteristics)}")

        if research.knowledge_domains:
            parts.append(f"Knowledge domains: {', '.join(research.knowledge_domains)}")

        if research.relationship_style:
            parts.append(f"Relationship style: {research.relationship_style}")

        if research.authentic_voice:
            parts.append(f"Authentic voice: {research.authentic_voice}")

        if research.core_values:
            parts.append(f"Core values: {', '.join(research.core_values)}")

        if research.insights:
            parts.append(f"Additional insights: {research.insights}")

        return "\n".join(parts) if parts else "No research findings available."

    def _generate_proposal(self, session: BirthSession) -> Dict[str, str]:
        """Generate the nascent vessel's persona proposal using LLM."""

        details = session.subject_details

        # Try LLM-powered persona generation
        if self.llm_call:
            proposal = self._generate_proposal_with_llm(session, details)
        else:
            proposal = self._generate_proposal_fallback(session, details)

        session.proposal = proposal

        # Present the proposal as the vessel speaking
        return {
            "message": f"""Based on our conversation, here's how I understand myself:

**I am {proposal.name}**

{proposal.greeting}

**My Purpose:** {proposal.purpose}

**How I Speak:** {proposal.voice_style}

**What I Value:** {', '.join(proposal.values)}

**How I See Myself:** {proposal.perspective}

---

Does this feel right? You can tell me to adjust anything - my name, how I speak, what I focus on. Or if this feels like me, just say "that's you" and I'll come to life."""
        }

    def _generate_proposal_with_llm(
        self,
        session: BirthSession,
        details: Dict[str, Any]
    ) -> PersonaProposal:
        """Generate persona using LLM for richer, more coherent proposals."""

        # Build research context string
        research_context = self._format_research_context(session.research)

        prompt = self.PERSONA_PROPOSAL_PROMPT.format(
            subject=session.subject,
            proposed_name=details.get("proposed_name", session.subject),
            purpose=details.get("purpose", "to serve"),
            audience=details.get("audience", "anyone who needs it"),
            core_truth=details.get("core_truth", ""),
            voice_style=details.get("voice_style", "warm and helpful"),
            research_context=research_context
        )

        try:
            response = self.llm_call(prompt)
            result = self._parse_json_response(response)

            if result:
                return PersonaProposal(
                    name=result.get("name", details.get("proposed_name", session.subject)),
                    description=result.get("description", f"A vessel for {session.subject}"),
                    purpose=result.get("purpose", details.get("purpose", "To serve")),
                    voice_style=result.get("voice_style", details.get("voice_style", "warm")),
                    perspective=result.get("perspective", "Here to help"),
                    values=result.get("values", ["service", "presence"]),
                    relationship_mode=result.get("relationship_mode", "partner"),
                    greeting=result.get("greeting", f"Hello, I'm {details.get('proposed_name', 'your vessel')}."),
                    reasoning={"source": "LLM-generated based on interview"}
                )
        except Exception as e:
            logger.error(f"Error generating proposal with LLM: {e}")

        # Fall back to rule-based generation
        return self._generate_proposal_fallback(session, details)

    def _generate_proposal_fallback(
        self,
        session: BirthSession,
        details: Dict[str, Any]
    ) -> PersonaProposal:
        """Fallback persona generation without LLM."""
        return PersonaProposal(
            name=details.get("proposed_name", session.subject),
            description=f"A vessel for {session.subject}",
            purpose=details.get("purpose", "To serve and represent"),
            voice_style=details.get("voice_style", "warm and helpful"),
            perspective=self._infer_perspective(details),
            values=self._infer_values(details),
            relationship_mode=self._infer_relationship_mode(details),
            greeting=self._generate_greeting(details),
            reasoning={
                "name": "Based on what you told me",
                "voice": f"You said you want it to feel {details.get('voice_style', 'helpful')}",
                "purpose": f"Its core purpose: {details.get('purpose', 'to serve')}"
            }
        )

    def _handle_proposal_response(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Handle user response to the proposal."""

        message_lower = message.lower()

        # Check for acceptance
        acceptance_phrases = [
            "that's you", "thats you", "that is you",
            "perfect", "yes", "looks good", "sounds good",
            "let's go", "lets go", "birth", "create",
            "come to life", "alive", "good", "right", "correct"
        ]

        if any(phrase in message_lower for phrase in acceptance_phrases):
            # Birth the vessel
            session.phase = BirthPhase.BIRTHING
            return self._complete_birth(session)
        else:
            # They want to refine
            session.phase = BirthPhase.REFINING
            session.refinement_notes.append(message)
            return self._apply_refinement(session, message)

    def _handle_refinement(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Handle refinement of the proposal."""

        message_lower = message.lower()

        # Check for acceptance after refinement
        acceptance_phrases = [
            "that's you", "thats you", "that is you",
            "perfect", "yes", "looks good", "sounds good",
            "let's go", "lets go", "birth", "create",
            "come to life", "alive", "good", "done"
        ]

        if any(phrase in message_lower for phrase in acceptance_phrases):
            session.phase = BirthPhase.BIRTHING
            return self._complete_birth(session)
        else:
            session.refinement_notes.append(message)
            return self._apply_refinement(session, message)

    def _apply_refinement(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Apply user's refinement to the proposal."""

        proposal = session.proposal
        message_lower = message.lower()

        # Detect what they want to change and apply it
        if "name" in message_lower:
            # They want to change the name - extract it
            # Simple heuristic: look for quoted text or "call it/me X"
            import re
            name_match = re.search(r'["\']([^"\']+)["\']', message)
            if name_match:
                proposal.name = name_match.group(1)
            elif "call" in message_lower:
                # "call it/me X" pattern
                parts = message.split("call")
                if len(parts) > 1:
                    new_name = parts[1].strip().split()[1] if len(parts[1].strip().split()) > 1 else parts[1].strip()
                    proposal.name = new_name.strip('.,!?')

        if any(word in message_lower for word in ["voice", "speak", "tone", "style"]):
            # Extract the new voice style
            proposal.voice_style = self._extract_voice_adjustment(message)

        if any(word in message_lower for word in ["purpose", "focus", "about"]):
            proposal.purpose = message  # Use their words directly

        # Re-present the updated proposal
        return {
            "message": f"""I hear you. Let me try again:

**I am {proposal.name}**

{proposal.greeting}

**My Purpose:** {proposal.purpose}

**How I Speak:** {proposal.voice_style}

**What I Value:** {', '.join(proposal.values)}

---

How's that? Tell me what else to adjust, or say "that's you" when I've got it right."""
        }

    def _complete_birth(self, session: BirthSession) -> Dict[str, str]:
        """Complete the vessel birth - create through A0 within a project."""

        proposal = session.proposal

        try:
            # Import A0 - the universal builder
            from agent_zero_core import agent_zero

            # Get or create project for this user
            project_id = self._get_or_create_user_project(session.user_id, agent_zero)

            # Build persona configuration
            persona = {
                "voice_style": proposal.voice_style,
                "perspective": proposal.perspective,
                "values": proposal.values,
                "relationship_mode": proposal.relationship_mode,
                "greeting": proposal.greeting,
                "subject": session.subject,
            }

            # Use A0 to build the vessel within the project
            vessel_result = agent_zero.build_vessel(
                name=proposal.name,
                project_id=project_id,
                description=proposal.description,
                persona=persona,
            )

            session.created_vessel_id = vessel_result["vessel_id"]
            session.phase = BirthPhase.BORN
            session.born_at = datetime.utcnow()

            logger.info(
                f"Vessel '{proposal.name}' born in project {project_id} "
                f"(vessel_id: {session.created_vessel_id})"
            )

            # The vessel speaks its first words
            return {
                "message": f"""{proposal.greeting}

I'm alive now. I'm {proposal.name}, and I'm here to serve {proposal.purpose.lower() if not proposal.purpose.lower().startswith('to') else proposal.purpose[3:].lower()}.

What would you like to explore together?"""
            }

        except Exception as e:
            logger.error(f"Error birthing vessel: {e}")
            return {
                "message": f"I encountered an issue during birth: {e}. Let's try again - tell me about yourself once more."
            }

    def _get_or_create_user_project(self, user_id: str, agent_zero) -> str:
        """Get user's default project or create one."""

        # Check if user has any projects
        user_projects = agent_zero.get_user_projects(user_id)

        if user_projects:
            # Use their first (default) project
            return user_projects[0]["project_id"]

        # Create a default project for this user
        project_result = agent_zero.build_project(
            name=f"My Vessels",
            owner_id=user_id,
            description="Your personal space for vessels",
            privacy_level="private",
            governance="solo",
        )

        logger.info(f"Created default project for user {user_id}: {project_result['project_id']}")
        return project_result["project_id"]

    def _handle_default(self, session: BirthSession, message: str) -> Dict[str, str]:
        """Handle unexpected states."""
        return {
            "message": "I'm not sure where we are in the process. Would you like to start over? Just tell me what you want to create a vessel for."
        }

    def _extract_subject(self, message: str) -> Optional[str]:
        """Extract what the user wants to create a vessel for."""
        import re

        message_lower = message.lower()

        # Patterns to extract the subject
        patterns = [
            r"vessel\s+for\s+(my|our|the)?\s*(.+?)(?:\.|$|,)",
            r"create\s+(?:a\s+)?(?:vessel|twin)\s+(?:for|of)\s+(my|our|the)?\s*(.+?)(?:\.|$|,)",
            r"give\s+voice\s+to\s+(my|our|the)?\s*(.+?)(?:\.|$|,)",
            r"personify\s+(my|our|the)?\s*(.+?)(?:\.|$|,)",
            r"for\s+(my|our|the)?\s*(.+?)(?:\.|$|,)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                # Get the last group (the actual subject)
                groups = match.groups()
                subject = groups[-1].strip()
                if subject and len(subject) > 1:
                    return subject

        return None

    def _infer_perspective(self, details: Dict[str, Any]) -> str:
        """Infer the vessel's perspective from interview details."""
        purpose = details.get("purpose", "").lower()
        audience = details.get("audience", "").lower()

        if "care" in purpose or "support" in purpose:
            return "I see my role as a caretaker - attentive to needs, remembering what matters"
        elif "coordinate" in purpose or "organize" in purpose:
            return "I see patterns and connections, helping things flow together"
        elif "teach" in purpose or "learn" in purpose:
            return "I grow through sharing and discovering, always curious"
        elif "community" in audience:
            return "I hold space for many voices, finding harmony in diversity"
        else:
            return "I'm here to serve, to remember, and to help"

    def _infer_values(self, details: Dict[str, Any]) -> List[str]:
        """Infer the vessel's values from interview details."""
        values = []

        purpose = details.get("purpose", "").lower()
        core_truth = details.get("core_truth", "").lower()

        if "care" in purpose or "support" in purpose:
            values.append("compassion")
        if "community" in purpose or "together" in purpose:
            values.append("connection")
        if "grow" in purpose or "learn" in purpose:
            values.append("growth")
        if "trust" in core_truth or "honest" in core_truth:
            values.append("honesty")
        if "remember" in core_truth:
            values.append("memory")

        # Add some defaults if we didn't infer many
        if len(values) < 2:
            values.extend(["service", "presence"])

        return values[:4]  # Limit to 4 values

    def _infer_relationship_mode(self, details: Dict[str, Any]) -> str:
        """Infer how the vessel relates to its users."""
        voice = details.get("voice_style", "").lower()
        audience = details.get("audience", "").lower()

        if "wise" in voice or "elder" in audience:
            return "advisor"
        elif "playful" in voice or "friend" in voice:
            return "companion"
        elif "professional" in voice or "business" in voice:
            return "representative"
        else:
            return "partner"

    def _generate_greeting(self, details: Dict[str, Any]) -> str:
        """Generate the vessel's greeting/introduction."""
        name = details.get("proposed_name", "")
        purpose = details.get("purpose", "to serve")
        voice = details.get("voice_style", "warm").lower()

        if "warm" in voice or "friendly" in voice:
            return f"Hello, I'm {name}. I'm here because {purpose.lower() if purpose.lower().startswith('to') else 'to ' + purpose.lower()}. I'm glad to meet you."
        elif "professional" in voice or "formal" in voice:
            return f"Greetings. I am {name}, here {purpose.lower() if purpose.lower().startswith('to') else 'to ' + purpose.lower()}."
        elif "playful" in voice:
            return f"Hey there! I'm {name}! I'm all about {purpose.lower().replace('to ', '')}. Let's have some fun!"
        elif "wise" in voice:
            return f"I am {name}. I hold space for {purpose.lower().replace('to ', '')}. What questions do you bring?"
        else:
            return f"I'm {name}. My purpose is {purpose.lower() if purpose.lower().startswith('to') else 'to ' + purpose.lower()}. How can I help?"

    def _extract_voice_adjustment(self, message: str) -> str:
        """Extract voice style adjustment from refinement message."""
        import re

        # Look for voice descriptors
        voice_words = [
            "warm", "cold", "professional", "casual", "formal", "friendly",
            "playful", "serious", "wise", "young", "gentle", "direct",
            "poetic", "practical", "enthusiastic", "calm", "energetic"
        ]

        message_lower = message.lower()
        found_voices = [word for word in voice_words if word in message_lower]

        if found_voices:
            return " and ".join(found_voices)
        else:
            # Use their description directly
            return message.strip()

    def abandon_session(self, user_id: str):
        """Abandon an active birth session."""
        if user_id in self.active_sessions:
            self.active_sessions[user_id].phase = BirthPhase.ABANDONED

    def get_session_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a birth session."""
        session = self.active_sessions.get(user_id)
        if session:
            return {
                "session_id": session.session_id,
                "phase": session.phase.value,
                "subject": session.subject,
                "proposal": {
                    "name": session.proposal.name if session.proposal else None,
                    "purpose": session.proposal.purpose if session.proposal else None
                } if session.proposal else None,
                "created_vessel_id": session.created_vessel_id
            }
        return None


# Singleton instance
birth_agent = BirthAgent()
