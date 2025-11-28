"""
Vessels core abstractions.

This module provides the foundational Vessel abstraction that binds together:
- Servant projects
- Community graph namespaces
- Constraint manifolds
- Privacy regimes
- Tier configurations
- Connectors

Default backend is FalkorDB. SQLite registry is available for testing/fallback.
"""

from .vessel import Vessel, VesselConfig, PrivacyLevel, ConnectorConfig, TierConfig, TierLevel
from .project import Project, ProjectConfig, ProjectStatus, GovernanceModel
from .registry import VesselRegistry as SQLiteVesselRegistry
from .falkordb_registry import FalkorDBVesselRegistry
from .context import (
    VesselContext,
    map_user_to_vessel,
    get_user_vessel_id,
    clear_user_vessel_mappings,
)
from .tier_router import TierRouter, TierSelection, RequestType, get_tier_router
from .tool_registry import ToolRegistry, ToolDefinition, tool_registry

# Default to FalkorDB registry - use SQLiteVesselRegistry for testing/fallback
VesselRegistry = FalkorDBVesselRegistry

__all__ = [
    # Project (community)
    "Project",
    "ProjectConfig",
    "ProjectStatus",
    "GovernanceModel",
    # Vessel
    "Vessel",
    "VesselConfig",
    "PrivacyLevel",
    "ConnectorConfig",
    "TierConfig",
    "TierLevel",
    # Registries
    "VesselRegistry",
    "FalkorDBVesselRegistry",
    "SQLiteVesselRegistry",
    # Context
    "VesselContext",
    "map_user_to_vessel",
    "get_user_vessel_id",
    "clear_user_vessel_mappings",
    # Tier routing
    "TierRouter",
    "TierSelection",
    "RequestType",
    "get_tier_router",
    # Tool registry
    "ToolRegistry",
    "ToolDefinition",
    "tool_registry",
]

