"""
Operational metrics measurement.

Directly measures the 5D operational state:
- Activity level
- Coordination density
- Effectiveness
- Resource consumption
- System health
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

from .state import OperationalState


class OperationalMetrics:
    """
    Tracks and measures operational metrics for agents.

    This class maintains sliding windows of metrics and computes
    normalized operational state vectors.
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize operational metrics tracker.

        Args:
            window_size: Number of recent actions to consider for metrics
        """
        self.window_size = window_size
        self.actions: Dict[str, List[Dict]] = defaultdict(list)
        self.errors: Dict[str, List[datetime]] = defaultdict(list)
        self.costs: Dict[str, List[float]] = defaultdict(list)
        self.collaborations: Dict[str, List[datetime]] = defaultdict(list)
        self.task_outcomes: Dict[str, List[float]] = defaultdict(list)

    def record_action(self, agent_id: str, action_type: str, metadata: Optional[Dict] = None):
        """Record an agent action."""
        self.actions[agent_id].append({
            'timestamp': datetime.utcnow(),
            'type': action_type,
            'metadata': metadata or {}
        })
        # Keep only recent actions
        self.actions[agent_id] = self.actions[agent_id][-self.window_size:]

    def record_error(self, agent_id: str):
        """Record an error event."""
        self.errors[agent_id].append(datetime.utcnow())
        self.errors[agent_id] = self.errors[agent_id][-self.window_size:]

    def record_cost(self, agent_id: str, cost: float):
        """Record resource consumption (API cost, compute cost, etc.)."""
        self.costs[agent_id].append(cost)
        self.costs[agent_id] = self.costs[agent_id][-self.window_size:]

    def record_collaboration(self, agent_id: str):
        """Record a collaboration event."""
        self.collaborations[agent_id].append(datetime.utcnow())
        self.collaborations[agent_id] = self.collaborations[agent_id][-self.window_size:]

    def record_task_outcome(self, agent_id: str, success_rate: float):
        """
        Record task completion quality.

        Args:
            success_rate: 0-1 score for task quality/success
        """
        self.task_outcomes[agent_id].append(success_rate)
        self.task_outcomes[agent_id] = self.task_outcomes[agent_id][-self.window_size:]

    def measure(self, agent_id: str) -> OperationalState:
        """
        Measure current operational state for an agent.

        Returns:
            OperationalState with all dimensions in [0, 1]
        """
        # Activity level: actions per unit time, normalized
        activity = self._measure_activity(agent_id)

        # Coordination density: collaboration frequency
        coordination = self._measure_coordination(agent_id)

        # Effectiveness: task success rate
        effectiveness = self._measure_effectiveness(agent_id)

        # Resource consumption: normalized cost
        resource_consumption = self._measure_resource_consumption(agent_id)

        # System health: inverse of error rate
        system_health = self._measure_system_health(agent_id)

        return OperationalState(
            activity_level=activity,
            coordination_density=coordination,
            effectiveness=effectiveness,
            resource_consumption=resource_consumption,
            system_health=system_health
        )

    def _measure_activity(self, agent_id: str) -> float:
        """Measure activity level (0-1)."""
        actions = self.actions.get(agent_id, [])
        if not actions:
            return 0.0

        # Calculate actions per minute over the window
        now = datetime.utcnow()
        recent = [a for a in actions if (now - a['timestamp']) < timedelta(hours=1)]

        if not recent:
            return 0.0

        # Normalize: assume max reasonable activity is 60 actions/hour = 1.0
        actions_per_hour = len(recent)
        return min(actions_per_hour / 60.0, 1.0)

    def _measure_coordination(self, agent_id: str) -> float:
        """Measure coordination density (0-1)."""
        collabs = self.collaborations.get(agent_id, [])
        actions = self.actions.get(agent_id, [])

        if not actions:
            return 0.0

        # Ratio of collaborative actions to total actions
        now = datetime.utcnow()
        recent_collabs = [c for c in collabs if (now - c) < timedelta(hours=1)]
        recent_actions = [a for a in actions if (now - a['timestamp']) < timedelta(hours=1)]

        if not recent_actions:
            return 0.0

        return min(len(recent_collabs) / max(len(recent_actions), 1), 1.0)

    def _measure_effectiveness(self, agent_id: str) -> float:
        """Measure effectiveness (0-1)."""
        outcomes = self.task_outcomes.get(agent_id, [])
        if not outcomes:
            return 0.5  # Neutral default

        # Average recent task outcomes
        return float(np.mean(outcomes[-20:]))

    def _measure_resource_consumption(self, agent_id: str) -> float:
        """Measure resource consumption (0-1)."""
        costs = self.costs.get(agent_id, [])
        if not costs:
            return 0.0

        # Normalize cost: assume $1/hour is max (1.0)
        recent_costs = costs[-60:]  # Last 60 actions
        avg_cost = np.mean(recent_costs) if recent_costs else 0.0

        # Scale so $1 = 1.0
        return min(avg_cost, 1.0)

    def _measure_system_health(self, agent_id: str) -> float:
        """Measure system health (0-1, higher is better)."""
        errors = self.errors.get(agent_id, [])
        actions = self.actions.get(agent_id, [])

        if not actions:
            return 1.0  # No actions = no errors

        # Error rate over recent window
        now = datetime.utcnow()
        recent_errors = [e for e in errors if (now - e) < timedelta(hours=1)]
        recent_actions = [a for a in actions if (now - a['timestamp']) < timedelta(hours=1)]

        if not recent_actions:
            return 1.0

        error_rate = len(recent_errors) / max(len(recent_actions), 1)

        # Health = 1 - error_rate
        return max(1.0 - error_rate, 0.0)

    def get_confidence(self, agent_id: str) -> Dict[str, float]:
        """
        Estimate confidence in operational measurements.

        Returns:
            Dictionary mapping dimension names to confidence scores (0-1)
        """
        actions = self.actions.get(agent_id, [])
        num_actions = len(actions)

        # Confidence increases with more data
        base_confidence = min(num_actions / 50.0, 1.0)

        return {
            'activity_level': base_confidence,
            'coordination_density': base_confidence * 0.8,  # Harder to measure
            'effectiveness': min(len(self.task_outcomes.get(agent_id, [])) / 10.0, 1.0),
            'resource_consumption': base_confidence,
            'system_health': base_confidence
        }
