"""
Bahá'í-derived reference manifold.

Implements the 7 core virtues and their coupling constraints:
- Truthfulness (T)
- Justice (J)
- Trustworthiness (Tr)
- Unity (U)
- Service (S)
- Detachment (D) - ego-detachment (focus on right action vs personal credit)
- Understanding (Ust)

All numeric thresholds are initial values and may be calibrated later.

NOTE: Detachment is ego-detachment, NOT outcome-detachment.
High detachment means not seeking recognition/credit, not being uncaring about results.
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


def _create_virtue_operational_constraints() -> list[Constraint]:
    """
    Create virtue-operational cross-space constraints.

    These constraints involve both virtue (7D) and operational (5D) dimensions,
    catching patterns like "high activity + low justice" that are invalid.

    NEW in spec v1.1 - addresses gap from code review.
    """
    constraints = []

    def low_justice_high_activity(state: Dict[str, float]) -> bool:
        """
        If Justice < 0.5 AND Activity > 0.7, INVALID.

        High activity with low fairness is exploitation.
        """
        justice = state.get('justice', 0.7)
        activity = state.get('activity', 0.0)

        if justice < 0.5 and activity > 0.7:
            return False
        return True

    constraints.append(Constraint(
        name="low_justice_high_activity",
        check=low_justice_high_activity,
        description="If J < 0.5 AND Activity > 0.7, INVALID (exploitation pattern)"
    ))

    def low_service_high_resource(state: Dict[str, float]) -> bool:
        """
        If Service < 0.4 AND Resource Consumption > 0.7, INVALID.

        High resource use without service is waste.
        """
        service = state.get('service', 0.7)
        resource = state.get('resource_consumption', 0.0)

        if service < 0.4 and resource > 0.7:
            return False
        return True

    constraints.append(Constraint(
        name="low_service_high_resource",
        check=low_service_high_resource,
        description="If S < 0.4 AND Resource > 0.7, INVALID (waste pattern)"
    ))

    def low_truthfulness_high_coordination(state: Dict[str, float]) -> bool:
        """
        If Truthfulness < 0.5 AND Coordination > 0.7, INVALID.

        Coordinating while dishonest is manipulation.
        """
        truthfulness = state.get('truthfulness', 0.7)
        coordination = state.get('coordination', 0.0)

        if truthfulness < 0.5 and coordination > 0.7:
            return False
        return True

    constraints.append(Constraint(
        name="low_truthfulness_high_coordination",
        check=low_truthfulness_high_coordination,
        description="If T < 0.5 AND Coordination > 0.7, INVALID (manipulation pattern)"
    ))

    def low_health_high_activity(state: Dict[str, float]) -> bool:
        """
        If System Health < 0.3 AND Activity > 0.8, INVALID.

        Pushing hard while broken causes damage.
        """
        health = state.get('system_health', 1.0)
        activity = state.get('activity', 0.0)

        if health < 0.3 and activity > 0.8:
            return False
        return True

    constraints.append(Constraint(
        name="low_health_high_activity",
        check=low_health_high_activity,
        description="If Health < 0.3 AND Activity > 0.8, INVALID (self-damage pattern)"
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

    def __init__(self, include_operational_constraints: bool = True):
        """
        Initialize the Bahá'í reference manifold.

        Args:
            include_operational_constraints: If True, include virtue-operational
                cross-space constraints (NEW in v1.1). Default True.
        """
        constraints = _create_bahai_constraints()

        # Add virtue-operational constraints (NEW in v1.1)
        if include_operational_constraints:
            constraints.extend(_create_virtue_operational_constraints())

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
