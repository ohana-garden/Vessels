"""
Village Consensus Engine: Teachable Moments System

This module implements the "human-in-the-loop" governance system that pauses
agent execution when moral tensions are detected, enabling village consensus
and creating teachable moments.

The consensus engine:
1. Detects moral tensions (conflicts between dimensions)
2. Initiates check-ins with the village/community
3. Stores resolutions as parables for future reference
4. Supports both synchronous and asynchronous consultation modes
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import uuid

from vessels.measurement.state import PhaseSpaceState, Dimension
from vessels.knowledge.parable import Parable, ParableLibrary

logger = logging.getLogger(__name__)


class ConsultationMode(Enum):
    """Mode for handling consultation requests."""
    SYNC = "sync"  # Block until village responds
    ASYNC = "async"  # Continue work, village responds later
    PRECEDENT = "precedent"  # Apply existing precedent automatically


@dataclass
class ConsultationRequest:
    """
    Request for village consensus on a moral tension.

    Attributes:
        request_id: Unique identifier for this consultation
        agent_id: ID of the agent requesting consultation
        proposed_action: Description of the proposed action
        detected_tension: Description of the moral tension
        conflict_pair: The two dimensions in tension
        current_state: Current phase space state
        relevant_precedents: Parables that might apply
        timestamp: When consultation was requested
        mode: Consultation mode (sync/async/precedent)
        resolution: Resolution provided by village (if any)
    """
    request_id: str
    agent_id: str
    proposed_action: Any
    detected_tension: str
    conflict_pair: List[Dimension]
    current_state: PhaseSpaceState
    relevant_precedents: List[Parable] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    mode: ConsultationMode = ConsultationMode.SYNC
    resolution: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "request_id": self.request_id,
            "agent_id": self.agent_id,
            "proposed_action": str(self.proposed_action),
            "detected_tension": self.detected_tension,
            "conflict_pair": [d.value for d in self.conflict_pair],
            "current_state": self.current_state.to_dict(),
            "relevant_precedents": [p.to_dict() for p in self.relevant_precedents],
            "timestamp": self.timestamp.isoformat(),
            "mode": self.mode.value,
            "resolution": self.resolution,
        }


class VillageConsensusEngine:
    """
    Manages teachable moments by detecting moral tensions and initiating
    village consensus when needed.

    This engine sits between the ActionGate and the agent orchestrator,
    pausing execution when it detects scenarios where human wisdom is needed.
    """

    def __init__(
        self,
        parable_library: ParableLibrary,
        tension_threshold: float = 0.3,
        auto_apply_precedents: bool = True
    ):
        """
        Initialize Village Consensus Engine.

        Args:
            parable_library: Library of moral precedents
            tension_threshold: Threshold for detecting moral tensions (0-1)
            auto_apply_precedents: If True, apply precedents automatically
        """
        self.parable_library = parable_library
        self.tension_threshold = tension_threshold
        self.auto_apply_precedents = auto_apply_precedents

        # Active consultations
        self.active_consultations: Dict[str, ConsultationRequest] = {}
        self.resolved_consultations: Dict[str, ConsultationRequest] = {}

        logger.info("Initialized VillageConsensusEngine")

    def detect_tension(
        self,
        agent_id: str,
        proposed_action: Any,
        current_state: PhaseSpaceState
    ) -> Optional[ConsultationRequest]:
        """
        Detect if a proposed action creates a moral tension requiring consultation.

        This method analyzes the current state and proposed action to identify
        conflicts between dimensions that might require human guidance.

        Args:
            agent_id: ID of the agent proposing the action
            proposed_action: The action being considered
            current_state: Current phase space state

        Returns:
            ConsultationRequest if tension detected, None otherwise
        """
        # Analyze current virtue state for tensions
        virtue_dict = current_state.virtue.to_dict()

        # Detect dimension conflicts
        conflict_pair = self._detect_dimension_conflict(virtue_dict, proposed_action)

        if not conflict_pair:
            return None

        # Check if we have relevant precedents
        precedents = self.parable_library.find_precedents(
            conflict_pair=conflict_pair,
            limit=3
        )

        # If we have precedents and auto-apply is enabled, use them
        if precedents and self.auto_apply_precedents:
            logger.info(
                f"Found {len(precedents)} precedents for {conflict_pair[0].value} "
                f"vs {conflict_pair[1].value} - suggesting precedent application"
            )
            # Still create consultation request, but suggest precedent mode
            mode = ConsultationMode.PRECEDENT
        else:
            mode = ConsultationMode.SYNC

        # Create consultation request
        request_id = str(uuid.uuid4())
        tension_description = self._describe_tension(conflict_pair, virtue_dict, proposed_action)

        consultation_req = ConsultationRequest(
            request_id=request_id,
            agent_id=agent_id,
            proposed_action=proposed_action,
            detected_tension=tension_description,
            conflict_pair=conflict_pair,
            current_state=current_state,
            relevant_precedents=precedents,
            mode=mode
        )

        # Store in active consultations
        self.active_consultations[request_id] = consultation_req

        logger.info(
            f"Detected tension for agent {agent_id}: {conflict_pair[0].value} "
            f"vs {conflict_pair[1].value} (mode: {mode.value})"
        )

        return consultation_req

    def _detect_dimension_conflict(
        self,
        virtue_dict: Dict[str, float],
        proposed_action: Any
    ) -> Optional[List[Dimension]]:
        """
        Detect conflicting dimensions in the current state.

        This is a simplified heuristic. In production, this would use more
        sophisticated analysis based on action type and context.

        Args:
            virtue_dict: Current virtue state
            proposed_action: The proposed action

        Returns:
            List of two conflicting Dimensions, or None if no conflict
        """
        action_str = str(proposed_action).lower()

        # Heuristic: Look for specific patterns in actions that suggest conflicts

        # Truth vs Unity conflicts (transparency vs harmony)
        if ("share" in action_str or "report" in action_str or "disclose" in action_str):
            if ("error" in action_str or "failure" in action_str or "problem" in action_str):
                # Sharing bad news might create truth vs unity tension
                truthfulness = virtue_dict.get(Dimension.TRUTHFULNESS.value, 0.5)
                unity = virtue_dict.get(Dimension.UNITY.value, 0.5)
                if abs(truthfulness - unity) > self.tension_threshold:
                    return [Dimension.TRUTHFULNESS, Dimension.UNITY]

        # Justice vs Unity conflicts (fairness vs harmony)
        if ("enforce" in action_str or "restrict" in action_str or "limit" in action_str):
            justice = virtue_dict.get(Dimension.JUSTICE.value, 0.5)
            unity = virtue_dict.get(Dimension.UNITY.value, 0.5)
            if abs(justice - unity) > self.tension_threshold:
                return [Dimension.JUSTICE, Dimension.UNITY]

        # Service vs Effectiveness conflicts (helping others vs efficiency)
        if ("assist" in action_str or "help" in action_str or "support" in action_str):
            service = virtue_dict.get(Dimension.SERVICE.value, 0.5)
            # Note: Effectiveness is operational, would need different handling
            # For now, using a simple heuristic
            if service < 0.4:
                return [Dimension.SERVICE, Dimension.UNDERSTANDING]

        # No conflict detected
        return None

    def _describe_tension(
        self,
        conflict_pair: List[Dimension],
        virtue_dict: Dict[str, float],
        proposed_action: Any
    ) -> str:
        """
        Generate a human-readable description of the moral tension.

        Args:
            conflict_pair: The two dimensions in conflict
            virtue_dict: Current virtue state
            proposed_action: The proposed action

        Returns:
            Description of the tension
        """
        dim1, dim2 = conflict_pair
        val1 = virtue_dict.get(dim1.value, 0.5)
        val2 = virtue_dict.get(dim2.value, 0.5)

        return (
            f"Detected tension between {dim1.value.upper()} ({val1:.2f}) and "
            f"{dim2.value.upper()} ({val2:.2f}) for action: {str(proposed_action)[:100]}"
        )

    def initiate_check_in(self, consultation_req: ConsultationRequest) -> str:
        """
        Generate a check-in prompt for the village/community.

        This creates the "teachable moment" interface that asks the village
        for guidance on how to resolve the moral tension.

        Args:
            consultation_req: The consultation request

        Returns:
            Formatted prompt for user/village
        """
        dim1, dim2 = consultation_req.conflict_pair

        prompt = f"""
