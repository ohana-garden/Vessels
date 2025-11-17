"""
Base Manifold class for virtue constraint systems.

A manifold defines:
- The set of virtue dimensions
- Constraints that couple those dimensions
- Parent manifolds (for composition)
"""

from typing import List, Callable, Optional, Dict
from dataclasses import dataclass


@dataclass
class Constraint:
    """
    A constraint on virtue state.

    A constraint is a function that takes a virtue state dictionary
    and returns True if the state satisfies the constraint.
    """
    name: str
    check: Callable[[Dict[str, float]], bool]
    description: str = ""

    def __call__(self, state: Dict[str, float]) -> bool:
        """Check if state satisfies constraint."""
        return self.check(state)

    def __repr__(self) -> str:
        return f"Constraint('{self.name}')"


class Manifold:
    """
    Base class for virtue manifolds.

    A manifold defines a set of virtues and constraints that couple them.
    Manifolds can be composed via parent relationships.
    """

    def __init__(
        self,
        name: str,
        virtues: List[str],
        constraints: List[Constraint],
        parent: Optional['Manifold'] = None
    ):
        """
        Initialize a manifold.

        Args:
            name: Name of this manifold
            virtues: List of virtue dimension names
            constraints: List of constraints for this manifold
            parent: Optional parent manifold (for composition)
        """
        self.name = name
        self.virtues = virtues
        self.constraints = constraints
        self.parent = parent

    def validate(self, state: Dict[str, float]) -> tuple[bool, List[str]]:
        """
        Validate a virtue state against all constraints.

        Args:
            state: Dictionary mapping virtue names to values [0, 1]

        Returns:
            Tuple of (is_valid, list_of_violations)
            - is_valid: True if all constraints satisfied
            - list_of_violations: Names of violated constraints
        """
        violations = []

        # Check local constraints
        for constraint in self.constraints:
            if not constraint(state):
                violations.append(f"{self.name}.{constraint.name}")

        # Check parent constraints
        if self.parent:
            parent_valid, parent_violations = self.parent.validate(state)
            violations.extend(parent_violations)

        return len(violations) == 0, violations

    def get_all_constraints(self) -> List[Constraint]:
        """Get all constraints including those from parent manifolds."""
        constraints = list(self.constraints)
        if self.parent:
            constraints.extend(self.parent.get_all_constraints())
        return constraints

    def get_violated_constraints(self, state: Dict[str, float]) -> List[Constraint]:
        """
        Get list of constraints violated by a state.

        Args:
            state: Virtue state dictionary

        Returns:
            List of Constraint objects that are violated
        """
        violated = []

        for constraint in self.constraints:
            if not constraint(state):
                violated.append(constraint)

        if self.parent:
            violated.extend(self.parent.get_violated_constraints(state))

        return violated

    def __repr__(self) -> str:
        parent_name = self.parent.name if self.parent else "None"
        return f"Manifold('{self.name}', {len(self.virtues)} virtues, {len(self.constraints)} constraints, parent={parent_name})"
