"""
Policy enforcement for data governance.

Checks read/write access across vessels and by agent class.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from vessels.core import VesselRegistry, PrivacyLevel
from vessels.agents.taxonomy import AgentClass, AgentIdentity

logger = logging.getLogger(__name__)


@dataclass
class AccessDecision:
    """Result of an access policy check."""
    allowed: bool
    reason: str


class PolicyEnforcer:
    """
    Enforces data governance policies.

    Controls:
    - Cross-vessel data access based on privacy levels
    - Agent class-based restrictions
    - Node/edge type filtering
    """

    def __init__(self, vessel_registry: VesselRegistry):
        """
        Initialize policy enforcer.

        Args:
            vessel_registry: Vessel registry for access control
        """
        self.vessel_registry = vessel_registry

    def check_read_access(
        self,
        vessel_id: str,
        agent_identity: AgentIdentity,
        resource: str
    ) -> AccessDecision:
        """
        Check if an agent can read from a vessel's resources.

        Args:
            vessel_id: Target vessel ID
            agent_identity: Agent requesting access
            resource: Resource type (e.g., "community_graph", "vector_store")

        Returns:
            Access decision
        """
        vessel = self.vessel_registry.get_vessel(vessel_id)
        if vessel is None:
            return AccessDecision(
                allowed=False,
                reason=f"Vessel {vessel_id} not found"
            )

        # Commercial agents cannot access community servant knowledge
        if agent_identity.agent_class == AgentClass.COMMERCIAL_AGENT:
            if resource == "community_graph" or resource == "servant_knowledge":
                return AccessDecision(
                    allowed=False,
                    reason="Commercial agents cannot access community servant knowledge"
                )

        # Check privacy level
        privacy_level = vessel.config.privacy_level

        if privacy_level == PrivacyLevel.PUBLIC:
            # Public: anyone can read
            return AccessDecision(allowed=True, reason="Public vessel")

        if privacy_level == PrivacyLevel.SHARED:
            # Shared: only trusted communities
            requesting_community = agent_identity.community_id
            if requesting_community and vessel.is_trusted_community(requesting_community):
                return AccessDecision(allowed=True, reason="Trusted community")
            return AccessDecision(
                allowed=False,
                reason="Community not trusted for shared access"
            )

        if privacy_level == PrivacyLevel.PRIVATE:
            # Private: only same community
            requesting_community = agent_identity.community_id
            if requesting_community in vessel.community_ids:
                return AccessDecision(allowed=True, reason="Same community")
            return AccessDecision(
                allowed=False,
                reason="Private vessel, cross-community access denied"
            )

        return AccessDecision(
            allowed=False,
            reason=f"Unknown privacy level: {privacy_level}"
        )

    def check_write_access(
        self,
        vessel_id: str,
        agent_identity: AgentIdentity,
        resource: str
    ) -> AccessDecision:
        """
        Check if an agent can write to a vessel's resources.

        Args:
            vessel_id: Target vessel ID
            agent_identity: Agent requesting access
            resource: Resource type

        Returns:
            Access decision
        """
        vessel = self.vessel_registry.get_vessel(vessel_id)
        if vessel is None:
            return AccessDecision(
                allowed=False,
                reason=f"Vessel {vessel_id} not found"
            )

        # Commercial agents CANNOT write to community graphs
        if agent_identity.agent_class == AgentClass.COMMERCIAL_AGENT:
            return AccessDecision(
                allowed=False,
                reason="Commercial agents cannot write to community resources"
            )

        # Servants can write to their own vessel
        if agent_identity.agent_class == AgentClass.COMMUNITY_SERVANT:
            requesting_community = agent_identity.community_id
            if requesting_community in vessel.community_ids:
                return AccessDecision(allowed=True, reason="Community servant, same vessel")
            return AccessDecision(
                allowed=False,
                reason="Community servant, different vessel"
            )

        # Hybrid agents: case-by-case
        if agent_identity.agent_class == AgentClass.HYBRID_CONSULTANT:
            # For now, deny write access for hybrid agents
            return AccessDecision(
                allowed=False,
                reason="Hybrid agents require explicit write permission"
            )

        return AccessDecision(
            allowed=False,
            reason=f"Write access not granted for agent class {agent_identity.agent_class.value}"
        )
