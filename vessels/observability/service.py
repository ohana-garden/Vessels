from typing import List, Optional

from vessels.phase_space.tracker import TrajectoryTracker

from .models import AttractorView, GatingEventView, VesselMetrics


class ObservabilityService:
    """Expose observability views over gating and phase space data."""

    def __init__(self, tracker: Optional[TrajectoryTracker] = None):
        self.tracker = tracker or TrajectoryTracker()

    def list_gating_events(
        self, vessel_id: Optional[str] = None, agent_id: Optional[str] = None, limit: int = 50
    ) -> List[GatingEventView]:
        events = self.tracker.get_security_events(agent_id=agent_id, limit=limit)
        views: List[GatingEventView] = []
        for event in events:
            metadata = event.metadata or {}
            if vessel_id and metadata.get("vessel_id") != vessel_id:
                continue
            views.append(
                GatingEventView(
                    agent_id=event.agent_id,
                    blocked=event.blocked,
                    event_type=event.event_type,
                    timestamp=event.timestamp,
                    vessel_id=metadata.get("vessel_id"),
                    metadata=metadata,
                )
            )
        return views

    def list_attractors(self, vessel_id: Optional[str] = None) -> List[AttractorView]:
        attractors = self.tracker.get_attractors()
        views: List[AttractorView] = []
        for attr in attractors:
            metadata = attr.get("metadata", {}) or {}
            if vessel_id and metadata.get("vessel_id") != vessel_id:
                continue
            views.append(
                AttractorView(
                    attractor_id=attr["id"],
                    classification=attr["classification"],
                    discovered_at=attr["discovered_at"],
                    metadata=metadata,
                )
            )
        return views

    def get_vessel_metrics(self, vessel_id: str) -> VesselMetrics:
        events = self.list_gating_events(vessel_id=vessel_id)
        total = len(events)
        blocked = len([e for e in events if e.blocked])
        return VesselMetrics(vessel_id=vessel_id, total_events=total, blocked_events=blocked)
