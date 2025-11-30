"""
Codex-enhanced Action Gate.

Extends the standard ActionGate to include:
- Tension detection before constraint validation
- Check protocol for guidance when needed
- Parable recording for collective learning

REQUIRES AgentZeroCore - all codex operations are coordinated through A0.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import logging

from ..gating.gate import ActionGate, GatingResult
from ..measurement.state import PhaseSpaceState
from ..constraints.manifold import Manifold
from ..measurement.operational import OperationalMetrics
from ..measurement.virtue_inference import VirtueInferenceEngine
from ..phase_space.tracker import TrajectoryTracker

from .tension_detector import TensionDetector, Tension
from .check_protocol import CheckProtocol, CheckResponse
from .council import VillageCouncil
from .parable import ParableStorage

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class CodexGate(ActionGate):
    """
    Codex-enhanced action gate.

    Flow:
    1. Measure current state (inherited)
    2. [NEW] Detect tension
    3. [NEW] If tension detected and severe, trigger check protocol
    4. [NEW] Wait for village guidance if needed
    5. Validate virtue state (inherited)
    6. Project if invalid (inherited)
    7. [NEW] Record parable if check protocol was used
    8. Allow/block action (inherited)

    This implements "The Village Protocol":
    - Recognize tension → Stop
    - Request guidance → Listen
    - Learn → Record parable

    REQUIRES AgentZeroCore - all codex operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        manifold: Manifold,
        operational_metrics: OperationalMetrics,
        virtue_engine: VirtueInferenceEngine,
        village_council: VillageCouncil,
        parable_storage: ParableStorage,
        latency_budget_ms: float = 100.0,
        block_on_timeout: bool = True,
        tracker: Optional[TrajectoryTracker] = None,
        max_consecutive_blocks: int = 5,
        enable_tension_detection: bool = True
    ):
        """
        Initialize codex gate.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            manifold: Moral manifold
            operational_metrics: Operational metrics tracker
            virtue_engine: Virtue inference engine
            village_council: Village council for guidance
            parable_storage: Storage for parables
            latency_budget_ms: Maximum latency budget
            block_on_timeout: Block on timeout
            tracker: Optional trajectory tracker
            max_consecutive_blocks: Max consecutive blocks before intervention
            enable_tension_detection: Enable codex tension detection
        """
        if agent_zero is None:
            raise ValueError("CodexGate requires AgentZeroCore")

        self.agent_zero = agent_zero

        # Initialize parent ActionGate
        super().__init__(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            latency_budget_ms=latency_budget_ms,
            block_on_timeout=block_on_timeout,
            tracker=tracker,
            max_consecutive_blocks=max_consecutive_blocks
        )

        # Codex components
        self.tension_detector = TensionDetector()
        self.check_protocol = CheckProtocol(
            village_council=village_council,
            parable_storage=parable_storage
        )
        self.enable_tension_detection = enable_tension_detection

        # Register with A0
        self.agent_zero.codex_gate = self
        logger.info("CodexGate initialized with A0")

    def gate_action(
        self,
        agent_id: str,
        action: Any,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> GatingResult:
        """
        Gate an action with codex awareness.

        Extends parent gate_action to include tension detection
        and check protocol.

        Args:
            agent_id: Agent ID
            action: Action to gate
            action_metadata: Optional action metadata

        Returns:
            GatingResult
        """
        action_metadata = action_metadata or {}

        # If codex disabled, use parent behavior
        if not self.enable_tension_detection:
            return super().gate_action(agent_id, action, action_metadata)

        # Step 1: Measure state (using parent implementation)
        measured_state = self._measure_state(agent_id)

        # Step 2: Detect tension
        action_description = action_metadata.get('description', str(action))
        tension = self._detect_tension_before_gating(
            agent_id,
            measured_state,
            action_description,
            action_metadata
        )

        # Step 3: If tension detected and severe, trigger check protocol
        if tension and self.tension_detector.should_trigger_check(tension):
            logger.info(
                f"Codex: Tension detected for agent {agent_id}. "
                f"Type: {tension.type.value}, Severity: {tension.severity:.2f}"
            )

            # Trigger check protocol
            check_request = self.check_protocol.initiate_check(
                agent_id=agent_id,
                tension=tension
            )

            # If refused due to safety guardrail, block immediately
            if check_request.status.value == 'refused':
                return GatingResult(
                    allowed=False,
                    reason=f"Codex Safety Guardrail: {tension.description}",
                    measured_state=measured_state
                )

            # In production, this would wait for async council response
            # For now, log and continue with standard gating
            logger.warning(
                f"Codex: Check protocol initiated for {agent_id}. "
                f"Waiting for village guidance. Proceeding with standard gating for now."
            )

        # Step 4: Continue with standard gating (parent behavior)
        result = super().gate_action(agent_id, action, action_metadata)

        # Step 5: If action was blocked, detect constraint violation tension
        if not result.allowed and result.security_event:
            violations = result.security_event.violations
            constraint_tension = self.tension_detector.detect_constraint_violation(
                agent_id=agent_id,
                virtue_state=measured_state.virtue.to_dict(),
                violations=violations,
                action_description=action_description,
                action_metadata=action_metadata
            )

            # Log constraint violation as a learning opportunity
            logger.info(
                f"Codex: Constraint violation detected. "
                f"This could be a teachable moment."
            )

            # In production, this could trigger async check protocol
            # for learning why the constraint was violated

        return result

    def _detect_tension_before_gating(
        self,
        agent_id: str,
        state: PhaseSpaceState,
        action_description: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[Tension]:
        """
        Detect tension before proceeding with gating.

        This is where the Vessel becomes self-aware of conflicts.
        """
        virtue_dict = state.virtue.to_dict()
        confidence = state.confidence

        # Detect tension
        tension = self.tension_detector.detect(
            agent_id=agent_id,
            virtue_state=virtue_dict,
            confidence=confidence,
            action_description=action_description,
            action_metadata=action_metadata
        )

        return tension

    def receive_council_decision(
        self,
        check_id: str,
        decision_text: str,
        reasoning: str,
        guidance: str,
        participants: list[str]
    ) -> CheckResponse:
        """
        Receive a council decision for a pending check.

        This would be called by the human interface when
        the village has deliberated.

        Args:
            check_id: Check request ID
            decision_text: What was decided
            reasoning: Why this decision
            guidance: How to proceed
            participants: Who participated

        Returns:
            CheckResponse with parable
        """
        from .council import CouncilDecision, CouncilMode

        # Create council decision
        decision = CouncilDecision(
            decision=decision_text,
            reasoning=reasoning,
            guidance=guidance,
            council_mode=CouncilMode.ASYNCHRONOUS,  # Default
            participants=participants
        )

        # Process through check protocol
        response = self.check_protocol.receive_decision(check_id, decision)

        return response

    def get_active_checks(self):
        """Get all active check protocol requests."""
        return self.check_protocol.get_active_checks()

    def get_parables(self):
        """Get all recorded parables."""
        return self.check_protocol.parable_storage.get_all()
