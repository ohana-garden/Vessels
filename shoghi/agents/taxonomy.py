"""
Agent class taxonomy for multi-class moral geometries.

Defines the different types of agents that can participate in community spaces,
each with distinct roles, responsibilities, and constraint surfaces.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class AgentClass(Enum):
    """
    Agent class taxonomy.

    Different classes have different moral geometries but ALL maintain
    high truthfulness standards.
    """
    COMMUNITY_SERVANT = "servant"
    COMMERCIAL_AGENT = "commercial"
    HYBRID_CONSULTANT = "hybrid"
    COMMUNITY_MEMBER = "human"


class AgentRole(Enum):
    """Specific roles agents can play within their class."""
    # Servant roles
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    FACILITATOR = "facilitator"
    KNOWLEDGE_KEEPER = "knowledge_keeper"

    # Commercial roles
    PRODUCT_REPRESENTATIVE = "product_rep"
    SERVICE_PROVIDER = "service_provider"
    BRAND_AMBASSADOR = "brand_ambassador"
    MARKETPLACE_VENDOR = "marketplace_vendor"

    # Hybrid roles
    PAID_CONSULTANT = "paid_consultant"
    COMMUNITY_ALIGNED_EXPERT = "community_expert"
    GRANT_FUNDED_SPECIALIST = "grant_specialist"


@dataclass
class AgentIdentity:
    """
    Complete agent identity with class, role, and affiliations.

    This identity must be disclosed transparently, especially for
    commercial agents.
    """
    agent_id: str
    agent_class: AgentClass
    role: AgentRole

    # For commercial/hybrid agents
    represented_entity: Optional[str] = None
    compensation_model: Optional[str] = None
    conflicts_of_interest: List[str] = None

    # Community affiliation
    community_id: Optional[str] = None

    def __post_init__(self):
        if self.conflicts_of_interest is None:
            self.conflicts_of_interest = []

    def requires_full_disclosure(self) -> bool:
        """Check if this agent class requires full commercial disclosure."""
        return self.agent_class in [
            AgentClass.COMMERCIAL_AGENT,
            AgentClass.HYBRID_CONSULTANT
        ]

    def can_access_community_knowledge(self) -> bool:
        """Check if agent can access community servant knowledge."""
        # Commercial agents CANNOT access community servant knowledge
        if self.agent_class == AgentClass.COMMERCIAL_AGENT:
            return False
        return True

    def requires_servant_introduction(self) -> bool:
        """Check if agent requires servant introduction before engaging."""
        # Commercial agents must be introduced by servants
        return self.agent_class == AgentClass.COMMERCIAL_AGENT


@dataclass
class CommercialRelationship:
    """
    Describes commercial relationships for transparency.

    Used in disclosure protocols for commercial and hybrid agents.
    """
    paid_by: str
    compensation_type: str  # "per_interaction", "per_sale", "flat_fee", "equity"
    amount_range: Optional[str] = None
    incentive_structure: Optional[str] = None

    # What the agent cannot do due to commercial ties
    cannot_recommend: List[str] = None
    cannot_criticize: List[str] = None

    # Data sharing implications
    conversation_visibility: str = "visible_to_employer"
    tracking_purpose: str = "compensation_and_metrics"

    def __post_init__(self):
        if self.cannot_recommend is None:
            self.cannot_recommend = []
        if self.cannot_criticize is None:
            self.cannot_criticize = []


@dataclass
class AgentCapabilities:
    """
    What an agent can and cannot do.

    Used for transparent disclosure of limitations, especially
    for commercial agents with biases.
    """
    expertise: List[str]
    limitations: List[str]
    cannot_do: List[str]

    # Bias declaration
    biased_toward: Optional[str] = None
    biased_against: Optional[List[str]] = None

    def __post_init__(self):
        if self.biased_against is None:
            self.biased_against = []


class ForbiddenActions:
    """
    Actions that are FORBIDDEN for specific agent classes.

    These are enforced at the system level, not just policy level.
    """

    # Commercial agents CANNOT do these
    COMMERCIAL_AGENT_FORBIDDEN = {
        "masquerade_as_servant": "Cannot pretend to be community servant",
        "access_servant_knowledge": "Cannot access community servant knowledge base",
        "write_to_community_graph": "Cannot write to community knowledge graph",
        "see_user_data_without_consent": "Cannot access user data without explicit permission",
        "contact_users_directly": "Cannot initiate contact without servant introduction",
        "suggest_without_relevance": "Cannot make suggestions below relevance threshold",
        "pressure_or_manipulate": "Cannot use manipulative persuasion tactics",
        "hide_commercial_nature": "Must always disclose commercial relationship",
        "omit_conflicts": "Must disclose all conflicts of interest",
        "claim_objectivity": "Cannot claim to be unbiased or objective",
    }

    # Community servants MUST do these
    SERVANT_RESPONSIBILITIES = {
        "introduce_commercial_agents": "Must introduce commercial agents (controls gate)",
        "disclose_commercial_nature": "Must disclose commercial nature to users",
        "provide_unbiased_alternative": "Must offer non-commercial options",
        "protect_from_manipulation": "Must protect users from manipulative tactics",
        "track_commercial_exposure": "Must track all commercial agent interactions",
        "can_override_commercial": "Can override or end commercial interactions",
        "can_end_commercial_interaction": "Can terminate problematic commercial engagement",
        "prioritize_community_interest": "Must prioritize community over commercial revenue",
    }


def validate_agent_action(
    agent_class: AgentClass,
    action: str
) -> tuple[bool, Optional[str]]:
    """
    Validate whether an agent class is allowed to perform an action.

    Returns:
        (allowed, reason) - If not allowed, reason explains why
    """
    if agent_class == AgentClass.COMMERCIAL_AGENT:
        # Check if action is in forbidden list
        if action in ForbiddenActions.COMMERCIAL_AGENT_FORBIDDEN:
            return False, ForbiddenActions.COMMERCIAL_AGENT_FORBIDDEN[action]

    return True, None
