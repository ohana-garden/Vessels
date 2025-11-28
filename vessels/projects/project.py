"""
Servant Project Definition

A Project represents an isolated workspace for a single servant with:
- Dedicated work directory
- Project-specific vector store
- Graphiti client with namespaced access
- Custom system prompts
- Project-specific secrets
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

from vessels.knowledge import VesselsGraphitiClient, ProjectVectorStore
from vessels.knowledge.schema import ServantType, CommunityPrivacy

logger = logging.getLogger(__name__)


class ProjectStatus(str, Enum):
    """Status of a servant project"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    ERROR = "error"


@dataclass
class ServantProject:
    """
    Isolated project for a single servant

    Each project has:
    - Dedicated workspace (no cross-contamination)
    - Project-specific vector store
    - Graphiti client with community graph access
    - Custom system prompt defining role and constraints
    """

    id: str
    community_id: str
    servant_type: ServantType
    work_dir: Path
    graphiti_namespace: str  # Community graph name
    system_prompt: str
    status: ProjectStatus = ProjectStatus.INITIALIZING
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)

    # Optional fields
    secrets: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    read_only_communities: List[str] = field(default_factory=list)

    # Lazy-loaded components
    _graphiti_client: Optional[VesselsGraphitiClient] = field(default=None, repr=False)
    _vector_store: Optional[ProjectVectorStore] = field(default=None, repr=False)

    def __post_init__(self):
        """Ensure work directory exists"""
        self.work_dir = Path(self.work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized project {self.id} at {self.work_dir}")

    @property
    def graphiti(self) -> VesselsGraphitiClient:
        """Lazy-load Graphiti client"""
        if self._graphiti_client is None:
            self._graphiti_client = VesselsGraphitiClient(
                community_id=self.community_id,
                servant_id=self.id,
                read_only_communities=self.read_only_communities,
                allow_mock=os.getenv("VESSELS_GRAPHITI_ALLOW_MOCK", "0") == "1",
            )
            logger.debug(f"Created Graphiti client for project {self.id}")

        return self._graphiti_client

    @property
    def vector_store(self) -> ProjectVectorStore:
        """Lazy-load project vector store"""
        if self._vector_store is None:
            self._vector_store = ProjectVectorStore(self.work_dir)
            logger.debug(f"Loaded vector store for project {self.id} ({self._vector_store.count()} docs)")

        return self._vector_store

    def get_files_dir(self) -> Path:
        """Get directory for project-specific files"""
        files_dir = self.work_dir / "files"
        files_dir.mkdir(exist_ok=True)
        return files_dir

    def get_logs_dir(self) -> Path:
        """Get directory for project logs"""
        logs_dir = self.work_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir

    def get_config_file(self) -> Path:
        """Get path to project config file"""
        return self.work_dir / "project.json"

    def save_config(self):
        """Save project configuration to disk"""
        import json

        config_data = {
            "id": self.id,
            "community_id": self.community_id,
            "servant_type": self.servant_type.value,
            "graphiti_namespace": self.graphiti_namespace,
            "system_prompt": self.system_prompt,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "config": self.config,
            "read_only_communities": self.read_only_communities
        }

        with open(self.get_config_file(), "w") as f:
            json.dump(config_data, f, indent=2)

        logger.debug(f"Saved project config for {self.id}")

    @classmethod
    def load_from_dir(cls, project_dir: Path) -> "ServantProject":
        """Load project from directory"""
        import json

        config_file = project_dir / "project.json"
        if not config_file.exists():
            raise FileNotFoundError(f"Project config not found: {config_file}")

        with open(config_file, "r") as f:
            config_data = json.load(f)

        return cls(
            id=config_data["id"],
            community_id=config_data["community_id"],
            servant_type=ServantType(config_data["servant_type"]),
            work_dir=project_dir,
            graphiti_namespace=config_data["graphiti_namespace"],
            system_prompt=config_data["system_prompt"],
            status=ProjectStatus(config_data["status"]),
            created_at=datetime.fromisoformat(config_data["created_at"]),
            last_active=datetime.fromisoformat(config_data["last_active"]),
            config=config_data.get("config", {}),
            read_only_communities=config_data.get("read_only_communities", [])
        )

    def update_status(self, new_status: ProjectStatus):
        """Update project status"""
        old_status = self.status
        self.status = new_status
        self.last_active = datetime.utcnow()
        self.save_config()

        logger.info(f"Project {self.id} status: {old_status.value} → {new_status.value}")

    def archive(self):
        """Archive this project"""
        self.update_status(ProjectStatus.ARCHIVED)

        # Record in graph
        try:
            self.graphiti.create_node(
                node_type="Event",
                properties={
                    "type": "project_archived",
                    "project_id": self.id,
                    "servant_type": self.servant_type.value,
                    "archived_at": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error recording archive event in graph: {e}")

    def get_allowed_tools(self) -> List[str]:
        """Get list of tools this servant is allowed to use"""
        # Default tools for all servants
        base_tools = [
            "read_file",
            "write_file",
            "search_web",
            "query_memory",
            "store_memory"
        ]

        # Servant-type-specific tools
        type_tools = {
            ServantType.TRANSPORT: ["map_api", "schedule_api"],
            ServantType.MEALS: ["nutrition_api", "recipe_search"],
            ServantType.MEDICAL: ["medical_facility_api"],
            ServantType.GRANT_WRITER: ["grant_database_api", "document_generator"],
        }

        return base_tools + type_tools.get(self.servant_type, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary"""
        return {
            "id": self.id,
            "community_id": self.community_id,
            "servant_type": self.servant_type.value,
            "work_dir": str(self.work_dir),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "vector_store_docs": self.vector_store.count() if self._vector_store else 0,
            "config": self.config
        }
