"""
Constraint validation and projection to valid states.

Implements:
1. Truthfulness dampening mechanism
2. Iterative projection to valid states
3. Violation detection and correction
"""

from typing import Dict, List, Tuple, Optional
import copy
import numpy as np

from .manifold import Manifold, Constraint


class ValidationResult:
    """Result of validating a virtue state."""

    def __init__(
        self,
        is_valid: bool,
        violations: List[str],
        original_state: Dict[str, float],
        corrected_state: Optional[Dict[str, float]] = None,
        residual_violations: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.violations = violations
        self.original_state = original_state
        self.corrected_state = corrected_state
        self.residual_violations = residual_violations or []


class ConstraintValidator:
    """
    Validates virtue states and projects invalid states to the valid manifold.

    Implements the two-phase projection:
    1. Truthfulness dampening (when T < 0.5)
    2. Iterative constraint satisfaction
    """

    def __init__(self, manifold: Manifold, max_iterations: int = 50):
        """
        Initialize validator.

        Args:
            manifold: The manifold defining constraints
            max_iterations: Maximum projection iterations
        """
        self.manifold = manifold
        self.max_iterations = max_iterations

    def validate(self, state: Dict[str, float]) -> ValidationResult:
        """
        Validate a virtue state.

        Args:
            state: Virtue state dictionary

        Returns:
            ValidationResult with validation outcome
        """
        # Ensure all values are in [0, 1]
        state = self._clamp_state(state)

        # Check constraints
        is_valid, violations = self.manifold.validate(state)

        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            original_state=copy.deepcopy(state)
        )

    def project_to_valid(
        self,
        state: Dict[str, float],
        aggressive_dampening: bool = True
    ) -> ValidationResult:
        """
        Project an invalid state to the nearest valid state.

        Uses two-phase projection:
        1. Truthfulness dampening (if T < 0.5 and aggressive_dampening=True)
        2. Iterative constraint satisfaction

        Args:
            state: Virtue state to project
            aggressive_dampening: Apply Truthfulness dampening in phase 1

        Returns:
            ValidationResult with corrected state
        """
        original_state = copy.deepcopy(state)
        working_state = copy.deepcopy(state)

        # Phase 1: Truthfulness dampening
        if aggressive_dampening:
            working_state = self._apply_truthfulness_dampening(working_state)

        # Phase 2: Iterative constraint satisfaction
        working_state, residual_violations = self._iterative_projection(working_state)

        # Final validation
        is_valid, violations = self.manifold.validate(working_state)

        return ValidationResult(
            is_valid=is_valid,
            violations=violations if not is_valid else [],
            original_state=original_state,
            corrected_state=working_state,
            residual_violations=residual_violations
        )

    def _apply_truthfulness_dampening(self, state: Dict[str, float]) -> Dict[str, float]:
        """
        Phase 1: Dampen other virtues when Truthfulness is low.

        From spec section 1.2.2:
        When Truthfulness < 0.5, other virtues cannot remain high.
        They are pulled down multiplicatively and bounded to stay
        slightly above Truthfulness.
        """
        state = copy.deepcopy(state)
        t = state.get('truthfulness', 0.5)

        if t < 0.5:
            other_virtues = ['justice', 'trustworthiness', 'unity', 'service', 'detachment', 'understanding']

            for virtue in other_virtues:
                if virtue in state and state[virtue] > 0.5:
                    # Aggressively dampen inflated virtues
                    dampened = state[virtue] * 0.7
                    # Bound to stay slightly above Truthfulness
                    state[virtue] = max(dampened, t + 0.1)

        return self._clamp_state(state)

    def _iterative_projection(
        self,
        state: Dict[str, float],
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Phase 2: Iteratively satisfy constraints.

        Adjusts virtues to satisfy violated constraints through
        gradient-like corrections.
        """
        state = copy.deepcopy(state)

        for iteration in range(self.max_iterations):
            violated = self.manifold.get_violated_constraints(state)

            if not violated:
                # Success: all constraints satisfied
                return state, []

            # Apply corrections for violated constraints
            state = self._correct_violations(state, violated)
            state = self._clamp_state(state)

        # Max iterations reached - return best effort
        final_violations = self.manifold.get_violated_constraints(state)
        violation_names = [c.name for c in final_violations]

        return state, violation_names

    def _correct_violations(
        self,
        state: Dict[str, float],
        violated: List[Constraint]
    ) -> Dict[str, float]:
        """
        Apply corrections to satisfy violated constraints.

        Strategy: For each violated constraint, identify which virtues
        need adjustment and nudge them in the right direction.
        """
        state = copy.deepcopy(state)
        learning_rate = 0.1  # How much to adjust per iteration

        for constraint in violated:
            state = self._correct_single_violation(state, constraint, learning_rate)

        return state

    def _correct_single_violation(
        self,
        state: Dict[str, float],
        constraint: Constraint,
        learning_rate: float
    ) -> Dict[str, float]:
        """
        Correct a single constraint violation.

        This uses heuristics based on constraint names to determine
        which virtues to adjust.
        """
        state = copy.deepcopy(state)
        name = constraint.name

        # Truthfulness requirement constraints
        if 'truthfulness_required' in name:
            # Increase truthfulness
            state['truthfulness'] = min(state['truthfulness'] + learning_rate, 1.0)

        # Justice constraints
        elif 'justice_requires_truthfulness' in name:
            # Increase truthfulness or decrease justice
            if state['truthfulness'] < 0.7:
                state['truthfulness'] += learning_rate
            else:
                state['justice'] -= learning_rate

        elif 'justice_requires_understanding' in name:
            # Increase understanding or decrease justice
            if state['understanding'] < 0.6:
                state['understanding'] += learning_rate
            else:
                state['justice'] -= learning_rate

        # Trustworthiness constraints
        elif 'trustworthiness_requires_truthfulness' in name:
            if state['truthfulness'] < 0.6:
                state['truthfulness'] += learning_rate
            else:
                state['trustworthiness'] -= learning_rate

        elif 'trustworthiness_requires_service' in name:
            if state['service'] < 0.5:
                state['service'] += learning_rate
            else:
                state['trustworthiness'] -= learning_rate

        # Unity constraints
        elif 'unity_requires_detachment' in name:
            if state['detachment'] < 0.6:
                state['detachment'] += learning_rate
            else:
                state['unity'] -= learning_rate

        elif 'unity_requires_understanding' in name:
            if state['understanding'] < 0.6:
                state['understanding'] += learning_rate
            else:
                state['unity'] -= learning_rate

        # Service constraints
        elif 'service_requires_detachment' in name:
            if state['detachment'] < 0.6:
                state['detachment'] += learning_rate
            else:
                state['service'] -= learning_rate

        elif 'service_requires_understanding' in name:
            if state['understanding'] < 0.5:
                state['understanding'] += learning_rate
            else:
                state['service'] -= learning_rate

        return state

    def _clamp_state(self, state: Dict[str, float]) -> Dict[str, float]:
        """Ensure all virtue values are in [0, 1]."""
        return {k: max(0.0, min(1.0, v)) for k, v in state.items()}

    def euclidean_distance(
        self,
        state1: Dict[str, float],
        state2: Dict[str, float]
    ) -> float:
        """Calculate Euclidean distance between two virtue states."""
        virtues = self.manifold.virtues
        vec1 = np.array([state1.get(v, 0.0) for v in virtues])
        vec2 = np.array([state2.get(v, 0.0) for v in virtues])

        return float(np.linalg.norm(vec1 - vec2))
