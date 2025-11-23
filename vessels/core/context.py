"""
Vessel Context - Runtime context management for vessels.

Provides utilities for resolving and propagating vessel context
throughout the system.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

from .vessel import PrivacyLevel, Vessel
from .registry import VesselRegistry

logger = logging.getLogger(__name__)


# Simple in-memory user-to-vessel mapping
# In production, this could be backed by a database
_USER_VESSEL_MAPPING: Dict[str, str] = {}


@dataclass
class VesselContext:
    """
    Runtime context for a vessel.

    Holds the active vessel and provides helper methods for:
    - Propagating vessel_id
    - Getting graph namespace
    - Getting privacy settings
    - Creating scoped clients (graphiti, etc.)
    """
    vessel: Vessel
    registry: VesselRegistry

    @property
    def vessel_id(self) -> str:
        """Get vessel ID."""
        return self.vessel.vessel_id

    @property
    def graph_namespace(self) -> str:
        """Get graph namespace for this vessel."""
        return self.vessel.graph_namespace

    @property
    def community_ids(self) -> list:
        """Get community IDs for this vessel."""
        return self.vessel.community_ids

    @property
    def privacy_level(self):
        """Get privacy level."""
        return self.vessel.privacy_level

    @property
    def tier_config(self):
        """Get tier configuration."""
        return self.vessel.tier_config

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata for passing to tools, gates, etc.

        Returns:
            Dictionary with vessel_id, graph_namespace, etc.
        """
        return {
            "vessel_id": self.vessel_id,
            "graph_namespace": self.graph_namespace,
            "community_ids": self.community_ids,
            "privacy_level": self.privacy_level.value,
        }

    def get_graphiti_client(self, **kwargs):
        """
        Create a GraphitiClient for this vessel's namespace.

        Args:
            **kwargs: Additional arguments to pass to GraphitiClient

        Returns:
            VesselsGraphitiClient instance
        """
        from vessels.knowledge.graphiti_client import VesselsGraphitiClient

        # Use vessel's first community ID as the primary community
        community_id = self.community_ids[0] if self.community_ids else "default"

        return VesselsGraphitiClient(
            community_id=community_id,
            **kwargs
        )

    @classmethod
    def from_vessel_id(
        cls,
        vessel_id: str,
        registry: VesselRegistry
    ) -> Optional["VesselContext"]:
        """
        Create context from vessel ID.

        Args:
            vessel_id: Vessel ID
            registry: Vessel registry

        Returns:
            VesselContext or None if vessel not found
        """
        vessel = registry.get_vessel(vessel_id)
        if vessel is None:
            logger.warning(f"Vessel {vessel_id} not found")
            return None

        return cls(vessel=vessel, registry=registry)

    @classmethod
    def from_vessel_name(
        cls,
        name: str,
        registry: VesselRegistry
    ) -> Optional["VesselContext"]:
        """
        Create context from vessel name.

        Args:
            name: Vessel name
            registry: Vessel registry

        Returns:
            VesselContext or None if vessel not found
        """
        vessels = registry.list_vessels()
        for vessel in vessels:
            if vessel.name == name:
                return cls(vessel=vessel, registry=registry)

        logger.warning(f"Vessel with name '{name}' not found")
        return None

    @classmethod
    def from_user_id(
        cls,
        user_id: str,
        registry: VesselRegistry,
        default_vessel_id: Optional[str] = None
    ) -> Optional["VesselContext"]:
        """
        Create context from user ID.

        Looks up user's assigned vessel. If not found and default_vessel_id
        is provided, uses that. Otherwise returns None.

        Args:
            user_id: User ID
            registry: Vessel registry
            default_vessel_id: Optional default vessel ID if user has no mapping

        Returns:
            VesselContext or None
        """
        vessel_id = _USER_VESSEL_MAPPING.get(user_id)

        if vessel_id is None:
            if default_vessel_id:
                logger.info(f"User {user_id} has no vessel mapping, using default {default_vessel_id}")
                vessel_id = default_vessel_id
            else:
                logger.warning(f"User {user_id} has no vessel mapping and no default provided")
                return None

        return cls.from_vessel_id(vessel_id, registry)

    @classmethod
    def get_default(cls, registry: VesselRegistry) -> Optional["VesselContext"]:
        """
        Get default vessel context.

        Uses first available vessel or creates a default one if none exist.

        Args:
            registry: Vessel registry

        Returns:
            VesselContext for default vessel
        """
        vessels = registry.list_vessels()

        if vessels:
            # Use first vessel as default
            return cls(vessel=vessels[0], registry=registry)

        # No vessels exist - create a default one
        logger.info("No vessels found, creating default vessel")
        vessel = Vessel.create(
            name="Default Vessel",
            community_id="default_community",
            description="Auto-created default vessel",
            privacy_level=PrivacyLevel.PRIVATE,
        )
        registry.create_vessel(vessel)

        return cls(vessel=vessel, registry=registry)


def map_user_to_vessel(user_id: str, vessel_id: str) -> None:
    """
    Map a user to a vessel.

    Args:
        user_id: User ID
        vessel_id: Vessel ID
    """
    _USER_VESSEL_MAPPING[user_id] = vessel_id
    logger.info(f"Mapped user {user_id} to vessel {vessel_id}")


def get_user_vessel_id(user_id: str) -> Optional[str]:
    """
    Get vessel ID for a user.

    Args:
        user_id: User ID

    Returns:
        Vessel ID or None
    """
    return _USER_VESSEL_MAPPING.get(user_id)


def clear_user_vessel_mappings() -> None:
    """Clear all user-to-vessel mappings (for testing)."""
    global _USER_VESSEL_MAPPING
    _USER_VESSEL_MAPPING = {}
