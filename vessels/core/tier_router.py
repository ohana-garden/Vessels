"""
Tier Router - Routes requests to appropriate compute tier.

Implements the three-tier architecture:
- Tier 0: Device (local, fast, privacy-preserving)
- Tier 1: Edge (community edge server, medium latency)
- Tier 2: Cloud (external cloud APIs, highest capability)

Routing decisions are based on:
- Request complexity
- Privacy requirements
- Tier availability
- Cost considerations
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List

from .vessel import TierConfig, TierLevel, Vessel

logger = logging.getLogger(__name__)


class RequestType(Enum):
    """Types of requests for tier routing."""
    SIMPLE_QA = "simple_qa"              # Basic Q&A, local knowledge
    CLASSIFICATION = "classification"     # Intent/sentiment classification
    EMBEDDING = "embedding"               # Vector embeddings
    SUMMARIZATION = "summarization"       # Text summarization
    GENERATION = "generation"             # Text generation
    REASONING = "reasoning"               # Complex reasoning
    CODE_GENERATION = "code_generation"   # Code generation
    MULTIMODAL = "multimodal"            # Image/audio processing


@dataclass
class TierSelection:
    """Result of tier selection."""
    tier: TierLevel
    model: str
    endpoint: str
    fallback_tier: Optional[TierLevel] = None
    reason: str = ""


class TierRouter:
    """
    Routes requests to the appropriate compute tier.

    Tier selection priorities:
    1. Privacy: If data is sensitive, prefer local tiers
    2. Capability: Match request complexity to tier capability
    3. Availability: Use available tiers, fallback if necessary
    4. Cost: Prefer cheaper tiers when capability is sufficient
    """

    # Request type to minimum tier capability mapping
    # Higher tier = more capability
    CAPABILITY_REQUIREMENTS: Dict[RequestType, int] = {
        RequestType.SIMPLE_QA: 0,         # Tier 0 can handle
        RequestType.CLASSIFICATION: 0,     # Tier 0 can handle
        RequestType.EMBEDDING: 0,          # Tier 0 can handle
        RequestType.SUMMARIZATION: 1,      # Needs at least Tier 1
        RequestType.GENERATION: 1,         # Needs at least Tier 1
        RequestType.REASONING: 2,          # Best on Tier 2
        RequestType.CODE_GENERATION: 1,    # Needs at least Tier 1
        RequestType.MULTIMODAL: 2,         # Best on Tier 2
    }

    # Tier level to capability score
    TIER_CAPABILITY: Dict[TierLevel, int] = {
        TierLevel.TIER0: 0,
        TierLevel.TIER1: 1,
        TierLevel.TIER2: 2,
    }

    def __init__(
        self,
        prefer_local: bool = True,
        cost_sensitive: bool = True,
        allow_tier2_fallback: bool = True
    ):
        """
        Initialize tier router.

        Args:
            prefer_local: Prefer local/edge tiers when possible
            cost_sensitive: Minimize cloud API costs
            allow_tier2_fallback: Allow fallback to cloud if needed
        """
        self.prefer_local = prefer_local
        self.cost_sensitive = cost_sensitive
        self.allow_tier2_fallback = allow_tier2_fallback

    def select_tier(
        self,
        request_type: RequestType,
        vessel: Vessel,
        privacy_sensitive: bool = False,
        force_tier: Optional[TierLevel] = None
    ) -> TierSelection:
        """
        Select the appropriate tier for a request.

        Args:
            request_type: Type of request
            vessel: Vessel with tier configuration
            privacy_sensitive: If True, avoid cloud tiers
            force_tier: Force a specific tier (if available)

        Returns:
            TierSelection with tier, model, and endpoint
        """
        tier_config = vessel.tier_config

        # If forcing a specific tier, check availability
        if force_tier:
            if self._tier_available(force_tier, tier_config):
                return self._create_selection(force_tier, tier_config, "forced")
            logger.warning(f"Forced tier {force_tier} not available, selecting best alternative")

        # Get available tiers
        available_tiers = self._get_available_tiers(tier_config)
        if not available_tiers:
            raise ValueError("No compute tiers available")

        # Get minimum required capability
        min_capability = self.CAPABILITY_REQUIREMENTS.get(request_type, 0)

        # Filter tiers by capability
        capable_tiers = [
            t for t in available_tiers
            if self.TIER_CAPABILITY[t] >= min_capability
        ]

        # If no tier has sufficient capability, use highest available
        if not capable_tiers:
            capable_tiers = [max(available_tiers, key=lambda t: self.TIER_CAPABILITY[t])]
            logger.warning(
                f"No tier meets capability requirement {min_capability} for {request_type}, "
                f"using {capable_tiers[0]}"
            )

        # Apply privacy filter
        if privacy_sensitive:
            # Exclude cloud tier for privacy-sensitive requests
            local_tiers = [t for t in capable_tiers if t != TierLevel.TIER2]
            if local_tiers:
                capable_tiers = local_tiers
            else:
                logger.warning("Privacy-sensitive request but only cloud tier available")

        # Select based on preferences
        if self.prefer_local and self.cost_sensitive:
            # Prefer lowest capable tier (most local, cheapest)
            selected = min(capable_tiers, key=lambda t: self.TIER_CAPABILITY[t])
        elif self.prefer_local:
            # Prefer local but use highest capability if local
            local = [t for t in capable_tiers if t != TierLevel.TIER2]
            selected = max(local, key=lambda t: self.TIER_CAPABILITY[t]) if local else capable_tiers[0]
        else:
            # Prefer highest capability
            selected = max(capable_tiers, key=lambda t: self.TIER_CAPABILITY[t])

        # Determine fallback
        fallback = self._get_fallback_tier(selected, available_tiers, privacy_sensitive)

        return self._create_selection(
            selected,
            tier_config,
            f"selected for {request_type.value}",
            fallback
        )

    def _tier_available(self, tier: TierLevel, config: TierConfig) -> bool:
        """Check if a tier is available."""
        if tier == TierLevel.TIER0:
            return config.tier0_enabled
        elif tier == TierLevel.TIER1:
            return config.tier1_enabled
        elif tier == TierLevel.TIER2:
            return config.tier2_enabled
        return False

    def _get_available_tiers(self, config: TierConfig) -> List[TierLevel]:
        """Get list of available tiers."""
        available = []
        if config.tier0_enabled:
            available.append(TierLevel.TIER0)
        if config.tier1_enabled:
            available.append(TierLevel.TIER1)
        if config.tier2_enabled and self.allow_tier2_fallback:
            available.append(TierLevel.TIER2)
        return available

    def _get_fallback_tier(
        self,
        selected: TierLevel,
        available: List[TierLevel],
        privacy_sensitive: bool
    ) -> Optional[TierLevel]:
        """Determine fallback tier if selected fails."""
        capability = self.TIER_CAPABILITY[selected]

        # Find next higher capability tier
        for tier in available:
            tier_cap = self.TIER_CAPABILITY[tier]
            if tier_cap > capability:
                if privacy_sensitive and tier == TierLevel.TIER2:
                    continue  # Skip cloud for privacy
                return tier

        return None

    def _create_selection(
        self,
        tier: TierLevel,
        config: TierConfig,
        reason: str,
        fallback: Optional[TierLevel] = None
    ) -> TierSelection:
        """Create TierSelection from tier and config."""
        if tier == TierLevel.TIER0:
            model = config.tier0_model
            endpoint = config.tier0_endpoints.get("inference", f"http://localhost:8000")
        elif tier == TierLevel.TIER1:
            model = config.tier1_model
            host = config.tier1_host
            port = config.tier1_port
            endpoint = config.tier1_endpoints.get("inference", f"http://{host}:{port}")
        else:  # TIER2
            model = config.tier2_allowed_models[0] if config.tier2_allowed_models else "gpt-4"
            endpoint = config.tier2_endpoints.get("inference", "https://api.openai.com/v1")

        return TierSelection(
            tier=tier,
            model=model,
            endpoint=endpoint,
            fallback_tier=fallback,
            reason=reason
        )

    def route_with_fallback(
        self,
        request_type: RequestType,
        vessel: Vessel,
        executor_fn,
        *args,
        **kwargs
    ) -> Any:
        """
        Route request with automatic fallback on failure.

        Args:
            request_type: Type of request
            vessel: Vessel with tier config
            executor_fn: Function to execute (takes tier_selection as first arg)
            *args, **kwargs: Additional arguments for executor_fn

        Returns:
            Result from executor_fn
        """
        selection = self.select_tier(request_type, vessel)

        try:
            return executor_fn(selection, *args, **kwargs)
        except Exception as e:
            logger.warning(f"Tier {selection.tier} failed: {e}")

            if selection.fallback_tier:
                logger.info(f"Falling back to {selection.fallback_tier}")
                fallback_selection = self._create_selection(
                    selection.fallback_tier,
                    vessel.tier_config,
                    f"fallback from {selection.tier}"
                )
                return executor_fn(fallback_selection, *args, **kwargs)

            raise


# Singleton router instance
_default_router: Optional[TierRouter] = None


def get_tier_router(
    prefer_local: bool = True,
    cost_sensitive: bool = True
) -> TierRouter:
    """
    Get or create default tier router.

    Args:
        prefer_local: Prefer local tiers
        cost_sensitive: Minimize costs

    Returns:
        TierRouter instance
    """
    global _default_router
    if _default_router is None:
        _default_router = TierRouter(
            prefer_local=prefer_local,
            cost_sensitive=cost_sensitive
        )
    return _default_router
