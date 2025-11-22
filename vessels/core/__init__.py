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

from .vessel import Vessel, VesselConfig, PrivacyLevel, ConnectorConfig
from .registry import VesselRegistry

__all__ = [
    "Vessel",
    "VesselConfig",
    "PrivacyLevel",
    "ConnectorConfig",
    "VesselRegistry",
]
