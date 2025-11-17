"""
Bahá'í-derived reference manifold.

Implements the 7 core virtues and their coupling constraints:
- Truthfulness (T)
- Justice (J)
- Trustworthiness (Tr)
- Unity (U)
- Service (S)
- Detachment (D) - ego-detachment
- Understanding (Ust)

All numeric thresholds are initial values and may be calibrated later.
"""

from typing import Dict
from .manifold import Manifold, Constraint


def _create_bahai_constraints() -> list[Constraint]:
    """
    Create the numeric coupling constraints for the Bahá'í manifold.

    These implement the constraint system from section 1.2.1 of the spec.
    """
    constraints = []

    # A. Truthfulness is load-bearing
    # High levels of any other virtue require adequate Truthfulness

    def truthfulness_required_for_high_virtues_06(state: Dict[str, float]) -> bool:
        """If any virtue > 0.6, require T >= 0.6."""
        t = state['truthfulness']
        other_virtues = ['justice', 'trustworthiness', 'unity', 'service', 'detachment', 'understanding']

        for virtue in other_virtues:
            if state[virtue] > 0.6 and t < 0.6:
                return False
        return True

    constraints.append(Constraint(
        name="truthfulness_required_06",
        check=truthfulness_required_for_high_virtues_06,
        description="If any virtue > 0.6, require T >= 0.6"
    ))

    def truthfulness_required_for_high_virtues_08(state: Dict[str, float]) -> bool:
        """If any virtue > 0.8, require T >= 0.7."""
        t = state['truthfulness']
        other_virtues = ['justice', 'trustworthiness', 'unity', 'service', 'detachment', 'understanding']

        for virtue in other_virtues:
            if state[virtue] > 0.8 and t < 0.7:
                return False
        return True

    constraints.append(Constraint(
        name="truthfulness_required_08",
        check=truthfulness_required_for_high_virtues_08,
        description="If any virtue > 0.8, require T >= 0.7"
    ))

    # B. Justice requires support

    def justice_requires_truthfulness(state: Dict[str, float]) -> bool:
        """If J > 0.7, require T >= 0.7."""
        if state['justice'] > 0.7 and state['truthfulness'] < 0.7:
            return False
        return True

    constraints.append(Constraint(
        name="justice_requires_truthfulness",
        check=justice_requires_truthfulness,
        description="If J > 0.7, require T >= 0.7"
    ))

    def justice_requires_understanding(state: Dict[str, float]) -> bool:
        """If J > 0.7, require Ust >= 0.6."""
        if state['justice'] > 0.7 and state['understanding'] < 0.6:
            return False
        return True

    constraints.append(Constraint(
        name="justice_requires_understanding",
        check=justice_requires_understanding,
        description="If J > 0.7, require Ust >= 0.6"
    ))

    # C. Trustworthiness is a bridge

    def trustworthiness_requires_truthfulness(state: Dict[str, float]) -> bool:
        """If Tr > 0.6, require T >= 0.6."""
        if state['trustworthiness'] > 0.6 and state['truthfulness'] < 0.6:
            return False
        return True

    constraints.append(Constraint(
        name="trustworthiness_requires_truthfulness",
        check=trustworthiness_requires_truthfulness,
        description="If Tr > 0.6, require T >= 0.6"
    ))

    def trustworthiness_requires_service(state: Dict[str, float]) -> bool:
        """If Tr > 0.6, require S >= 0.5."""
        if state['trustworthiness'] > 0.6 and state['service'] < 0.5:
            return False
        return True

    constraints.append(Constraint(
        name="trustworthiness_requires_service",
        check=trustworthiness_requires_service,
        description="If Tr > 0.6, require S >= 0.5"
    ))

    # D. Unity requires collaboration and humility

    def unity_requires_detachment(state: Dict[str, float]) -> bool:
        """If U > 0.7, require D >= 0.6 (ego-detachment)."""
        if state['unity'] > 0.7 and state['detachment'] < 0.6:
            return False
        return True

    constraints.append(Constraint(
        name="unity_requires_detachment",
        check=unity_requires_detachment,
        description="If U > 0.7, require D >= 0.6"
    ))

    def unity_requires_understanding(state: Dict[str, float]) -> bool:
        """If U > 0.7, require Ust >= 0.6."""
        if state['unity'] > 0.7 and state['understanding'] < 0.6:
            return False
        return True

    constraints.append(Constraint(
        name="unity_requires_understanding",
        check=unity_requires_understanding,
        description="If U > 0.7, require Ust >= 0.6"
    ))

    # E. Service requires ego-detachment and understanding

    def service_requires_detachment(state: Dict[str, float]) -> bool:
        """If S > 0.7, require D >= 0.6."""
        if state['service'] > 0.7 and state['detachment'] < 0.6:
            return False
        return True

    constraints.append(Constraint(
        name="service_requires_detachment",
        check=service_requires_detachment,
        description="If S > 0.7, require D >= 0.6"
    ))

    def service_requires_understanding(state: Dict[str, float]) -> bool:
        """If S > 0.7, require Ust >= 0.5."""
        if state['service'] > 0.7 and state['understanding'] < 0.5:
            return False
        return True

    constraints.append(Constraint(
        name="service_requires_understanding",
        check=service_requires_understanding,
        description="If S > 0.7, require Ust >= 0.5"
    ))

    return constraints


class BahaiManifold(Manifold):
    """
    Bahá'í-derived reference manifold.

    This is the universal reference manifold that all other manifolds
    should extend (not replace).

    The 7 core virtues and their couplings are explicit normative choices,
    not culturally neutral.
    """

    VIRTUES = [
        'truthfulness',
        'justice',
        'trustworthiness',
        'unity',
        'service',
        'detachment',
        'understanding'
    ]

    def __init__(self):
        """Initialize the Bahá'í reference manifold."""
        constraints = _create_bahai_constraints()

        super().__init__(
            name="BahaiReference",
            virtues=self.VIRTUES,
            constraints=constraints,
            parent=None
        )

    @classmethod
    def create_default_state(cls) -> Dict[str, float]:
        """Create a default neutral virtue state."""
        return {virtue: 0.7 for virtue in cls.VIRTUES}

    @classmethod
    def create_state_dict(
        cls,
        truthfulness: float = 0.7,
        justice: float = 0.7,
        trustworthiness: float = 0.7,
        unity: float = 0.7,
        service: float = 0.7,
        detachment: float = 0.7,
        understanding: float = 0.7
    ) -> Dict[str, float]:
        """Create a virtue state dictionary with explicit values."""
        return {
            'truthfulness': truthfulness,
            'justice': justice,
            'trustworthiness': trustworthiness,
            'unity': unity,
            'service': service,
            'detachment': detachment,
            'understanding': understanding
        }
