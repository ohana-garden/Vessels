"""
Project tracking for quadratic funding and community initiatives.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Status of a community project."""
    PROPOSED = "proposed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


@dataclass
class ProjectMilestone:
    """Milestone in project execution."""
    id: str
    description: str
    target_date: datetime
    completed: bool = False
    completed_date: Optional[datetime] = None


class ProjectTracker:
    """
    Tracks community projects for funding and governance.

    Integrates with QuadraticFundingAllocator for democratic funding.
    """

    def __init__(self):
        """Initialize project tracker."""
        self.projects: Dict[str, 'Project'] = {}

    def create_project(
        self,
        name: str,
        description: str,
        owner_id: str
    ) -> 'Project':
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            owner_id: Project owner ID

        Returns:
            Created Project object
        """
        from vessels.economics.quadratic_funding import Project

        project_id = str(uuid.uuid4())

        project = Project(
            id=project_id,
            name=name,
            description=description,
            owner_id=owner_id
        )

        self.projects[project_id] = project

        logger.info(f"Created project: {name} (ID: {project_id})")

        return project

    def get_active_projects(self) -> List['Project']:
        """Get all active projects."""
        return [p for p in self.projects.values() if p.status == "active"]

    def get_project(self, project_id: str) -> Optional['Project']:
        """Get project by ID."""
        return self.projects.get(project_id)
