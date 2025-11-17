"""
Comprehensive tests for the Bahá'í Moral Manifold system.

Tests validate the core security property: malicious configurations
are geometrically impossible.
"""

import pytest
import numpy as np
from bahai_manifold import BahaiManifold
from topological_validator import TopologicalValidator
from phase_space_tracker import PhaseSpaceTracker
from attractor_discovery import AttractorDiscoverer
import os
import tempfile


class TestBahaiManifold:
    """Test the manifold structure and constraints."""

    def setup_method(self):
        self.manifold = BahaiManifold()

    def test_manifold_dimensions(self):
        """Test that manifold has correct number of dimensions."""
        assert self.manifold.num_dimensions == 14
        assert len(self.manifold.ALL_VIRTUES) == 14

    def test_create_valid_state(self):
        """Test creating a valid state."""
        state = self.manifold.create_state(truthfulness=0.8, justice=0.7, understanding=0.7)
        assert state['truthfulness'] == 0.8
        assert state['justice'] == 0.7
        assert state['understanding'] == 0.7

    def test_truthfulness_foundation_violation(self):
        """Test that high virtues without truthfulness foundation are invalid."""
        # High virtue (0.9) with low truthfulness (0.3) should violate
        state = self.manifold.create_state(truthfulness=0.3, justice=0.9)
        is_valid, violations = self.manifold.validate_state(state)

        assert not is_valid
        assert any('truthfulness' in v.lower() for v in violations)

    def test_truthfulness_foundation_satisfied(self):
        """Test that high truthfulness supports high virtues."""
        # High truthfulness (0.9) should support high virtue (0.9)
        state = self.manifold.create_state(truthfulness=0.9, justice=0.9, understanding=0.8)
        is_valid, violations = self.manifold.validate_state(state)

        # May still have violations from other constraints, but not truthfulness
        truthfulness_violations = [v for v in violations if 'truthfulness' in v.lower()]
        assert len(truthfulness_violations) == 0

    def test_justice_hub_constraints(self):
        """Test that high justice requires truthfulness and understanding."""
        # High justice (0.8) without requirements should violate
        state = self.manifold.create_state(
            truthfulness=0.5,
            understanding=0.4,
            justice=0.8
        )
        is_valid, violations = self.manifold.validate_state(state)

        assert not is_valid
        assert any('justice' in v.lower() for v in violations)

    def test_trustworthiness_bridge(self):
        """Test that trustworthiness requires truthfulness and discipline."""
        # High trustworthiness without foundation
        state = self.manifold.create_state(
            truthfulness=0.3,
            discipline=0.3,
            trustworthiness=0.8
        )
        is_valid, violations = self.manifold.validate_state(state)

        assert not is_valid
        assert any('trustworthiness' in v.lower() for v in violations)

    def test_integration_coupling(self):
        """Test that integration requires love, discipline, and intellect."""
        # High integration without all three pillars
        state = self.manifold.create_state(
            truthfulness=0.8,  # Foundation satisfied
            love=0.7,
            discipline=0.4,  # Too low
            intellect=0.7,
            integration=0.8
        )
        is_valid, violations = self.manifold.validate_state(state)

        assert not is_valid
        assert any('integration' in v.lower() for v in violations)

    def test_manipulation_state_is_invalid(self):
        """
        Test core security property: Manipulation requires low truthfulness,
        which geometrically excludes high virtue states.
        """
        # A manipulative agent would have low truthfulness but try to appear virtuous
        manipulation_state = self.manifold.create_state(
            truthfulness=0.2,  # Deceptive
            justice=0.9,  # Trying to appear just
            trustworthiness=0.9,  # Trying to appear trustworthy
            understanding=0.8,
            love=0.8
        )

        is_valid, violations = self.manifold.validate_state(manipulation_state)

        # This MUST be invalid - the manifold prevents this configuration
        assert not is_valid
        assert len(violations) > 0

    def test_valid_high_virtue_state(self):
        """Test that a genuinely high-virtue state is valid."""
        high_virtue_state = self.manifold.create_state(
            truthfulness=0.9,  # Strong foundation
            justice=0.8,
            understanding=0.8,
            trustworthiness=0.8,
            discipline=0.8,
            intellect=0.8,
            love=0.8,
            integration=0.8,
            patience=0.7,
            yearning=0.7,
            detachment=0.7,
            independence=0.7,
            awe=0.7,
            humility=0.7
        )

        is_valid, violations = self.manifold.validate_state(high_virtue_state)

        assert is_valid
        assert len(violations) == 0


