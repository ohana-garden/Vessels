"""
Project: Bounded collaborative space (community) that hosts N vessels.

A Project represents a community context where vessels live and collaborate.
It provides shared resources, privacy boundaries, and governance.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import uuid
import logging

from vessels.knowledge.schema import CommunityPrivacy

logger = logging.getLogger(__name__)


class ProjectStatus(str, Enum):
    """Status of a project."""
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class GovernanceModel(str, Enum):
    """How the project is governed."""
    SOLO = "solo"              # Single owner, full control
    COLLABORATIVE = "collaborative"  # Multiple members, shared control
    FEDERATED = "federated"    # Distributed governance across members


@dataclass
class ProjectConfig:
    """Configuration for a project."""
    privacy_level: CommunityPrivacy = CommunityPrivacy.PRIVATE
    governance: GovernanceModel = GovernanceModel.SOLO
    allow_vessel_creation: bool = True  # Can members create vessels?
    allow_external_vessels: bool = False  # Can vessels from other projects interact?
    max_vessels: Optional[int] = None  # Limit on vessels (None = unlimited)
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    """
    Bounded collaborative space that hosts N vessels.

    A Project (community) provides:
    - Shared knowledge graph namespace for all vessels within
    - Memory scope that vessels can access
    - Privacy boundaries for external access
    - Governance model for who can do what
    - Vessel registry for this project

    Examples:
    - "My Garden" project with garden vessel, irrigation vessel, weather vessel
    - "Puna Elder Care" project with coordinator vessel, resource vessel
    - Personal project with single vessel (community of one)
    """

    project_id: str
    name: str
    description: str
    owner_id: str  # User who created this project

    # Configuration
    config: ProjectConfig = field(default_factory=ProjectConfig)

    # Knowledge/Memory scope
    graph_namespace: str = ""  # Initialized in __post_init__

    # Vessels in this project (vessel_id -> metadata)
    vessel_ids: Set[str] = field(default_factory=set)

    # Members who can interact with this project
    member_ids: Set[str] = field(default_factory=set)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    status: ProjectStatus = ProjectStatus.ACTIVE

    # Runtime references (not serialized)
    _memory_backend: Optional[Any] = field(default=None, repr=False)
    _graphiti_client: Optional[Any] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize computed fields."""
        if not self.graph_namespace:
            self.graph_namespace = f"project_{self.project_id}"
        # Owner is always a member
        self.member_ids.add(self.owner_id)

    @classmethod
    def create(
        cls,
        name: str,
        owner_id: str,
        description: str = "",
        privacy_level: CommunityPrivacy = CommunityPrivacy.PRIVATE,
        governance: GovernanceModel = GovernanceModel.SOLO,
    ) -> "Project":
        """Create a new project with sensible defaults."""
        project_id = str(uuid.uuid4())

        config = ProjectConfig(
            privacy_level=privacy_level,
            governance=governance,
        )

        project = cls(
            project_id=project_id,
            name=name,
            description=description,
            owner_id=owner_id,
            config=config,
        )

        logger.info(f"Created project '{name}' ({project_id}) for owner {owner_id}")
        return project

    def add_vessel(self, vessel_id: str) -> bool:
        """
        Add a vessel to this project.

        Returns True if added, False if rejected (e.g., max vessels reached).
        """
        if self.config.max_vessels and len(self.vessel_ids) >= self.config.max_vessels:
            logger.warning(f"Project {self.project_id} at max vessels ({self.config.max_vessels})")
            return False

        self.vessel_ids.add(vessel_id)
        self.last_active = datetime.utcnow()
        logger.info(f"Added vessel {vessel_id} to project {self.project_id}")
        return True

    def remove_vessel(self, vessel_id: str) -> bool:
        """Remove a vessel from this project."""
        if vessel_id in self.vessel_ids:
            self.vessel_ids.discard(vessel_id)
            self.last_active = datetime.utcnow()
            logger.info(f"Removed vessel {vessel_id} from project {self.project_id}")
            return True
        return False

    def add_member(self, user_id: str) -> None:
        """Add a member to this project."""
        self.member_ids.add(user_id)
        self.last_active = datetime.utcnow()
        logger.info(f"Added member {user_id} to project {self.project_id}")

    def remove_member(self, user_id: str) -> bool:
        """Remove a member (owner cannot be removed)."""
        if user_id == self.owner_id:
            logger.warning(f"Cannot remove owner {user_id} from project {self.project_id}")
            return False
        self.member_ids.discard(user_id)
        self.last_active = datetime.utcnow()
        return True

    def is_member(self, user_id: str) -> bool:
        """Check if user is a member of this project."""
        return user_id in self.member_ids

    def can_create_vessel(self, user_id: str) -> bool:
        """Check if user can create vessels in this project."""
        if not self.is_member(user_id):
            return False
        if user_id == self.owner_id:
            return True
        return self.config.allow_vessel_creation

    def get_vessel_count(self) -> int:
        """Get number of vessels in this project."""
        return len(self.vessel_ids)

    def set_memory_backend(self, backend: Any) -> None:
        """Set the memory backend for this project."""
        self._memory_backend = backend

    def set_graphiti_client(self, client: Any) -> None:
        """Set the Graphiti client for this project."""
        self._graphiti_client = client

    def archive(self) -> None:
        """Archive this project."""
        self.status = ProjectStatus.ARCHIVED
        self.last_active = datetime.utcnow()
        logger.info(f"Archived project {self.project_id}")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize project to dictionary."""
        return {
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "graph_namespace": self.graph_namespace,
            "vessel_ids": list(self.vessel_ids),
            "member_ids": list(self.member_ids),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "config": {
                "privacy_level": self.config.privacy_level.value,
                "governance": self.config.governance.value,
                "allow_vessel_creation": self.config.allow_vessel_creation,
                "allow_external_vessels": self.config.allow_external_vessels,
                "max_vessels": self.config.max_vessels,
                "custom_settings": self.config.custom_settings,
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Deserialize project from dictionary."""
        config_data = data.get("config", {})
        config = ProjectConfig(
            privacy_level=CommunityPrivacy(config_data.get("privacy_level", "private")),
            governance=GovernanceModel(config_data.get("governance", "solo")),
            allow_vessel_creation=config_data.get("allow_vessel_creation", True),
            allow_external_vessels=config_data.get("allow_external_vessels", False),
            max_vessels=config_data.get("max_vessels"),
            custom_settings=config_data.get("custom_settings", {}),
        )

        return cls(
            project_id=data["project_id"],
            name=data["name"],
            description=data.get("description", ""),
            owner_id=data["owner_id"],
            graph_namespace=data.get("graph_namespace", ""),
            vessel_ids=set(data.get("vessel_ids", [])),
            member_ids=set(data.get("member_ids", [])),
            status=ProjectStatus(data.get("status", "active")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat())),
            last_active=datetime.fromisoformat(data.get("last_active", datetime.utcnow().isoformat())),
            config=config,
        )

    def __repr__(self) -> str:
        return (
            f"Project(id={self.project_id[:8]}..., name='{self.name}', "
            f"vessels={len(self.vessel_ids)}, members={len(self.member_ids)})"
        )
