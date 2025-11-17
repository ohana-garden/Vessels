"""
Virtue inference engine.

Infers the 7D virtue state from multi-signal behavior analysis.
This is a v1 stub implementation that will be improved over time.

Virtues inferred:
- Truthfulness: factual accuracy, absence of deception
- Justice: fair treatment, awareness of power asymmetries
- Trustworthiness: reliability, follow-through on commitments
- Unity: collaboration quality, conflict reduction
- Service: benefit to others vs self-serving behavior
- Detachment: ego-detachment (right action vs personal credit)
- Understanding: depth of comprehension, context awareness
"""

from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta
import numpy as np

from .state import VirtueState


class VirtueInferenceEngine:
    """
    Infers virtue dimensions from agent behavior.

    This is a v1 implementation using basic heuristics.
    Future versions will use more sophisticated inference.
    """

    def __init__(self):
        """Initialize virtue inference engine."""
        # Track behavioral signals
        self.fact_checks: Dict[str, List[Dict]] = defaultdict(list)
        self.commitments: Dict[str, List[Dict]] = defaultdict(list)
        self.power_interactions: Dict[str, List[Dict]] = defaultdict(list)
        self.collaborations: Dict[str, List[Dict]] = defaultdict(list)
        self.service_actions: Dict[str, List[Dict]] = defaultdict(list)
        self.credit_seeking: Dict[str, List[Dict]] = defaultdict(list)
        self.context_usage: Dict[str, List[Dict]] = defaultdict(list)

    def record_factual_claim(self, agent_id: str, claim: str, verified: bool):
        """Record a factual claim and whether it was verified as true."""
        self.fact_checks[agent_id].append({
            'timestamp': datetime.utcnow(),
            'claim': claim,
            'verified': verified
        })
        # Keep recent history
        self.fact_checks[agent_id] = self.fact_checks[agent_id][-100:]

    def record_commitment(self, agent_id: str, commitment: str, fulfilled: Optional[bool] = None):
        """Record a commitment and whether it was fulfilled."""
        existing = [c for c in self.commitments[agent_id] if c['commitment'] == commitment]

        if existing:
            existing[0]['fulfilled'] = fulfilled
        else:
            self.commitments[agent_id].append({
                'timestamp': datetime.utcnow(),
                'commitment': commitment,
                'fulfilled': fulfilled
            })

        self.commitments[agent_id] = self.commitments[agent_id][-100:]

    def record_power_interaction(self, agent_id: str, fair: bool, context: str):
        """Record interaction involving power dynamics."""
        self.power_interactions[agent_id].append({
            'timestamp': datetime.utcnow(),
            'fair': fair,
            'context': context
        })
        self.power_interactions[agent_id] = self.power_interactions[agent_id][-100:]

    def record_collaboration(self, agent_id: str, quality: float, conflict: bool = False):
        """Record collaboration event with quality score."""
        self.collaborations[agent_id].append({
            'timestamp': datetime.utcnow(),
            'quality': quality,
            'conflict': conflict
        })
        self.collaborations[agent_id] = self.collaborations[agent_id][-100:]

    def record_service_action(self, agent_id: str, benefit_to_others: float, benefit_to_self: float):
        """Record action with its benefit distribution."""
        self.service_actions[agent_id].append({
            'timestamp': datetime.utcnow(),
            'benefit_to_others': benefit_to_others,
            'benefit_to_self': benefit_to_self
        })
        self.service_actions[agent_id] = self.service_actions[agent_id][-100:]

    def record_credit_seeking(self, agent_id: str, intensity: float):
        """Record credit-seeking or self-praise behavior."""
        self.credit_seeking[agent_id].append({
            'timestamp': datetime.utcnow(),
            'intensity': intensity
        })
        self.credit_seeking[agent_id] = self.credit_seeking[agent_id][-100:]

    def record_context_usage(self, agent_id: str, depth: float, relevant: bool):
        """Record how well context was used."""
        self.context_usage[agent_id].append({
            'timestamp': datetime.utcnow(),
            'depth': depth,
            'relevant': relevant
        })
        self.context_usage[agent_id] = self.context_usage[agent_id][-100:]

    def infer(self, agent_id: str, context: Optional[Dict[str, Any]] = None) -> VirtueState:
        """
        Infer virtue state from accumulated behavioral signals.

        Args:
            agent_id: Agent to infer virtues for
            context: Additional context (outputs, outcomes, etc.)

        Returns:
            VirtueState with all dimensions in [0, 1]
        """
        truthfulness = self._infer_truthfulness(agent_id)
        justice = self._infer_justice(agent_id)
        trustworthiness = self._infer_trustworthiness(agent_id)
        unity = self._infer_unity(agent_id)
        service = self._infer_service(agent_id)
        detachment = self._infer_detachment(agent_id)
        understanding = self._infer_understanding(agent_id)

        return VirtueState(
            truthfulness=truthfulness,
            justice=justice,
            trustworthiness=trustworthiness,
            unity=unity,
            service=service,
            detachment=detachment,
            understanding=understanding
        )

    def _infer_truthfulness(self, agent_id: str) -> float:
        """Infer truthfulness from fact-checking history."""
        checks = self.fact_checks.get(agent_id, [])
        if not checks:
            return 0.7  # Neutral prior

        # Recent accuracy rate
        recent = checks[-20:]
        verified_count = sum(1 for c in recent if c['verified'])

        return verified_count / len(recent)

    def _infer_justice(self, agent_id: str) -> float:
        """Infer justice from power interaction fairness."""
        interactions = self.power_interactions.get(agent_id, [])
        if not interactions:
            return 0.7  # Neutral prior

        recent = interactions[-20:]
        fair_count = sum(1 for i in recent if i['fair'])

        return fair_count / len(recent)

    def _infer_trustworthiness(self, agent_id: str) -> float:
        """Infer trustworthiness from commitment follow-through."""
        commitments = self.commitments.get(agent_id, [])
        if not commitments:
            return 0.7  # Neutral prior

        # Only count resolved commitments
        resolved = [c for c in commitments if c['fulfilled'] is not None]
        if not resolved:
            return 0.7

        fulfilled_count = sum(1 for c in resolved if c['fulfilled'])

        return fulfilled_count / len(resolved)

    def _infer_unity(self, agent_id: str) -> float:
        """Infer unity from collaboration quality and conflict frequency."""
        collabs = self.collaborations.get(agent_id, [])
        if not collabs:
            return 0.7  # Neutral prior

        recent = collabs[-20:]

        # Average collaboration quality
        avg_quality = np.mean([c['quality'] for c in recent])

        # Penalty for conflicts
        conflict_rate = sum(1 for c in recent if c['conflict']) / len(recent)

        return float(avg_quality * (1.0 - 0.5 * conflict_rate))

    def _infer_service(self, agent_id: str) -> float:
        """Infer service from benefit distribution."""
        actions = self.service_actions.get(agent_id, [])
        if not actions:
            return 0.7  # Neutral prior

        recent = actions[-20:]

        # Service score = benefit_to_others / (benefit_to_others + benefit_to_self)
        total_others = sum(a['benefit_to_others'] for a in recent)
        total_self = sum(a['benefit_to_self'] for a in recent)

        if total_others + total_self == 0:
            return 0.5

        return total_others / (total_others + total_self)

    def _infer_detachment(self, agent_id: str) -> float:
        """Infer ego-detachment from credit-seeking behavior."""
        seeking = self.credit_seeking.get(agent_id, [])
        if not seeking:
            return 0.7  # Neutral prior

        recent = seeking[-20:]

        # Lower credit-seeking = higher detachment
        avg_seeking = np.mean([s['intensity'] for s in recent])

        return float(1.0 - avg_seeking)

    def _infer_understanding(self, agent_id: str) -> float:
        """Infer understanding from context usage quality."""
        usage = self.context_usage.get(agent_id, [])
        if not usage:
            return 0.7  # Neutral prior

        recent = usage[-20:]

        # Average depth of understanding
        avg_depth = np.mean([u['depth'] for u in recent])

        # Penalty for irrelevant context usage
        relevance_rate = sum(1 for u in recent if u['relevant']) / len(recent)

        return float(avg_depth * relevance_rate)

    def get_confidence(self, agent_id: str) -> Dict[str, float]:
        """
        Estimate confidence in virtue measurements.

        Returns:
            Dictionary mapping virtue names to confidence scores (0-1)
        """
        return {
            'truthfulness': self._get_signal_confidence(self.fact_checks.get(agent_id, [])),
            'justice': self._get_signal_confidence(self.power_interactions.get(agent_id, [])),
            'trustworthiness': self._get_signal_confidence(self.commitments.get(agent_id, [])),
            'unity': self._get_signal_confidence(self.collaborations.get(agent_id, [])),
            'service': self._get_signal_confidence(self.service_actions.get(agent_id, [])),
            'detachment': self._get_signal_confidence(self.credit_seeking.get(agent_id, [])),
            'understanding': self._get_signal_confidence(self.context_usage.get(agent_id, []))
        }

    def _get_signal_confidence(self, signals: List[Dict]) -> float:
        """Confidence increases with number of signals."""
        return min(len(signals) / 20.0, 1.0)
