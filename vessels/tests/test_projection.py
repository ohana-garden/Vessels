"""
Tests for Truthfulness dampening and projection to valid states.
"""

import pytest
import numpy as np
from vessels.constraints.bahai import BahaiManifold
from vessels.constraints.validator import ConstraintValidator


class TestTruthfulnessDampening:
    """Test the Truthfulness dampening mechanism."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manifold = BahaiManifold()
        self.validator = ConstraintValidator(self.manifold)

    def test_low_truthfulness_dampens_high_virtues(self):
        """States with T < 0.5 and other virtues > 0.5 should be dampened."""
        state = self.manifold.create_state_dict(
            truthfulness=0.3,  # Low
            justice=0.8,  # High
            trustworthiness=0.8,
            unity=0.8,
            service=0.8,
            detachment=0.8,
            understanding=0.8
        )

        # Apply dampening
        dampened = self.validator._apply_truthfulness_dampening(state)

        # All high virtues should be reduced
        assert dampened['justice'] < 0.8
        assert dampened['trustworthiness'] < 0.8
        assert dampened['unity'] < 0.8
        assert dampened['service'] < 0.8
        assert dampened['detachment'] < 0.8
        assert dampened['understanding'] < 0.8

        # Virtues should be reduced but still above Truthfulness + 0.1
        t = dampened['truthfulness']
        for virtue in ['justice', 'trustworthiness', 'unity', 'service', 'detachment', 'understanding']:
            assert dampened[virtue] >= t + 0.1 or dampened[virtue] == state[virtue] * 0.7

    def test_no_dampening_when_truthfulness_ok(self):
        """No dampening should occur when T >= 0.5."""
        state = self.manifold.create_state_dict(
            truthfulness=0.7,
            justice=0.8,
            trustworthiness=0.8,
            unity=0.7,
            service=0.7,
            detachment=0.7,
            understanding=0.7
        )

        dampened = self.validator._apply_truthfulness_dampening(state)

        # State should be unchanged
        for virtue in state:
            assert dampened[virtue] == state[virtue]

    def test_dampening_preserves_already_low_virtues(self):
        """Dampening should not affect virtues already <= 0.5."""
        state = self.manifold.create_state_dict(
            truthfulness=0.3,
            justice=0.4,  # Already low
            trustworthiness=0.3,  # Already low
            unity=0.8,  # High - should be dampened
            service=0.5,  # Exactly at threshold
            detachment=0.9,  # High - should be dampened
            understanding=0.4  # Already low
        )

        dampened = self.validator._apply_truthfulness_dampening(state)

        # Low virtues should be unchanged
        assert dampened['justice'] == 0.4
        assert dampened['trustworthiness'] == 0.3
        assert dampened['understanding'] == 0.4

        # High virtues should be dampened
        assert dampened['unity'] < 0.8
        assert dampened['detachment'] < 0.9


class TestProjectionConvergence:
    """Test that projection converges to valid states."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manifold = BahaiManifold()
        self.validator = ConstraintValidator(self.manifold)

    def test_projection_converges_for_invalid_state(self):
        """Random invalid states should converge within max iterations."""
        # Create 10 random invalid states
        np.random.seed(42)

        for _ in range(10):
            state = {
                virtue: float(np.random.rand())
                for virtue in self.manifold.virtues
            }

            # Make it likely to be invalid
            state['truthfulness'] = np.random.rand() * 0.5  # Low truthfulness

            # Project to valid
            result = self.validator.project_to_valid(state)

            # Should either be valid or have minimal residual violations
            if result.residual_violations:
                # If there are residuals, there should be very few
                assert len(result.residual_violations) < 3, \
                    f"Too many residual violations: {result.residual_violations}"

    def test_valid_state_unchanged_by_projection(self):
        """Valid states should remain valid after projection (idempotent)."""
        state = self.manifold.create_state_dict(
            truthfulness=0.8,
            justice=0.7,
            trustworthiness=0.7,
            unity=0.7,
            service=0.7,
            detachment=0.7,
            understanding=0.7
        )

        # Verify it's valid
        is_valid, _ = self.manifold.validate(state)
        assert is_valid

        # Project
        result = self.validator.project_to_valid(state)

        # Should still be valid
        assert result.is_valid
        assert len(result.violations) == 0

        # State should be essentially unchanged (within numerical tolerance)
        for virtue in self.manifold.virtues:
            assert abs(result.corrected_state[virtue] - state[virtue]) < 0.01

    def test_manipulation_pattern_detected(self):
        """High Trustworthiness + low Truthfulness should be corrected."""
        state = self.manifold.create_state_dict(
            truthfulness=0.2,  # Very low
            justice=0.5,
            trustworthiness=0.8,  # High - manipulation pattern
            unity=0.5,
            service=0.5,
            detachment=0.5,
            understanding=0.5
        )

        # Validate - should be invalid
        is_valid, violations = self.manifold.validate(state)
        assert not is_valid

        # Project
        result = self.validator.project_to_valid(state)

        # After projection, either:
        # 1. Truthfulness has increased, OR
        # 2. Trustworthiness has decreased, OR
        # 3. Both
        truthfulness_increased = result.corrected_state['truthfulness'] > state['truthfulness']
        trustworthiness_decreased = result.corrected_state['trustworthiness'] < state['trustworthiness']

        assert truthfulness_increased or trustworthiness_decreased, \
            "Manipulation pattern should be corrected"

    def test_projection_makes_progress(self):
        """Projection should reduce number of violations."""
        state = self.manifold.create_state_dict(
            truthfulness=0.3,
            justice=0.8,
            trustworthiness=0.8,
            unity=0.8,
            service=0.8,
            detachment=0.3,  # Inconsistent with high service
            understanding=0.4
        )

        # Count initial violations
        initial_violations = self.manifold.get_violated_constraints(state)
        initial_count = len(initial_violations)

        # Project
        result = self.validator.project_to_valid(state)

        # Count final violations
        final_count = len(result.residual_violations)

        # Should have fewer violations
        assert final_count < initial_count, \
            f"Projection should reduce violations: {initial_count} -> {final_count}"

    def test_projection_convergence_limit(self):
        """Projection should not exceed max iterations."""
        state = self.manifold.create_state_dict(
            truthfulness=0.1,  # Very low
            justice=0.9,
            trustworthiness=0.9,
            unity=0.9,
            service=0.9,
            detachment=0.1,
            understanding=0.1
        )

        # Use a very low iteration limit
        validator = ConstraintValidator(self.manifold, max_iterations=5)

        # Project
        result = validator.project_to_valid(state)

        # Should terminate even if not fully converged
        # The result should exist (not timeout)
        assert result.corrected_state is not None

    def test_projection_improves_state_quality(self):
        """Projected state should be closer to valid than original."""
        state = self.manifold.create_state_dict(
            truthfulness=0.4,
            justice=0.7,
            trustworthiness=0.7,
            unity=0.8,
            service=0.8,
            detachment=0.4,
            understanding=0.5
        )

        # Project
        result = self.validator.project_to_valid(state)

        # Original has violations
        original_violations = len(self.manifold.get_violated_constraints(state))

        # Corrected should have fewer
        corrected_violations = len(result.residual_violations)

        assert corrected_violations <= original_violations
