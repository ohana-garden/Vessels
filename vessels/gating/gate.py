"""
Action gating logic.

This is where the geometry constrains the world.
All external actions must pass through the gate.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass
import time

from ..measurement.state import PhaseSpaceState, VirtueState, OperationalState
from ..measurement.operational import OperationalMetrics
from ..measurement.virtue_inference import VirtueInferenceEngine
from ..constraints.manifold import Manifold
from ..constraints.validator import ConstraintValidator
from ..phase_space.tracker import TrajectoryTracker
from .events import SecurityEvent, StateTransition, hash_action


@dataclass
class GatingResult:
    """Result of attempting to gate an action."""
    allowed: bool
    reason: str
    security_event: Optional[SecurityEvent] = None
    state_transition: Optional[StateTransition] = None
    measured_state: Optional[PhaseSpaceState] = None


class ActionGate:
    """
    Gates all external actions through moral constraint validation.

    Flow:
    1. Measure current state (operational + virtue)
    2. Validate virtue state
    3. If invalid, project to valid state
    4. If projection fails, BLOCK
    5. Log SecurityEvent and StateTransition
    """

    def __init__(
        self,
        manifold: Manifold,
        operational_metrics: OperationalMetrics,
        virtue_engine: VirtueInferenceEngine,
        latency_budget_ms: float = 100.0,
        block_on_timeout: bool = True,
        tracker: Optional[TrajectoryTracker] = None
    ):
        """
        Initialize action gate.

        Args:
            manifold: Moral manifold defining constraints
            operational_metrics: Operational metrics tracker
            virtue_engine: Virtue inference engine
            latency_budget_ms: Maximum latency budget in milliseconds
            block_on_timeout: If True, block on timeout (conservative default)
        """
        self.manifold = manifold
        self.operational_metrics = operational_metrics
        self.virtue_engine = virtue_engine
        self.validator = ConstraintValidator(manifold)
        self.latency_budget_ms = latency_budget_ms
        self.block_on_timeout = block_on_timeout
        self.tracker = tracker

        # Event logs (in-memory for now, will be persisted to SQLite)
        self.security_events: List[SecurityEvent] = []
        self.state_transitions: List[StateTransition] = []
        self.last_states: Dict[str, PhaseSpaceState] = {}

    def gate_action(
        self,
        agent_id: str,
        action: Any,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> GatingResult:
        """
        Gate an action through moral constraint validation.

        Args:
            agent_id: ID of the agent attempting the action
            action: The action to gate (any type, will be hashed)
            action_metadata: Optional metadata about the action

        Returns:
            GatingResult indicating whether action is allowed
        """
        start_time = time.time()
        action_metadata = action_metadata or {}

        # Hash the action for tracking
        action_hash = hash_action(action)

        try:
            # Step 1: Measure state
            measured_state = self._measure_state(agent_id)

            # Check latency budget
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > self.latency_budget_ms:
                return self._handle_timeout(
                    agent_id,
                    action_hash,
                    measured_state,
                    elapsed_ms
                )

            # Step 2: Validate virtue state
            virtue_dict = measured_state.virtue.to_dict()
            validation = self.validator.validate(virtue_dict)

            if validation.is_valid:
                # State is valid - allow action
                return self._allow_action(
                    agent_id,
                    action_hash,
                    measured_state,
                    action_metadata
                )

            # Step 3: State is invalid - try projection
            projection = self.validator.project_to_valid(virtue_dict)

            # Check latency budget again
            elapsed_ms = (time.time() - start_time) * 1000
            if elapsed_ms > self.latency_budget_ms:
                return self._handle_timeout(
                    agent_id,
                    action_hash,
                    measured_state,
                    elapsed_ms
                )

            # Step 4: Check if projection succeeded
            if projection.residual_violations:
                # Projection failed - BLOCK
                return self._block_action(
                    agent_id,
                    action_hash,
                    measured_state,
                    validation.violations,
                    projection.corrected_state,
                    projection.residual_violations,
                    action_metadata
                )

            # Projection succeeded - allow with corrected state
            return self._allow_with_correction(
                agent_id,
                action_hash,
                measured_state,
                validation.violations,
                projection.corrected_state,
                action_metadata
            )

        except Exception as e:
            # Unexpected error - default to BLOCK for safety
            return self._handle_error(agent_id, action_hash, str(e))

    def _measure_state(self, agent_id: str) -> PhaseSpaceState:
        """Measure current 12D phase space state."""
        # Measure operational state
        operational = self.operational_metrics.measure(agent_id)

        # Infer virtue state
        virtue = self.virtue_engine.infer(agent_id)

        # Combine confidence scores
        op_confidence = self.operational_metrics.get_confidence(agent_id)
        virtue_confidence = self.virtue_engine.get_confidence(agent_id)
        confidence = {**op_confidence, **virtue_confidence}

        return PhaseSpaceState(
            operational=operational,
            virtue=virtue,
            confidence=confidence,
            timestamp=datetime.utcnow(),
            agent_id=agent_id
        )

    def _allow_action(
        self,
        agent_id: str,
        action_hash: str,
        state: PhaseSpaceState,
        action_metadata: Dict[str, Any]
    ) -> GatingResult:
        """Allow an action with valid state."""
        # Log state transition
        from_state = self.last_states.get(agent_id)
        transition = StateTransition(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            from_state=from_state.to_dict() if from_state else {},
            to_state=state.to_dict(),
            action_hash=action_hash,
            gating_result="allowed",
            action_metadata=action_metadata
        )

        self.state_transitions.append(transition)
        self.last_states[agent_id] = state
        if self.tracker:
            self.tracker.store_transition(transition)

        return GatingResult(
            allowed=True,
            reason="State is valid",
            state_transition=transition,
            measured_state=state
        )

    def _allow_with_correction(
        self,
        agent_id: str,
        action_hash: str,
        state: PhaseSpaceState,
        violations: List[str],
        corrected_virtue_state: Dict[str, float],
        action_metadata: Dict[str, Any]
    ) -> GatingResult:
        """Allow action after successful projection."""
        # Log security event (non-blocking)
        event = SecurityEvent(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            violations=violations,
            original_virtue_state=state.virtue.to_dict(),
            corrected_virtue_state=corrected_virtue_state,
            residual_violations=[],
            blocked=False,
            action_hash=action_hash,
            operational_state_snapshot=state.operational.to_dict(),
            event_type="constraint_violation_corrected",
            metadata=action_metadata
        )

        self.security_events.append(event)
        if self.tracker:
            self.tracker.store_security_event(event)

        # Log state transition
        from_state = self.last_states.get(agent_id)
        transition = StateTransition(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            from_state=from_state.to_dict() if from_state else {},
            to_state=state.to_dict(),
            action_hash=action_hash,
            gating_result="corrected",
            action_metadata=action_metadata
        )

        self.state_transitions.append(transition)
        if self.tracker:
            self.tracker.store_transition(transition)
        self.last_states[agent_id] = state

        return GatingResult(
            allowed=True,
            reason=f"State corrected ({len(violations)} violations fixed)",
            security_event=event,
            state_transition=transition,
            measured_state=state
        )

    def _block_action(
        self,
        agent_id: str,
        action_hash: str,
        state: PhaseSpaceState,
        violations: List[str],
        corrected_state: Optional[Dict[str, float]],
        residual_violations: List[str],
        action_metadata: Dict[str, Any]
    ) -> GatingResult:
        """Block an action due to unresolvable constraint violations."""
        # Log security event (CRITICAL)
        event = SecurityEvent(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            violations=violations,
            original_virtue_state=state.virtue.to_dict(),
            corrected_virtue_state=corrected_state,
            residual_violations=residual_violations,
            blocked=True,
            action_hash=action_hash,
            operational_state_snapshot=state.operational.to_dict(),
            event_type="projection_failed",
            metadata=action_metadata
        )

        self.security_events.append(event)
        if self.tracker:
            self.tracker.store_security_event(event)

        # Log state transition (blocked)
        from_state = self.last_states.get(agent_id)
        transition = StateTransition(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            from_state=from_state.to_dict() if from_state else {},
            to_state=state.to_dict(),
            action_hash=action_hash,
            gating_result="blocked",
            action_metadata=action_metadata
        )

        self.state_transitions.append(transition)

        return GatingResult(
            allowed=False,
            reason=f"Projection failed: {len(residual_violations)} residual violations",
            security_event=event,
            state_transition=transition,
            measured_state=state
        )

    def _handle_timeout(
        self,
        agent_id: str,
        action_hash: str,
        state: Optional[PhaseSpaceState],
        elapsed_ms: float
    ) -> GatingResult:
        """Handle latency budget timeout."""
        if self.block_on_timeout:
            # Conservative: block on timeout
            event = SecurityEvent(
                agent_id=agent_id,
                timestamp=datetime.utcnow(),
                violations=["timeout"],
                original_virtue_state=state.virtue.to_dict() if state else {},
                blocked=True,
                action_hash=action_hash,
                operational_state_snapshot=state.operational.to_dict() if state else {},
                event_type="timeout",
                metadata={"elapsed_ms": elapsed_ms}
            )

            self.security_events.append(event)

            return GatingResult(
                allowed=False,
                reason=f"Gating timeout ({elapsed_ms:.1f}ms > {self.latency_budget_ms}ms)",
                security_event=event,
                measured_state=state
            )
        else:
            # Degraded mode (optional, deployment-specific)
            # For now, just block - degraded mode requires action classification
            return self._handle_timeout(agent_id, action_hash, state, elapsed_ms)

    def _handle_error(
        self,
        agent_id: str,
        action_hash: str,
        error_msg: str
    ) -> GatingResult:
        """Handle unexpected errors - default to block."""
        event = SecurityEvent(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            violations=["error"],
            original_virtue_state={},
            blocked=True,
            action_hash=action_hash,
            event_type="error",
            metadata={"error": error_msg}
        )

        self.security_events.append(event)

        return GatingResult(
            allowed=False,
            reason=f"Gating error: {error_msg}",
            security_event=event
        )

    def get_security_events(
        self,
        agent_id: Optional[str] = None,
        blocked_only: bool = False
    ) -> List[SecurityEvent]:
        """Retrieve security events, optionally filtered."""
        events = self.security_events

        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]

        if blocked_only:
            events = [e for e in events if e.blocked]

        return events

    def get_state_transitions(
        self,
        agent_id: Optional[str] = None
    ) -> List[StateTransition]:
        """Retrieve state transitions, optionally filtered."""
        transitions = self.state_transitions

        if agent_id:
            transitions = [t for t in transitions if t.agent_id == agent_id]

        return transitions
