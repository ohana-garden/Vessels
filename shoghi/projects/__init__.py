"""
Shoghi Projects - Servant Isolation

Provides project-based isolation for servants with:
- Isolated workspaces
- Project-specific vector stores
- Graphiti client access
- Servant lifecycle management
"""

from .project import ServantProject, ProjectStatus
from .manager import ProjectManager

__all__ = [
    "ServantProject",
    "ProjectStatus",
    "ProjectManager",
]
