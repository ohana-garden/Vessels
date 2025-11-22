from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class GatingEventView:
    agent_id: str
    blocked: bool
    event_type: str
    timestamp: datetime
    vessel_id: Optional[str]
    metadata: Dict


@dataclass
class AttractorView:
    attractor_id: int
    classification: str
    discovered_at: str
    metadata: Dict


@dataclass
class VesselMetrics:
    vessel_id: str
    total_events: int
    blocked_events: int
