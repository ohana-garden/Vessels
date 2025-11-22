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
    """Describe compute tier availability for a vessel."""

    tier0_enabled: bool = False
    tier1_enabled: bool = False
    tier2_enabled: bool = False
    tier0_endpoints: Dict[str, str] = field(default_factory=dict)
    tier1_endpoints: Dict[str, str] = field(default_factory=dict)
    tier2_endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class Vessel:
    """First-class representation of a vessel configuration."""

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

    def attach_project(self, project_id: str) -> None:
        """Attach a servant project to this vessel."""
        if project_id not in self.servant_project_ids:
            self.servant_project_ids.append(project_id)

    def detach_project(self, project_id: str) -> None:
        """Detach a servant project from this vessel."""
        if project_id in self.servant_project_ids:
            self.servant_project_ids.remove(project_id)

