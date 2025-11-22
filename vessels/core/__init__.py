"""
Vessels core abstractions.

This module provides the foundational Vessel abstraction that binds together:
- Servant projects
- Community graph namespaces
- Constraint manifolds
- Privacy regimes
- Tier configurations
- Connectors
"""

from .vessel import Vessel, VesselConfig, PrivacyLevel, ConnectorConfig, TierConfig
from .registry import VesselRegistry
from .context import VesselContext, map_user_to_vessel, get_user_vessel_id

__all__ = [
    "Vessel",
    "VesselConfig",
    "PrivacyLevel",
    "ConnectorConfig",
    "TierConfig",
    "VesselRegistry",
    "VesselContext",
    "map_user_to_vessel",
    "get_user_vessel_id",
]

