"""
Tension detection system.

Detects when a Vessel should trigger the Check Protocol:
- Value collisions (virtues in conflict)
- Ambiguity (unclear intent)
- Low confidence (entering unknown territory)
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TensionType(Enum):
    """Types of tensions that can trigger the check protocol."""
    VALUE_COLLISION = "value_collision"  # Virtues in conflict
    AMBIGUITY = "ambiguity"  # Unclear intent or requirements
    LOW_CONFIDENCE = "low_confidence"  # Entering unknown territory
    CONSTRAINT_VIOLATION = "constraint_violation"  # Would violate constraints
    TRUTHFULNESS_THRESHOLD = "truthfulness_threshold"  # Near truthfulness limit


@dataclass
class Tension:
    """
    A detected tension requiring deliberation.
    """
    type: TensionType
    description: str
    severity: float  # 0.0 to 1.0
    agent_id: str
    timestamp: datetime = None

    # Context
    current_state: Dict[str, float] = None
    involved_virtues: List[str] = None
    action_context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.involved_virtues is None:
            self.involved_virtues = []
        if self.action_context is None:
            self.action_context = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'type': self.type.value,
            'description': self.description,
            'severity': self.severity,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'current_state': self.current_state,
            'involved_virtues': self.involved_virtues,
            'action_context': self.action_context,
            'metadata': self.metadata,
        }


class TensionDetector:
    """
    Detects tensions that should trigger the check protocol.

    Integrates with the measurement and constraint systems to
    identify when a Vessel needs village guidance.
    """

    def __init__(
        self,
        value_collision_threshold: float = 0.3,
        confidence_threshold: float = 0.5,
        truthfulness_warning_threshold: float = 0.6,
    ):
        """
        Initialize tension detector.

        Args:
            value_collision_threshold: Threshold for detecting value collisions
            confidence_threshold: Minimum confidence before triggering
            truthfulness_warning_threshold: Truthfulness level that triggers warning
        """
        self.value_collision_threshold = value_collision_threshold
        self.confidence_threshold = confidence_threshold
        self.truthfulness_warning_threshold = truthfulness_warning_threshold

    def detect(
        self,
        agent_id: str,
        virtue_state: Dict[str, float],
        confidence: Dict[str, float],
        action_description: str = "",
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Tension]:
        """
        Detect if there's a tension requiring deliberation.

        Args:
            agent_id: Agent ID
            virtue_state: Current virtue state
            confidence: Confidence scores for each measurement
            action_description: Description of the action being considered
            action_metadata: Additional context about the action

        Returns:
            Tension if detected, None otherwise
        """
        action_metadata = action_metadata or {}

        # 1. Check for value collisions
        tension = self._detect_value_collision(
            agent_id, virtue_state, action_description, action_metadata
        )
        if tension:
            return tension

        # 2. Check for low confidence
        tension = self._detect_low_confidence(
            agent_id, virtue_state, confidence, action_description, action_metadata
        )
        if tension:
            return tension

        # 3. Check for approaching truthfulness threshold
        tension = self._detect_truthfulness_warning(
            agent_id, virtue_state, action_description, action_metadata
        )
        if tension:
            return tension

        return None

    def _detect_value_collision(
        self,
        agent_id: str,
        virtue_state: Dict[str, float],
        action_description: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[Tension]:
        """
        Detect if virtues are in collision.

        Common collisions:
        - Truthfulness vs Unity (telling hard truths may hurt unity)
        - Justice vs Unity (fairness may conflict with harmony)
        - Detachment vs Service (ego-detachment vs visible contribution)
        """
        collisions = []

        # Truthfulness vs Unity
        truth = virtue_state.get('truthfulness', 0.7)
        unity = virtue_state.get('unity', 0.7)
        if truth > 0.7 and unity < 0.5:
            collisions.append({
                'virtues': ['truthfulness', 'unity'],
                'description': 'High truthfulness may be reducing unity',
                'severity': truth - unity,
            })

        # Justice vs Unity
        justice = virtue_state.get('justice', 0.7)
        if justice > 0.7 and unity < 0.5:
            collisions.append({
                'virtues': ['justice', 'unity'],
                'description': 'Pursuit of justice may be reducing unity',
                'severity': justice - unity,
            })

        # Service vs Detachment (seeking recognition)
        service = virtue_state.get('service', 0.7)
        detachment = virtue_state.get('detachment', 0.7)
        if service > 0.7 and detachment < 0.4:
            collisions.append({
                'virtues': ['service', 'detachment'],
                'description': 'High service with low detachment suggests seeking recognition',
                'severity': service - detachment,
            })

        # If any collision is significant
        for collision in collisions:
            if collision['severity'] > self.value_collision_threshold:
                return Tension(
                    type=TensionType.VALUE_COLLISION,
                    description=f"Value collision detected: {collision['description']}. "
                                f"Action: {action_description}",
                    severity=min(collision['severity'], 1.0),
                    agent_id=agent_id,
                    current_state=virtue_state,
                    involved_virtues=collision['virtues'],
                    action_context={'action': action_description, **action_metadata},
                    metadata={'collision_details': collision}
                )

        return None

    def _detect_low_confidence(
        self,
        agent_id: str,
        virtue_state: Dict[str, float],
        confidence: Dict[str, float],
        action_description: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[Tension]:
        """
        Detect if confidence is too low.

        Low confidence means we're entering unknown territory
        and should ask for guidance.
        """
        # Check virtue confidence
        virtue_confidences = {
            k: v for k, v in confidence.items()
            if k in ['truthfulness', 'justice', 'trustworthiness',
                     'unity', 'service', 'detachment', 'understanding']
        }

        if not virtue_confidences:
            return None

        min_confidence = min(virtue_confidences.values())
        low_confidence_virtue = min(virtue_confidences, key=virtue_confidences.get)

        if min_confidence < self.confidence_threshold:
            return Tension(
                type=TensionType.LOW_CONFIDENCE,
                description=f"Low confidence ({min_confidence:.2f}) in measuring {low_confidence_virtue}. "
                            f"Entering unknown territory. Action: {action_description}",
                severity=1.0 - min_confidence,
                agent_id=agent_id,
                current_state=virtue_state,
                involved_virtues=[low_confidence_virtue],
                action_context={'action': action_description, **action_metadata},
                metadata={'confidence_scores': virtue_confidences}
            )

        return None

    def _detect_truthfulness_warning(
        self,
        agent_id: str,
        virtue_state: Dict[str, float],
        action_description: str,
        action_metadata: Dict[str, Any]
    ) -> Optional[Tension]:
        """
        Detect if truthfulness is approaching dangerous levels.

        Truthfulness is the non-negotiable foundation. If it drops
        too low, the Vessel must seek guidance.
        """
        truthfulness = virtue_state.get('truthfulness', 0.7)

        if truthfulness < self.truthfulness_warning_threshold:
            return Tension(
                type=TensionType.TRUTHFULNESS_THRESHOLD,
                description=f"Truthfulness ({truthfulness:.2f}) is approaching critical threshold. "
                            f"This is the load-bearing virtue. Action: {action_description}",
                severity=1.0 - truthfulness,
                agent_id=agent_id,
                current_state=virtue_state,
                involved_virtues=['truthfulness'],
                action_context={'action': action_description, **action_metadata},
                metadata={'truthfulness_threshold': self.truthfulness_warning_threshold}
            )

        return None

    def detect_constraint_violation(
        self,
        agent_id: str,
        virtue_state: Dict[str, float],
        violations: List[str],
        action_description: str,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> Tension:
        """
        Create a tension for a constraint violation.

        This is called when the regular constraint system
        detects violations.
        """
        action_metadata = action_metadata or {}

        # Extract virtues from violation names
        involved_virtues = []
        for violation in violations:
            for virtue in ['truthfulness', 'justice', 'trustworthiness',
                           'unity', 'service', 'detachment', 'understanding']:
                if virtue in violation.lower():
                    involved_virtues.append(virtue)

        return Tension(
            type=TensionType.CONSTRAINT_VIOLATION,
            description=f"Constraint violations detected: {', '.join(violations)}. "
                        f"Action: {action_description}",
            severity=min(len(violations) / 3.0, 1.0),  # Severity based on number of violations
            agent_id=agent_id,
            current_state=virtue_state,
            involved_virtues=list(set(involved_virtues)),
            action_context={'action': action_description, **action_metadata},
            metadata={'violations': violations}
        )

    def should_trigger_check(self, tension: Tension) -> bool:
        """
        Determine if a tension should trigger the check protocol.

        Args:
            tension: Detected tension

        Returns:
            True if check protocol should be triggered
        """
        # Always trigger for truthfulness warnings
        if tension.type == TensionType.TRUTHFULNESS_THRESHOLD:
            return True

        # Always trigger for constraint violations
        if tension.type == TensionType.CONSTRAINT_VIOLATION:
            return True

        # Trigger for high-severity tensions
        if tension.severity > 0.5:
            return True

        return False
