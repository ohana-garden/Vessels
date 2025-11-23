"""
Observability service.

Provides queries for gating events, attractors, and vessel metrics.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from vessels.core import VesselRegistry
from vessels.phase_space.tracker import TrajectoryTracker
from .models import AttractorView, GatingEventView, VesselMetrics

logger = logging.getLogger(__name__)


class ObservabilityService:
    """Expose observability views over gating and phase space data."""

    def __init__(
        self,
        tracker: TrajectoryTracker,
        vessel_registry: Optional[VesselRegistry] = None,
    ):
        self.tracker = tracker
        self.vessel_registry = vessel_registry

    def list_gating_events(
        self,
        vessel_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        blocked_only: bool = False,
    ) -> List[GatingEventView]:
        events = self.tracker.get_security_events(
            agent_id=agent_id,
            blocked_only=blocked_only,
            limit=limit,
        )

        views: List[GatingEventView] = []
        for event in events:
            metadata = event.metadata or {}
            view = GatingEventView(
                agent_id=event.agent_id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                blocked=event.blocked,
                violations=event.violations,
                reason=self._summarize_violations(event.violations, event.blocked),
                action_hash=event.action_hash,
                vessel_id=metadata.get("vessel_id"),
                metadata=metadata,
            )
            if vessel_id and view.vessel_id != vessel_id:
                continue
            views.append(view)

        return views

    def list_attractors(self, vessel_id: Optional[str] = None) -> List[AttractorView]:
        cursor = self.tracker.conn.cursor()
        cursor.execute("SELECT * FROM attractors ORDER BY discovered_at DESC")

        views: List[AttractorView] = []
        for row in cursor.fetchall():
            metadata = json.loads(row[7]) if len(row) > 7 and row[7] else {}
            outcomes = json.loads(row[6]) if len(row) > 6 and row[6] else None
            vessel_from_metadata = metadata.get("vessel_id") if isinstance(metadata, dict) else None
            if vessel_id and vessel_from_metadata != vessel_id:
                continue

            views.append(
                AttractorView(
                    attractor_id=row[0],
                    center=json.loads(row[1]),
                    radius=row[2],
                    classification=row[3],
                    agent_count=row[4],
                    discovered_at=datetime.fromisoformat(row[5]),
                    outcomes=outcomes,
                    metadata=metadata if isinstance(metadata, dict) else {},
                    vessel_id=vessel_from_metadata,
                )
            )

        return views

    def get_vessel_metrics(self, vessel_id: str, window_hours: float = 24.0) -> VesselMetrics:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=window_hours)

        events = self.tracker.get_security_events()
        filtered_events = [
            e
            for e in events
            if start_time <= e.timestamp <= end_time
            and ((e.metadata or {}).get("vessel_id") == vessel_id if vessel_id else True)
        ]

        total_events = len(filtered_events)
        blocked_events = sum(1 for e in filtered_events if e.blocked)
        corrected_events = sum(
            1 for e in filtered_events if not e.blocked and e.corrected_virtue_state is not None
        )

        vessel_name = ""
        if self.vessel_registry:
            vessel = self.vessel_registry.get_vessel(vessel_id)
            vessel_name = vessel.name if vessel else ""

        return VesselMetrics(
            vessel_id=vessel_id,
            total_events=total_events,
            blocked_events=blocked_events,
            corrected_events=corrected_events,
            start_time=start_time,
            end_time=end_time,
            vessel_name=vessel_name,
            window_hours=window_hours,
        )

    def _summarize_violations(self, violations: List[str], blocked: bool) -> str:
        if not violations:
            return "No violations"
        if blocked:
            return f"Blocked: {', '.join(violations[:3])}"
        return f"Corrected: {', '.join(violations[:3])}"
