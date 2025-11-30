"""
Vessel: First-class abstraction binding projects, communities, and policies.

A Vessel represents a complete, isolated environment for coordinating community work.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import uuid

from vessels.knowledge.schema import CommunityPrivacy


class PrivacyLevel(Enum):
    """Privacy levels for vessel data."""
    PRIVATE = "private"          # No external access
    SHARED = "shared"            # Trusted communities only
    PUBLIC = "public"            # Publicly accessible
    FEDERATED = "federated"      # Cross-community with consent


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
    tier0_endpoints: Dict[str, str] = field(default_factory=dict)

    tier1_enabled: bool = True
    tier1_host: str = "localhost"
    tier1_port: int = 8080
    tier1_model: str = "Llama-3.1-70B"
    tier1_endpoints: Dict[str, str] = field(default_factory=dict)

    tier2_enabled: bool = False
    tier2_allowed_models: List[str] = field(default_factory=list)
    tier2_sanitize_data: bool = True
    tier2_endpoints: Dict[str, str] = field(default_factory=dict)


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
    vessel_id: str
    name: str
    description: str
    community_ids: List[str]
    graph_namespace: str
    privacy_level: CommunityPrivacy
    constraint_profile_id: str
    servant_project_ids: List[str] = field(default_factory=list)
    connectors: Dict[str, Dict[str, str]] = field(default_factory=dict)
    tier_config: TierConfig = field(default_factory=TierConfig)

    # Agent coordination resources (vessel-native)
    action_gate: Optional[Any] = None  # ActionGate for privacy/moral enforcement
    memory_backend: Optional[Any] = None  # Memory backend for agent memories
    tools: Dict[str, Any] = field(default_factory=dict)  # Tool bindings for agents
    privacy_policy: Optional[Any] = None  # Explicit privacy policy (if different from privacy_level)
    moral_manifold: Optional[Any] = None  # Cached moral manifold instance

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # active, paused, archived

    # Convenience config property for backward compatibility
    @property
    def config(self) -> VesselConfig:
        """Get vessel configuration as VesselConfig object."""
        return VesselConfig(
            privacy_level=PrivacyLevel(self.privacy_level.value),
            constraint_profile_id=self.constraint_profile_id,
            tier_config=self.tier_config,
            connector_config=ConnectorConfig(
                nostr_enabled=self.connectors.get("nostr", {}).get("enabled", False) == "true",
                petals_enabled=self.connectors.get("petals", {}).get("enabled", False) == "true",
            ),
            trusted_communities=self._get_trusted_communities(),
        )

    def _get_trusted_communities(self) -> List[str]:
        """Extract trusted communities from connectors or other metadata."""
        # This can be extended to pull from connectors or a dedicated field
        return []

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

        # Map PrivacyLevel to CommunityPrivacy
        community_privacy = CommunityPrivacy(privacy_level.value)

        return cls(
            vessel_id=vessel_id,
            name=name,
            description=description,
            community_ids=[community_id],
            graph_namespace=graph_namespace,
            privacy_level=community_privacy,
            constraint_profile_id=constraint_profile_id,
        )

    def attach_project(self, project_id: str) -> None:
        """Attach a servant project to this vessel."""
        if project_id not in self.servant_project_ids:
            self.servant_project_ids.append(project_id)
            self.last_active = datetime.utcnow()

    def detach_project(self, project_id: str) -> None:
        """Detach a servant project from this vessel."""
        if project_id in self.servant_project_ids:
            self.servant_project_ids.remove(project_id)
            self.last_active = datetime.utcnow()

    def set_privacy_level(self, privacy_level: PrivacyLevel):
        """Update vessel privacy level."""
        self.privacy_level = CommunityPrivacy(privacy_level.value)
        self.last_active = datetime.utcnow()

    def add_trusted_community(self, community_id: str):
        """Add a trusted community for cross-vessel access."""
        # For now, store in connectors metadata
        # In future, could add a dedicated field
        if "trusted" not in self.connectors:
            self.connectors["trusted"] = {}
        if "communities" not in self.connectors["trusted"]:
            self.connectors["trusted"]["communities"] = []
        if community_id not in self.connectors["trusted"]["communities"]:
            self.connectors["trusted"]["communities"].append(community_id)
            self.last_active = datetime.utcnow()

    def is_trusted_community(self, community_id: str) -> bool:
        """Check if a community is trusted for cross-access."""
        trusted = self.connectors.get("trusted", {}).get("communities", [])
        return community_id in trusted

    def set_action_gate(self, action_gate: Any) -> None:
        """Set the action gate for this vessel."""
        self.action_gate = action_gate
        self.last_active = datetime.utcnow()

    def set_memory_backend(self, memory_backend: Any) -> None:
        """Set the memory backend for this vessel."""
        self.memory_backend = memory_backend
        self.last_active = datetime.utcnow()

    def set_tools(self, tools: Dict[str, Any]) -> None:
        """Set the tool bindings for this vessel."""
        self.tools = tools
        self.last_active = datetime.utcnow()

    def add_tool(self, tool_name: str, tool_impl: Any) -> None:
        """Add a single tool to this vessel."""
        self.tools[tool_name] = tool_impl
        self.last_active = datetime.utcnow()

    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool implementation by name."""
        return self.tools.get(tool_name)

    def set_moral_manifold(self, moral_manifold: Any) -> None:
        """Set the cached moral manifold for this vessel."""
        self.moral_manifold = moral_manifold
        self.last_active = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize vessel to dictionary."""
        return {
            "vessel_id": self.vessel_id,
            "name": self.name,
            "description": self.description,
            "community_ids": self.community_ids,
            "graph_namespace": self.graph_namespace,
            "servant_project_ids": self.servant_project_ids,
            "privacy_level": self.privacy_level.value,
            "constraint_profile_id": self.constraint_profile_id,
            "connectors": self.connectors,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "tier_config": {
                "tier0_enabled": self.tier_config.tier0_enabled,
                "tier0_model": self.tier_config.tier0_model,
                "tier0_device": self.tier_config.tier0_device,
                "tier1_enabled": self.tier_config.tier1_enabled,
                "tier1_host": self.tier_config.tier1_host,
                "tier1_port": self.tier_config.tier1_port,
                "tier1_model": self.tier_config.tier1_model,
                "tier2_enabled": self.tier_config.tier2_enabled,
                "tier2_allowed_models": self.tier_config.tier2_allowed_models,
                "tier2_sanitize_data": self.tier_config.tier2_sanitize_data,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Vessel":
        """Deserialize vessel from dictionary."""
        tier_config_data = data.get("tier_config", {})
        tier_config = TierConfig(
            tier0_enabled=tier_config_data.get("tier0_enabled", True),
            tier0_model=tier_config_data.get("tier0_model", "Llama-3.2-1B"),
            tier0_device=tier_config_data.get("tier0_device", "cpu"),
            tier1_enabled=tier_config_data.get("tier1_enabled", True),
            tier1_host=tier_config_data.get("tier1_host", "localhost"),
            tier1_port=tier_config_data.get("tier1_port", 8080),
            tier1_model=tier_config_data.get("tier1_model", "Llama-3.1-70B"),
            tier2_enabled=tier_config_data.get("tier2_enabled", False),
            tier2_allowed_models=tier_config_data.get("tier2_allowed_models", []),
            tier2_sanitize_data=tier_config_data.get("tier2_sanitize_data", True),
        )

        return cls(
            vessel_id=data["vessel_id"],
            name=data["name"],
            description=data.get("description", ""),
            community_ids=data["community_ids"],
            graph_namespace=data["graph_namespace"],
            privacy_level=CommunityPrivacy(data.get("privacy_level", "private")),
            constraint_profile_id=data.get("constraint_profile_id", "servant_default"),
            servant_project_ids=data.get("servant_project_ids", []),
            connectors=data.get("connectors", {}),
            tier_config=tier_config,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.utcnow().isoformat())),
            status=data.get("status", "active"),
        )
