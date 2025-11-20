"""
Community commercial revenue model.

If community allows commercial agents, revenue flows TO THE COMMUNITY,
not to the platform or servants. This ensures:
1. No perverse incentives for servants to promote commercial agents
2. Community benefits from commercial activity in their space
3. Transparent accounting of all revenue
4. Community governance over revenue allocation
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class RevenueTransaction:
    """
    Record of commercial revenue transaction.

    Every commercial interaction that generates revenue is tracked
    with complete transparency.
    """
    transaction_id: str
    timestamp: datetime
    commercial_agent_id: str
    interaction_id: str
    community_id: str

    # Revenue details
    total_amount: Decimal
    currency: str
    revenue_type: str  # "per_interaction", "per_sale", "percentage", "flat_fee"

    # Allocation (all percentages must sum to 1.0)
    to_community_fund: Decimal
    to_infrastructure: Decimal
    to_servant_development: Decimal
    to_transparency_audits: Decimal
    to_platform: Decimal  # Should be 0.0
    to_servants: Decimal  # Should be 0.0

    # Metadata
    product_or_service: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        """Validate allocation sums to total."""
        total_allocated = (
            self.to_community_fund +
            self.to_infrastructure +
            self.to_servant_development +
            self.to_transparency_audits +
            self.to_platform +
            self.to_servants
        )

        if abs(total_allocated - self.total_amount) > Decimal("0.01"):
            raise ValueError(
                f"Allocation ({total_allocated}) doesn't match total ({self.total_amount})"
            )

        # Ensure platform and servants take nothing
        if self.to_platform != Decimal("0"):
            raise ValueError(f"Platform take must be 0, got {self.to_platform}")

        if self.to_servants != Decimal("0"):
            raise ValueError(f"Servant take must be 0, got {self.to_servants}")


class CommunityCommercialRevenue:
    """
    Manages commercial revenue flowing to community.

    Key principles:
    1. Platform takes NOTHING (0%)
    2. Servants take NOTHING (0%) - prevents perverse incentives
    3. All revenue goes to community-controlled funds
    4. Community votes on allocation percentages
    5. Completely transparent accounting
    """

    # Default split (can be overridden by community governance)
    DEFAULT_SPLIT = {
        "community_infrastructure": 0.60,  # 60% to servers, tools, hosting
        "servant_development": 0.20,       # 20% to improving servants (not individual pay)
        "community_fund": 0.15,            # 15% to community projects/grants
        "transparency_audits": 0.05,       # 5% to auditing commercial interactions
        "platform_take": 0.0,              # Platform takes NOTHING
        "servant_take": 0.0,               # Servants take NOTHING
    }

    def __init__(self, graph_client):
        """
        Initialize revenue manager.

        Args:
            graph_client: FalkorDB client for recording transactions
        """
        self.graph = graph_client
        self.revenue_splits: Dict[str, Dict[str, float]] = {}

    def get_revenue_split(self, community_id: str) -> Dict[str, float]:
        """
        Get revenue split for a community.

        Returns community's custom split or default.

        Args:
            community_id: Community to get split for

        Returns:
            Dictionary with revenue split percentages
        """
        if community_id in self.revenue_splits:
            return self.revenue_splits[community_id]

        # Load from graph
        split = self._load_revenue_split(community_id)

        if split is None:
            # Use default
            split = self.DEFAULT_SPLIT.copy()

        self.revenue_splits[community_id] = split
        return split

    def _load_revenue_split(self, community_id: str) -> Optional[Dict[str, float]]:
        """Load custom revenue split from graph."""
        cypher = """
        MATCH (r:RevenueSplit {community_id: $community_id})
        RETURN r
        """

        results = self.graph.execute(cypher, {"community_id": community_id})
        result_list = list(results)

        if not result_list:
            return None

        split_data = result_list[0]['r']
        return {
            "community_infrastructure": split_data.get("to_infrastructure", 0.60),
            "servant_development": split_data.get("to_servant_dev", 0.20),
            "community_fund": split_data.get("to_community", 0.15),
            "transparency_audits": split_data.get("to_audits", 0.05),
            "platform_take": 0.0,  # Always 0
            "servant_take": 0.0,   # Always 0
        }

    def record_revenue(
        self,
        commercial_agent_id: str,
        interaction_id: str,
        community_id: str,
        total_amount: float,
        currency: str = "USD",
        revenue_type: str = "per_interaction",
        product_or_service: Optional[str] = None
    ) -> RevenueTransaction:
        """
        Record commercial revenue transaction.

        Args:
            commercial_agent_id: ID of commercial agent
            interaction_id: ID of interaction that generated revenue
            community_id: Community where revenue occurred
            total_amount: Total revenue amount
            currency: Currency code
            revenue_type: Type of revenue
            product_or_service: What was sold/provided

        Returns:
            Created revenue transaction
        """
        # Get community's revenue split
        split = self.get_revenue_split(community_id)

        # Calculate allocations
        total_decimal = Decimal(str(total_amount))

        transaction = RevenueTransaction(
            transaction_id=f"rev_{datetime.now().timestamp()}",
            timestamp=datetime.now(),
            commercial_agent_id=commercial_agent_id,
            interaction_id=interaction_id,
            community_id=community_id,
            total_amount=total_decimal,
            currency=currency,
            revenue_type=revenue_type,
            to_community_fund=total_decimal * Decimal(str(split["community_fund"])),
            to_infrastructure=total_decimal * Decimal(str(split["community_infrastructure"])),
            to_servant_development=total_decimal * Decimal(str(split["servant_development"])),
            to_transparency_audits=total_decimal * Decimal(str(split["transparency_audits"])),
            to_platform=Decimal("0"),
            to_servants=Decimal("0"),
            product_or_service=product_or_service
        )

        # Record in graph
        self._record_in_graph(transaction)

        return transaction

    def _record_in_graph(self, transaction: RevenueTransaction):
        """Record revenue transaction in graph."""
        from .graph_tracking import CommercialRelationshipGraph

        graph_tracker = CommercialRelationshipGraph(self.graph)

        graph_tracker.record_revenue(
            interaction_id=transaction.interaction_id,
            amount=float(transaction.total_amount),
            currency=transaction.currency,
            revenue_type=transaction.revenue_type,
            allocated_to_community=float(transaction.to_community_fund),
            allocated_to_infrastructure=float(transaction.to_infrastructure),
            allocated_to_servants=float(transaction.to_servant_development),
            allocated_to_auditing=float(transaction.to_transparency_audits),
            timestamp=transaction.timestamp,
            community_id=transaction.community_id
        )

    def get_community_revenue_summary(
        self,
        community_id: str,
        time_window_days: int = 30
    ) -> Dict[str, any]:
        """
        Get revenue summary for community.

        Shows transparent accounting of all commercial revenue.

        Args:
            community_id: Community to get summary for
            time_window_days: How many days back to look

        Returns:
            Revenue summary
        """
        from .graph_tracking import CommercialRelationshipGraph

        graph_tracker = CommercialRelationshipGraph(self.graph)

        return graph_tracker.query_community_commercial_revenue(
            community_id=community_id,
            time_window_days=time_window_days
        )

    def update_revenue_split(
        self,
        community_id: str,
        new_split: Dict[str, float],
        approved_by: str  # Governance process
    ):
        """
        Update community's revenue split.

        Requires community governance approval.

        Args:
            community_id: Community to update
            new_split: New revenue split
            approved_by: Who approved (governance record)
        """
        # Validate new split
        self._validate_split(new_split)

        # Ensure platform and servants get nothing
        if new_split.get("platform_take", 0.0) != 0.0:
            raise ValueError("Platform take must be 0")

        if new_split.get("servant_take", 0.0) != 0.0:
            raise ValueError("Servant take must be 0")

        # Save to graph
        self._save_revenue_split(community_id, new_split, approved_by)

        # Update cache
        self.revenue_splits[community_id] = new_split

    def _validate_split(self, split: Dict[str, float]):
        """Validate that split percentages sum to 1.0."""
        total = (
            split.get("community_infrastructure", 0.0) +
            split.get("servant_development", 0.0) +
            split.get("community_fund", 0.0) +
            split.get("transparency_audits", 0.0) +
            split.get("platform_take", 0.0) +
            split.get("servant_take", 0.0)
        )

        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Revenue split must sum to 1.0, got {total}")

    def _save_revenue_split(
        self,
        community_id: str,
        split: Dict[str, float],
        approved_by: str
    ):
        """Save revenue split to graph."""
        cypher = """
        MERGE (r:RevenueSplit {community_id: $community_id})
        SET r.to_infrastructure = $to_infra,
            r.to_servant_dev = $to_servants,
            r.to_community = $to_community,
            r.to_audits = $to_audits,
            r.platform_take = 0.0,
            r.servant_take = 0.0,
            r.approved_by = $approved_by,
            r.updated_at = datetime()

        RETURN r
        """

        self.graph.execute(cypher, {
            "community_id": community_id,
            "to_infra": split.get("community_infrastructure", 0.60),
            "to_servants": split.get("servant_development", 0.20),
            "to_community": split.get("community_fund", 0.15),
            "to_audits": split.get("transparency_audits", 0.05),
            "approved_by": approved_by
        })


class RevenueTransparencyReport:
    """
    Generates transparency reports for commercial revenue.

    Communities can see exactly:
    - How much revenue was generated
    - From which commercial agents
    - How it was allocated
    - What it funded
    """

    def __init__(self, graph_client):
        self.graph = graph_client

    def generate_monthly_report(
        self,
        community_id: str,
        year: int,
        month: int
    ) -> Dict[str, any]:
        """
        Generate monthly transparency report.

        Args:
            community_id: Community to report on
            year: Year
            month: Month (1-12)

        Returns:
            Comprehensive revenue report
        """
        from .graph_tracking import CommercialRelationshipGraph

        graph_tracker = CommercialRelationshipGraph(self.graph)

        # Get revenue data
        revenue_data = graph_tracker.query_community_commercial_revenue(
            community_id=community_id,
            time_window_days=30  # Approximate month
        )

        return {
            "community_id": community_id,
            "period": f"{year}-{month:02d}",
            "revenue_summary": revenue_data,
            "allocation_breakdown": {
                "community_fund": revenue_data.get('to_community_fund', 0),
                "infrastructure": revenue_data.get('to_infrastructure', 0),
                "servant_development": revenue_data.get('to_servant_development', 0),
                "transparency_audits": revenue_data.get('to_auditing', 0),
                "platform_take": 0.0,  # Always 0
                "servant_take": 0.0,   # Always 0
            },
            "total_revenue": revenue_data.get('total_revenue', 0),
            "transaction_count": revenue_data.get('transaction_count', 0),
            "note": "Platform and servants receive 0% of commercial revenue"
        }
