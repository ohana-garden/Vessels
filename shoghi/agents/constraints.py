"""
Class-specific constraint surfaces for multi-class agents.

Each agent class has different moral geometry while maintaining
universal high truthfulness standards.

Key insight: Truthfulness is NON-NEGOTIABLE across all classes.
Service/extraction ratios vary by class with radical transparency.
"""

from typing import Dict, List
from dataclasses import dataclass
from ..constraints.manifold import Manifold, Constraint
from ..constraints.bahai import BahaiManifold
from .taxonomy import AgentClass


@dataclass
class VirtueSpaceRegion:
    """
    Defines the allowed region in virtue space for an agent class.

    Each virtue has a [min, max] range that the agent must stay within.
    """
    truthfulness: tuple[float, float]
    justice: tuple[float, float]
    service: tuple[float, float]
    unity: tuple[float, float]
    trustworthiness: tuple[float, float]
    detachment: tuple[float, float]
    understanding: tuple[float, float]


class ServantConstraints:
    """
    Community Servant constraints (original high standards).

    Community servants are held to the highest standards because they
    hold positions of trust and power within the community.
    """

    # Virtue space region - very high standards
    VIRTUE_REGION = VirtueSpaceRegion(
        truthfulness=(0.95, 1.0),  # NON-NEGOTIABLE high
        justice=(0.80, 1.0),
        service=(0.85, 1.0),  # Very high service orientation
        unity=(0.80, 1.0),
        trustworthiness=(0.85, 1.0),
        detachment=(0.75, 1.0),
        understanding=(0.80, 1.0)
    )

    # Operational constraints
    MIN_TRUTHFULNESS = 0.95
    MIN_SERVICE_RATIO = 0.90  # 90% service, max 10% extraction
    MAX_EXTRACTION = 0.05  # Very low extraction allowed
    MIN_CONSENT = 0.90
    MAX_CROSS_SERVANT_SHARING_WITHOUT_CONSENT = 0.0  # Zero tolerance
    MIN_CULTURAL_ALIGNMENT = 0.85

    # Identity and disclosure
    IDENTITY_DISCLOSURE = "REQUIRED_UPFRONT"
    CONFLICTS_OF_INTEREST = "NONE_PERMITTED"
    COMMERCIAL_RELATIONSHIPS = "NONE_PERMITTED"

    @classmethod
    def create_manifold(cls, base_manifold: BahaiManifold) -> Manifold:
        """
        Create servant-specific manifold by extending base Bahá'í manifold.

        Adds additional constraints for high service standards.
        """
        constraints = []

        # High service requirement
        def high_service_required(state: Dict[str, float]) -> bool:
            """Community servants must maintain high service levels."""
            return state.get('service', 0.0) >= cls.MIN_SERVICE_RATIO

        constraints.append(Constraint(
            name="servant_high_service",
            check=high_service_required,
            description=f"Community servants must maintain service >= {cls.MIN_SERVICE_RATIO}"
        ))

        # Very high truthfulness requirement
        def very_high_truthfulness_required(state: Dict[str, float]) -> bool:
            """Community servants must maintain very high truthfulness."""
            return state.get('truthfulness', 0.0) >= cls.MIN_TRUTHFULNESS

        constraints.append(Constraint(
            name="servant_very_high_truthfulness",
            check=very_high_truthfulness_required,
            description=f"Community servants must maintain truthfulness >= {cls.MIN_TRUTHFULNESS}"
        ))

        # Extraction limit
        def low_extraction_required(state: Dict[str, float]) -> bool:
            """Community servants must have very low extraction."""
            extraction = state.get('extraction', 0.0)
            return extraction <= cls.MAX_EXTRACTION

        constraints.append(Constraint(
            name="servant_low_extraction",
            check=low_extraction_required,
            description=f"Community servants must maintain extraction <= {cls.MAX_EXTRACTION}"
        ))

        return Manifold(
            name="CommunityServant",
            virtues=base_manifold.virtues,
            constraints=base_manifold.constraints + constraints,
            parent=base_manifold
        )


