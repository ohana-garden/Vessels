"""
Graph-based tracking for commercial agent relationships.

Extends the Vessels knowledge graph schema to track:
- Commercial agent registrations
- Servant introductions of commercial agents
- User interactions with commercial agents
- Consent and disclosure records
- Revenue flows to community

All commercial activity is tracked in FalkorDB for full transparency
and auditability.

REQUIRES AgentZeroCore - all graph tracking is coordinated through A0.
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from ..knowledge.schema import NodeType, RelationType, PropertyName

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


# Extend node types for commercial tracking
class CommercialNodeType(str, Enum):
    """Additional node types for commercial agent tracking."""
    COMMERCIAL_AGENT = "CommercialAgent"
    COMMERCIAL_INTRODUCTION = "CommercialIntroduction"
    COMMERCIAL_INTERACTION = "CommercialInteraction"
    CONSENT_RECORD = "ConsentRecord"
    DISCLOSURE_RECORD = "DisclosureRecord"
    REVENUE_RECORD = "RevenueRecord"
    INTERVENTION_RECORD = "InterventionRecord"


# Extend relationship types for commercial tracking
class CommercialRelationType(str, Enum):
    """Additional relationship types for commercial tracking."""
    INTRODUCED = "INTRODUCED"  # Servant -[INTRODUCED]-> CommercialAgent
    INTERACTED_WITH = "INTERACTED_WITH"  # CommercialAgent -[INTERACTED_WITH]-> User
    CONSENTED_TO = "CONSENTED_TO"  # User -[CONSENTED_TO]-> CommercialAgent
    DISCLOSED_BY = "DISCLOSED_BY"  # DisclosureRecord -[DISCLOSED_BY]-> CommercialAgent
    GENERATED_REVENUE = "GENERATED_REVENUE"  # CommercialInteraction -[GENERATED_REVENUE]-> RevenueRecord
    INTERVENED_IN = "INTERVENED_IN"  # Servant -[INTERVENED_IN]-> CommercialInteraction
    REPRESENTS = "REPRESENTS"  # CommercialAgent -[REPRESENTS]-> Organization


class CommercialRelationshipGraph:
    """
    Tracks commercial relationships in FalkorDB for transparency.

    Every commercial agent introduction, interaction, and transaction
    is recorded in the graph for audit and transparency.

    REQUIRES AgentZeroCore - all graph tracking is coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        falkor_client=None,
        graph_name: str = "vessels_commercial"
    ):
        """
        Initialize with FalkorDB client.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            falkor_client: FalkorDBClient instance (defaults to A0's memory_system)
            graph_name: Graph namespace for commercial tracking
        """
        if agent_zero is None:
            raise ValueError("CommercialRelationshipGraph requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.falkor_client = falkor_client or agent_zero.memory_system
        self.graph = self.falkor_client.get_graph(graph_name) if self.falkor_client else None

        # Register with A0
        self.agent_zero.commercial_graph = self
        logger.info("CommercialRelationshipGraph initialized with A0")

    def register_commercial_agent(
        self,
        agent_id: str,
        company: str,
        compensation_model: str,
        agent_class: str,
        expertise: List[str],
        community_id: str
    ):
        """
        Register a commercial agent in the graph.

        Args:
            agent_id: Unique agent identifier
            company: Company the agent represents
            compensation_model: How agent is compensated
            agent_class: Agent class (commercial, hybrid)
            expertise: List of expertise areas
            community_id: Community where agent can participate
        """
        cypher = """
        MERGE (c:CommercialAgent {id: $agent_id})
        SET c.company = $company,
            c.compensation_model = $compensation_model,
            c.agent_class = $agent_class,
            c.expertise = $expertise,
            c.registered_at = datetime(),
            c.community_id = $community_id,
            c.status = 'active'

        // Link to organization
        MERGE (org:Organization {name: $company, community_id: $community_id})
        MERGE (c)-[:REPRESENTS]->(org)

        RETURN c
        """

        self.graph.query(cypher, {
            "agent_id": agent_id,
            "company": company,
            "compensation_model": compensation_model,
            "agent_class": agent_class,
            "expertise": expertise,
            "community_id": community_id
        })

    def record_commercial_introduction(
        self,
        servant_id: str,
        commercial_agent_id: str,
        user_id: str,
        query: str,
        relevance_score: float,
        user_consented: bool,
        timestamp: datetime,
        community_id: str
    ):
        """
        Record when a servant introduces a commercial agent.

        This creates an audit trail of:
        - Who introduced the agent
        - When and why
        - Whether user consented
        - Relevance to query

        Args:
            servant_id: ID of servant making introduction
            commercial_agent_id: ID of commercial agent
            user_id: ID of user
            query: User's query that triggered introduction
            relevance_score: How relevant agent is (0-1)
            user_consented: Whether user agreed to interact
            timestamp: When introduction occurred
            community_id: Community context
        """
        cypher = """
        MATCH (s:Servant {id: $servant_id})
        MATCH (c:CommercialAgent {id: $commercial_agent_id})
        MATCH (u:Person {id: $user_id})

        CREATE (intro:CommercialIntroduction {
            id: randomUUID(),
            timestamp: $timestamp,
            query: $query,
            relevance_score: $relevance_score,
            user_consented: $consented,
            community_id: $community_id
        })

        CREATE (s)-[:INTRODUCED {
            timestamp: $timestamp,
            relevance_score: $relevance_score
        }]->(intro)

        CREATE (intro)-[:INVOLVES_AGENT]->(c)
        CREATE (intro)-[:INVOLVES_USER]->(u)

        // If user consented, record that too
        WITH c, u, $consented AS consented
        WHERE consented = true
        CREATE (u)-[:CONSENTED_TO {
            timestamp: $timestamp,
            context: $query
        }]->(c)

        RETURN intro
        """

        self.graph.query(cypher, {
            "servant_id": servant_id,
            "commercial_agent_id": commercial_agent_id,
            "user_id": user_id,
            "query": query,
            "relevance_score": relevance_score,
            "consented": user_consented,
            "timestamp": timestamp.isoformat(),
            "community_id": community_id
        })

    def record_commercial_interaction(
        self,
        interaction_id: str,
        commercial_agent_id: str,
        user_id: str,
        message_content: str,
        manipulation_score: float,
        pressure_score: float,
        timestamp: datetime,
        community_id: str
    ):
        """
        Record a commercial agent interaction.

        Tracks the actual conversation for transparency and monitoring.

        Args:
            interaction_id: Unique interaction ID
            commercial_agent_id: ID of commercial agent
            user_id: ID of user
            message_content: What was said (for audit)
            manipulation_score: Detected manipulation (0-1)
            pressure_score: Detected pressure (0-1)
            timestamp: When interaction occurred
            community_id: Community context
        """
        cypher = """
        MATCH (c:CommercialAgent {id: $agent_id})
        MATCH (u:Person {id: $user_id})

        CREATE (i:CommercialInteraction {
            id: $interaction_id,
            timestamp: $timestamp,
            message_content: $message,
            manipulation_score: $manipulation,
            pressure_score: $pressure,
            community_id: $community_id
        })

        CREATE (c)-[:INTERACTED_WITH {
            timestamp: $timestamp,
            manipulation_score: $manipulation,
            pressure_score: $pressure
        }]->(i)

        CREATE (i)-[:WITH_USER]->(u)

        RETURN i
        """

        self.graph.query(cypher, {
            "interaction_id": interaction_id,
            "agent_id": commercial_agent_id,
            "user_id": user_id,
            "message": message_content,
            "manipulation": manipulation_score,
            "pressure": pressure_score,
            "timestamp": timestamp.isoformat(),
            "community_id": community_id
        })

    def record_servant_intervention(
        self,
        servant_id: str,
        interaction_id: str,
        reason: str,
        action_taken: str,
        timestamp: datetime,
        community_id: str
    ):
        """
        Record when servant intervenes in commercial interaction.

        Args:
            servant_id: ID of intervening servant
            interaction_id: ID of interaction intervened in
            reason: Why servant intervened
            action_taken: What servant did
            timestamp: When intervention occurred
            community_id: Community context
        """
        cypher = """
        MATCH (s:Servant {id: $servant_id})
        MATCH (i:CommercialInteraction {id: $interaction_id})

        CREATE (intervention:InterventionRecord {
            id: randomUUID(),
            timestamp: $timestamp,
            reason: $reason,
            action_taken: $action,
            community_id: $community_id
        })

        CREATE (s)-[:INTERVENED_IN {
            timestamp: $timestamp,
            reason: $reason
        }]->(intervention)

        CREATE (intervention)-[:CONCERNS]->(i)

        RETURN intervention
        """

        self.graph.query(cypher, {
            "servant_id": servant_id,
            "interaction_id": interaction_id,
            "reason": reason,
            "action": action_taken,
            "timestamp": timestamp.isoformat(),
            "community_id": community_id
        })

    def record_disclosure(
        self,
        commercial_agent_id: str,
        user_id: str,
        disclosure_content: str,
        completeness_score: float,
        timestamp: datetime,
        community_id: str
    ):
        """
        Record commercial agent disclosure to user.

        Tracks that proper disclosure happened.

        Args:
            commercial_agent_id: ID of commercial agent
            user_id: ID of user who received disclosure
            disclosure_content: What was disclosed
            completeness_score: How complete disclosure was (0-1)
            timestamp: When disclosure occurred
            community_id: Community context
        """
        cypher = """
        MATCH (c:CommercialAgent {id: $agent_id})
        MATCH (u:Person {id: $user_id})

        CREATE (d:DisclosureRecord {
            id: randomUUID(),
            timestamp: $timestamp,
            content: $content,
            completeness_score: $completeness,
            community_id: $community_id
        })

        CREATE (d)-[:DISCLOSED_BY]->(c)
        CREATE (d)-[:DISCLOSED_TO]->(u)

        RETURN d
        """

        self.graph.query(cypher, {
            "agent_id": commercial_agent_id,
            "user_id": user_id,
            "content": disclosure_content,
            "completeness": completeness_score,
            "timestamp": timestamp.isoformat(),
            "community_id": community_id
        })

    def record_revenue(
        self,
        interaction_id: str,
        amount: float,
        currency: str,
        revenue_type: str,  # "per_interaction", "per_sale", etc.
        allocated_to_community: float,
        allocated_to_infrastructure: float,
        allocated_to_servants: float,
        allocated_to_auditing: float,
        timestamp: datetime,
        community_id: str
    ):
        """
        Record revenue from commercial interaction.

        Tracks how revenue flows to community (NOT to platform or servants).

        Args:
            interaction_id: ID of interaction that generated revenue
            amount: Total amount
            currency: Currency code
            revenue_type: Type of revenue
            allocated_to_community: Amount to community fund
            allocated_to_infrastructure: Amount to infrastructure
            allocated_to_servants: Amount to servant development
            allocated_to_auditing: Amount to auditing
            timestamp: When revenue occurred
            community_id: Community context
        """
        cypher = """
        MATCH (i:CommercialInteraction {id: $interaction_id})

        CREATE (r:RevenueRecord {
            id: randomUUID(),
            timestamp: $timestamp,
            amount: $amount,
            currency: $currency,
            revenue_type: $revenue_type,
            allocated_to_community: $to_community,
            allocated_to_infrastructure: $to_infra,
            allocated_to_servants: $to_servants,
            allocated_to_auditing: $to_audit,
            platform_take: 0.0,
            community_id: $community_id
        })

        CREATE (i)-[:GENERATED_REVENUE]->(r)

        RETURN r
        """

        self.graph.query(cypher, {
            "interaction_id": interaction_id,
            "amount": amount,
            "currency": currency,
            "revenue_type": revenue_type,
            "to_community": allocated_to_community,
            "to_infra": allocated_to_infrastructure,
            "to_servants": allocated_to_servants,
            "to_audit": allocated_to_auditing,
            "timestamp": timestamp.isoformat(),
            "community_id": community_id
        })

    def query_commercial_influence(
        self,
        user_id: str,
        time_window_days: int = 30
    ) -> List[Dict]:
        """
        Query commercial agent exposure for a user.

        User can see all commercial agent interactions in time window.

        Args:
            user_id: User to query for
            time_window_days: How many days back to look

        Returns:
            List of commercial interactions
        """
        cypher = """
        MATCH (u:Person {id: $user_id})-[:CONSENTED_TO]->(c:CommercialAgent)
        MATCH (c)-[i:INTERACTED_WITH]->(interaction:CommercialInteraction)
        WHERE interaction.timestamp > datetime() - duration({days: $days})

        RETURN
            c.company AS company,
            c.compensation_model AS compensation_model,
            count(i) AS interaction_count,
            avg(interaction.manipulation_score) AS avg_manipulation,
            avg(interaction.pressure_score) AS avg_pressure,
            max(interaction.timestamp) AS last_interaction
        ORDER BY interaction_count DESC
        """

        result = self.graph.query(cypher, {
            "user_id": user_id,
            "days": time_window_days
        })

        if not result or not result.result_set:
            return []

        return [
            {
                "company": row[0],
                "compensation_model": row[1],
                "interaction_count": row[2],
                "avg_manipulation": row[3],
                "avg_pressure": row[4],
                "last_interaction": row[5]
            }
            for row in result.result_set
        ]

    def query_servant_introductions(
        self,
        servant_id: str,
        time_window_days: int = 30
    ) -> List[Dict]:
        """
        Query commercial introductions made by a servant.

        Shows servant's commercial introduction activity.

        Args:
            servant_id: Servant to query for
            time_window_days: How many days back to look

        Returns:
            List of introductions made
        """
        cypher = """
        MATCH (s:Servant {id: $servant_id})-[:INTRODUCED]->(intro:CommercialIntroduction)
        WHERE intro.timestamp > datetime() - duration({days: $days})
        MATCH (intro)-[:INVOLVES_AGENT]->(c:CommercialAgent)

        RETURN
            intro.timestamp AS when_introduced,
            c.company AS company,
            intro.query AS user_query,
            intro.relevance_score AS relevance,
            intro.user_consented AS user_consented
        ORDER BY intro.timestamp DESC
        """

        result = self.graph.query(cypher, {
            "servant_id": servant_id,
            "days": time_window_days
        })

        if not result or not result.result_set:
            return []

        return [
            {
                "when_introduced": row[0],
                "company": row[1],
                "user_query": row[2],
                "relevance": row[3],
                "user_consented": row[4]
            }
            for row in result.result_set
        ]

    def query_community_commercial_revenue(
        self,
        community_id: str,
        time_window_days: int = 30
    ) -> Dict[str, float]:
        """
        Query total commercial revenue for community.

        Shows transparent accounting of commercial revenue flows.

        Args:
            community_id: Community to query for
            time_window_days: How many days back to look

        Returns:
            Revenue breakdown by category
        """
        cypher = """
        MATCH (r:RevenueRecord {community_id: $community_id})
        WHERE r.timestamp > datetime() - duration({days: $days})

        RETURN
            sum(r.amount) AS total_revenue,
            sum(r.allocated_to_community) AS to_community_fund,
            sum(r.allocated_to_infrastructure) AS to_infrastructure,
            sum(r.allocated_to_servants) AS to_servant_development,
            sum(r.allocated_to_auditing) AS to_auditing,
            sum(r.platform_take) AS to_platform,
            count(r) AS transaction_count
        """

        result = self.graph.query(cypher, {
            "community_id": community_id,
            "days": time_window_days
        })

        if not result or not result.result_set:
            return {
                "total_revenue": 0.0,
                "to_community_fund": 0.0,
                "to_infrastructure": 0.0,
                "to_servant_development": 0.0,
                "to_auditing": 0.0,
                "to_platform": 0.0,
                "transaction_count": 0
            }

        row = result.result_set[0]
        return {
            "total_revenue": row[0] or 0.0,
            "to_community_fund": row[1] or 0.0,
            "to_infrastructure": row[2] or 0.0,
            "to_servant_development": row[3] or 0.0,
            "to_auditing": row[4] or 0.0,
            "to_platform": row[5] or 0.0,
            "transaction_count": row[6] or 0
        }
