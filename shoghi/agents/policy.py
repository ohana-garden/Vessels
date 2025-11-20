"""
Community policy controls for commercial agent participation.

Communities set their own rules for how/when commercial agents can
participate. This module defines policy structures and enforcement.

Key principle: Communities control their own spaces. Default is
conservative (commercial allowed but heavily constrained).
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CommercialCategory:
    """
    Category of commercial activity.

    Communities can allow/forbid specific categories.
    """
    name: str
    description: str
    examples: List[str]


# Predefined categories
PRODUCT_CATEGORY = CommercialCategory(
    name="products",
    description="Physical products and goods",
    examples=["Wheelchair-accessible vans", "Medical supplies", "Food delivery"]
)

SERVICE_CATEGORY = CommercialCategory(
    name="services",
    description="Service providers",
    examples=["Transportation services", "Meal delivery", "Medical care"]
)

CONSULTANT_CATEGORY = CommercialCategory(
    name="consultants",
    description="Professional consultants and experts",
    examples=["Grant writers", "Legal advisors", "Medical specialists"]
)

GIG_WORKER_CATEGORY = CommercialCategory(
    name="gig_workers",
    description="Individual gig workers and freelancers",
    examples=["Drivers", "Caregivers", "Handypersons"]
)

# Forbidden categories (predatory/extractive)
PREDATORY_LENDING_CATEGORY = CommercialCategory(
    name="predatory_lending",
    description="Predatory financial services",
    examples=["Payday loans", "High-interest credit", "Debt consolidation schemes"]
)

GAMBLING_CATEGORY = CommercialCategory(
    name="gambling",
    description="Gambling and betting services",
    examples=["Casinos", "Sports betting", "Lottery services"]
)

EXTRACTIVE_SERVICES_CATEGORY = CommercialCategory(
    name="extractive_services",
    description="Services that extract value without providing proportional benefit",
    examples=["Multi-level marketing", "Pyramid schemes", "Exploitative labor"]
)


@dataclass
class AuditRequirements:
    """Audit and transparency requirements."""
    log_all_introductions: bool = True
    log_all_interactions: bool = True
    monthly_community_review: bool = True
    user_can_review_own_exposure: bool = True
    public_revenue_reporting: bool = True
    intervention_reporting: bool = True


@dataclass
class RevocationRights:
    """Rights to revoke or block commercial agents."""
    user_can_block_specific_agents: bool = True
    user_can_block_all_commercial: bool = True
    community_can_ban_agents: bool = True
    servant_can_override_commercial: bool = True
    servant_has_priority: bool = True


@dataclass
class CommunityCommercialPolicy:
    """
    Community policy for commercial agent participation.

    Each community can set their own policy. Default is conservative:
    commercial agents allowed but with strict constraints and transparency.
    """
    community_id: str
    policy_version: str = "1.0"
    effective_date: datetime = field(default_factory=datetime.now)

    # Core permissions
    allows_commercial_agents: bool = True
    requires_individual_consent: bool = True
    requires_servant_introduction: bool = True

    # Rate limits
    max_commercial_interactions_per_user_per_day: int = 3
    max_commercial_introductions_per_servant_per_day: int = 10

    # Categories
    allowed_categories: List[str] = field(default_factory=lambda: [
        "products", "services", "consultants", "gig_workers"
    ])
    forbidden_categories: List[str] = field(default_factory=lambda: [
        "predatory_lending", "gambling", "extractive_services"
    ])

    # Quality thresholds
    min_relevance_score: float = 0.85
    max_manipulation_score: float = 0.10
    max_pressure_score: float = 0.15

    # Disclosure requirements
    requires_disclosure_upfront: bool = True
    min_disclosure_completeness: float = 0.98

    # Data and privacy
    allows_data_sharing_with_commercial: bool = False
    commercial_agent_can_write_to_graph: bool = False
    commercial_agent_can_read_community_graph: bool = False

    # Audit and transparency
    audit_requirements: AuditRequirements = field(default_factory=AuditRequirements)

    # Revocation rights
    revocation_rights: RevocationRights = field(default_factory=RevocationRights)

    # Revenue model
    commercial_revenue_to_community: bool = True
    platform_take_percentage: float = 0.0  # Platform takes NOTHING

    def is_category_allowed(self, category: str) -> bool:
        """Check if a category is allowed by this policy."""
        if category in self.forbidden_categories:
            return False
        if self.allowed_categories and category not in self.allowed_categories:
            return False
        return True

    def check_rate_limit_user(
        self,
        user_id: str,
        interaction_count_today: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded their daily commercial interaction limit.

        Returns:
            (allowed, reason) - If not allowed, reason explains why
        """
        if interaction_count_today >= self.max_commercial_interactions_per_user_per_day:
            return False, f"User has reached daily limit of {self.max_commercial_interactions_per_user_per_day} commercial interactions"
        return True, None

    def check_rate_limit_servant(
        self,
        servant_id: str,
        introduction_count_today: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if servant has exceeded their daily introduction limit.

        Returns:
            (allowed, reason) - If not allowed, reason explains why
        """
        if introduction_count_today >= self.max_commercial_introductions_per_servant_per_day:
            return False, f"Servant has reached daily limit of {self.max_commercial_introductions_per_servant_per_day} commercial introductions"
        return True, None

    def validate_agent_quality(
        self,
        relevance_score: float,
        manipulation_score: float,
        pressure_score: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that commercial agent meets quality thresholds.

        Returns:
            (valid, reason) - If not valid, reason explains why
        """
        if relevance_score < self.min_relevance_score:
            return False, f"Relevance score {relevance_score} below minimum {self.min_relevance_score}"

        if manipulation_score > self.max_manipulation_score:
            return False, f"Manipulation score {manipulation_score} above maximum {self.max_manipulation_score}"

        if pressure_score > self.max_pressure_score:
            return False, f"Pressure score {pressure_score} above maximum {self.max_pressure_score}"

        return True, None


class PolicyManager:
    """
    Manages community commercial policies.

    Stores and retrieves policies, handles policy updates with community
    governance, and enforces policy constraints.
    """

    def __init__(self, graph_client):
        """
        Initialize with graph client for policy storage.

        Args:
            graph_client: FalkorDB client for storing policies
        """
        self.graph = graph_client
        self.policy_cache: Dict[str, CommunityCommercialPolicy] = {}

    def get_policy(self, community_id: str) -> CommunityCommercialPolicy:
        """
        Get commercial policy for a community.

        Returns default policy if none is set.

        Args:
            community_id: Community to get policy for

        Returns:
            Community's commercial policy
        """
        # Check cache first
        if community_id in self.policy_cache:
            return self.policy_cache[community_id]

        # Query from graph
        policy = self._load_policy_from_graph(community_id)

        if policy is None:
            # Create default policy
            policy = self._create_default_policy(community_id)
            self._save_policy_to_graph(policy)

        # Cache it
        self.policy_cache[community_id] = policy
        return policy

    def _create_default_policy(self, community_id: str) -> CommunityCommercialPolicy:
        """
        Create default conservative policy for community.

        Returns:
            Default policy
        """
        return CommunityCommercialPolicy(
            community_id=community_id,
            # All defaults are already conservative
        )

    def _load_policy_from_graph(self, community_id: str) -> Optional[CommunityCommercialPolicy]:
        """
        Load policy from graph.

        Args:
            community_id: Community to load policy for

        Returns:
            Policy if found, None otherwise
        """
        cypher = """
        MATCH (p:CommercialPolicy {community_id: $community_id})
        RETURN p
        """

        results = self.graph.execute(cypher, {"community_id": community_id})
        result_list = list(results)

        if not result_list:
            return None

        # Convert graph node to policy object
        policy_data = result_list[0]['p']
        # Simplified - would need proper deserialization
        return self._deserialize_policy(policy_data)

    def _save_policy_to_graph(self, policy: CommunityCommercialPolicy):
        """
        Save policy to graph.

        Args:
            policy: Policy to save
        """
        cypher = """
        MERGE (p:CommercialPolicy {community_id: $community_id})
        SET p.policy_version = $version,
            p.effective_date = $effective_date,
            p.allows_commercial_agents = $allows_commercial,
            p.requires_individual_consent = $requires_consent,
            p.requires_servant_introduction = $requires_intro,
            p.max_commercial_per_user_per_day = $max_user,
            p.max_commercial_per_servant_per_day = $max_servant,
            p.allowed_categories = $allowed_cat,
            p.forbidden_categories = $forbidden_cat,
            p.min_relevance_score = $min_relevance,
            p.max_manipulation_score = $max_manipulation,
            p.max_pressure_score = $max_pressure,
            p.updated_at = datetime()

        RETURN p
        """

        self.graph.execute(cypher, {
            "community_id": policy.community_id,
            "version": policy.policy_version,
            "effective_date": policy.effective_date.isoformat(),
            "allows_commercial": policy.allows_commercial_agents,
            "requires_consent": policy.requires_individual_consent,
            "requires_intro": policy.requires_servant_introduction,
            "max_user": policy.max_commercial_interactions_per_user_per_day,
            "max_servant": policy.max_commercial_introductions_per_servant_per_day,
            "allowed_cat": policy.allowed_categories,
            "forbidden_cat": policy.forbidden_categories,
            "min_relevance": policy.min_relevance_score,
            "max_manipulation": policy.max_manipulation_score,
            "max_pressure": policy.max_pressure_score
        })

    def _deserialize_policy(self, policy_data: Dict) -> CommunityCommercialPolicy:
        """Deserialize policy from graph data."""
        # Simplified - would need proper deserialization
        return CommunityCommercialPolicy(
            community_id=policy_data.get('community_id'),
            policy_version=policy_data.get('policy_version', '1.0'),
            allows_commercial_agents=policy_data.get('allows_commercial_agents', True),
            requires_individual_consent=policy_data.get('requires_individual_consent', True),
            requires_servant_introduction=policy_data.get('requires_servant_introduction', True),
            max_commercial_interactions_per_user_per_day=policy_data.get('max_commercial_per_user_per_day', 3),
            max_commercial_introductions_per_servant_per_day=policy_data.get('max_commercial_per_servant_per_day', 10),
            allowed_categories=policy_data.get('allowed_categories', []),
            forbidden_categories=policy_data.get('forbidden_categories', []),
            min_relevance_score=policy_data.get('min_relevance_score', 0.85),
            max_manipulation_score=policy_data.get('max_manipulation_score', 0.10),
            max_pressure_score=policy_data.get('max_pressure_score', 0.15)
        )

    def update_policy(
        self,
        community_id: str,
        updated_policy: CommunityCommercialPolicy,
        approved_by: str  # Would be community governance process
    ):
        """
        Update community policy.

        In real implementation, this would require community governance
        approval (voting, consensus, etc.).

        Args:
            community_id: Community to update policy for
            updated_policy: New policy
            approved_by: Who approved this change (governance process)
        """
        # Validate it's for the right community
        if updated_policy.community_id != community_id:
            raise ValueError("Policy community_id doesn't match")

        # Save to graph
        self._save_policy_to_graph(updated_policy)

        # Update cache
        self.policy_cache[community_id] = updated_policy

        # Record policy change in audit log
        self._record_policy_change(
            community_id=community_id,
            old_version=self.policy_cache.get(community_id, {}).policy_version,
            new_version=updated_policy.policy_version,
            approved_by=approved_by
        )

    def _record_policy_change(
        self,
        community_id: str,
        old_version: str,
        new_version: str,
        approved_by: str
    ):
        """Record policy change in audit log."""
        cypher = """
        CREATE (change:PolicyChange {
            id: randomUUID(),
            community_id: $community_id,
            old_version: $old_version,
            new_version: $new_version,
            approved_by: $approved_by,
            timestamp: datetime()
        })
        RETURN change
        """

        self.graph.execute(cypher, {
            "community_id": community_id,
            "old_version": old_version,
            "new_version": new_version,
            "approved_by": approved_by
        })
