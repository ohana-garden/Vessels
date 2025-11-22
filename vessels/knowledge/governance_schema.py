"""
Governance entity schema extensions.

Defines entity types for representing human governance structures
and decisions in the knowledge graph.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class GovernanceBody:
    """
    Represents a human governance structure.

    Examples: Council, Board, Assembly, Working Group
    """
    id: str
    name: str
    body_type: str  # "council", "board", "assembly", "working_group"
    community_id: str
    members: List[str]  # List of member IDs
    created_at: datetime
    active: bool = True


@dataclass
class Decision:
    """
    Represents a governance decision.

    Links governance bodies to vessels, policies, and actions.
    """
    id: str
    governance_body_id: str
    decision_type: str  # "approval", "policy_change", "override", "rejection"
    description: str
    approved_at: datetime
    approved_by: List[str]  # Member IDs who approved
    effective_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None


class GovernanceSchemaExtension:
    """
    Schema extensions for governance entities in knowledge graph.

    Provides node types and relationship types for representing
    human governance structures.
    """

    # Node types
    GOVERNANCE_BODY = "GovernanceBody"
    DECISION = "Decision"
    POLICY = "Policy"
    OVERRIDE = "Override"

    # Relationship types
    MADE_DECISION = "MADE_DECISION"
    APPROVES = "APPROVES"
    MODIFIES = "MODIFIES"
    OVERRIDES = "OVERRIDES"
    MEMBER_OF = "MEMBER_OF"
    ACCOUNTABLE_TO = "ACCOUNTABLE_TO"

    @staticmethod
    def create_governance_body_node(
        graphiti_client,
        body: GovernanceBody
    ) -> str:
        """
        Create a governance body node in the graph.

        Args:
            graphiti_client: Graphiti client instance
            body: Governance body to create

        Returns:
            Node ID
        """
        return graphiti_client.create_node(
            node_type=GovernanceSchemaExtension.GOVERNANCE_BODY,
            properties={
                "id": body.id,
                "name": body.name,
                "body_type": body.body_type,
                "community_id": body.community_id,
                "members": ",".join(body.members),
                "created_at": body.created_at.isoformat(),
                "active": body.active
            }
        )

    @staticmethod
    def create_decision_node(
        graphiti_client,
        decision: Decision
    ) -> str:
        """
        Create a decision node in the graph.

        Args:
            graphiti_client: Graphiti client instance
            decision: Decision to create

        Returns:
            Node ID
        """
        properties = {
            "id": decision.id,
            "governance_body_id": decision.governance_body_id,
            "decision_type": decision.decision_type,
            "description": decision.description,
            "approved_at": decision.approved_at.isoformat(),
            "approved_by": ",".join(decision.approved_by)
        }

        if decision.effective_at:
            properties["effective_at"] = decision.effective_at.isoformat()
        if decision.expires_at:
            properties["expires_at"] = decision.expires_at.isoformat()

        return graphiti_client.create_node(
            node_type=GovernanceSchemaExtension.DECISION,
            properties=properties
        )

    @staticmethod
    def link_decision_to_vessel(
        graphiti_client,
        decision_id: str,
        vessel_id: str
    ):
        """Link a decision to a vessel it governs."""
        graphiti_client.create_relationship(
            source_id=decision_id,
            relationship_type=GovernanceSchemaExtension.APPROVES,
            target_id=vessel_id
        )

    @staticmethod
    def link_vessel_to_governance(
        graphiti_client,
        vessel_id: str,
        governance_body_id: str
    ):
        """Link a vessel to its governing body."""
        graphiti_client.create_relationship(
            source_id=vessel_id,
            relationship_type=GovernanceSchemaExtension.ACCOUNTABLE_TO,
            target_id=governance_body_id
        )

    @staticmethod
    def get_governance_history(
        graphiti_client,
        vessel_id: str
    ) -> List[Dict[str, Any]]:
        """
        Query governance history for a vessel.

        Args:
            graphiti_client: Graphiti client instance
            vessel_id: Vessel ID

        Returns:
            List of governance events
        """
        # This is a stub - actual implementation requires Graphiti query
        # For now, return empty list
        return []
