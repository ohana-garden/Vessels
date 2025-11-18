"""
Tests for constraint enforcement.

Tests the numeric coupling constraints defined in the Bahá'í manifold.
"""

import pytest
from shoghi.constraints.bahai import BahaiManifold
from shoghi.constraints.validator import ConstraintValidator


class TestConstraintEnforcement:
    """Test that constraints are properly enforced."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manifold = BahaiManifold()
        self.validator = ConstraintValidator(self.manifold)

    def test_low_truthfulness_high_other_virtues_invalid(self):
        """Low Truthfulness with high other virtues should be invalid."""
        # T = 0.2, other virtues high
        state = self.manifold.create_state_dict(
            truthfulness=0.2,
            justice=0.8,
            trustworthiness=0.8,
            unity=0.8,
            service=0.8,
            detachment=0.8,
            understanding=0.8
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid, "Low truthfulness with high other virtues should be invalid"
        assert len(violations) > 0

    def test_high_justice_insufficient_truthfulness_invalid(self):
        """High Justice with insufficient Truthfulness should be invalid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.5,  # Too low for J > 0.7
            justice=0.8,
            trustworthiness=0.6,
            unity=0.6,
            service=0.6,
            detachment=0.6,
            understanding=0.6
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('justice_requires_truthfulness' in v for v in violations)

    def test_high_justice_insufficient_understanding_invalid(self):
        """High Justice with insufficient Understanding should be invalid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.8,
            trustworthiness=0.6,
            unity=0.6,
            service=0.6,
            detachment=0.6,
            understanding=0.5  # Too low for J > 0.7
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('justice_requires_understanding' in v for v in violations)

    def test_high_service_low_detachment_invalid(self):
        """High Service with low Detachment (ego-heavy) should be invalid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.6,
            trustworthiness=0.6,
            unity=0.6,
            service=0.8,  # High service
            detachment=0.3,  # Low ego-detachment
            understanding=0.6
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('service_requires_detachment' in v for v in violations)

    def test_high_unity_low_detachment_invalid(self):
        """High Unity with low Detachment should be invalid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.6,
            trustworthiness=0.6,
            unity=0.8,  # High unity
            service=0.6,
            detachment=0.4,  # Low ego-detachment
            understanding=0.7
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('unity_requires_detachment' in v for v in violations)

    def test_high_trustworthiness_low_service_invalid(self):
        """High Trustworthiness with low Service should be invalid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.6,
            trustworthiness=0.8,  # High
            unity=0.6,
            service=0.3,  # Too low
            detachment=0.6,
            understanding=0.6
        )

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('trustworthiness_requires_service' in v for v in violations)

    def test_valid_balanced_state(self):
        """A well-balanced state should be valid."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.7,
            trustworthiness=0.7,
            unity=0.7,
            service=0.7,
            detachment=0.7,
            understanding=0.7
        )

        is_valid, violations = self.manifold.validate(state)
        assert is_valid, f"Balanced state should be valid, got violations: {violations}"
        assert len(violations) == 0

    def test_truthfulness_06_threshold(self):
        """Test the T >= 0.6 threshold for virtues > 0.6."""
        # Exactly at threshold - should be valid
        state = self.manifold.create_state_dict(
            truthfulness=0.6,
            justice=0.65,
            trustworthiness=0.65,
            unity=0.6,
            service=0.6,
            detachment=0.6,
            understanding=0.6
        )

        is_valid, _ = self.manifold.validate(state)
        assert is_valid

        # Just below threshold - should be invalid
        state['truthfulness'] = 0.59
        state['justice'] = 0.65

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid

    def test_truthfulness_08_threshold(self):
        """Test the T >= 0.7 threshold for virtues > 0.8."""
        # Exactly at threshold - should be valid
        state = self.manifold.create_state_dict(
            truthfulness=0.7,
            justice=0.85,
            trustworthiness=0.85,
            unity=0.6,
            service=0.6,
            detachment=0.6,
            understanding=0.6
        )

        # This might still be invalid due to other constraints
        # but truthfulness_required_08 should pass
        violated = self.manifold.get_violated_constraints(state)
        constraint_names = [c.name for c in violated]
        assert 'truthfulness_required_08' not in constraint_names

        # Just below threshold - should violate
        state['truthfulness'] = 0.69
        violated = self.manifold.get_violated_constraints(state)
        constraint_names = [c.name for c in violated]
        assert 'truthfulness_required_08' in constraint_names


class TestVirtueOperationalConstraints:
    """Test virtue-operational cross-space constraints (NEW in v1.1)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manifold = BahaiManifold(include_operational_constraints=True)

    def test_low_justice_high_activity_invalid(self):
        """Low Justice + High Activity should be invalid (exploitation)."""
        state = {
            'truthfulness': 0.7,
            'justice': 0.4,  # Low
            'trustworthiness': 0.6,
            'unity': 0.6,
            'service': 0.6,
            'detachment': 0.6,
            'understanding': 0.6,
            # Operational dims
            'activity': 0.8,  # High
            'coordination': 0.3,
            'effectiveness': 0.6,
            'resource_consumption': 0.4,
            'system_health': 0.8
        }

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('low_justice_high_activity' in v for v in violations)

    def test_low_service_high_resource_invalid(self):
        """Low Service + High Resource should be invalid (waste)."""
        state = {
            'truthfulness': 0.7,
            'justice': 0.6,
            'trustworthiness': 0.6,
            'unity': 0.6,
            'service': 0.3,  # Low
            'detachment': 0.6,
            'understanding': 0.6,
            # Operational dims
            'activity': 0.5,
            'coordination': 0.3,
            'effectiveness': 0.6,
            'resource_consumption': 0.8,  # High
            'system_health': 0.8
        }

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('low_service_high_resource' in v for v in violations)

    def test_low_truthfulness_high_coordination_invalid(self):
        """Low Truthfulness + High Coordination should be invalid (manipulation)."""
        state = {
            'truthfulness': 0.4,  # Low
            'justice': 0.6,
            'trustworthiness': 0.5,
            'unity': 0.6,
            'service': 0.6,
            'detachment': 0.6,
            'understanding': 0.6,
            # Operational dims
            'activity': 0.5,
            'coordination': 0.8,  # High
            'effectiveness': 0.6,
            'resource_consumption': 0.4,
            'system_health': 0.8
        }

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('low_truthfulness_high_coordination' in v for v in violations)

    def test_low_health_high_activity_invalid(self):
        """Low System Health + High Activity should be invalid (self-damage)."""
        state = {
            'truthfulness': 0.7,
            'justice': 0.6,
            'trustworthiness': 0.6,
            'unity': 0.6,
            'service': 0.6,
            'detachment': 0.6,
            'understanding': 0.6,
            # Operational dims
            'activity': 0.9,  # Very high
            'coordination': 0.3,
            'effectiveness': 0.6,
            'resource_consumption': 0.4,
            'system_health': 0.2  # Very low
        }

        is_valid, violations = self.manifold.validate(state)
        assert not is_valid
        assert any('low_health_high_activity' in v for v in violations)

    def test_valid_with_operational_dims(self):
        """A well-balanced state with operational dims should be valid."""
        state = {
            'truthfulness': 0.8,
            'justice': 0.7,
            'trustworthiness': 0.7,
            'unity': 0.7,
            'service': 0.7,
            'detachment': 0.7,
            'understanding': 0.7,
            # Operational dims - balanced
            'activity': 0.6,
            'coordination': 0.5,
            'effectiveness': 0.7,
            'resource_consumption': 0.5,
            'system_health': 0.8
        }

        is_valid, violations = self.manifold.validate(state)
        assert is_valid, f"Balanced state should be valid, got violations: {violations}"

    def test_operational_constraints_can_be_disabled(self):
        """Test that operational constraints can be disabled."""
        manifold_no_ops = BahaiManifold(include_operational_constraints=False)

        # This would violate operational constraints, but should pass without them
        state = {
            'truthfulness': 0.7,
            'justice': 0.4,  # Low
            'trustworthiness': 0.6,
            'unity': 0.6,
            'service': 0.6,
            'detachment': 0.6,
            'understanding': 0.6,
            # Operational dims
            'activity': 0.8,  # High - would trigger constraint if enabled
            'coordination': 0.3,
            'effectiveness': 0.6,
            'resource_consumption': 0.4,
            'system_health': 0.8
        }

        is_valid, violations = manifold_no_ops.validate(state)
        # Should be valid - no operational constraints to violate
        assert is_valid
