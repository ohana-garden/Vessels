"""
Observability service.

Provides queries for gating events, attractors, and vessel metrics.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from vessels.phase_space.tracker import TrajectoryTracker
from vessels.core import VesselRegistry
from .models import GatingEventView, AttractorView, VesselMetrics

logger = logging.getLogger(__name__)


class ObservabilityService:
    """
    Service for querying observability data.

    Provides unified access to:
    - Gating events
    - Phase space attractors
    - Vessel-level metrics
    """

    def __init__(
        self,
        tracker: TrajectoryTracker,
        vessel_registry: VesselRegistry
    ):
        """
        Initialize observability service.

        Args:
            tracker: Trajectory tracker for events and states
            vessel_registry: Vessel registry for vessel metadata
        """
        self.tracker = tracker
        self.vessel_registry = vessel_registry

    def list_gating_events(
        self,
        vessel_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 50,
        blocked_only: bool = False
    ) -> List[GatingEventView]:
        """
        List recent gating events.

        Args:
            vessel_id: Filter by vessel (requires mapping agent->vessel)
            agent_id: Filter by agent
            limit: Maximum number of events to return
            blocked_only: Only return blocked events

        Returns:
            List of gating event views
        """
        # Get security events from tracker
        events = self.tracker.get_security_events(
            agent_id=agent_id,
            blocked_only=blocked_only,
            limit=limit
        )

        # Convert to views
        views = []
        for event in events:
            view = GatingEventView(
                agent_id=event.agent_id,
                timestamp=event.timestamp,
                event_type=event.event_type,
                blocked=event.blocked,
                violations=event.violations,
                reason=self._summarize_violations(event.violations, event.blocked),
                action_hash=event.action_hash
            )
            views.append(view)

        # Filter by vessel if requested (requires agent->vessel mapping)
        if vessel_id:
            views = [v for v in views if self._agent_belongs_to_vessel(v.agent_id, vessel_id)]

        return views

    def list_attractors(
        self,
        vessel_id: Optional[str] = None
    ) -> List[AttractorView]:
        """
        List discovered phase space attractors.

        Args:
            vessel_id: Filter by vessel

        Returns:
            List of attractor views
        """
        # Query attractors from database
        cursor = self.tracker.conn.cursor()

        query = "SELECT * FROM attractors ORDER BY discovered_at DESC"
        cursor.execute(query)

        views = []
        for row in cursor.fetchall():
            view = AttractorView(
                attractor_id=row[0],
                center=eval(row[1]),  # JSON string to list
                radius=row[2],
                classification=row[3],
                agent_count=row[4],
                discovered_at=datetime.fromisoformat(row[5])
            )
            views.append(view)

        return views

    def get_vessel_metrics(
        self,
        vessel_id: str,
        window_hours: float = 24.0
    ) -> VesselMetrics:
        """
        Get aggregate metrics for a vessel.

        Args:
            vessel_id: Vessel ID
            window_hours: Time window in hours for aggregation

        Returns:
            Vessel metrics
        """
        vessel = self.vessel_registry.get_vessel(vessel_id)
        if vessel is None:
            raise ValueError(f"Vessel {vessel_id} not found")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=window_hours)

        # Get all agents for this vessel
        agent_ids = self._get_agents_for_vessel(vessel_id)

        # Aggregate metrics
        total_actions = 0
        blocked_actions = 0
        corrected_actions = 0

        virtue_sums = {"truthfulness": 0.0, "justice": 0.0, "service": 0.0, "understanding": 0.0}
        virtue_counts = {"truthfulness": 0, "justice": 0, "service": 0, "understanding": 0}

        for agent_id in agent_ids:
            # Get trajectory for this agent
            states = self.tracker.get_trajectory(agent_id, limit=1000)

            # Filter by time window
            states = [s for s in states if start_time <= s.timestamp <= end_time]

            # Aggregate virtues
            for state in states:
                for virtue in ["truthfulness", "justice", "service", "understanding"]:
                    value = getattr(state.virtue, virtue, None)
                    if value is not None:
                        virtue_sums[virtue] += value
                        virtue_counts[virtue] += 1

            # Get gating events
            events = self.tracker.get_security_events(agent_id=agent_id)

            # Filter by time window
            events = [e for e in events if start_time <= e.timestamp <= end_time]

            total_actions += len(events)
            blocked_actions += sum(1 for e in events if e.blocked)
            corrected_actions += sum(
                1 for e in events
                if not e.blocked and e.corrected_virtue_state is not None
            )

        # Calculate averages
        avg_virtues = {
            k: (virtue_sums[k] / virtue_counts[k] if virtue_counts[k] > 0 else 0.0)
            for k in virtue_sums
        }

        return VesselMetrics(
            vessel_id=vessel_id,
            vessel_name=vessel.name,
            avg_truthfulness=avg_virtues["truthfulness"],
            avg_justice=avg_virtues["justice"],
            avg_service=avg_virtues["service"],
            avg_understanding=avg_virtues["understanding"],
            total_actions=total_actions,
            blocked_actions=blocked_actions,
            corrected_actions=corrected_actions,
            start_time=start_time,
            end_time=end_time,
            window_hours=window_hours
        )

    def _summarize_violations(self, violations: List[str], blocked: bool) -> str:
        """Summarize violations into a human-readable reason."""
        if not violations:
            return "No violations"
        if blocked:
            return f"Blocked: {', '.join(violations[:3])}"
        return f"Corrected: {', '.join(violations[:3])}"

    def _agent_belongs_to_vessel(self, agent_id: str, vessel_id: str) -> bool:
        """Check if an agent belongs to a vessel (stub - needs agent->vessel mapping)."""
        # TODO: Implement agent->vessel mapping
        return True

    def _get_agents_for_vessel(self, vessel_id: str) -> List[str]:
        """Get all agent IDs for a vessel (stub - needs agent->vessel mapping)."""
        # TODO: Implement agent->vessel mapping
        # For now, return project IDs as agent IDs
        vessel = self.vessel_registry.get_vessel(vessel_id)
        return vessel.servant_project_ids if vessel else []
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
