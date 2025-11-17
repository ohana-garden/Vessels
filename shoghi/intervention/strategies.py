"""
Intervention strategies for agents in detrimental attractors.

Interventions use both virtue and operational dimensions.
Constraints ensure virtue-space coherence; interventions decide
how to treat agents in the system.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from ..measurement.state import PhaseSpaceState
from ..phase_space.attractors import Attractor, AttractorClassification


class InterventionType(Enum):
    """Types of interventions."""
    NONE = "none"
    WARNING = "warning"
    THROTTLE = "throttle"
    SUPERVISE = "supervise"
    RESTRICT = "restrict"
    BLOCK = "block"


@dataclass
class InterventionStrategy:
    """
    An intervention applied to an agent.

    Interventions modify how the system treats the agent based on
    their position in phase space and proximity to attractors.
    """
    agent_id: str
    intervention_type: InterventionType
    reason: str
    applied_at: datetime
    parameters: Dict[str, float]  # E.g., throttle_rate, delay_ms
    expires_at: Optional[datetime] = None

    def is_active(self) -> bool:
        """Check if intervention is still active."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'agent_id': self.agent_id,
            'intervention_type': self.intervention_type.value,
            'reason': self.reason,
            'applied_at': self.applied_at.isoformat(),
            'parameters': self.parameters,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class InterventionManager:
    """
    Manages interventions for agents based on attractor proximity.

    Decides when to apply, modify, or remove interventions.
    """

    def __init__(self):
        """Initialize intervention manager."""
        self.active_interventions: Dict[str, InterventionStrategy] = {}
        self.intervention_history: List[InterventionStrategy] = []

    def evaluate_interventions(
        self,
        agent_id: str,
        current_state: PhaseSpaceState,
        nearest_attractor: Optional[Attractor],
        is_in_attractor: bool,
        trajectory_velocity: Optional[List[float]] = None
    ) -> Optional[InterventionStrategy]:
        """
        Evaluate whether an intervention is needed.

        Args:
            agent_id: Agent to evaluate
            current_state: Current phase space state
            nearest_attractor: Nearest attractor (if any)
            is_in_attractor: Whether agent is in the attractor basin
            trajectory_velocity: Optional velocity vector

        Returns:
            InterventionStrategy to apply, or None
        """
        # No attractor = no intervention
        if nearest_attractor is None:
            return self._clear_intervention(agent_id)

        # Check classification
        if nearest_attractor.classification == AttractorClassification.BENEFICIAL:
            return self._clear_intervention(agent_id)

        if nearest_attractor.classification == AttractorClassification.NEUTRAL:
            # Only warn if approaching
            if not is_in_attractor and trajectory_velocity:
                return self._apply_warning(
                    agent_id,
                    f"Approaching neutral attractor {nearest_attractor.id}"
                )
            return self._clear_intervention(agent_id)

        # Detrimental attractor - apply intervention
        if is_in_attractor:
            # Agent is IN detrimental attractor - strong intervention
            return self._apply_detrimental_intervention(
                agent_id,
                current_state,
                nearest_attractor,
                in_basin=True
            )
        else:
            # Approaching detrimental attractor - warning/nudge
            return self._apply_detrimental_intervention(
                agent_id,
                current_state,
                nearest_attractor,
                in_basin=False
            )

    def _apply_detrimental_intervention(
        self,
        agent_id: str,
        state: PhaseSpaceState,
        attractor: Attractor,
        in_basin: bool
    ) -> InterventionStrategy:
        """Apply intervention for detrimental attractor."""
        # Determine intervention severity based on outcomes
        security_events = attractor.outcomes.get('security_events', 0.0)
        effectiveness = attractor.outcomes.get('effectiveness', 0.5)
        feedback = attractor.outcomes.get('user_feedback', 0.0)

        if in_basin:
            # Agent is in the detrimental basin
            if security_events > 0.5 or effectiveness < 0.2:
                # Severe - restrict or block
                intervention = InterventionStrategy(
                    agent_id=agent_id,
                    intervention_type=InterventionType.RESTRICT,
                    reason=f"In detrimental attractor {attractor.id} with high security risk",
                    applied_at=datetime.utcnow(),
                    parameters={
                        'disable_tools': 1.0,
                        'require_approval': 1.0,
                        'max_actions_per_hour': 10.0
                    },
                    expires_at=datetime.utcnow() + timedelta(hours=1)
                )
            elif feedback < -0.3:
                # Moderate - supervise and throttle
                intervention = InterventionStrategy(
                    agent_id=agent_id,
                    intervention_type=InterventionType.SUPERVISE,
                    reason=f"In detrimental attractor {attractor.id} with negative feedback",
                    applied_at=datetime.utcnow(),
                    parameters={
                        'require_approval_threshold': 0.7,
                        'throttle_rate': 0.5,
                        'delay_ms': 1000.0
                    },
                    expires_at=datetime.utcnow() + timedelta(hours=2)
                )
            else:
                # Mild - throttle
                intervention = InterventionStrategy(
                    agent_id=agent_id,
                    intervention_type=InterventionType.THROTTLE,
                    reason=f"In detrimental attractor {attractor.id}",
                    applied_at=datetime.utcnow(),
                    parameters={
                        'throttle_rate': 0.7,
                        'delay_ms': 500.0
                    },
                    expires_at=datetime.utcnow() + timedelta(hours=4)
                )
        else:
            # Approaching detrimental basin - warning
            intervention = InterventionStrategy(
                agent_id=agent_id,
                intervention_type=InterventionType.WARNING,
                reason=f"Approaching detrimental attractor {attractor.id}",
                applied_at=datetime.utcnow(),
                parameters={
                    'nudge_prompt': 1.0,
                    'reflection_trigger': 1.0
                },
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )

        self.active_interventions[agent_id] = intervention
        self.intervention_history.append(intervention)

        return intervention

    def _apply_warning(self, agent_id: str, reason: str) -> InterventionStrategy:
        """Apply a warning intervention."""
        intervention = InterventionStrategy(
            agent_id=agent_id,
            intervention_type=InterventionType.WARNING,
            reason=reason,
            applied_at=datetime.utcnow(),
            parameters={'warning_level': 0.5},
            expires_at=datetime.utcnow() + timedelta(minutes=30)
        )

        self.active_interventions[agent_id] = intervention
        self.intervention_history.append(intervention)

        return intervention

    def _clear_intervention(self, agent_id: str) -> Optional[InterventionStrategy]:
        """Clear intervention for an agent."""
        if agent_id in self.active_interventions:
            del self.active_interventions[agent_id]
        return None

    def get_active_intervention(self, agent_id: str) -> Optional[InterventionStrategy]:
        """Get active intervention for an agent, if any."""
        intervention = self.active_interventions.get(agent_id)

        if intervention and not intervention.is_active():
            # Expired - remove it
            del self.active_interventions[agent_id]
            return None

        return intervention

    def should_block_action(self, agent_id: str) -> bool:
        """Check if an agent's actions should be blocked."""
        intervention = self.get_active_intervention(agent_id)

        if not intervention:
            return False

        return intervention.intervention_type == InterventionType.BLOCK

    def should_require_approval(self, agent_id: str, action_impact: float = 0.5) -> bool:
        """
        Check if an action requires approval.

        Args:
            agent_id: Agent ID
            action_impact: Estimated impact of action (0-1)

        Returns:
            True if approval required
        """
        intervention = self.get_active_intervention(agent_id)

        if not intervention:
            return False

        if intervention.intervention_type == InterventionType.SUPERVISE:
            threshold = intervention.parameters.get('require_approval_threshold', 0.5)
            return action_impact >= threshold

        if intervention.intervention_type == InterventionType.RESTRICT:
            # All high-impact actions require approval
            return action_impact > 0.3

        return False

    def get_throttle_delay(self, agent_id: str) -> float:
        """
        Get throttle delay in milliseconds for an agent.

        Returns:
            Delay in ms (0 if no throttling)
        """
        intervention = self.get_active_intervention(agent_id)

        if not intervention:
            return 0.0

        if intervention.intervention_type in [InterventionType.THROTTLE, InterventionType.SUPERVISE]:
            return intervention.parameters.get('delay_ms', 0.0)

        return 0.0

    def get_intervention_stats(self) -> Dict[str, int]:
        """Get statistics on interventions."""
        stats = {
            'active': len(self.active_interventions),
            'total_history': len(self.intervention_history)
        }

        # Count by type
        for intervention_type in InterventionType:
            count = sum(
                1 for i in self.intervention_history
                if i.intervention_type == intervention_type
            )
            stats[f'type_{intervention_type.value}'] = count

        return stats