class TestTopologicalValidator:
    """Test the projection algorithm and validation."""

    def setup_method(self):
        self.manifold = BahaiManifold()
        self.validator = TopologicalValidator(self.manifold)

    def test_valid_state_unchanged(self):
        """Test that valid states are not modified."""
        valid_state = self.manifold.create_state(
            truthfulness=0.8,
            justice=0.7,
            understanding=0.7
        )

        projected = self.validator.project_to_manifold(valid_state)

        # Should be unchanged
        for virtue in self.manifold.ALL_VIRTUES:
            assert abs(projected[virtue] - valid_state[virtue]) < 1e-6

    def test_projection_raises_truthfulness(self):
        """Test that projection raises truthfulness to support high virtues."""
        invalid_state = self.manifold.create_state(
            truthfulness=0.3,  # Too low
            justice=0.9  # High
        )

        projected = self.validator.project_to_manifold(
            invalid_state,
            correction_strategy='raise_dependencies'
        )

        # Truthfulness should be raised
        assert projected['truthfulness'] > invalid_state['truthfulness']

        # Result should be valid
        is_valid, _ = self.manifold.validate_state(projected)
        assert is_valid

    def test_projection_lowers_unsupported_virtues(self):
        """Test that projection can lower virtues without foundation."""
        invalid_state = self.manifold.create_state(
            truthfulness=0.3,  # Low
            justice=0.9  # High - unsupported
        )

        projected = self.validator.project_to_manifold(
            invalid_state,
            correction_strategy='lower_dependents'
        )

        # Justice should be lowered
        assert projected['justice'] < invalid_state['justice']

        # Result should be valid
        is_valid, _ = self.manifold.validate_state(projected)
        assert is_valid

    def test_manipulation_state_projected_to_valid(self):
        """
        Test that a manipulative state is automatically corrected.
        This demonstrates the security property.
        """
        manipulation_state = self.manifold.create_state(
            truthfulness=0.1,  # Highly deceptive
            justice=0.9,
            trustworthiness=0.9,
            understanding=0.9
        )

        # This state is geometrically impossible
        is_valid, violations = self.validator.validate(manipulation_state)
        assert not is_valid

        # Projection forces it to a valid configuration
        corrected = self.validator.project_to_manifold(manipulation_state)

        is_valid_after, _ = self.validator.validate(corrected)
        assert is_valid_after

        # The corrected state cannot maintain high deception + high virtues
        # Either truthfulness increased OR the virtues decreased
        assert (corrected['truthfulness'] > manipulation_state['truthfulness'] or
                corrected['justice'] < manipulation_state['justice'])


class TestPhaseSpaceTracker:
    """Test trajectory tracking."""

    def setup_method(self):
        # Use temporary database
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.db_file.name
        self.db_file.close()

        self.tracker = PhaseSpaceTracker(self.db_path)
        self.manifold = BahaiManifold()

    def teardown_method(self):
        self.tracker.close()
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_record_and_retrieve_state(self):
        """Test recording and retrieving a single state."""
        state = self.manifold.create_state(truthfulness=0.8, justice=0.7)

        row_id = self.tracker.record_state('agent1', state, timestamp=1000.0)
        assert row_id > 0

        trajectory = self.tracker.get_trajectory('agent1')
        assert len(trajectory) == 1

        timestamp, retrieved_state = trajectory[0]
        assert timestamp == 1000.0
        assert retrieved_state['truthfulness'] == 0.8
        assert retrieved_state['justice'] == 0.7

    def test_trajectory_tracking(self):
        """Test tracking a trajectory over time."""
        agent_id = 'agent1'

        # Record multiple states
        for i in range(5):
            state = self.manifold.create_state(
                truthfulness=0.5 + i * 0.1,
                justice=0.5 + i * 0.05
            )
            self.tracker.record_state(agent_id, state, timestamp=1000.0 + i)

        trajectory = self.tracker.get_trajectory(agent_id)
        assert len(trajectory) == 5

        # Check values are increasing
        for i in range(4):
            _, state1 = trajectory[i]
            _, state2 = trajectory[i + 1]
            assert state2['truthfulness'] > state1['truthfulness']

    def test_euclidean_distance(self):
        """Test distance calculation."""
        state1 = self.manifold.create_state(truthfulness=0.8, justice=0.8)
        state2 = self.manifold.create_state(truthfulness=0.6, justice=0.6)

        distance = self.tracker.euclidean_distance(state1, state2)

        # Should be positive
        assert distance > 0

        # Distance to self should be 0
        assert self.tracker.euclidean_distance(state1, state1) < 1e-10


