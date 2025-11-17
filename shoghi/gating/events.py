"""
SecurityEvent and StateTransition models.

These track constraint violations and state changes through the gate.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import json


@dataclass
class SecurityEvent:
    """
    Records a security-relevant event (constraint violation).

    Generated when:
    - A state fails validation
    - Projection fails to converge
    - A timeout occurs during gating
    """
    agent_id: str
    timestamp: datetime
    violations: List[str]  # Names of violated constraints
    original_virtue_state: Dict[str, float]
    corrected_virtue_state: Optional[Dict[str, float]] = None
    residual_violations: List[str] = field(default_factory=list)
    blocked: bool = False
    action_hash: Optional[str] = None  # Content-addressed action reference
    operational_state_snapshot: Optional[Dict[str, float]] = None
    event_type: str = "constraint_violation"  # or "timeout", "projection_failed"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'violations': self.violations,
            'original_virtue_state': self.original_virtue_state,
            'corrected_virtue_state': self.corrected_virtue_state,
            'residual_violations': self.residual_violations,
            'blocked': self.blocked,
            'action_hash': self.action_hash,
            'operational_state_snapshot': self.operational_state_snapshot,
            'event_type': self.event_type,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'SecurityEvent':
        """Deserialize from dictionary."""
        d = dict(d)  # Copy to avoid mutation
        if 'timestamp' in d and isinstance(d['timestamp'], str):
            d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        return cls(**d)

    def __repr__(self) -> str:
        return (
            f"SecurityEvent(agent={self.agent_id}, "
            f"type={self.event_type}, "
            f"violations={len(self.violations)}, "
            f"blocked={self.blocked})"
        )


@dataclass
class StateTransition:
    """
    Records a state transition through the action gate.

    Tracks how states evolve as agents take actions.
    """
    agent_id: str
    timestamp: datetime
    from_state: Dict[str, float]  # Full 12D state as dict
    to_state: Dict[str, float]  # Full 12D state as dict
    action_hash: str
    gating_result: str  # "allowed", "blocked", "corrected"
    action_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'from_state': self.from_state,
            'to_state': self.to_state,
            'action_hash': self.action_hash,
            'gating_result': self.gating_result,
            'action_metadata': self.action_metadata
        }

    @classmethod
    def from_dict(cls, d: Dict) -> 'StateTransition':
        """Deserialize from dictionary."""
        d = dict(d)  # Copy to avoid mutation
        if 'timestamp' in d and isinstance(d['timestamp'], str):
            d['timestamp'] = datetime.fromisoformat(d['timestamp'])
        return cls(**d)

    def __repr__(self) -> str:
        return (
            f"StateTransition(agent={self.agent_id}, "
            f"result={self.gating_result})"
        )


def hash_action(action: Any) -> str:
    """
    Create a content-addressed hash for an action.

    Args:
        action: Action data (will be JSON-serialized)

    Returns:
        SHA256 hash of the action
    """
    # Serialize action to JSON
    if isinstance(action, dict):
        action_str = json.dumps(action, sort_keys=True)
    elif isinstance(action, str):
        action_str = action
    else:
        action_str = str(action)

    # Hash it
    return hashlib.sha256(action_str.encode()).hexdigest()
