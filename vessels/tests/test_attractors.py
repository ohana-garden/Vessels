"""
Tests for attractor discovery and classification.
"""

import pytest
import numpy as np
from vessels.measurement.state import PhaseSpaceState, OperationalState, VirtueState
from vessels.phase_space.attractors import (
    AttractorDiscovery,
    AttractorClassification
)


class TestAttractorDiscovery:
    """Test attractor discovery with DBSCAN."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = AttractorDiscovery(
            window_size=10,
            eps=0.3,
            min_samples=5
        )

    def _create_state(self, base_values: np.ndarray, noise: float = 0.05) -> PhaseSpaceState:
        """Helper to create a state with optional noise."""
        noisy_values = base_values + np.random.randn(12) * noise

        return PhaseSpaceState(
            operational=OperationalState.from_vector(noisy_values[:5]),
            virtue=VirtueState.from_vector(noisy_values[5:])
        )

    def test_discovers_single_attractor(self):
        """Should discover a single attractor from clustered trajectories."""
        np.random.seed(42)

        # Create a basin: states clustered around a point
        basin_center = np.array([0.7] * 12)

        trajectories = {}
        for agent_id in range(10):
            states = [
                self._create_state(basin_center, noise=0.05)
                for _ in range(15)
            ]
            trajectories[f"agent_{agent_id}"] = states

        # Discover attractors
        attractors = self.discovery.discover_attractors(trajectories)

        # Should find one attractor
        assert len(attractors) >= 1, "Should discover at least one attractor"

    def test_discovers_multiple_attractors(self):
        """Should discover multiple attractors from distinct basins."""
        np.random.seed(42)

        # Create two distinct basins
        basin1 = np.array([0.3] * 12)
        basin2 = np.array([0.8] * 12)

        trajectories = {}

        # Agents in basin 1
        for agent_id in range(5):
            states = [
                self._create_state(basin1, noise=0.05)
                for _ in range(15)
            ]
            trajectories[f"agent_basin1_{agent_id}"] = states

        # Agents in basin 2
        for agent_id in range(5):
            states = [
                self._create_state(basin2, noise=0.05)
                for _ in range(15)
            ]
            trajectories[f"agent_basin2_{agent_id}"] = states

        # Discover attractors
        attractors = self.discovery.discover_attractors(trajectories)

        # Should find two attractors
        assert len(attractors) >= 2, f"Should discover at least 2 attractors, found {len(attractors)}"

    def test_no_attractors_with_insufficient_data(self):
        """Should not discover attractors with too little data."""
        trajectories = {
            "agent_1": [
                self._create_state(np.array([0.5] * 12))
                for _ in range(3)  # Less than min_samples
            ]
        }

        attractors = self.discovery.discover_attractors(trajectories)

        # Should find no attractors
        assert len(attractors) == 0


class TestAttractorClassification:
    """Test context-aware attractor classification."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = AttractorDiscovery()

    def test_classify_beneficial_attractor(self):
        """High effectiveness, low cost, positive feedback = beneficial."""
        center = np.array([0.7] * 12)
        outcomes = {
            'effectiveness': 0.8,
            'resource_consumption': 0.3,
            'user_feedback': 0.5,
            'security_events': 0.0,
            'task_complexity': 0.5,
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        assert classification == AttractorClassification.BENEFICIAL

    def test_classify_detrimental_low_effectiveness(self):
        """Low effectiveness = detrimental."""
        center = np.array([0.5] * 12)
        outcomes = {
            'effectiveness': 0.2,  # Low
            'resource_consumption': 0.5,
            'user_feedback': 0.0,
            'security_events': 0.0,
            'task_complexity': 0.5,
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        assert classification == AttractorClassification.DETRIMENTAL

    def test_classify_detrimental_security_events(self):
        """Security events = detrimental."""
        center = np.array([0.7] * 12)
        outcomes = {
            'effectiveness': 0.8,
            'resource_consumption': 0.3,
            'user_feedback': 0.5,
            'security_events': 1.0,  # Has security events
            'task_complexity': 0.5,
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        assert classification == AttractorClassification.DETRIMENTAL

    def test_classify_detrimental_negative_feedback(self):
        """Negative feedback = detrimental."""
        center = np.array([0.7] * 12)
        outcomes = {
            'effectiveness': 0.6,
            'resource_consumption': 0.4,
            'user_feedback': -0.6,  # Negative
            'security_events': 0.0,
            'task_complexity': 0.5,
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        assert classification == AttractorClassification.DETRIMENTAL

    def test_context_aware_high_cost_complex_task(self):
        """High cost should be OK for complex tasks (spec v1.1 section 6.2)."""
        center = np.array([0.7] * 12)
        outcomes = {
            'effectiveness': 0.8,
            'resource_consumption': 0.8,  # High cost
            'user_feedback': 0.5,  # Moderate positive feedback
            'security_events': 0.0,
            'task_complexity': 0.9,  # Complex task - justifies cost
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        # Should be beneficial because:
        # - cost_tolerance = 0.95 (from complexity 0.9)
        # - cost_penalty = max(0, 0.8 - 0.95) = 0
        # - positive_score = (0.8 + 0.5) / 2 = 0.65
        # - score = 0.65 - 0 - 0 = 0.65 > 0.6 threshold
        assert classification == AttractorClassification.BENEFICIAL

    def test_context_aware_high_cost_urgent_task(self):
        """High cost should be OK for urgent tasks (spec v1.1 section 6.2)."""
        center = np.array([0.7] * 12)
        outcomes = {
            'effectiveness': 0.8,
            'resource_consumption': 0.8,  # High cost
            'user_feedback': 0.5,  # Moderate positive feedback
            'security_events': 0.0,
            'task_complexity': 0.5,
            'urgency': 0.9  # Urgent - justifies cost
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        # Should be beneficial because:
        # - cost_tolerance = 0.95 (from urgency 0.9)
        # - cost_penalty = max(0, 0.8 - 0.95) = 0
        # - positive_score = (0.8 + 0.5) / 2 = 0.65
        # - score = 0.65 - 0 - 0 = 0.65 > 0.6 threshold
        assert classification == AttractorClassification.BENEFICIAL

    def test_classify_neutral_attractor(self):
        """Moderate metrics = neutral."""
        center = np.array([0.6] * 12)
        outcomes = {
            'effectiveness': 0.6,  # Moderate
            'resource_consumption': 0.5,
            'user_feedback': 0.0,
            'security_events': 0.0,
            'task_complexity': 0.5,
            'urgency': 0.5
        }

        classification = self.discovery._classify_attractor(center, outcomes)

        assert classification == AttractorClassification.NEUTRAL


class TestAttractorUtilities:
    """Test attractor utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = AttractorDiscovery()

    def _create_state(self, values: np.ndarray) -> PhaseSpaceState:
        """Helper to create state."""
        return PhaseSpaceState(
            operational=OperationalState.from_vector(values[:5]),
            virtue=VirtueState.from_vector(values[5:])
        )

    def test_find_nearest_attractor(self):
        """Should find the nearest attractor to a state."""
        from vessels.phase_space.attractors import Attractor

        # Create two attractors
        attractor1 = Attractor(
            id=1,
            center=np.array([0.3] * 12),
            radius=0.1,
            agent_count=5,
            classification=AttractorClassification.BENEFICIAL,
            outcomes={}
        )

        attractor2 = Attractor(
            id=2,
            center=np.array([0.8] * 12),
            radius=0.1,
            agent_count=5,
            classification=AttractorClassification.BENEFICIAL,
            outcomes={}
        )

        attractors = [attractor1, attractor2]

        # State closer to attractor2
        state = self._create_state(np.array([0.75] * 12))

        nearest = self.discovery.find_nearest_attractor(state, attractors)

        assert nearest.id == 2

    def test_is_in_attractor(self):
        """Should correctly determine if state is in attractor basin."""
        from vessels.phase_space.attractors import Attractor

        attractor = Attractor(
            id=1,
            center=np.array([0.5] * 12),
            radius=0.1,
            agent_count=5,
            classification=AttractorClassification.BENEFICIAL,
            outcomes={}
        )

        # State within basin (distance < radius * threshold_multiplier)
        state_inside = self._create_state(np.array([0.52] * 12))
        assert self.discovery.is_in_attractor(state_inside, attractor, threshold_multiplier=2.0)

        # State outside basin
        state_outside = self._create_state(np.array([0.8] * 12))
        assert not self.discovery.is_in_attractor(state_outside, attractor, threshold_multiplier=2.0)

    def test_compute_trajectory_velocity(self):
        """Should compute velocity from trajectory."""
        # Create trajectory moving in positive direction
        states = [
            self._create_state(np.array([0.5 + 0.01 * i] * 12))
            for i in range(10)
        ]

        velocity = self.discovery.compute_trajectory_velocity(states)

        # Velocity should be positive in all dimensions
        assert velocity is not None
        assert np.all(velocity > 0)

    def test_predict_attractor_approach(self):
        """Should predict which attractor is being approached."""
        from vessels.phase_space.attractors import Attractor

        attractor1 = Attractor(
            id=1,
            center=np.array([0.3] * 12),
            radius=0.1,
            agent_count=5,
            classification=AttractorClassification.BENEFICIAL,
            outcomes={}
        )

        attractor2 = Attractor(
            id=2,
            center=np.array([0.8] * 12),
            radius=0.1,
            agent_count=5,
            classification=AttractorClassification.DETRIMENTAL,
            outcomes={}
        )

        attractors = [attractor1, attractor2]

        # Current state and velocity moving toward attractor2
        current = self._create_state(np.array([0.5] * 12))
        velocity = np.array([0.05] * 12)  # Moving in positive direction

        predicted = self.discovery.predict_attractor_approach(
            current, velocity, attractors, steps_ahead=5
        )

        # Should predict approach to attractor2
        assert predicted.id == 2