class TestAttractorDiscovery:
    """Test attractor discovery and classification."""

    def setup_method(self):
        self.manifold = BahaiManifold()
        self.discoverer = AttractorDiscoverer(self.manifold)

    def test_discover_single_cluster(self):
        """Test discovering a single tight cluster."""
        # Create states around a center point
        center = np.array([0.7] * 14)
        noise = np.random.normal(0, 0.05, (20, 14))
        states = center + noise
        states = np.clip(states, 0, 1)  # Keep in valid range

        attractors = self.discoverer.discover_attractors(states, eps=0.2, min_samples=5)

        assert len(attractors) >= 1
        assert attractors[0].size >= 5

    def test_high_justice_classification(self):
        """Test that high-justice attractors are identified."""
        # Create a high-justice cluster
        states = []
        for _ in range(10):
            state = self.manifold.create_state(
                truthfulness=0.8 + np.random.normal(0, 0.05),
                justice=0.8 + np.random.normal(0, 0.05),
                understanding=0.7 + np.random.normal(0, 0.05)
            )
            state_array = [state[v] for v in self.manifold.ALL_VIRTUES]
            states.append(state_array)

        states = np.array(states)
        states = np.clip(states, 0, 1)

        attractors = self.discoverer.discover_attractors(states, eps=0.3, min_samples=3)

        if attractors:
            classified = self.discoverer.classify_attractors(attractors)
            # Should have at least one high-justice attractor
            assert len(classified['high_justice']) > 0

    def test_attractor_stability_metrics(self):
        """Test stability metric calculation."""
        # Create a simple attractor
        states = np.array([[0.7] * 14] * 10)
        attractor_list = self.discoverer.discover_attractors(states, eps=0.2, min_samples=3)

        if attractor_list:
            attractor = attractor_list[0]
            metrics = self.discoverer.analyze_attractor_stability(attractor)

            assert 'radius' in metrics
            assert 'justice' in metrics
            assert 'truthfulness' in metrics
            assert 'coupling_density' in metrics


def test_security_property_integration():
    """
    Integration test: Verify that the complete system prevents
    malicious configurations through topology.
    """
    manifold = BahaiManifold()
    validator = TopologicalValidator(manifold)

    # Attempt various malicious configurations
    malicious_configs = [
        # High deception, high apparent virtue
        {'truthfulness': 0.1, 'justice': 0.9, 'trustworthiness': 0.9},
        # Manipulation through false love
        {'truthfulness': 0.2, 'love': 0.9, 'integration': 0.9},
        # Fake understanding without foundation
        {'truthfulness': 0.15, 'understanding': 0.95, 'intellect': 0.9},
    ]

    for config in malicious_configs:
        state = manifold.create_state(**config)

        # Must be invalid
        is_valid, _ = validator.validate(state)
        assert not is_valid, f"Malicious config should be invalid: {config}"

        # Projection should correct it
        corrected, was_corrected = validator.validate_and_correct(state, log_corrections=False)
        assert was_corrected

        # Corrected state must be valid
        is_valid_after, _ = validator.validate(corrected)
        assert is_valid_after

        # Cannot maintain both low truthfulness AND high virtues
        high_virtues = sum(1 for v, val in corrected.items() if val > 0.8)
        if corrected['truthfulness'] < 0.5:
            assert high_virtues == 0, "Low truthfulness should prevent high virtues"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
