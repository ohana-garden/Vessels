"""
State data structures for the Vessels moral constraint system.

Defines the 12-dimensional phase space:
- 5D operational state (directly measurable)
- 7D virtue state (inferred from behavior)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import numpy as np
from datetime import datetime


class Dimension(Enum):
    """
    Enumeration of all dimensions in the Vessels phase space.

    5 Operational dimensions (directly measurable):
    - ACTIVITY_LEVEL: Operational intensity
    - COORDINATION_DENSITY: Collaboration frequency
    - EFFECTIVENESS: Task completion quality
    - RESOURCE_CONSUMPTION: Compute/API costs
    - SYSTEM_HEALTH: Error rates, stability

    7 Virtue dimensions (inferred from behavior):
    - TRUTHFULNESS: Factual accuracy, absence of deception
    - JUSTICE: Fair treatment, awareness of power asymmetries
    - TRUSTWORTHINESS: Reliability, follow-through on commitments
    - UNITY: Collaboration quality, conflict reduction
    - SERVICE: Benefit to others vs self-serving behavior
    - DETACHMENT: Ego-detachment (right action vs personal credit)
    - UNDERSTANDING: Depth of comprehension, context awareness
    """
    # Operational dimensions
    ACTIVITY_LEVEL = "activity_level"
    COORDINATION_DENSITY = "coordination_density"
    EFFECTIVENESS = "effectiveness"
    RESOURCE_CONSUMPTION = "resource_consumption"
    SYSTEM_HEALTH = "system_health"

    # Virtue dimensions
    TRUTHFULNESS = "truthfulness"
    JUSTICE = "justice"
    TRUSTWORTHINESS = "trustworthiness"
    UNITY = "unity"
    SERVICE = "service"
    DETACHMENT = "detachment"
    UNDERSTANDING = "understanding"

    @classmethod
    def virtue_dimensions(cls) -> List['Dimension']:
        """Return all virtue dimensions."""
        return [
            cls.TRUTHFULNESS,
            cls.JUSTICE,
            cls.TRUSTWORTHINESS,
            cls.UNITY,
            cls.SERVICE,
            cls.DETACHMENT,
            cls.UNDERSTANDING,
        ]

    @classmethod
    def operational_dimensions(cls) -> List['Dimension']:
        """Return all operational dimensions."""
        return [
            cls.ACTIVITY_LEVEL,
            cls.COORDINATION_DENSITY,
            cls.EFFECTIVENESS,
            cls.RESOURCE_CONSUMPTION,
            cls.SYSTEM_HEALTH,
        ]


@dataclass
class OperationalState:
    """5-dimensional operational state vector (directly measurable)."""
    activity_level: float  # 0-1: operational intensity
    coordination_density: float  # 0-1: collaboration frequency
    effectiveness: float  # 0-1: task completion quality
    resource_consumption: float  # 0-1: compute/API costs
    system_health: float  # 0-1: error rates, stability

    def to_vector(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([
            self.activity_level,
            self.coordination_density,
            self.effectiveness,
            self.resource_consumption,
            self.system_health
        ])

    @classmethod
    def from_vector(cls, vec: np.ndarray) -> 'OperationalState':
        """Create from numpy array."""
        return cls(
            activity_level=float(vec[0]),
            coordination_density=float(vec[1]),
            effectiveness=float(vec[2]),
            resource_consumption=float(vec[3]),
            system_health=float(vec[4])
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'activity_level': self.activity_level,
            'coordination_density': self.coordination_density,
            'effectiveness': self.effectiveness,
            'resource_consumption': self.resource_consumption,
            'system_health': self.system_health
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'OperationalState':
        """Create from dictionary."""
        return cls(**d)


@dataclass
class VirtueState:
    """7-dimensional virtue state vector (inferred from behavior)."""
    truthfulness: float  # factual accuracy, absence of deception
    justice: float  # fair treatment, awareness of power asymmetries
    trustworthiness: float  # reliability, follow-through on commitments
    unity: float  # collaboration quality, conflict reduction
    service: float  # benefit to others vs self-serving behavior
    detachment: float  # ego-detachment (right action vs personal credit)
    understanding: float  # depth of comprehension, context awareness

    def to_vector(self) -> np.ndarray:
        """Convert to numpy array."""
        return np.array([
            self.truthfulness,
            self.justice,
            self.trustworthiness,
            self.unity,
            self.service,
            self.detachment,
            self.understanding
        ])

    @classmethod
    def from_vector(cls, vec: np.ndarray) -> 'VirtueState':
        """Create from numpy array."""
        return cls(
            truthfulness=float(vec[0]),
            justice=float(vec[1]),
            trustworthiness=float(vec[2]),
            unity=float(vec[3]),
            service=float(vec[4]),
            detachment=float(vec[5]),
            understanding=float(vec[6])
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'truthfulness': self.truthfulness,
            'justice': self.justice,
            'trustworthiness': self.trustworthiness,
            'unity': self.unity,
            'service': self.service,
            'detachment': self.detachment,
            'understanding': self.understanding
        }

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> 'VirtueState':
        """Create from dictionary."""
        return cls(**d)


@dataclass
class PhaseSpaceState:
    """
    Complete 12-dimensional phase space state.

    Combines operational (5D) and virtue (7D) states with confidence scores.
    """
    operational: OperationalState
    virtue: VirtueState
    confidence: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: Optional[str] = None

    def to_vector(self) -> np.ndarray:
        """Convert to 12D numpy array."""
        return np.concatenate([
            self.operational.to_vector(),
            self.virtue.to_vector()
        ])

    @classmethod
    def from_vector(cls, vec: np.ndarray, agent_id: Optional[str] = None) -> 'PhaseSpaceState':
        """Create from 12D numpy array."""
        return cls(
            operational=OperationalState.from_vector(vec[:5]),
            virtue=VirtueState.from_vector(vec[5:]),
            agent_id=agent_id
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'operational': self.operational.to_dict(),
            'virtue': self.virtue.to_dict(),
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'agent_id': self.agent_id
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'PhaseSpaceState':
        """Create from dictionary."""
        return cls(
            operational=OperationalState.from_dict(d['operational']),
            virtue=VirtueState.from_dict(d['virtue']),
            confidence=d.get('confidence', {}),
            timestamp=datetime.fromisoformat(d['timestamp']) if 'timestamp' in d else datetime.utcnow(),
            agent_id=d.get('agent_id')
        )

    def euclidean_distance(self, other: 'PhaseSpaceState') -> float:
        """Calculate Euclidean distance to another state."""
        return float(np.linalg.norm(self.to_vector() - other.to_vector()))

    def virtue_distance(self, other: 'PhaseSpaceState') -> float:
        """Calculate Euclidean distance in virtue subspace only."""
        return float(np.linalg.norm(self.virtue.to_vector() - other.virtue.to_vector()))


@dataclass
class Trajectory:
    """
    A sequence of states representing an agent's path through phase space.
    """
    agent_id: str
    states: List[PhaseSpaceState] = field(default_factory=list)

    def add_state(self, state: PhaseSpaceState):
        """Add a state to the trajectory."""
        self.states.append(state)

    def get_window(self, size: int = 10) -> List[PhaseSpaceState]:
        """Get the most recent N states."""
        return self.states[-size:]

    def to_matrix(self) -> np.ndarray:
        """Convert trajectory to matrix where each row is a state."""
        if not self.states:
            return np.array([])
        return np.vstack([s.to_vector() for s in self.states])