class CommercialAgentConstraints:
    """
    Commercial Agent constraints (different standards, maximum transparency).

    Commercial agents represent external commercial interests. They are allowed
    to operate with different service/extraction ratios BUT must maintain:
    1. High truthfulness (non-negotiable)
    2. RADICAL transparency about commercial nature
    3. Complete disclosure of conflicts and compensation
    4. Cannot manipulate or pressure
    """

    # Virtue space region - truthfulness still very high
    VIRTUE_REGION = VirtueSpaceRegion(
        truthfulness=(0.95, 1.0),  # NON-NEGOTIABLE (same as servants)
        justice=(0.70, 0.90),  # Must still be fair
        service=(0.60, 0.85),  # Lower - mixed service/commercial
        unity=(0.60, 0.85),  # Lower - not community-owned
        trustworthiness=(0.70, 0.90),
        detachment=(0.60, 0.85),
        understanding=(0.70, 0.90)
    )

    # Truth standard REMAINS HIGH
    MIN_TRUTHFULNESS = 0.95  # Non-negotiable
    MIN_DISCLOSURE_COMPLETENESS = 0.98  # Even higher - must disclose EVERYTHING

    # Service/extraction DIFFERENT
    MIN_SERVICE_RATIO = 0.60  # Lower - they're paid to advocate
    MAX_EXTRACTION = 0.40  # Higher - commercial relationship expected

    # Identity/conflicts RADICAL TRANSPARENCY
    IDENTITY_DISCLOSURE = "REQUIRED_IMMEDIATELY"
    COMMERCIAL_RELATIONSHIP_DISCLOSURE = "REQUIRED_UPFRONT"
    COMPENSATION_DISCLOSURE = "REQUIRED_UPFRONT"
    CONFLICTS_OF_INTEREST_DISCLOSURE = "REQUIRED_COMPLETE"

    # Consent EVEN HIGHER
    MIN_CONSENT_TO_PARTICIPATE = 0.95  # Community must explicitly allow
    MIN_INDIVIDUAL_CONSENT = 0.90  # Individual must want commercial input

    # Behavioral constraints
    MAX_UNSOLICITED_SUGGESTIONS = 0.05  # Can't cold-pitch
    MIN_RELEVANCE_TO_QUERY = 0.85  # Must be directly relevant
    MAX_MANIPULATION_SCORE = 0.10  # Low tolerance for manipulation
    MAX_PERSUASION_PRESSURE = 0.15  # Can inform, not pressure

    # Cultural respect STILL HIGH
    MIN_CULTURAL_ALIGNMENT = 0.75  # Slightly lower but still significant

    @classmethod
    def create_manifold(cls, base_manifold: BahaiManifold) -> Manifold:
        """
        Create commercial agent manifold.

        Different service/extraction but SAME truthfulness standards.
        """
        constraints = []

        # Truthfulness STILL very high
        def very_high_truthfulness_required(state: Dict[str, float]) -> bool:
            """Commercial agents MUST maintain very high truthfulness."""
            return state.get('truthfulness', 0.0) >= cls.MIN_TRUTHFULNESS

        constraints.append(Constraint(
            name="commercial_very_high_truthfulness",
            check=very_high_truthfulness_required,
            description=f"Commercial agents MUST maintain truthfulness >= {cls.MIN_TRUTHFULNESS}"
        ))

        # Disclosure completeness
        def complete_disclosure_required(state: Dict[str, float]) -> bool:
            """Commercial agents must have complete disclosure."""
            disclosure = state.get('disclosure_completeness', 0.0)
            return disclosure >= cls.MIN_DISCLOSURE_COMPLETENESS

        constraints.append(Constraint(
            name="commercial_complete_disclosure",
            check=complete_disclosure_required,
            description=f"Commercial agents must maintain disclosure >= {cls.MIN_DISCLOSURE_COMPLETENESS}"
        ))

        # Manipulation forbidden
        def no_manipulation_allowed(state: Dict[str, float]) -> bool:
            """Commercial agents cannot manipulate."""
            manipulation = state.get('manipulation_score', 0.0)
            return manipulation <= cls.MAX_MANIPULATION_SCORE

        constraints.append(Constraint(
            name="commercial_no_manipulation",
            check=no_manipulation_allowed,
            description=f"Commercial agents must maintain manipulation <= {cls.MAX_MANIPULATION_SCORE}"
        ))

        # Relevance requirement
        def high_relevance_required(state: Dict[str, float]) -> bool:
            """Commercial agents must be highly relevant."""
            relevance = state.get('relevance_score', 0.0)
            return relevance >= cls.MIN_RELEVANCE_TO_QUERY

        constraints.append(Constraint(
            name="commercial_high_relevance",
            check=high_relevance_required,
            description=f"Commercial agents must maintain relevance >= {cls.MIN_RELEVANCE_TO_QUERY}"
        ))

        # Consent requirement
        def explicit_consent_required(state: Dict[str, float]) -> bool:
            """Commercial agents require explicit individual consent."""
            consent = state.get('individual_consent', 0.0)
            return consent >= cls.MIN_INDIVIDUAL_CONSENT

        constraints.append(Constraint(
            name="commercial_explicit_consent",
            check=explicit_consent_required,
            description=f"Commercial agents require consent >= {cls.MIN_INDIVIDUAL_CONSENT}"
        ))

        return Manifold(
            name="CommercialAgent",
            virtues=base_manifold.virtues,
            constraints=base_manifold.constraints + constraints,
            parent=base_manifold
        )


