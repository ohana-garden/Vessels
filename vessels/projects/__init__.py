"""
Vessels Project Management System

Provides isolated project environments for servant agents.

Each project includes:
- Isolated working directory
- Project-specific vector store
- Graphiti namespace for knowledge graph
- Custom system prompts and configuration
- Resource tracking and lifecycle management
"""

from .project import ServantProject, ProjectStatus
from .manager import ProjectManager

__all__ = [
    'ServantProject',
    'ProjectStatus',
    'ProjectManager',
]
