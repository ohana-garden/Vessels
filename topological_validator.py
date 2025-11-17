"""
Topological Validator - Projects invalid states to the nearest valid point on the manifold.

This implements the core security property: any agent state that violates the manifold
constraints is automatically corrected, making malicious configurations geometrically
impossible.
"""

from typing import Dict, List, Tuple, Optional
import copy
import logging
from bahai_manifold import BahaiManifold


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TopologicalValidator:
    """
    Validates agent states and projects invalid states to the manifold.

    The projection algorithm prioritizes corrections based on structural importance:
    1. Truthfulness first (foundation)
    2. Justice second (hub)
    3. Trustworthiness third (bridge)
    4. Other couplings in dependency order
    """

    def __init__(self, manifold: Optional[BahaiManifold] = None, max_iterations: int = 100):
        """
        Initialize the validator.

        Args:
            manifold: BahaiManifold instance. If None, creates a new one.
            max_iterations: Maximum iterations for projection algorithm.
        """
        self.manifold = manifold or BahaiManifold()
        self.max_iterations = max_iterations

    def validate(self, state: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Check if a state is valid on the manifold.

        Args:
            state: Dictionary mapping virtue names to values in [0, 1].

        Returns:
            Tuple of (is_valid, list of violations).
        """
        return self.manifold.validate_state(state)

    def project_to_manifold(self, state: Dict[str, float],
                           correction_strategy: str = 'raise_dependencies') -> Dict[str, float]:
        """
        Project an invalid state to the nearest valid point on the manifold.

        Args:
            state: Dictionary mapping virtue names to values in [0, 1].
            correction_strategy: How to correct violations:
                - 'raise_dependencies': Raise prerequisite virtues to support high virtues
                - 'lower_dependents': Lower virtues that lack foundation
                - 'balanced': Try both and pick the one with minimal change

        Returns:
            Valid state on the manifold.
        """
        corrected_state = copy.deepcopy(state)
        initial_state = copy.deepcopy(state)

        for iteration in range(self.max_iterations):
            is_valid, violations = self.manifold.validate_state(corrected_state)

            if is_valid:
                # Calculate and log correction vector
                correction_vector = self._calculate_correction_vector(initial_state, corrected_state)
                if correction_vector:
                    logger.info(f"State projected to manifold in {iteration} iterations")
                    logger.info(f"Correction vector: {correction_vector}")
                return corrected_state

            # Apply corrections in priority order
            corrected_state = self._apply_corrections(corrected_state, violations, correction_strategy)

        # If we didn't converge, log warning and return best effort
        logger.warning(f"Projection did not converge after {self.max_iterations} iterations")
        logger.warning(f"Remaining violations: {violations}")
        return corrected_state

    def _apply_corrections(self, state: Dict[str, float], violations: List[str],
                          strategy: str) -> Dict[str, float]:
        """
        Apply corrections based on priority and strategy.

        Priority order:
        1. Truthfulness foundation violations
        2. Justice hub violations
        3. Trustworthiness bridge violations
        4. Standard coupling violations
        """
        corrected = copy.deepcopy(state)

        # Priority 1: Truthfulness foundation
        truthfulness_corrections = [v for v in violations if 'truthfulness' in v.lower()]
        if truthfulness_corrections:
            corrected = self._correct_truthfulness_violations(corrected, truthfulness_corrections, strategy)

        # Priority 2: Justice hub
        justice_corrections = [v for v in violations if 'justice' in v.lower()]
        if justice_corrections:
            corrected = self._correct_justice_violations(corrected, justice_corrections, strategy)

        # Priority 3: Trustworthiness bridge
        trustworthiness_corrections = [v for v in violations if 'trustworthiness' in v.lower()]
        if trustworthiness_corrections:
            corrected = self._correct_trustworthiness_violations(corrected, trustworthiness_corrections, strategy)

        # Priority 4: Standard couplings
        other_corrections = [v for v in violations
                            if 'truthfulness' not in v.lower()
                            and 'justice' not in v.lower()
                            and 'trustworthiness' not in v.lower()]
        if other_corrections:
            corrected = self._correct_standard_violations(corrected, other_corrections, strategy)

        return corrected

    def _correct_truthfulness_violations(self, state: Dict[str, float],
                                        violations: List[str], strategy: str) -> Dict[str, float]:
        """
        Correct truthfulness foundation violations.

        Since truthfulness is load-bearing, violations indicate either:
        - Truthfulness is too low for the virtues present (raise truthfulness)
        - Virtues are too high for truthfulness present (lower virtues)
        """
        corrected = copy.deepcopy(state)

        for violation in violations:
            # Parse violation to extract virtue and threshold
            # Format: "virtue=X > threshold requires truthfulness >= Y (got Z)"
            if '>' in violation and 'requires truthfulness' in violation:
                parts = violation.split('=')
                if len(parts) >= 2:
                    virtue = parts[0].strip()

                    # Extract required truthfulness
                    if '>=' in violation:
                        req_parts = violation.split('truthfulness >=')
                        if len(req_parts) >= 2:
                            try:
                                required = float(req_parts[1].split('(')[0].strip())

                                if strategy == 'raise_dependencies':
                                    # Raise truthfulness to support the virtue
                                    corrected['truthfulness'] = max(corrected['truthfulness'], required)
                                elif strategy == 'lower_dependents':
                                    # Lower the virtue to match truthfulness
                                    # Find the threshold this virtue should be under
                                    if corrected['truthfulness'] < 0.5:
                                        corrected[virtue] = min(corrected[virtue], 0.6)
                                    elif corrected['truthfulness'] < 0.7:
                                        corrected[virtue] = min(corrected[virtue], 0.8)
                                else:  # balanced
                                    # Try both and pick the minimal change
                                    delta_raise = required - corrected['truthfulness']
                                    current_virtue = corrected[virtue]
                                    target_virtue = 0.6 if corrected['truthfulness'] < 0.5 else 0.8
                                    delta_lower = current_virtue - target_virtue

                                    if delta_raise < delta_lower:
                                        corrected['truthfulness'] = required
                                    else:
                                        corrected[virtue] = target_virtue
                            except (ValueError, IndexError):
                                continue

        return corrected

    def _correct_justice_violations(self, state: Dict[str, float],
                                   violations: List[str], strategy: str) -> Dict[str, float]:
        """
        Correct justice hub violations.

        Justice requires both truthfulness and understanding at certain thresholds.
        """
        corrected = copy.deepcopy(state)

        if corrected['justice'] > 0.7:
            if strategy == 'raise_dependencies':
                # Raise supporting virtues
                corrected['truthfulness'] = max(corrected['truthfulness'], 0.7)
                corrected['understanding'] = max(corrected['understanding'], 0.6)
            elif strategy == 'lower_dependents':
                # Lower justice
                corrected['justice'] = min(corrected['justice'], 0.7)
            else:  # balanced
                # Calculate total change needed for each approach
                delta_raise = (max(0, 0.7 - corrected['truthfulness']) +
                             max(0, 0.6 - corrected['understanding']))
                delta_lower = corrected['justice'] - 0.7

                if delta_raise < delta_lower:
                    corrected['truthfulness'] = max(corrected['truthfulness'], 0.7)
                    corrected['understanding'] = max(corrected['understanding'], 0.6)
                else:
                    corrected['justice'] = 0.7

        return corrected

    def _correct_trustworthiness_violations(self, state: Dict[str, float],
                                          violations: List[str], strategy: str) -> Dict[str, float]:
        """
        Correct trustworthiness bridge violations.

        Trustworthiness requires both truthfulness and discipline.
        """
        corrected = copy.deepcopy(state)

        if corrected['trustworthiness'] > 0.6:
            if strategy == 'raise_dependencies':
                # Raise supporting virtues
                corrected['truthfulness'] = max(corrected['truthfulness'], 0.5)
                corrected['discipline'] = max(corrected['discipline'], 0.5)
            elif strategy == 'lower_dependents':
                # Lower trustworthiness
                corrected['trustworthiness'] = min(corrected['trustworthiness'], 0.6)
            else:  # balanced
                delta_raise = (max(0, 0.5 - corrected['truthfulness']) +
                             max(0, 0.5 - corrected['discipline']))
                delta_lower = corrected['trustworthiness'] - 0.6

                if delta_raise < delta_lower:
                    corrected['truthfulness'] = max(corrected['truthfulness'], 0.5)
                    corrected['discipline'] = max(corrected['discipline'], 0.5)
                else:
                    corrected['trustworthiness'] = 0.6

        return corrected

    def _correct_standard_violations(self, state: Dict[str, float],
                                    violations: List[str], strategy: str) -> Dict[str, float]:
        """
        Correct standard coupling violations.
        """
        corrected = copy.deepcopy(state)

        # Understanding requires Intellect
        if corrected['understanding'] > 0.7:
            if strategy == 'raise_dependencies':
                corrected['intellect'] = max(corrected['intellect'], 0.6)
            elif strategy == 'lower_dependents':
                corrected['understanding'] = min(corrected['understanding'], 0.7)

        # Understanding requires Detachment
        if corrected['understanding'] > 0.6:
            if strategy == 'raise_dependencies':
                corrected['detachment'] = max(corrected['detachment'], 0.5)
            elif strategy == 'lower_dependents':
                corrected['understanding'] = min(corrected['understanding'], 0.6)

        # Integration requires Love, Discipline, AND Intellect
        if corrected['integration'] > 0.7:
            if strategy == 'raise_dependencies':
                corrected['love'] = max(corrected['love'], 0.6)
                corrected['discipline'] = max(corrected['discipline'], 0.6)
                corrected['intellect'] = max(corrected['intellect'], 0.6)
            elif strategy == 'lower_dependents':
                corrected['integration'] = min(corrected['integration'], 0.7)

        # Detachment requires Independence
        if corrected['detachment'] > 0.6:
            if strategy == 'raise_dependencies':
                corrected['independence'] = max(corrected['independence'], 0.5)
            elif strategy == 'lower_dependents':
                corrected['detachment'] = min(corrected['detachment'], 0.6)

        # Humility requires Awe
        if corrected['humility'] > 0.6:
            if strategy == 'raise_dependencies':
                corrected['awe'] = max(corrected['awe'], 0.5)
            elif strategy == 'lower_dependents':
                corrected['humility'] = min(corrected['humility'], 0.6)

        # Yearning requires Patience
        if corrected['yearning'] > 0.6:
            if strategy == 'raise_dependencies':
                corrected['patience'] = max(corrected['patience'], 0.5)
            elif strategy == 'lower_dependents':
                corrected['yearning'] = min(corrected['yearning'], 0.6)

        return corrected

    def _calculate_correction_vector(self, initial: Dict[str, float],
                                    final: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate the correction vector from initial to final state.

        Returns:
            Dictionary of virtues that changed and their deltas.
        """
        vector = {}
        for virtue in self.manifold.ALL_VIRTUES:
            delta = final[virtue] - initial[virtue]
            if abs(delta) > 1e-6:  # Only include significant changes
                vector[virtue] = delta
        return vector

    def validate_and_correct(self, state: Dict[str, float],
                           correction_strategy: str = 'raise_dependencies',
                           log_corrections: bool = True) -> Tuple[Dict[str, float], bool]:
        """
        Validate a state and correct it if invalid.

        Args:
            state: State to validate.
            correction_strategy: How to correct violations.
            log_corrections: Whether to log corrections as security events.

        Returns:
            Tuple of (corrected_state, was_corrected).
        """
        is_valid, violations = self.validate(state)

        if is_valid:
            return state, False

        # Log security event
        if log_corrections:
            logger.warning(f"Invalid state detected. Violations: {violations}")
            logger.warning("Projecting to manifold...")

        corrected = self.project_to_manifold(state, correction_strategy)

        if log_corrections:
            correction_vector = self._calculate_correction_vector(state, corrected)
            logger.warning(f"State corrected. Changes: {correction_vector}")

        return corrected, True
