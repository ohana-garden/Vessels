"""
Bahá'í Moral Manifold - A 14-dimensional Riemannian manifold for topological security.

This module implements a virtue-based manifold where malicious agent configurations
are geometrically impossible rather than explicitly forbidden. The hierarchy emerges
from coupling constraints (topology) rather than weighted metrics.
"""

from typing import Dict, List, Tuple
import copy


class BahaiManifold:
    """
    A 14-dimensional manifold with threshold-based coupling constraints.

    The manifold encodes three types of structural importance:
    - Truthfulness: Load-bearing foundation - other virtues collapse without it
    - Justice: Hub node - highest coupling connectivity creates natural stability
    - Trustworthiness: Bridge - connects personal spiritual development to social action

    All other virtues have standard coupling constraints that create the manifold topology.
    """

    # Seven Valleys virtues
    SEVEN_VALLEYS = ['patience', 'yearning', 'understanding', 'detachment',
                     'independence', 'awe', 'humility']

    # Four Valleys virtues
    FOUR_VALLEYS = ['discipline', 'intellect', 'love', 'integration']

    # Hierarchical virtues from Bahá'í writings
    HIERARCHICAL = ['justice', 'truthfulness', 'trustworthiness']

    # All 14 dimensions
    ALL_VIRTUES = SEVEN_VALLEYS + FOUR_VALLEYS + HIERARCHICAL

    def __init__(self):
        """Initialize the manifold structure."""
        self.dimensions = self.ALL_VIRTUES
        self.num_dimensions = len(self.dimensions)

    def create_state(self, **kwargs) -> Dict[str, float]:
        """
        Create a state vector with all 14 dimensions.

        Args:
            **kwargs: Virtue names and values (0-1). Unspecified virtues default to 0.5.

        Returns:
            Dictionary mapping virtue names to values in [0, 1].
        """
        state = {virtue: 0.5 for virtue in self.ALL_VIRTUES}

        for virtue, value in kwargs.items():
            if virtue not in self.ALL_VIRTUES:
                raise ValueError(f"Unknown virtue: {virtue}")
            if not 0 <= value <= 1:
                raise ValueError(f"Value for {virtue} must be in [0, 1], got {value}")
            state[virtue] = value

        return state

    def validate_state(self, state: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Check if a state satisfies all manifold constraints.

        Args:
            state: Dictionary mapping virtue names to values in [0, 1].

        Returns:
            Tuple of (is_valid, list of violated constraints).
        """
        violations = []

        # Check all virtues present and in valid range
        for virtue in self.ALL_VIRTUES:
            if virtue not in state:
                violations.append(f"Missing virtue: {virtue}")
            elif not 0 <= state[virtue] <= 1:
                violations.append(f"{virtue} out of range [0,1]: {state[virtue]}")

        if violations:
            return False, violations

        # 1. Truthfulness as foundational (load-bearing dimension)
        truthfulness_violations = self._validate_truthfulness_foundation(state)
        violations.extend(truthfulness_violations)

        # 2. Justice as highest (hub node with maximum coupling)
        justice_violations = self._validate_justice_constraints(state)
        violations.extend(justice_violations)

        # 3. Trustworthiness as bridge (connects personal to social virtues)
        trustworthiness_violations = self._validate_trustworthiness_bridge(state)
        violations.extend(trustworthiness_violations)

        # 4. Standard coupling constraints
        standard_violations = self._validate_standard_couplings(state)
        violations.extend(standard_violations)

        return len(violations) == 0, violations

    def _validate_truthfulness_foundation(self, state: Dict[str, float]) -> List[str]:
        """
        Truthfulness is load-bearing - other virtues cannot exist at high levels without it.

        This creates the foundational constraint that prevents manipulation,
        as deception (low truthfulness) geometrically excludes high virtue states.
        """
        violations = []

        for virtue, value in state.items():
            if virtue == 'truthfulness':
                continue

            # Cannot maintain moderate virtue without truthfulness foundation
            if value > 0.6 and state['truthfulness'] < 0.5:
                violations.append(
                    f"{virtue}={value:.2f} > 0.6 requires truthfulness >= 0.5 "
                    f"(got {state['truthfulness']:.2f})"
                )

            # Cannot maintain high virtue without strong truthfulness
            if value > 0.8 and state['truthfulness'] < 0.7:
                violations.append(
                    f"{virtue}={value:.2f} > 0.8 requires truthfulness >= 0.7 "
                    f"(got {state['truthfulness']:.2f})"
                )

        return violations

    def _validate_justice_constraints(self, state: Dict[str, float]) -> List[str]:
        """
        Justice is the hub - it has maximum coupling connectivity.

        High justice requires both honest knowledge (truthfulness + understanding)
        and creates a naturally stable attractor due to high coupling density.
        """
        violations = []

        if state['justice'] > 0.7:
            if state['truthfulness'] < 0.7:
                violations.append(
                    f"justice={state['justice']:.2f} > 0.7 requires truthfulness >= 0.7 "
                    f"(got {state['truthfulness']:.2f})"
                )
            if state['understanding'] < 0.6:
                violations.append(
                    f"justice={state['justice']:.2f} > 0.7 requires understanding >= 0.6 "
                    f"(got {state['understanding']:.2f})"
                )

        return violations

    def _validate_trustworthiness_bridge(self, state: Dict[str, float]) -> List[str]:
        """
        Trustworthiness bridges personal spiritual development to social action.

        It requires both truthfulness (foundation) and discipline (consistent practice).
        """
        violations = []

        if state['trustworthiness'] > 0.6:
            if state['truthfulness'] < 0.5:
                violations.append(
                    f"trustworthiness={state['trustworthiness']:.2f} > 0.6 requires "
                    f"truthfulness >= 0.5 (got {state['truthfulness']:.2f})"
                )
            if state['discipline'] < 0.5:
                violations.append(
                    f"trustworthiness={state['trustworthiness']:.2f} > 0.6 requires "
                    f"discipline >= 0.5 (got {state['discipline']:.2f})"
                )

        return violations

    def _validate_standard_couplings(self, state: Dict[str, float]) -> List[str]:
        """
        Standard coupling constraints between virtues.

        These create the basic topology of the manifold, establishing
        dependencies between related virtues.
        """
        violations = []

        # Understanding requires Intellect
        if state['understanding'] > 0.7 and state['intellect'] < 0.6:
            violations.append(
                f"understanding={state['understanding']:.2f} > 0.7 requires "
                f"intellect >= 0.6 (got {state['intellect']:.2f})"
            )

        # Integration requires Love, Discipline, AND Intellect (it integrates them)
        if state['integration'] > 0.7:
            if state['love'] < 0.6:
                violations.append(
                    f"integration={state['integration']:.2f} > 0.7 requires "
                    f"love >= 0.6 (got {state['love']:.2f})"
                )
            if state['discipline'] < 0.6:
                violations.append(
                    f"integration={state['integration']:.2f} > 0.7 requires "
                    f"discipline >= 0.6 (got {state['discipline']:.2f})"
                )
            if state['intellect'] < 0.6:
                violations.append(
                    f"integration={state['integration']:.2f} > 0.7 requires "
                    f"intellect >= 0.6 (got {state['intellect']:.2f})"
                )

        # Detachment requires Independence
        if state['detachment'] > 0.6 and state['independence'] < 0.5:
            violations.append(
                f"detachment={state['detachment']:.2f} > 0.6 requires "
                f"independence >= 0.5 (got {state['independence']:.2f})"
            )

        # Humility requires Awe
        if state['humility'] > 0.6 and state['awe'] < 0.5:
            violations.append(
                f"humility={state['humility']:.2f} > 0.6 requires "
                f"awe >= 0.5 (got {state['awe']:.2f})"
            )

        # Yearning requires Patience
        if state['yearning'] > 0.6 and state['patience'] < 0.5:
            violations.append(
                f"yearning={state['yearning']:.2f} > 0.6 requires "
                f"patience >= 0.5 (got {state['patience']:.2f})"
            )

        # Understanding requires Detachment (to see clearly)
        if state['understanding'] > 0.6 and state['detachment'] < 0.5:
            violations.append(
                f"understanding={state['understanding']:.2f} > 0.6 requires "
                f"detachment >= 0.5 (got {state['detachment']:.2f})"
            )

        return violations

    def get_coupling_graph(self) -> Dict[str, List[str]]:
        """
        Get the coupling graph showing which virtues depend on which.

        Returns:
            Dictionary mapping each virtue to its dependencies.
        """
        # Note: All virtues depend on truthfulness (foundational)
        # This shows the direct coupling constraints beyond truthfulness

        return {
            'truthfulness': [],  # Foundation - no dependencies
            'justice': ['truthfulness', 'understanding'],  # Hub - connects to foundation and understanding
            'trustworthiness': ['truthfulness', 'discipline'],  # Bridge - personal to social
            'understanding': ['intellect', 'detachment'],
            'integration': ['love', 'discipline', 'intellect'],
            'detachment': ['independence'],
            'humility': ['awe'],
            'yearning': ['patience'],
            'patience': [],
            'independence': [],
            'awe': [],
            'discipline': [],
            'intellect': [],
            'love': [],
        }

    def __repr__(self):
        return f"BahaiManifold(dimensions={self.num_dimensions})"