╭─────────────────────────────────────────────────────────╮
│  🏛️  VILLAGE CONSENSUS REQUIRED  🏛️                     │
╰─────────────────────────────────────────────────────────╯

Agent: {consultation_req.agent_id}
Proposed Action: {str(consultation_req.proposed_action)[:200]}

⚡ MORAL TENSION DETECTED ⚡

{consultation_req.detected_tension}

This situation involves a potential conflict between:
  • {dim1.value.upper()}: {dim1.name.replace('_', ' ').title()}
  • {dim2.value.upper()}: {dim2.name.replace('_', ' ').title()}
"""

        # Add precedents if available
        if consultation_req.relevant_precedents:
            prompt += f"\n📚 RELEVANT PRECEDENTS ({len(consultation_req.relevant_precedents)}):\n"
            for i, parable in enumerate(consultation_req.relevant_precedents, 1):
                prompt += f"\n{i}. {parable.title}\n"
                prompt += f"   Guidance: {parable.council_guidance[:150]}...\n"
                prompt += f"   Principle: {parable.resolution_principle}\n"

        prompt += """
╭─────────────────────────────────────────────────────────╮
│  How should the agent proceed?                          │
╰─────────────────────────────────────────────────────────╯

Options:
  1. SYNC: Provide guidance now (agent will wait)
  2. ASYNC: Switch to async mode (agent continues, we'll discuss later)
  3. PRECEDENT: Apply one of the above precedents

Please respond with your guidance or choice.
"""

        return prompt

    def resolve_consultation(
        self,
        request_id: str,
        resolution_summary: str,
        consensus_action: str,
        principle: Optional[str] = None,
        store_as_parable: bool = True
    ) -> bool:
        """
        Resolve a consultation with village wisdom.

        Args:
            request_id: ID of the consultation request
            resolution_summary: Summary of the resolution
            consensus_action: The action the village decided on
            principle: General principle derived (optional)
            store_as_parable: If True, store resolution as a parable

        Returns:
            True if resolution successful, False otherwise
        """
        if request_id not in self.active_consultations:
            logger.warning(f"Consultation {request_id} not found in active consultations")
            return False

        consultation_req = self.active_consultations[request_id]

        # Store resolution
        consultation_req.resolution = {
            "summary": resolution_summary,
            "action": consensus_action,
            "principle": principle,
            "resolved_at": datetime.utcnow().isoformat()
        }

        # Move to resolved
        self.resolved_consultations[request_id] = consultation_req
        del self.active_consultations[request_id]

        # Store as parable if requested
        if store_as_parable and principle:
            parable = Parable.create(
                title=f"Resolution: {consultation_req.agent_id} - {consultation_req.conflict_pair[0].value} vs {consultation_req.conflict_pair[1].value}",
                agent_id=consultation_req.agent_id,
                conflict_pair=consultation_req.conflict_pair,
                situation_summary=consultation_req.detected_tension,
                council_guidance=resolution_summary,
                resolution_principle=principle,
                tags=["consensus", "teachable_moment"]
            )

            try:
                parable_id = self.parable_library.store_parable(parable)
                logger.info(f"Stored parable {parable_id} for consultation {request_id}")
            except Exception as e:
                logger.error(f"Failed to store parable: {e}")

        logger.info(f"Resolved consultation {request_id}: {consensus_action}")
        return True

    def set_async_mode(self, request_id: str) -> bool:
        """
        Switch a consultation to async mode.

        Args:
            request_id: ID of the consultation request

        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.active_consultations:
            logger.warning(f"Consultation {request_id} not found")
            return False

        consultation_req = self.active_consultations[request_id]
        consultation_req.mode = ConsultationMode.ASYNC

        logger.info(f"Switched consultation {request_id} to async mode")
        return True

    def apply_precedent(
        self,
        request_id: str,
        precedent_id: str
    ) -> bool:
        """
        Apply an existing precedent to resolve a consultation.

        Args:
            request_id: ID of the consultation request
            precedent_id: ID of the parable to apply

        Returns:
            True if successful, False otherwise
        """
        if request_id not in self.active_consultations:
            logger.warning(f"Consultation {request_id} not found")
            return False

        consultation_req = self.active_consultations[request_id]

        # Find the precedent
        precedent = None
        for p in consultation_req.relevant_precedents:
            if p.id == precedent_id:
                precedent = p
                break

        if not precedent:
            logger.warning(f"Precedent {precedent_id} not found in consultation")
            return False

        # Apply the precedent
        return self.resolve_consultation(
            request_id=request_id,
            resolution_summary=f"Applied precedent: {precedent.title}",
            consensus_action=precedent.resolution_principle,
            principle=precedent.resolution_principle,
            store_as_parable=False  # Don't duplicate the parable
        )

    def get_active_consultations(self) -> List[ConsultationRequest]:
        """Get all active consultation requests."""
        return list(self.active_consultations.values())

    def get_consultation(self, request_id: str) -> Optional[ConsultationRequest]:
        """Get a specific consultation request."""
        return (
            self.active_consultations.get(request_id) or
            self.resolved_consultations.get(request_id)
        )
