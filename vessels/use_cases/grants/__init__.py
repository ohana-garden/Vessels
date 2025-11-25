"""
Grants Use Case - Vessel-based grant management.

This module provides grant discovery, writing, and coordination as a Vessels use case.
All grant operations occur within a Vessel context, ensuring:
- Data is stored in the vessel's knowledge graph
- Actions are gated through the vessel's action gate
- Progress is tracked through vessel measurement
- Community memory learns from grant outcomes

Example usage:
    from vessels.core import VesselRegistry
    from vessels.use_cases.grants import GrantsUseCase

    # Get or create a vessel for grant management
    registry = VesselRegistry()
    vessel = registry.create_vessel("Elder Care Grants", "lower_puna_community")

    # Create grants use case for this vessel
    grants = GrantsUseCase(vessel)

    # Discover grants
    opportunities = grants.discover_grants(focus_areas=["elder_care", "healthcare"])

    # Generate application for a grant
    application = grants.create_application(grant_id="grant-123")
"""

from .models import GrantOpportunity, GrantApplication, GrantStatus
from .repository import GrantRepository
from .discovery import GrantDiscoveryService
from .writer import GrantApplicationWriter
from .use_case import GrantsUseCase

__all__ = [
    "GrantOpportunity",
    "GrantApplication",
    "GrantStatus",
    "GrantRepository",
    "GrantDiscoveryService",
    "GrantApplicationWriter",
    "GrantsUseCase",
]
