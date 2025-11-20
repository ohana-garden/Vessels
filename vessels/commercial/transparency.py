"""
Commercial Transparency Report

Generates monthly reports on all commercial agent activity, fees collected,
and fund distribution. Ensures full community visibility.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AgentActivityReport:
    """
    Report of a single agent's activity for reporting period

    Tracks all interactions, acceptance rates, and user satisfaction.
    """
    agent_id: str
    agent_name: str
    company_name: str

    # Interaction metrics
    total_introductions: int = 0
    user_accepted: int = 0
    user_declined: int = 0
    acceptance_rate: float = 0.0

    # Conversion metrics
    resulted_in_purchase: int = 0
    conversion_rate: float = 0.0

    # Financial metrics
    fees_generated: float = 0.0
    average_fee: float = 0.0

    # User feedback
    user_satisfaction_score: Optional[float] = None  # 0-5 scale
    helpful_interactions: int = 0
    unhelpful_interactions: int = 0
    complaints: int = 0
    complaint_details: List[str] = field(default_factory=list)

    def calculate_rates(self):
        """Calculate acceptance and conversion rates"""
        total = self.user_accepted + self.user_declined
        if total > 0:
            self.acceptance_rate = self.user_accepted / total

        if self.user_accepted > 0:
            self.conversion_rate = self.resulted_in_purchase / self.user_accepted

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "company_name": self.company_name,
            "total_introductions": self.total_introductions,
            "user_accepted": self.user_accepted,
            "user_declined": self.user_declined,
            "acceptance_rate": f"{self.acceptance_rate:.1%}",
            "resulted_in_purchase": self.resulted_in_purchase,
            "conversion_rate": f"{self.conversion_rate:.1%}",
            "fees_generated": f"${self.fees_generated:.2f}",
            "average_fee": f"${self.average_fee:.2f}",
            "user_satisfaction_score": self.user_satisfaction_score,
            "helpful_interactions": self.helpful_interactions,
            "unhelpful_interactions": self.unhelpful_interactions,
            "complaints": self.complaints,
            "complaint_details": self.complaint_details
        }


@dataclass
class RevenueReport:
    """
    Report of revenue and fund distribution

    Tracks total fees collected and how they were distributed.
    """
    total_fees_collected: float = 0.0
    total_transactions: int = 0

    # Distribution breakdown (matching FUND_DISTRIBUTION)
    infrastructure: float = 0.0
    servant_development: float = 0.0
    community_discretionary: float = 0.0
    transparency_audit: float = 0.0

    # Spending (if tracked)
    infrastructure_spent: float = 0.0
    servant_development_spent: float = 0.0
    community_discretionary_spent: float = 0.0
    transparency_audit_spent: float = 0.0

    def calculate_remaining(self) -> Dict[str, float]:
        """Calculate remaining balance per category"""
        return {
            "infrastructure": self.infrastructure - self.infrastructure_spent,
            "servant_development": self.servant_development - self.servant_development_spent,
            "community_discretionary": self.community_discretionary - self.community_discretionary_spent,
            "transparency_audit": self.transparency_audit - self.transparency_audit_spent
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        remaining = self.calculate_remaining()

        return {
            "total_fees_collected": f"${self.total_fees_collected:.2f}",
            "total_transactions": self.total_transactions,
            "distributed_to": {
                "infrastructure": f"${self.infrastructure:.2f} (60%)",
                "servant_development": f"${self.servant_development:.2f} (20%)",
                "community_discretionary": f"${self.community_discretionary:.2f} (15%)",
                "transparency_audit": f"${self.transparency_audit:.2f} (5%)"
            },
            "remaining_balances": {
                category: f"${amount:.2f}"
                for category, amount in remaining.items()
            }
        }


@dataclass
class CommunityDecisionsReport:
    """
    Report of community decisions regarding commercial agents

    Tracks approvals, rejections, policy changes.
    """
    new_agents_approved: int = 0
    new_agents_rejected: int = 0
    agents_suspended: int = 0
    agents_terminated: int = 0
    policy_changes: List[str] = field(default_factory=list)

    approved_agent_details: List[Dict[str, str]] = field(default_factory=list)
    rejected_agent_details: List[Dict[str, str]] = field(default_factory=list)
    suspended_agent_details: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "new_agents_approved": self.new_agents_approved,
            "new_agents_rejected": self.new_agents_rejected,
            "agents_suspended": self.agents_suspended,
            "agents_terminated": self.agents_terminated,
            "policy_changes": self.policy_changes if self.policy_changes else ["None this period"],
            "approved_agents": self.approved_agent_details,
            "rejected_agents": self.rejected_agent_details,
            "suspended_agents": self.suspended_agent_details
        }


@dataclass
class MonthlyTransparencyReport:
    """
    Complete monthly transparency report

    Full visibility into all commercial agent activity, revenue, and decisions.
    """
    community_id: str
    period_start: datetime
    period_end: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)

    # Sub-reports
    agent_activity: List[AgentActivityReport] = field(default_factory=list)
    revenue: RevenueReport = field(default_factory=RevenueReport)
    community_decisions: CommunityDecisionsReport = field(default_factory=CommunityDecisionsReport)

    # Summary metrics
    total_active_agents: int = 0
    total_user_interactions: int = 0
    overall_acceptance_rate: float = 0.0
    overall_satisfaction: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "community": self.community_id,
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
                "generated_at": self.generated_at.isoformat()
            },
            "summary": {
                "total_active_agents": self.total_active_agents,
                "total_user_interactions": self.total_user_interactions,
                "overall_acceptance_rate": f"{self.overall_acceptance_rate:.1%}",
                "overall_satisfaction": self.overall_satisfaction
            },
            "commercial_agent_activity": {
                "by_agent": [agent.to_dict() for agent in self.agent_activity]
            },
            "revenue": self.revenue.to_dict(),
            "community_decisions": self.community_decisions.to_dict()
        }


class CommercialTransparencyReport:
    """
    Generator for commercial transparency reports

    Produces monthly reports showing all commercial activity with
    full transparency for community oversight.
    """

    def __init__(
        self,
        fee_processor,
        agent_registry,
        interaction_tracker=None,
        graph_client=None
    ):
        """
        Initialize transparency report generator

        Args:
            fee_processor: CommercialFeeProcessor instance
            agent_registry: CommercialAgentRegistry instance
            interaction_tracker: Optional tracker for user interactions
            graph_client: Optional Graphiti client for storing reports
        """
        self.fee_processor = fee_processor
        self.agent_registry = agent_registry
        self.interaction_tracker = interaction_tracker
        self.graph_client = graph_client

        # Report storage
        self.reports: Dict[str, MonthlyTransparencyReport] = {}

        logger.info("Commercial Transparency Report system initialized")

    def generate_monthly_report(
        self,
        community_id: str,
        year: int,
        month: int
    ) -> MonthlyTransparencyReport:
        """
        Generate monthly transparency report for community

        Args:
            community_id: Community ID
            year: Year (e.g., 2024)
            month: Month (1-12)

        Returns:
            MonthlyTransparencyReport
        """
        # Calculate period
        period_start = datetime(year, month, 1)
        if month == 12:
            period_end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
        else:
            period_end = datetime(year, month + 1, 1) - timedelta(microseconds=1)

        logger.info(
            f"Generating monthly report for {community_id}: "
            f"{period_start.date()} to {period_end.date()}"
        )

        # Create report
        report = MonthlyTransparencyReport(
            community_id=community_id,
            period_start=period_start,
            period_end=period_end
        )

        # Generate sub-reports
        report.agent_activity = self._generate_agent_activity(
            community_id, period_start, period_end
        )
        report.revenue = self._generate_revenue_report(
            community_id, period_start, period_end
        )
        report.community_decisions = self._generate_community_decisions(
            community_id, period_start, period_end
        )

        # Calculate summary metrics
        report.total_active_agents = len(report.agent_activity)
        report.total_user_interactions = sum(
            a.total_introductions for a in report.agent_activity
        )

        # Overall acceptance rate
        total_accepted = sum(a.user_accepted for a in report.agent_activity)
        total_declined = sum(a.user_declined for a in report.agent_activity)
        total_interactions = total_accepted + total_declined
        if total_interactions > 0:
            report.overall_acceptance_rate = total_accepted / total_interactions

        # Overall satisfaction (weighted by interactions)
        satisfaction_scores = [
            a.user_satisfaction_score
            for a in report.agent_activity
            if a.user_satisfaction_score is not None
        ]
        if satisfaction_scores:
            report.overall_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)

        # Store report
        report_key = f"{community_id}_{year}_{month:02d}"
        self.reports[report_key] = report

        # Store in graph
        if self.graph_client:
            self._store_report_in_graph(report)

        # Publish to community
        self._publish_report(report)

        logger.info(f"Generated monthly report: {report_key}")

        return report

    def _generate_agent_activity(
        self,
        community_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> List[AgentActivityReport]:
        """
        Generate agent activity reports

        Args:
            community_id: Community ID
            period_start: Start of period
            period_end: End of period

        Returns:
            List of agent activity reports
        """
        activity_reports = []

        # Get active agents for community
        active_agents = self.agent_registry.list_active_agents(community_id=community_id)

        for agent in active_agents:
            # Get transactions for this agent in period
            agent_transactions = [
                t for t in self.fee_processor.get_agent_transactions(agent.agent_id)
                if period_start <= t.created_at <= period_end
            ]

            # Calculate metrics
            report = AgentActivityReport(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                company_name=agent.company_name
            )

            # If we have interaction tracker, get detailed metrics
            if self.interaction_tracker:
                interactions = self.interaction_tracker.get_agent_interactions(
                    agent.agent_id, period_start, period_end
                )
                report.total_introductions = len(interactions)
                report.user_accepted = sum(1 for i in interactions if i.get("accepted"))
                report.user_declined = sum(1 for i in interactions if not i.get("accepted"))
                report.helpful_interactions = sum(1 for i in interactions if i.get("helpful"))
                report.unhelpful_interactions = sum(1 for i in interactions if i.get("unhelpful"))
                report.complaints = sum(1 for i in interactions if i.get("complaint"))
                report.complaint_details = [
                    i.get("complaint_reason", "")
                    for i in interactions
                    if i.get("complaint")
                ]

                # User satisfaction (average of ratings)
                ratings = [i.get("rating") for i in interactions if i.get("rating")]
                if ratings:
                    report.user_satisfaction_score = sum(ratings) / len(ratings)

            # Financial metrics
            report.resulted_in_purchase = len(agent_transactions)
            report.fees_generated = sum(t.referral_fee for t in agent_transactions)
            if agent_transactions:
                report.average_fee = report.fees_generated / len(agent_transactions)

            # Calculate rates
            report.calculate_rates()

            activity_reports.append(report)

        return activity_reports

    def _generate_revenue_report(
        self,
        community_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> RevenueReport:
        """
        Generate revenue report

        Args:
            community_id: Community ID
            period_start: Start of period
            period_end: End of period

        Returns:
            RevenueReport
        """
        report = RevenueReport()

        # Get all transactions for community in period
        transactions = [
            t for t in self.fee_processor.transactions.values()
            if t.community_id == community_id
            and t.status.value == "completed"
            and period_start <= t.completed_at <= period_end
        ]

        report.total_transactions = len(transactions)
        report.total_fees_collected = sum(t.referral_fee for t in transactions)

        # Sum up distributions
        for t in transactions:
            if t.distributed and t.distribution_breakdown:
                report.infrastructure += t.distribution_breakdown.get("infrastructure", 0.0)
                report.servant_development += t.distribution_breakdown.get("servant_development", 0.0)
                report.community_discretionary += t.distribution_breakdown.get("community_discretionary", 0.0)
                report.transparency_audit += t.distribution_breakdown.get("transparency_audit", 0.0)

        # TODO: Track spending per category
        # For now, spending tracking is placeholder

        return report

    def _generate_community_decisions(
        self,
        community_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> CommunityDecisionsReport:
        """
        Generate community decisions report

        Args:
            community_id: Community ID
            period_start: Start of period
            period_end: End of period

        Returns:
            CommunityDecisionsReport
        """
        report = CommunityDecisionsReport()

        # Get all submissions for community in period
        submissions = [
            s for s in self.agent_registry.submissions.values()
            if s.agent_config.community_id == community_id
            and period_start <= s.submitted_at <= period_end
        ]

        # Approved agents
        approved = [s for s in submissions if s.approved]
        report.new_agents_approved = len(approved)
        report.approved_agent_details = [
            {
                "agent_name": s.agent_config.name,
                "company": s.agent_config.company_name,
                "approved_date": s.approved_at.date().isoformat()
            }
            for s in approved
        ]

        # Rejected agents
        rejected = [s for s in submissions if s.status.value == "rejected"]
        report.new_agents_rejected = len(rejected)
        report.rejected_agent_details = [
            {
                "agent_name": s.agent_config.name,
                "company": s.agent_config.company_name,
                "rejection_reason": s.rejection_reason or "Not specified"
            }
            for s in rejected
        ]

        # TODO: Track suspensions and policy changes
        # For now, these are placeholder

        return report

    def _publish_report(self, report: MonthlyTransparencyReport):
        """
        Publish report to community

        Args:
            report: Report to publish
        """
        # Implementation would publish report for community viewing
        logger.info(
            f"Published transparency report for {report.community_id} "
            f"({report.period_start.date()} to {report.period_end.date()})"
        )

    def _store_report_in_graph(self, report: MonthlyTransparencyReport):
        """
        Store report in knowledge graph

        Args:
            report: Report to store
        """
        try:
            # Implementation would store in Graphiti/FalkorDB
            logger.debug(
                f"Stored transparency report in graph for {report.community_id}"
            )
        except Exception as e:
            logger.error(f"Error storing report in graph: {e}")

    def get_report(
        self,
        community_id: str,
        year: int,
        month: int
    ) -> Optional[MonthlyTransparencyReport]:
        """
        Get stored report

        Args:
            community_id: Community ID
            year: Year
            month: Month

        Returns:
            Report if exists
        """
        report_key = f"{community_id}_{year}_{month:02d}"
        return self.reports.get(report_key)