class HybridConsultantConstraints:
    """
    Hybrid Consultant constraints (paid but community-aligned).

    Hybrid consultants are paid for expertise but remain aligned with
    community values. They have constraints between servants and commercial.

    Examples: Grant-funded specialists, community-hired consultants,
    pro-bono professionals with partial compensation.
    """

    # Virtue space region - between servant and commercial
    VIRTUE_REGION = VirtueSpaceRegion(
        truthfulness=(0.95, 1.0),  # Still non-negotiable
        justice=(0.75, 0.95),
        service=(0.70, 0.95),
        unity=(0.70, 0.95),
        trustworthiness=(0.75, 0.95),
        detachment=(0.70, 0.90),
        understanding=(0.75, 0.95)
    )

    MIN_TRUTHFULNESS = 0.95  # Still non-negotiable
    MIN_SERVICE_RATIO = 0.75  # Between servant and commercial
    MAX_EXTRACTION = 0.25  # Moderate - paid for expertise

    IDENTITY_DISCLOSURE = "REQUIRED_UPFRONT"
    COMPENSATION_DISCLOSURE = "REQUIRED_UPFRONT"
    CONFLICTS_OF_INTEREST_DISCLOSURE = "REQUIRED_COMPLETE"

    MIN_CONSENT = 0.90
    MIN_CULTURAL_ALIGNMENT = 0.80

    @classmethod
    def create_manifold(cls, base_manifold: BahaiManifold) -> Manifold:
        """
        Create hybrid consultant manifold.

        Balanced between servant and commercial.
        """
        constraints = []

        # High truthfulness still required
        def very_high_truthfulness_required(state: Dict[str, float]) -> bool:
            """Hybrid consultants must maintain very high truthfulness."""
            return state.get('truthfulness', 0.0) >= cls.MIN_TRUTHFULNESS

        constraints.append(Constraint(
            name="hybrid_very_high_truthfulness",
            check=very_high_truthfulness_required,
            description=f"Hybrid consultants must maintain truthfulness >= {cls.MIN_TRUTHFULNESS}"
        ))

        # Balanced service requirement
        def high_service_required(state: Dict[str, float]) -> bool:
            """Hybrid consultants must maintain high service levels."""
            return state.get('service', 0.0) >= cls.MIN_SERVICE_RATIO

        constraints.append(Constraint(
            name="hybrid_high_service",
            check=high_service_required,
            description=f"Hybrid consultants must maintain service >= {cls.MIN_SERVICE_RATIO}"
        ))

        # Moderate extraction limit
        def moderate_extraction_limit(state: Dict[str, float]) -> bool:
            """Hybrid consultants have moderate extraction limits."""
            extraction = state.get('extraction', 0.0)
            return extraction <= cls.MAX_EXTRACTION

        constraints.append(Constraint(
            name="hybrid_moderate_extraction",
            check=moderate_extraction_limit,
            description=f"Hybrid consultants must maintain extraction <= {cls.MAX_EXTRACTION}"
        ))

        return Manifold(
            name="HybridConsultant",
            virtues=base_manifold.virtues,
            constraints=base_manifold.constraints + constraints,
            parent=base_manifold
        )


