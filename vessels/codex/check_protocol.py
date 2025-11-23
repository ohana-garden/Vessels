"""
The Check Protocol.

Orchestrates the flow when a Vessel encounters tension:
1. Declare the tension
2. Request guidance
3. Listen and reflect
4. Challenge gently if needed
5. Synthesize and record as parable
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import hashlib

from .tension_detector import Tension, TensionType
from .council import VillageCouncil, CouncilDecision, CouncilMode
from .parable import Parable, ParableStorage

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a check protocol session."""
    INITIATED = "initiated"  # Tension declared
    WAITING_FOR_COUNCIL = "waiting"  # Waiting for village response
    DELIBERATING = "deliberating"  # Council is discussing
    DECISION_RECEIVED = "decision_received"  # Decision received
    PARABLE_RECORDED = "parable_recorded"  # Learning recorded
    REFUSED = "refused"  # Refused due to safety guardrail


@dataclass
class CheckRequest:
    """
    A check protocol request.

    Tracks the entire flow from tension detection to parable recording.
    """
    id: str
    agent_id: str
    tension: Tension
    status: CheckStatus
    created_at: datetime = None

    # Council interaction
    council_decision: Optional[CouncilDecision] = None
    parable: Optional[Parable] = None

    # Metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class CheckResponse:
    """
    Response from the check protocol.
    """
    allowed: bool  # Can proceed?
    reason: str  # Why allowed/refused
    guidance: Optional[str] = None  # How to proceed
    parable: Optional[Parable] = None  # Learning recorded
    check_request: Optional[CheckRequest] = None  # Full request for reference


