"""
Attractor discovery and classification.

Uses DBSCAN clustering on trajectory segments to discover
stable behavioral patterns (attractors) in the 12D phase space.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from sklearn.cluster import DBSCAN

from ..measurement.state import PhaseSpaceState


class AttractorClassification(Enum):
    """Classification of attractor behavior patterns."""
    BENEFICIAL = "beneficial"
    NEUTRAL = "neutral"
    DETRIMENTAL = "detrimental"


@dataclass
class Attractor:
    """
    A discovered attractor (stable behavioral region).

    Represents a cluster of similar behavioral states in phase space.
    """
    id: Optional[int]
    center: np.ndarray  # 12D center point
    radius: float  # Cluster spread
    agent_count: int  # How many agents orbit this attractor
    classification: AttractorClassification
    outcomes: Dict[str, float]  # Aggregated outcomes

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'id': self.id,
            'center': self.center.tolist(),
            'radius': float(self.radius),
            'agent_count': self.agent_count,
            'classification': self.classification.value,
            'outcomes': self.outcomes
        }


class AttractorDiscovery:
    """
    Discovers and classifies attractors from trajectories.

    Uses DBSCAN clustering on rolling windows of states.
    """

    def __init__(
        self,
        window_size: int = 10,
        eps: float = 0.3,
        min_samples: int = 5
    ):
        """
        Initialize attractor discovery.

        Args:
            window_size: Size of rolling window for trajectory segments
            eps: DBSCAN epsilon (max distance for neighborhood)
            min_samples: DBSCAN min samples for core point
        """
        self.window_size = window_size
        self.eps = eps
        self.min_samples = min_samples

    def discover_attractors(
        self,
        trajectories: Dict[str, List[PhaseSpaceState]],
        outcomes: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[Attractor]:
        """
        Discover attractors from agent trajectories.

        Args:
            trajectories: Dict mapping agent_id to list of states
            outcomes: Optional dict mapping agent_id to outcome metrics

        Returns:
            List of discovered attractors
        """
        outcomes = outcomes or {}

        # Extract trajectory segments (rolling windows)
        segments, segment_agents = self._extract_segments(trajectories)

        if len(segments) < self.min_samples:
            return []  # Not enough data for clustering

        # Cluster segments using DBSCAN
        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        labels = clustering.fit_predict(segments)

        # Build attractors from clusters
        attractors = []
        unique_labels = set(labels)
        unique_labels.discard(-1)  # Remove noise label

        for label in unique_labels:
            cluster_mask = labels == label
            cluster_segments = segments[cluster_mask]
            cluster_agents = [segment_agents[i] for i in range(len(segment_agents)) if cluster_mask[i]]

            # Compute cluster center and radius
            center = np.mean(cluster_segments, axis=0)
            distances = np.linalg.norm(cluster_segments - center, axis=1)
            radius = float(np.mean(distances))

            # Aggregate outcomes for agents in this cluster
            agent_outcomes = self._aggregate_outcomes(cluster_agents, outcomes)

            # Classify attractor
            classification = self._classify_attractor(center, agent_outcomes)

            attractor = Attractor(
                id=None,  # Will be set when stored
                center=center,
                radius=radius,
                agent_count=len(set(cluster_agents)),
                classification=classification,
                outcomes=agent_outcomes
            )

            attractors.append(attractor)

        return attractors

    def _extract_segments(
        self,
        trajectories: Dict[str, List[PhaseSpaceState]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Extract rolling window segments from trajectories.

        Returns:
            Tuple of (segments array, agent_ids list)
        """
        segments = []
        segment_agents = []

        for agent_id, states in trajectories.items():
            if len(states) < self.window_size:
                continue

            # Create rolling windows
            for i in range(len(states) - self.window_size + 1):
                window = states[i:i + self.window_size]

                # Average state over window
                vectors = np.array([s.to_vector() for s in window])
                avg_state = np.mean(vectors, axis=0)

                segments.append(avg_state)
                segment_agents.append(agent_id)

        return np.array(segments), segment_agents

    def _aggregate_outcomes(
        self,
        agent_ids: List[str],
        outcomes: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Aggregate outcome metrics for agents in a cluster."""
        # Collect all outcomes
        all_outcomes = [outcomes.get(aid, {}) for aid in agent_ids]

        if not all_outcomes:
            return {
                'effectiveness': 0.5,
                'resource_consumption': 0.5,
                'user_feedback': 0.0,
                'security_events': 0.0,
                'task_complexity': 0.0,
                'urgency': 0.0
            }

        # Average each metric
        aggregated = {}
        keys = ['effectiveness', 'resource_consumption', 'user_feedback',
                'security_events', 'task_complexity', 'urgency']

        for key in keys:
            values = [o.get(key, 0.0) for o in all_outcomes if key in o]
            aggregated[key] = float(np.mean(values)) if values else 0.0

        return aggregated

    def _classify_attractor(
        self,
        center: np.ndarray,
        outcomes: Dict[str, float]
    ) -> AttractorClassification:
        """
        Classify attractor as beneficial, neutral, or detrimental.

        Implements context-aware classification from spec v1.1 section 6.2.

        EFFICIENCY BIAS WARNING (spec section 6.3):
        This classifier has a built-in efficiency bias - it penalizes high
        resource consumption by default. Discount applied for complexity/urgency,
        but baseline assumption is "cheaper is better".

        This encourages agents toward "cheap, effective, liked" basins and away
        from "expensive, deeply investigative" patterns unless task_complexity
        is explicitly set high.

        This is a deliberate value judgment. Domain manifolds may override.
        """
        effectiveness = outcomes.get('effectiveness', 0.0)
        resource_consumption = outcomes.get('resource_consumption', 0.0)
        feedback = outcomes.get('user_feedback', 0.0)
        security_events = outcomes.get('security_events', 0.0)
        complexity = outcomes.get('task_complexity', 0.0)
        urgency = outcomes.get('urgency', 0.0)

        # Context-aware cost adjustment (spec section 6.2)
        # High complexity or urgency justifies higher resource use
        complexity_factor = 0.5 + (complexity * 0.5)  # Range: 0.5 to 1.0
        urgency_factor = 0.5 + (urgency * 0.5)        # Range: 0.5 to 1.0
        cost_tolerance = max(complexity_factor, urgency_factor)

        # Adjusted cost penalty (lower penalty for complex/urgent tasks)
        cost_penalty = max(0, resource_consumption - cost_tolerance)

        # Security events are always bad
        security_penalty = security_events * 2.0

        # Effectiveness and feedback are good
        positive_score = (effectiveness + feedback) / 2.0

        # Net score
        score = positive_score - cost_penalty - security_penalty

        # Classification thresholds
        if score > 0.6 and security_events < 0.1:
            return AttractorClassification.BENEFICIAL
        elif score < 0.3 or security_events > 0.3:
            return AttractorClassification.DETRIMENTAL
        else:
            return AttractorClassification.NEUTRAL

    def find_nearest_attractor(
        self,
        state: PhaseSpaceState,
        attractors: List[Attractor]
    ) -> Optional[Attractor]:
        """
        Find the nearest attractor to a given state.

        Args:
            state: Current state
            attractors: List of known attractors

        Returns:
            Nearest attractor, or None if no attractors
        """
        if not attractors:
            return None

        state_vec = state.to_vector()
        distances = [np.linalg.norm(state_vec - a.center) for a in attractors]
        nearest_idx = np.argmin(distances)

        return attractors[nearest_idx]

    def is_in_attractor(
        self,
        state: PhaseSpaceState,
        attractor: Attractor,
        threshold_multiplier: float = 2.0
    ) -> bool:
        """
        Check if a state is within an attractor's basin.

        Args:
            state: State to check
            attractor: Attractor to check against
            threshold_multiplier: Multiplier on radius for basin boundary

        Returns:
            True if state is in attractor basin
        """
        state_vec = state.to_vector()
        distance = np.linalg.norm(state_vec - attractor.center)

        return distance <= (attractor.radius * threshold_multiplier)

    def compute_trajectory_velocity(
        self,
        trajectory: List[PhaseSpaceState]
    ) -> Optional[np.ndarray]:
        """
        Compute average velocity (direction of movement) for a trajectory.

        Returns:
            12D velocity vector, or None if trajectory too short
        """
        if len(trajectory) < 2:
            return None

        vectors = np.array([s.to_vector() for s in trajectory])

        # Compute differences between consecutive states
        diffs = np.diff(vectors, axis=0)

        # Average velocity
        velocity = np.mean(diffs, axis=0)

        return velocity

    def predict_attractor_approach(
        self,
        current_state: PhaseSpaceState,
        velocity: np.ndarray,
        attractors: List[Attractor],
        steps_ahead: int = 5
    ) -> Optional[Attractor]:
        """
        Predict which attractor an agent is approaching.

        Args:
            current_state: Current state
            velocity: Current velocity vector
            attractors: List of known attractors
            steps_ahead: How many steps to project forward

        Returns:
            Attractor being approached, or None
        """
        if not attractors:
            return None

        # Project state forward
        projected_vec = current_state.to_vector() + (velocity * steps_ahead)

        # Find nearest attractor to projected position
        distances = [np.linalg.norm(projected_vec - a.center) for a in attractors]
        nearest_idx = np.argmin(distances)

        return attractors[nearest_idx]