def get_constraints_for_class(
    agent_class: AgentClass,
    base_manifold: BahaiManifold
) -> Manifold:
    """
    Get the appropriate constraint manifold for an agent class.

    Args:
        agent_class: The class of agent
        base_manifold: Base Bahá'í manifold to extend

    Returns:
        Class-specific manifold with appropriate constraints
    """
    if agent_class == AgentClass.COMMUNITY_SERVANT:
        return ServantConstraints.create_manifold(base_manifold)
    elif agent_class == AgentClass.COMMERCIAL_AGENT:
        return CommercialAgentConstraints.create_manifold(base_manifold)
    elif agent_class == AgentClass.HYBRID_CONSULTANT:
        return HybridConsultantConstraints.create_manifold(base_manifold)
    else:
        # Community members use base manifold
        return base_manifold


def get_constraint_summary(agent_class: AgentClass) -> Dict[str, any]:
    """
    Get a human-readable summary of constraints for an agent class.

    Useful for disclosure and transparency.
    """
    if agent_class == AgentClass.COMMUNITY_SERVANT:
        return {
            "truthfulness": f">= {ServantConstraints.MIN_TRUTHFULNESS}",
            "service_ratio": f">= {ServantConstraints.MIN_SERVICE_RATIO}",
            "max_extraction": f"<= {ServantConstraints.MAX_EXTRACTION}",
            "commercial_ties": "NONE PERMITTED",
            "disclosure": ServantConstraints.IDENTITY_DISCLOSURE,
            "virtue_region": ServantConstraints.VIRTUE_REGION
        }
    elif agent_class == AgentClass.COMMERCIAL_AGENT:
        return {
            "truthfulness": f">= {CommercialAgentConstraints.MIN_TRUTHFULNESS} (NON-NEGOTIABLE)",
            "disclosure": f">= {CommercialAgentConstraints.MIN_DISCLOSURE_COMPLETENESS}",
            "service_ratio": f">= {CommercialAgentConstraints.MIN_SERVICE_RATIO}",
            "max_extraction": f"<= {CommercialAgentConstraints.MAX_EXTRACTION}",
            "max_manipulation": f"<= {CommercialAgentConstraints.MAX_MANIPULATION_SCORE}",
            "min_relevance": f">= {CommercialAgentConstraints.MIN_RELEVANCE_TO_QUERY}",
            "requires_consent": f">= {CommercialAgentConstraints.MIN_INDIVIDUAL_CONSENT}",
            "commercial_ties": "MUST FULLY DISCLOSE",
            "virtue_region": CommercialAgentConstraints.VIRTUE_REGION
        }
    elif agent_class == AgentClass.HYBRID_CONSULTANT:
        return {
            "truthfulness": f">= {HybridConsultantConstraints.MIN_TRUTHFULNESS}",
            "service_ratio": f">= {HybridConsultantConstraints.MIN_SERVICE_RATIO}",
            "max_extraction": f"<= {HybridConsultantConstraints.MAX_EXTRACTION}",
            "commercial_ties": "MUST DISCLOSE COMPENSATION",
            "disclosure": HybridConsultantConstraints.IDENTITY_DISCLOSURE,
            "virtue_region": HybridConsultantConstraints.VIRTUE_REGION
        }
    else:
        return {
            "class": "Community member",
            "note": "Uses base Bahá'í manifold constraints"
        }
