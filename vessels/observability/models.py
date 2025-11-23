"""Simple dataclasses for presenting observability data."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class GatingEventView:
    """View model for a gating event."""

    agent_id: str
    timestamp: datetime
    event_type: str
    blocked: bool
    violations: List[str]
    reason: str
    action_hash: Optional[str] = None
    vessel_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttractorView:
    """View model for a phase space attractor."""

    attractor_id: int
    center: List[float]
    radius: float
    classification: str  # "good" or "bad"
    agent_count: int
    discovered_at: datetime
    outcomes: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    vessel_id: Optional[str] = None


@dataclass
class VesselMetrics:
    """Aggregate metrics for a vessel."""

    vessel_id: str
    total_events: int
    blocked_events: int
    corrected_events: int
    start_time: datetime
    end_time: datetime
    vessel_name: str = ""
    window_hours: float = 24.0
    avg_truthfulness: float = 0.0
    avg_justice: float = 0.0
    avg_service: float = 0.0
    avg_understanding: float = 0.0
