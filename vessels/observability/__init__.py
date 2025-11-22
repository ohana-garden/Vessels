"""
Observability layer for Vessels.

Provides visibility into gating decisions, phase space trajectories,
and cross-vessel interactions.
"""

from .models import GatingEventView, AttractorView, VesselMetrics
from .service import ObservabilityService

__all__ = [
    "GatingEventView",
    "AttractorView",
    "VesselMetrics",
    "ObservabilityService",
]
