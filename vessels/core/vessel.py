"""
Vessel: First-class abstraction binding projects, communities, and policies.

A Vessel represents a complete, isolated environment for coordinating community work.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import uuid


class PrivacyLevel(Enum):
    """Privacy levels for vessel data."""
    PRIVATE = "private"          # No external access
    SHARED = "shared"            # Trusted communities only
    PUBLIC = "public"            # Publicly accessible
    FEDERATED = "federated"      # Cross-community with consent


class TierLevel(Enum):
    """Compute tier levels."""
    TIER0 = "tier0"  # Device (phone, tablet, laptop)
    TIER1 = "tier1"  # Edge (local server)
    TIER2 = "tier2"  # Cloud (remote server or Petals network)
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from vessels.knowledge.schema import CommunityPrivacy


class TierLevel(str, Enum):
    """Compute tier level for a vessel."""

    TIER0 = "device"
    TIER1 = "edge"
    TIER2 = "cloud"


@dataclass
class TierConfig:
    """Configuration for compute tiers."""
    tier0_enabled: bool = True
    tier0_model: str = "Llama-3.2-1B"
    tier0_device: str = "cpu"

    tier1_enabled: bool = True
    tier1_host: str = "localhost"
    tier1_port: int = 8080
    tier1_model: str = "Llama-3.1-70B"

    tier2_enabled: bool = False
    tier2_allowed_models: List[str] = field(default_factory=list)
    tier2_sanitize_data: bool = True


@dataclass
class ConnectorConfig:
    """Configuration for external connectors."""
    nostr_enabled: bool = False
    nostr_relays: List[str] = field(default_factory=list)
    nostr_publish_types: List[str] = field(default_factory=list)

    petals_enabled: bool = False
    petals_allowed_models: List[str] = field(default_factory=list)


@dataclass
class VesselConfig:
    """Complete vessel configuration."""
    privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE
    constraint_profile_id: str = "servant_default"
    tier_config: TierConfig = field(default_factory=TierConfig)
    connector_config: ConnectorConfig = field(default_factory=ConnectorConfig)
    trusted_communities: List[str] = field(default_factory=list)
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    """Describe compute tier availability for a vessel."""

    tier0_enabled: bool = False
    tier1_enabled: bool = False
    tier2_enabled: bool = False
    tier0_endpoints: Dict[str, str] = field(default_factory=dict)
    tier1_endpoints: Dict[str, str] = field(default_factory=dict)
    tier2_endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class Vessel:
    """
    First-class Vessel abstraction.

    A Vessel binds together:
    - Servant projects
    - Community graph namespace(s)
    - Constraint manifold(s)
    - Privacy regime
    - Tier configuration
    - Connectors
    """
    """First-class representation of a vessel configuration."""

    vessel_id: str
    name: str
    description: str
    community_ids: List[str]
    graph_namespace: str
    config: VesselConfig

    # Associated resources
    servant_project_ids: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # active, paused, archived

    @classmethod
    def create(
        cls,
        name: str,
        community_id: str,
        description: str = "",
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        constraint_profile_id: str = "servant_default",
    ) -> "Vessel":
        """Create a new vessel with sensible defaults."""
        vessel_id = str(uuid.uuid4())
        graph_namespace = f"{community_id}_graph"

        config = VesselConfig(
            privacy_level=privacy_level,
            constraint_profile_id=constraint_profile_id,
        )

        return cls(
            vessel_id=vessel_id,
            name=name,
            description=description,
            community_ids=[community_id],
            graph_namespace=graph_namespace,
            config=config,
        )

    def attach_project(self, project_id: str):
        """Attach a servant project to this vessel."""
        if project_id not in self.servant_project_ids:
            self.servant_project_ids.append(project_id)
            self.last_active = datetime.utcnow()

    def detach_project(self, project_id: str):
        """Detach a servant project from this vessel."""
        if project_id in self.servant_project_ids:
            self.servant_project_ids.remove(project_id)
            self.last_active = datetime.utcnow()

    def set_privacy_level(self, privacy_level: PrivacyLevel):
        """Update vessel privacy level."""
        self.config.privacy_level = privacy_level
        self.last_active = datetime.utcnow()

    def add_trusted_community(self, community_id: str):
        """Add a trusted community for cross-vessel access."""
        if community_id not in self.config.trusted_communities:
            self.config.trusted_communities.append(community_id)
            self.last_active = datetime.utcnow()

    def is_trusted_community(self, community_id: str) -> bool:
        """Check if a community is trusted for cross-access."""
        return community_id in self.config.trusted_communities

    def to_dict(self) -> Dict[str, Any]:
        """Serialize vessel to dictionary."""
        return {
            "vessel_id": self.vessel_id,
            "name": self.name,
            "description": self.description,
            "community_ids": self.community_ids,
            "graph_namespace": self.graph_namespace,
            "servant_project_ids": self.servant_project_ids,
            "privacy_level": self.config.privacy_level.value,
            "constraint_profile_id": self.config.constraint_profile_id,
            "trusted_communities": self.config.trusted_communities,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "tier_config": {
                "tier0_enabled": self.config.tier_config.tier0_enabled,
                "tier0_model": self.config.tier_config.tier0_model,
                "tier1_enabled": self.config.tier_config.tier1_enabled,
                "tier1_host": self.config.tier_config.tier1_host,
                "tier2_enabled": self.config.tier_config.tier2_enabled,
            },
            "connectors": {
                "nostr_enabled": self.config.connector_config.nostr_enabled,
                "petals_enabled": self.config.connector_config.petals_enabled,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vessel":
        """Deserialize vessel from dictionary."""
        tier_config_data = data.get("tier_config", {})
        tier_config = TierConfig(
            tier0_enabled=tier_config_data.get("tier0_enabled", True),
            tier0_model=tier_config_data.get("tier0_model", "Llama-3.2-1B"),
            tier1_enabled=tier_config_data.get("tier1_enabled", True),
            tier1_host=tier_config_data.get("tier1_host", "localhost"),
            tier2_enabled=tier_config_data.get("tier2_enabled", False),
        )

        connector_config_data = data.get("connectors", {})
        connector_config = ConnectorConfig(
            nostr_enabled=connector_config_data.get("nostr_enabled", False),
            petals_enabled=connector_config_data.get("petals_enabled", False),
        )

        config = VesselConfig(
            privacy_level=PrivacyLevel(data.get("privacy_level", "private")),
            constraint_profile_id=data.get("constraint_profile_id", "servant_default"),
            tier_config=tier_config,
            connector_config=connector_config,
            trusted_communities=data.get("trusted_communities", []),
        )

        return cls(
            vessel_id=data["vessel_id"],
            name=data["name"],
            description=data.get("description", ""),
            community_ids=data["community_ids"],
            graph_namespace=data["graph_namespace"],
            config=config,
            servant_project_ids=data.get("servant_project_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            status=data.get("status", "active"),
        )
    privacy_level: CommunityPrivacy
    constraint_profile_id: str
    servant_project_ids: List[str] = field(default_factory=list)
    connectors: Dict[str, Dict[str, str]] = field(default_factory=dict)
    tier_config: TierConfig = field(default_factory=TierConfig)

    def attach_project(self, project_id: str) -> None:
        """Attach a servant project to this vessel."""
        if project_id not in self.servant_project_ids:
            self.servant_project_ids.append(project_id)

    def detach_project(self, project_id: str) -> None:
        """Detach a servant project from this vessel."""
        if project_id in self.servant_project_ids:
            self.servant_project_ids.remove(project_id)

