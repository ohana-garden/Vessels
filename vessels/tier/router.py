"""
Tier routing logic.

Routes requests to Tier 0 (device), Tier 1 (edge), or Tier 2 (cloud)
based on request type and vessel configuration.
"""

import logging
from dataclasses import dataclass
from enum import Enum

from vessels.core import Vessel, TierLevel

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests for routing."""
    SIMPLE_QA = "simple_qa"
    INTENT_CLASSIFICATION = "intent_classification"
    EMOTION_INFERENCE = "emotion_inference"
    MEDIUM_REASONING = "medium_reasoning"
    COMPLEX_REASONING = "complex_reasoning"
    VECTOR_SEARCH = "vector_search"
    GRAPH_QUERY = "graph_query"


@dataclass
class RoutingDecision:
    """Result of tier routing."""
    tier: TierLevel
    reason: str
    fallback: bool = False


class TierRouter:
    """
    Routes requests to appropriate compute tier.

    Tier 0 (Device):  Simple, low-latency tasks
    Tier 1 (Edge):    Medium complexity, local processing
    Tier 2 (Cloud):   Heavy processing, large models
    """

    # Request type to preferred tier mapping
    TIER_PREFERENCES = {
        RequestType.SIMPLE_QA: TierLevel.TIER0,
        RequestType.INTENT_CLASSIFICATION: TierLevel.TIER0,
        RequestType.EMOTION_INFERENCE: TierLevel.TIER0,
        RequestType.VECTOR_SEARCH: TierLevel.TIER1,
        RequestType.GRAPH_QUERY: TierLevel.TIER1,
        RequestType.MEDIUM_REASONING: TierLevel.TIER1,
        RequestType.COMPLEX_REASONING: TierLevel.TIER2,
    }

    def select_tier(
        self,
        request_type: RequestType,
        vessel: Vessel
    ) -> RoutingDecision:
        """
        Select appropriate tier for a request.

        Args:
            request_type: Type of request
            vessel: Vessel context

        Returns:
            Routing decision with tier selection
        """
        preferred_tier = self.TIER_PREFERENCES.get(request_type, TierLevel.TIER1)

        # Check if preferred tier is available
        if self._is_tier_available(preferred_tier, vessel):
            return RoutingDecision(
                tier=preferred_tier,
                reason=f"Preferred tier for {request_type.value}",
                fallback=False
            )

        # Fallback logic
        if preferred_tier == TierLevel.TIER0:
            # Try Tier 1
            if self._is_tier_available(TierLevel.TIER1, vessel):
                return RoutingDecision(
                    tier=TierLevel.TIER1,
                    reason="Tier 0 unavailable, falling back to Tier 1",
                    fallback=True
                )
            # Try Tier 2
            if self._is_tier_available(TierLevel.TIER2, vessel):
                return RoutingDecision(
                    tier=TierLevel.TIER2,
                    reason="Tier 0/1 unavailable, falling back to Tier 2",
                    fallback=True
                )

        if preferred_tier == TierLevel.TIER1:
            # Try Tier 0 (downgrade)
            if self._is_tier_available(TierLevel.TIER0, vessel):
                return RoutingDecision(
                    tier=TierLevel.TIER0,
                    reason="Tier 1 unavailable, falling back to Tier 0",
                    fallback=True
                )
            # Try Tier 2 (upgrade)
            if self._is_tier_available(TierLevel.TIER2, vessel):
                return RoutingDecision(
                    tier=TierLevel.TIER2,
                    reason="Tier 1 unavailable, falling back to Tier 2",
                    fallback=True
                )

        if preferred_tier == TierLevel.TIER2:
            # Try Tier 1
            if self._is_tier_available(TierLevel.TIER1, vessel):
                return RoutingDecision(
                    tier=TierLevel.TIER1,
                    reason="Tier 2 unavailable, falling back to Tier 1",
                    fallback=True
                )

        # No tier available - default to Tier 1
        logger.warning(f"No tier available for {request_type.value}, defaulting to Tier 1")
        return RoutingDecision(
            tier=TierLevel.TIER1,
            reason="No tier available, defaulting to Tier 1",
            fallback=True
        )

    def _is_tier_available(self, tier: TierLevel, vessel: Vessel) -> bool:
        """Check if a tier is available for the vessel."""
        tier_config = vessel.config.tier_config

        if tier == TierLevel.TIER0:
            return tier_config.tier0_enabled
        elif tier == TierLevel.TIER1:
            return tier_config.tier1_enabled
        elif tier == TierLevel.TIER2:
            return tier_config.tier2_enabled

        return False
