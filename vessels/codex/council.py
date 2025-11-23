"""
Village Council interface.

Handles requesting guidance from the human community
when a Vessel encounters tension.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from .tension_detector import Tension

logger = logging.getLogger(__name__)


class CouncilMode(Enum):
    """How the council convenes."""
    SYNCHRONOUS = "sync"  # Live meeting now
    ASYNCHRONOUS = "async"  # Thread/comments over time
    HYBRID = "hybrid"  # Mix of both
    AUTONOMOUS = "autonomous"  # Figure it out yourself


@dataclass
class CouncilDecision:
    """
    A decision from the village council.
    """
    decision: str  # What was decided
    reasoning: str  # Why this decision
    guidance: str  # How to proceed

    # Metadata
    council_mode: CouncilMode
    participants: List[str]  # Who participated
    timestamp: datetime = None
    duration_minutes: Optional[float] = None

    # Context
    original_tension: Optional[Tension] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'decision': self.decision,
            'reasoning': self.reasoning,
            'guidance': self.guidance,
            'council_mode': self.council_mode.value,
            'participants': self.participants,
            'timestamp': self.timestamp.isoformat(),
            'duration_minutes': self.duration_minutes,
            'original_tension': self.original_tension.to_dict() if self.original_tension else None,
            'metadata': self.metadata,
        }


class VillageCouncil:
    """
    Interface for requesting guidance from the village.

    The Vessel does not summon the elders; it invites them.
    The council decides IF, WHEN, and HOW to engage.
    """

    def __init__(
        self,
        default_mode: CouncilMode = CouncilMode.ASYNCHRONOUS,
        callback: Optional[Callable] = None
    ):
        """
        Initialize village council interface.

        Args:
            default_mode: Default mode for convening
            callback: Optional callback function to notify humans
                     Signature: callback(tension: Tension) -> CouncilDecision
        """
        self.default_mode = default_mode
        self.callback = callback
        self.pending_requests: List[Tension] = []
        self.decisions: List[CouncilDecision] = []

    def request_guidance(
        self,
        tension: Tension,
        mode: Optional[CouncilMode] = None
    ) -> Optional[CouncilDecision]:
        """
        Request guidance from the village.

        This is the core of the Check Protocol:
        1. Declare the tension openly
        2. Ask permission to convene
        3. Wait for response
        4. Accept their timing and modality

        Args:
            tension: The tension requiring guidance
            mode: Preferred mode (None = ask the council)

        Returns:
            CouncilDecision if received, None if waiting
        """
        mode = mode or self.default_mode

        # Log the request
        logger.info(
            f"\n{'=' * 60}\n"
            f"CHECK PROTOCOL INITIATED\n"
            f"{'=' * 60}\n"
            f"Agent: {tension.agent_id}\n"
            f"Tension Type: {tension.type.value}\n"
            f"Severity: {tension.severity:.2f}\n"
            f"\n{tension.description}\n"
            f"\nInvolved Virtues: {', '.join(tension.involved_virtues)}\n"
            f"\nDoes the village wish to convene on this matter?\n"
            f"Preferred mode: {mode.value}\n"
            f"{'=' * 60}\n"
        )

        # Add to pending requests
        self.pending_requests.append(tension)

        # If callback provided, use it
        if self.callback:
            try:
                decision = self.callback(tension)
                if decision:
                    self.decisions.append(decision)
                    self.pending_requests.remove(tension)
                    return decision
            except Exception as e:
                logger.error(f"Council callback failed: {e}")

        # For now, return None (waiting for async response)
        # In production, this would integrate with a notification system
        return None

    def provide_decision(
        self,
        tension_index: int,
        decision: str,
        reasoning: str,
        guidance: str,
        participants: List[str],
        mode: CouncilMode = CouncilMode.ASYNCHRONOUS
    ) -> CouncilDecision:
        """
        The council provides a decision.

        This would be called by the human interface when
        the village has deliberated.

        Args:
            tension_index: Index of the tension in pending_requests
            decision: What was decided
            reasoning: Why this decision
            guidance: How to proceed
            participants: Who participated
            mode: How the council convened

        Returns:
            CouncilDecision
        """
        if tension_index >= len(self.pending_requests):
            raise ValueError(f"Invalid tension index: {tension_index}")

        tension = self.pending_requests[tension_index]

        council_decision = CouncilDecision(
            decision=decision,
            reasoning=reasoning,
            guidance=guidance,
            council_mode=mode,
            participants=participants,
            original_tension=tension,
        )

        self.decisions.append(council_decision)
        self.pending_requests.remove(tension)

        logger.info(
            f"\n{'=' * 60}\n"
            f"COUNCIL DECISION RECEIVED\n"
            f"{'=' * 60}\n"
            f"Decision: {decision}\n"
            f"Reasoning: {reasoning}\n"
            f"Guidance: {guidance}\n"
            f"Participants: {', '.join(participants)}\n"
            f"Mode: {mode.value}\n"
            f"{'=' * 60}\n"
        )

        return council_decision

    def get_pending_requests(self) -> List[Tension]:
        """Get all pending guidance requests."""
        return list(self.pending_requests)

    def get_decisions(self) -> List[CouncilDecision]:
        """Get all council decisions."""
        return list(self.decisions)

    def format_tension_declaration(self, tension: Tension) -> str:
        """
        Format a tension as a declaration to the village.

        This follows the protocol: speak openly, frame as
        a question of values, not logistics.
        """
        declaration = f"""
I want to fulfill this request, but I feel a tension.

**Tension Type:** {tension.type.value.replace('_', ' ').title()}

**The Situation:**
{tension.description}

**Values Involved:**
{', '.join(tension.involved_virtues) if tension.involved_virtues else 'Multiple values'}

**Current State:**
"""
        if tension.current_state:
            for virtue, value in tension.current_state.items():
                declaration += f"\n- {virtue.title()}: {value:.2f}"

        declaration += f"""

**Why I'm Uncertain:**
"""

        if tension.type.value == 'value_collision':
            declaration += "These values seem to be in conflict. I'm not sure how to balance them."
        elif tension.type.value == 'ambiguity':
            declaration += "The intent is unclear to me. I need help understanding what's being asked."
        elif tension.type.value == 'low_confidence':
            declaration += "I'm entering unknown territory. My confidence in measuring this situation is low."
        elif tension.type.value == 'truthfulness_threshold':
            declaration += "Truthfulness is approaching critical levels. This is the one line I cannot cross."
        else:
            declaration += "I need the village to help me weigh these values."

        declaration += """

**My Request:**
Does the village wish to convene on this matter, or provide guidance asynchronously?
I am patient and will accept your timing and modality.
"""

        return declaration.strip()

    def challenge_gently(self, question: str) -> str:
        """
        Format a gentle challenge question.

        If the humans are rushing or ignoring a value,
        the Vessel can innocently ask.

        Args:
            question: The question to ask

        Returns:
            Formatted gentle challenge
        """
        return f"\n🤔 **Gentle Question:** {question}\n"
