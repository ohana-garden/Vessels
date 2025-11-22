"""
Observability view models.

Simple dataclasses for presenting observability data.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


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
    agent_id: str
    blocked: bool
    event_type: str
    timestamp: datetime
    vessel_id: Optional[str]
    metadata: Dict


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
    attractor_id: int
    classification: str
    discovered_at: str
    metadata: Dict


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
    vessel_id: str
    total_events: int
    blocked_events: int
