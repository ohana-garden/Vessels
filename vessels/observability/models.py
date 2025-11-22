"""
Observability view models.

Simple dataclasses for presenting observability data.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class GatingEventView:
    """View model for a gating event."""
    agent_id: str
    timestamp: datetime
    event_type: str
    blocked: bool
    violations: List[str]
    reason: str
    vessel_id: Optional[str] = None
    action_hash: Optional[str] = None


@dataclass
class AttractorView:
    """View model for a phase space attractor."""
    attractor_id: int
    center: List[float]
    radius: float
    classification: str  # "good" or "bad"
    agent_count: int
    discovered_at: datetime
    vessel_id: Optional[str] = None


@dataclass
class VesselMetrics:
    """Aggregate metrics for a vessel."""
    vessel_id: str
    vessel_name: str

    # Virtue aggregates
    avg_truthfulness: float
    avg_justice: float
    avg_service: float
    avg_understanding: float

    # Operational aggregates
    total_actions: int
    blocked_actions: int
    corrected_actions: int

    # Temporal
    start_time: datetime
    end_time: datetime
    window_hours: float
