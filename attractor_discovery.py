"""
Attractor Discovery - Finds and classifies stable regions in the moral manifold.

This module uses DBSCAN clustering to discover attractors in agent trajectories.
High-Justice states naturally form strong attractors due to their high coupling density.
"""

from typing import Dict, List, Tuple, Optional, Set
import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict
import logging

from bahai_manifold import BahaiManifold
from phase_space_tracker import PhaseSpaceTracker


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Attractor:
    """
    Represents a stable region (attractor) in the phase space.

    Attractors are regions where agent states cluster together,
    indicating stable configurations in the moral manifold.
    """

    def __init__(self, cluster_id: int, states: np.ndarray, virtue_names: List[str]):
        """
        Initialize an attractor.

        Args:
            cluster_id: Unique identifier for this cluster.
            states: N x 14 array of states in this attractor.
            virtue_names: Names of the 14 virtues (for interpretation).
        """
        self.cluster_id = cluster_id
        self.states = states
        self.virtue_names = virtue_names
        self.size = len(states)

        # Calculate centroid (center of the attractor)
        self.centroid = np.mean(states, axis=0)
        self.centroid_dict = {virtue_names[i]: self.centroid[i]
                             for i in range(len(virtue_names))}

        # Calculate spread (standard deviation in each dimension)
        self.spread = np.std(states, axis=0)
        self.spread_dict = {virtue_names[i]: self.spread[i]
                           for i in range(len(virtue_names))}

        # Calculate radius (max distance from centroid)
        distances = np.sqrt(np.sum((states - self.centroid) ** 2, axis=1))
        self.radius = np.max(distances)

    def __repr__(self):
        return f"Attractor(id={self.cluster_id}, size={self.size}, radius={self.radius:.3f})"

    def get_dominant_virtues(self, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Get the virtues with highest values in this attractor.

        Args:
            top_n: Number of top virtues to return.

        Returns:
            List of (virtue_name, value) tuples, sorted by value descending.
        """
        virtue_values = [(self.virtue_names[i], self.centroid[i])
                        for i in range(len(self.virtue_names))]
        virtue_values.sort(key=lambda x: x[1], reverse=True)
        return virtue_values[:top_n]

    def is_high_justice(self, threshold: float = 0.7) -> bool:
        """
        Check if this is a high-justice attractor.

        High-justice attractors are expected to be the most beneficial
        due to justice being the hub node with maximum coupling connectivity.

        Args:
            threshold: Justice value threshold.

        Returns:
            True if centroid justice >= threshold.
        """
        justice_idx = self.virtue_names.index('justice')
        return self.centroid[justice_idx] >= threshold


class AttractorDiscoverer:
    """
    Discovers attractors in the phase space using DBSCAN clustering.

    Identifies stable regions where agent states cluster, classifies them
    by their properties (especially justice level), and analyzes their
    characteristics.
    """

    def __init__(self, manifold: Optional[BahaiManifold] = None,
                 tracker: Optional[PhaseSpaceTracker] = None):
        """
        Initialize the attractor discoverer.

        Args:
            manifold: BahaiManifold instance.
            tracker: PhaseSpaceTracker instance.
        """
        self.manifold = manifold or BahaiManifold()
        self.tracker = tracker

    def discover_attractors(self, states: np.ndarray,
                          eps: float = 0.3,
                          min_samples: int = 5) -> List[Attractor]:
        """
        Discover attractors using DBSCAN clustering.

        Args:
            states: N x 14 array of agent states.
            eps: DBSCAN epsilon parameter (maximum distance for points to be neighbors).
            min_samples: Minimum samples to form a cluster.

        Returns:
            List of Attractor objects, sorted by size (descending).
        """
        if len(states) < min_samples:
            logger.warning(f"Not enough states ({len(states)}) for clustering (need >= {min_samples})")
            return []

        # Run DBSCAN
        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean')
        labels = clusterer.fit_predict(states)

        # Extract clusters (ignore noise points labeled -1)
        cluster_ids = set(labels) - {-1}

        attractors = []
        for cluster_id in cluster_ids:
            cluster_mask = labels == cluster_id
            cluster_states = states[cluster_mask]

            attractor = Attractor(cluster_id, cluster_states, self.manifold.ALL_VIRTUES)
            attractors.append(attractor)

        # Sort by size (descending)
        attractors.sort(key=lambda a: a.size, reverse=True)

        logger.info(f"Discovered {len(attractors)} attractors from {len(states)} states")
        logger.info(f"Noise points: {np.sum(labels == -1)}")

        return attractors

    def discover_from_tracker(self,
                            start_time: Optional[float] = None,
                            end_time: Optional[float] = None,
                            eps: float = 0.3,
                            min_samples: int = 5) -> List[Attractor]:
        """
        Discover attractors from tracked trajectories.

        Args:
            start_time: Start timestamp for data to include.
            end_time: End timestamp for data to include.
            eps: DBSCAN epsilon parameter.
            min_samples: Minimum samples to form a cluster.

        Returns:
            List of Attractor objects.
        """
        if self.tracker is None:
            raise ValueError("No tracker provided to discover_from_tracker")

        states, agent_ids, timestamps = self.tracker.get_states_matrix(start_time, end_time)

        if len(states) == 0:
            logger.warning("No states found in tracker for the given time period")
            return []

        return self.discover_attractors(states, eps, min_samples)

    def classify_attractors(self, attractors: List[Attractor]) -> Dict[str, List[Attractor]]:
        """
        Classify attractors by their characteristics.

        Args:
            attractors: List of attractors to classify.

        Returns:
            Dictionary mapping classification to list of attractors:
            - 'high_justice': Justice >= 0.7 (hub attractor - most beneficial)
            - 'moderate_justice': 0.4 <= Justice < 0.7
            - 'low_justice': Justice < 0.4
        """
        classification = {
            'high_justice': [],
            'moderate_justice': [],
            'low_justice': []
        }

        for attractor in attractors:
            justice_idx = self.manifold.ALL_VIRTUES.index('justice')
            justice_value = attractor.centroid[justice_idx]

            if justice_value >= 0.7:
                classification['high_justice'].append(attractor)
            elif justice_value >= 0.4:
                classification['moderate_justice'].append(attractor)
            else:
                classification['low_justice'].append(attractor)

        return classification

    def analyze_attractor_stability(self, attractor: Attractor) -> Dict[str, float]:
        """
        Analyze the stability characteristics of an attractor.

        Args:
            attractor: Attractor to analyze.

        Returns:
            Dictionary with stability metrics:
            - 'radius': Maximum distance from centroid
            - 'avg_spread': Average standard deviation across dimensions
            - 'justice': Justice value at centroid
            - 'truthfulness': Truthfulness value at centroid
            - 'coupling_density': Measure of how many virtues are above thresholds
        """
        justice_idx = self.manifold.ALL_VIRTUES.index('justice')
        truthfulness_idx = self.manifold.ALL_VIRTUES.index('truthfulness')

        # Count how many virtues are above moderate threshold (0.6)
        virtues_above_threshold = np.sum(attractor.centroid > 0.6)

        metrics = {
            'radius': attractor.radius,
            'avg_spread': np.mean(attractor.spread),
            'justice': attractor.centroid[justice_idx],
            'truthfulness': attractor.centroid[truthfulness_idx],
            'coupling_density': virtues_above_threshold / len(self.manifold.ALL_VIRTUES)
        }

        return metrics

    def get_basin_of_attraction(self, attractor: Attractor,
                                states: np.ndarray,
                                radius_multiplier: float = 1.5) -> np.ndarray:
        """
        Get the basin of attraction - all states within a certain radius.

        Args:
            attractor: The attractor.
            states: N x 14 array of all states to check.
            radius_multiplier: How much larger than attractor radius to search.

        Returns:
            Boolean mask indicating which states are in the basin.
        """
        distances = np.sqrt(np.sum((states - attractor.centroid) ** 2, axis=1))
        basin_radius = attractor.radius * radius_multiplier
        return distances <= basin_radius

    def compare_attractors(self, attr1: Attractor, attr2: Attractor) -> Dict[str, float]:
        """
        Compare two attractors.

        Args:
            attr1: First attractor.
            attr2: Second attractor.

        Returns:
            Dictionary with comparison metrics:
            - 'centroid_distance': Euclidean distance between centroids
            - 'size_ratio': Size of attr1 / size of attr2
            - 'justice_diff': Justice value difference (attr1 - attr2)
        """
        centroid_distance = np.sqrt(np.sum((attr1.centroid - attr2.centroid) ** 2))

        justice_idx = self.manifold.ALL_VIRTUES.index('justice')
        justice_diff = attr1.centroid[justice_idx] - attr2.centroid[justice_idx]

        return {
            'centroid_distance': centroid_distance,
            'size_ratio': attr1.size / attr2.size if attr2.size > 0 else float('inf'),
            'justice_diff': justice_diff
        }

    def find_nearest_attractor(self, state: Dict[str, float],
                              attractors: List[Attractor]) -> Optional[Tuple[Attractor, float]]:
        """
        Find the nearest attractor to a given state.

        Args:
            state: State to check.
            attractors: List of attractors to search.

        Returns:
            Tuple of (nearest_attractor, distance) or None if no attractors.
        """
        if not attractors:
            return None

        # Convert state to array
        state_array = np.array([state[virtue] for virtue in self.manifold.ALL_VIRTUES])

        # Calculate distances to all attractors
        distances = []
        for attractor in attractors:
            dist = np.sqrt(np.sum((state_array - attractor.centroid) ** 2))
            distances.append(dist)

        # Find minimum
        min_idx = np.argmin(distances)
        return attractors[min_idx], distances[min_idx]

    def generate_report(self, attractors: List[Attractor]) -> str:
        """
        Generate a human-readable report about discovered attractors.

        Args:
            attractors: List of attractors to report on.

        Returns:
            Formatted string report.
        """
        if not attractors:
            return "No attractors discovered."

        lines = []
        lines.append(f"\n=== Attractor Discovery Report ===")
        lines.append(f"Total attractors found: {len(attractors)}\n")

        # Classify
        classified = self.classify_attractors(attractors)

        lines.append(f"High-Justice attractors (≥0.7): {len(classified['high_justice'])}")
        lines.append(f"Moderate-Justice attractors (0.4-0.7): {len(classified['moderate_justice'])}")
        lines.append(f"Low-Justice attractors (<0.4): {len(classified['low_justice'])}\n")

        # Detail each attractor
        for i, attractor in enumerate(attractors[:10]):  # Top 10
            lines.append(f"--- Attractor {i+1} ---")
            lines.append(f"Size: {attractor.size} states")
            lines.append(f"Radius: {attractor.radius:.3f}")

            stability = self.analyze_attractor_stability(attractor)
            lines.append(f"Justice: {stability['justice']:.3f}")
            lines.append(f"Truthfulness: {stability['truthfulness']:.3f}")
            lines.append(f"Coupling density: {stability['coupling_density']:.3f}")

            dominant = attractor.get_dominant_virtues(3)
            lines.append(f"Top virtues: {', '.join([f'{v}={val:.2f}' for v, val in dominant])}")
            lines.append("")

        if len(attractors) > 10:
            lines.append(f"... and {len(attractors) - 10} more attractors")

        return '\n'.join(lines)