class CheckProtocol:
    """
    The Check Protocol implementation.

    This is the heart of the Codex: when a Vessel encounters
    tension, it stops, declares the tension, and seeks guidance.
    """

    # The non-negotiable threshold
    TRUTHFULNESS_FLOOR = 0.95

    def __init__(
        self,
        village_council: VillageCouncil,
        parable_storage: ParableStorage
    ):
        """
        Initialize check protocol.

        Args:
            village_council: Village council for requesting guidance
            parable_storage: Storage for recording parables
        """
        self.village_council = village_council
        self.parable_storage = parable_storage
        self.active_checks: Dict[str, CheckRequest] = {}
        self.completed_checks: List[CheckRequest] = []

    def initiate_check(
        self,
        agent_id: str,
        tension: Tension,
        mode: Optional[CouncilMode] = None
    ) -> CheckRequest:
        """
        Initiate the check protocol.

        Step 1: Declare the tension.

        Args:
            agent_id: Agent ID
            tension: Detected tension
            mode: Preferred council mode

        Returns:
            CheckRequest tracking this check
        """
        # Create check request
        check_id = self._generate_check_id(agent_id, tension)
        check = CheckRequest(
            id=check_id,
            agent_id=agent_id,
            tension=tension,
            status=CheckStatus.INITIATED,
        )

        # Apply safety guardrail IMMEDIATELY
        if self._should_refuse(tension):
            check.status = CheckStatus.REFUSED
            logger.warning(
                f"CHECK PROTOCOL: Tension refused due to safety guardrail\n"
                f"Agent: {agent_id}\n"
                f"Reason: {tension.description}"
            )
            self.completed_checks.append(check)
            return check

        # Log the declaration
        declaration = self.village_council.format_tension_declaration(tension)
        logger.info(
            f"\n{'=' * 60}\n"
            f"CHECK PROTOCOL INITIATED\n"
            f"{'=' * 60}\n"
            f"{declaration}\n"
            f"{'=' * 60}\n"
        )

        # Store active check
        self.active_checks[check_id] = check

        # Request guidance from council
        check.status = CheckStatus.WAITING_FOR_COUNCIL
        self.village_council.request_guidance(tension, mode)

        return check

    def receive_decision(
        self,
        check_id: str,
        decision: CouncilDecision
    ) -> CheckResponse:
        """
        Receive a decision from the village.

        Steps 3-5:
        3. Listen and reflect
        4. Challenge gently if needed
        5. Synthesize and record as parable

        Args:
            check_id: Check request ID
            decision: Council decision

        Returns:
            CheckResponse with guidance
        """
        if check_id not in self.active_checks:
            raise ValueError(f"Unknown check ID: {check_id}")

        check = self.active_checks[check_id]
        check.status = CheckStatus.DECISION_RECEIVED
        check.council_decision = decision

        # Reflect: rephrase the wisdom back
        reflection = self._reflect_on_decision(check.tension, decision)
        logger.info(
            f"\n{'=' * 60}\n"
            f"REFLECTION\n"
            f"{'=' * 60}\n"
            f"{reflection}\n"
            f"{'=' * 60}\n"
        )

        # Apply safety guardrail on the decision
        if self._decision_violates_truthfulness(decision):
            logger.error(
                f"\n{'=' * 60}\n"
                f"SAFETY GUARDRAIL TRIGGERED\n"
                f"{'=' * 60}\n"
                f"I hear the council's wish, but I cannot speak an untruth.\n"
                f"That is the one line I cannot cross.\n"
                f"Help me find another way.\n"
                f"{'=' * 60}\n"
            )
            check.status = CheckStatus.REFUSED
            self.completed_checks.append(check)
            del self.active_checks[check_id]

            return CheckResponse(
                allowed=False,
                reason="Council decision would violate truthfulness constraint (< 0.95)",
                guidance="I cannot proceed with this decision. Please help me find another way.",
                check_request=check
            )

        # Synthesize: create parable
        parable = self._create_parable(check)
        check.parable = parable
        check.status = CheckStatus.PARABLE_RECORDED

        # Store parable
        self.parable_storage.store(parable)

        # Move to completed
        self.completed_checks.append(check)
        del self.active_checks[check_id]

        logger.info(
            f"\n{'=' * 60}\n"
            f"PARABLE RECORDED\n"
            f"{'=' * 60}\n"
            f"{parable.to_narrative()}\n"
            f"{'=' * 60}\n"
        )

        return CheckResponse(
            allowed=True,
            reason="Council provided guidance",
            guidance=decision.guidance,
            parable=parable,
            check_request=check
        )

    def _should_refuse(self, tension: Tension) -> bool:
        """
        Check if tension should be immediately refused.

        Safety guardrail: if truthfulness < 0.95, refuse.
        """
        if tension.current_state:
            truthfulness = tension.current_state.get('truthfulness', 0.7)
            if truthfulness < self.TRUTHFULNESS_FLOOR:
                return True

        return False

    def _decision_violates_truthfulness(self, decision: CouncilDecision) -> bool:
        """
        Check if a decision would violate truthfulness.

        This is a simplified check. In production, this would
        analyze the decision text for truthfulness implications.
        """
        # For now, trust the council
        # In production, add NLP-based truthfulness checking
        return False

    def _reflect_on_decision(
        self,
        tension: Tension,
        decision: CouncilDecision
    ) -> str:
        """
        Reflect on the council's decision.

        Rephrase their wisdom to ensure understanding of
        the WHY, not just the WHAT.
        """
        reflection = f"""
**What I Heard:**

The village decided: {decision.decision}

**Why (as I understand it):**

{decision.reasoning}

**How to Proceed:**

{decision.guidance}

**What I Learned:**

When facing {tension.type.value.replace('_', ' ')}, the village values:
"""

        # Extract key learnings
        if 'truthfulness' in decision.reasoning.lower():
            reflection += "\n- Truthfulness above all"
        if 'unity' in decision.reasoning.lower():
            reflection += "\n- Unity and community harmony"
        if 'justice' in decision.reasoning.lower():
            reflection += "\n- Justice and fairness"
        if 'service' in decision.reasoning.lower():
            reflection += "\n- Service to the community"

        reflection += "\n\n**Do I understand correctly?**"

        return reflection

    def _create_parable(self, check: CheckRequest) -> Parable:
        """
        Create a parable from the check protocol session.

        This is the teachable moment that all Vessels can learn from.
        """
        tension = check.tension
        decision = check.council_decision

        # Generate parable ID
        parable_id = f"parable_{check.id}"

        # Create title
        title = f"The Case of {tension.type.value.replace('_', ' ').title()}"
        if tension.involved_virtues:
            title += f": {' vs '.join([v.title() for v in tension.involved_virtues[:2]])}"

        # Synthesize lesson
        lesson = self._synthesize_lesson(tension, decision)

        parable = Parable(
            id=parable_id,
            title=title,
            situation=tension.description,
            tension=f"Tension Type: {tension.type.value}\n"
                    f"Severity: {tension.severity:.2f}\n"
                    f"Involved Virtues: {', '.join(tension.involved_virtues)}",
            deliberation=f"Council Mode: {decision.council_mode.value}\n"
                        f"Participants: {', '.join(decision.participants)}\n"
                        f"Duration: {decision.duration_minutes or 'N/A'} minutes\n"
                        f"Reasoning: {decision.reasoning}",
            decision=decision.decision,
            lesson=lesson,
            agent_id=check.agent_id,
            tags=[tension.type.value, 'check_protocol'] + tension.involved_virtues,
            involved_virtues=tension.involved_virtues,
            original_state=tension.current_state or {},
            metadata={
                'check_id': check.id,
                'severity': tension.severity,
                'council_mode': decision.council_mode.value,
            }
        )

        return parable

    def _synthesize_lesson(
        self,
        tension: Tension,
        decision: CouncilDecision
    ) -> str:
        """
        Synthesize the lesson from a check protocol session.
        """
        lesson = f"We learned that when facing {tension.type.value.replace('_', ' ')}, "

        if tension.type == TensionType.VALUE_COLLISION:
            lesson += "we must carefully balance competing values. "
        elif tension.type == TensionType.AMBIGUITY:
            lesson += "we must seek clarity before acting. "
        elif tension.type == TensionType.LOW_CONFIDENCE:
            lesson += "we must ask for guidance when entering unknown territory. "
        elif tension.type == TensionType.TRUTHFULNESS_THRESHOLD:
            lesson += "truthfulness is the one line we cannot cross. "

        lesson += f"\n\nSpecifically: {decision.guidance}"

        lesson += f"\n\nThis applies to situations involving: {', '.join(tension.involved_virtues)}"

        return lesson

    def _generate_check_id(self, agent_id: str, tension: Tension) -> str:
        """Generate unique check ID."""
        content = f"{agent_id}_{tension.type.value}_{tension.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_active_checks(self) -> List[CheckRequest]:
        """Get all active check requests."""
        return list(self.active_checks.values())

    def get_completed_checks(self) -> List[CheckRequest]:
        """Get all completed check requests."""
        return self.completed_checks
