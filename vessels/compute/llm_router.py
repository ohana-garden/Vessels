"""
LLM Router - Intelligent request routing across three compute tiers

Routes LLM requests to the most appropriate tier based on:
- Latency requirements
- Context size
- Data sensitivity
- Quality requirements
- Resource availability

Tiers:
- Tier 0 (Device): < 200ms, < 2K context, all data OK
- Tier 1 (Edge): < 1s, < 32K context, all data OK
- Tier 2 (Petals): 2-10s, < 128K context, non-sensitive only
"""

import time
import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import IntEnum

logger = logging.getLogger(__name__)


class ComputeTier(IntEnum):
    """Compute tier levels"""
    DEVICE = 0  # On-device (phone, tablet)
    EDGE = 1    # Local edge node (home server)
    PETALS = 2  # Distributed network (optional)


@dataclass
class LLMRequest:
    """Request for LLM inference"""
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7
    latency_requirement_ms: int = 1000
    sensitive: bool = True
    context_length: int = 0
    quality_requirement: float = 0.7  # 0-1
    stop_sequences: Optional[List[str]] = None
    preferred_tier: Optional[ComputeTier] = None


@dataclass
class LLMResponse:
    """Response from LLM inference"""
    text: str
    tokens: int
    latency_ms: int
    tier_used: ComputeTier
    model: str
    fallback: bool = False
    error: Optional[str] = None


class LLMRouter:
    """
    Intelligent router for LLM requests across three tiers

    Decision matrix:
    - Sensitive data? → Tier 0 or 1 only
    - Real-time (< 200ms)? → Tier 0
    - Interactive (< 1s)? → Tier 0 or 1
    - Large context (> 32K)? → Tier 2 (if enabled)
    - Default → Tier 1
    """

    def __init__(self, config: Dict[str, Any] = None, tier_config=None):
        """
        Initialize LLM router

        Args:
            config: Traditional config dict (legacy)
            tier_config: TierConfig from vessel (preferred)
        """
        # Support both config dict and TierConfig
        if tier_config:
            from vessels.core.vessel import TierConfig
            self.tier_config = tier_config
            # Convert TierConfig to legacy config format
            self.config = {
                "tier0": {
                    "enabled": tier_config.tier0_enabled,
                    "model": tier_config.tier0_model,
                },
                "tier1": {
                    "enabled": tier_config.tier1_enabled,
                    "host": tier_config.tier1_host,
                    "port": tier_config.tier1_port,
                },
                "tier2": {
                    "enabled": tier_config.tier2_enabled,
                    "models": tier_config.tier2_allowed_models,
                }
            }
        else:
            self.config = config or {}
            self.tier_config = None

        # Initialize tier clients
        self.tier0 = None
        self.tier1 = None
        self.tier2 = None

        self._initialize_tiers()

        self.stats = {
            "total_requests": 0,
            "tier0_used": 0,
            "tier1_used": 0,
            "tier2_used": 0,
            "fallbacks": 0
        }

        logger.info("LLM Router initialized")

    def _initialize_tiers(self):
        """Initialize compute tier clients"""
        # Tier 0: Device LLM
        if self.config.get("tier0", {}).get("enabled", True):
            try:
                from ..device.local_llm import DeviceLLM

                self.tier0 = DeviceLLM(
                    model_name=self.config["tier0"].get("model", "Llama-3.2-1B")
                )
                logger.info("Tier 0 (Device) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Tier 0: {e}")

        # Tier 1: Edge node
        if self.config.get("tier1", {}).get("enabled", True):
            try:
                # TODO: Implement edge node client
                # For now, use a placeholder
                self.tier1 = {"type": "edge", "enabled": True}
                logger.info("Tier 1 (Edge) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Tier 1: {e}")

        # Tier 2: Petals
        if self.config.get("tier2", {}).get("enabled", False):
            try:
                from .petals_gateway import PetalsGateway

                self.tier2 = PetalsGateway(self.config["tier2"])
                logger.info("Tier 2 (Petals) initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Tier 2: {e}")

    async def route(self, request: LLMRequest) -> LLMResponse:
        """
        Route LLM request to appropriate tier

        Args:
            request: LLM inference request

        Returns:
            LLMResponse with result from selected tier
        """
        self.stats["total_requests"] += 1

        # Determine which tier to use
        tier = self._select_tier(request)

        logger.debug(f"Routing request to Tier {tier.value}")

        # Try selected tier
        response = await self._execute_on_tier(tier, request)

        # If failed, try fallback
        if response.error:
            logger.warning(f"Tier {tier.value} failed: {response.error}, trying fallback")
            response = await self._fallback(tier, request)

        return response

    def _select_tier(self, request: LLMRequest) -> ComputeTier:
        """
        Select appropriate compute tier based on request requirements

        Decision logic:
        1. Honor preferred_tier if specified and available
        2. NEVER send sensitive data to Tier 2
        3. Use Tier 0 for ultra-low latency (< 200ms) if available
        4. Use Tier 1 for most requests (default)
        5. Use Tier 2 only for large context + non-sensitive + high quality
        """
        # Honor preference if specified and available
        if request.preferred_tier is not None:
            if self._is_tier_available(request.preferred_tier):
                # But still enforce sensitivity rules
                if request.preferred_tier == ComputeTier.PETALS and request.sensitive:
                    logger.warning("Cannot use Petals for sensitive data, using Tier 1")
                    return ComputeTier.EDGE
                return request.preferred_tier

        # RULE 1: Sensitive data NEVER goes to Petals
        if request.sensitive:
            if request.latency_requirement_ms < 200:
                # Try Tier 0 for ultra-low latency, fall back to Tier 1 if unavailable
                if self._is_tier_available(ComputeTier.DEVICE):
                    return ComputeTier.DEVICE
                else:
                    logger.warning("Tier 0 not available for sensitive ultra-low latency request, using Tier 1")
                    return ComputeTier.EDGE
            else:
                return ComputeTier.EDGE

        # RULE 2: Ultra-low latency requires device
        if request.latency_requirement_ms < 200:
            if self._is_tier_available(ComputeTier.DEVICE):
                return ComputeTier.DEVICE
            else:
                logger.warning("Tier 0 not available, latency requirement may not be met")
                return ComputeTier.EDGE

        # RULE 3: Real-time requires device or edge
        if request.latency_requirement_ms < 1000:
            if self._is_tier_available(ComputeTier.EDGE):
                return ComputeTier.EDGE
            elif self._is_tier_available(ComputeTier.DEVICE):
                return ComputeTier.DEVICE
            else:
                return ComputeTier.EDGE  # Try anyway

        # RULE 4: Large context may need Petals
        if request.context_length > 32000:
            if self._is_tier_available(ComputeTier.PETALS) and not request.sensitive:
                return ComputeTier.PETALS
            else:
                logger.warning("Large context but Petals unavailable or data sensitive")
                return ComputeTier.EDGE

        # RULE 5: High quality + non-sensitive → consider Petals
        if request.quality_requirement > 0.85 and not request.sensitive:
            if self._is_tier_available(ComputeTier.PETALS):
                return ComputeTier.PETALS
            else:
                return ComputeTier.EDGE

        # DEFAULT: Edge node (most balanced)
        return ComputeTier.EDGE

    def _is_tier_available(self, tier: ComputeTier) -> bool:
        """Check if a compute tier is available based on config.

        A tier is available if it's enabled in the config. The actual
        client availability is checked during execution.
        """
        if tier == ComputeTier.DEVICE:
            # Check config first (preferred), then client
            if self.tier_config is not None:
                return self.tier_config.tier0_enabled
            return self.tier0 is not None
        elif tier == ComputeTier.EDGE:
            if self.tier_config is not None:
                return self.tier_config.tier1_enabled
            return self.tier1 is not None
        elif tier == ComputeTier.PETALS:
            if self.tier_config is not None:
                return self.tier_config.tier2_enabled
            return self.tier2 is not None and getattr(self.tier2, "enabled", False)
        return False

    async def _execute_on_tier(self, tier: ComputeTier, request: LLMRequest) -> LLMResponse:
        """Execute request on specified tier"""
        start_time = time.time()

        try:
            if tier == ComputeTier.DEVICE:
                result = self._execute_tier0(request)
                self.stats["tier0_used"] += 1

            elif tier == ComputeTier.EDGE:
                result = await self._execute_tier1(request)
                self.stats["tier1_used"] += 1

            elif tier == ComputeTier.PETALS:
                result = self._execute_tier2(request)
                self.stats["tier2_used"] += 1

            else:
                raise ValueError(f"Unknown tier: {tier}")

            latency_ms = int((time.time() - start_time) * 1000)

            return LLMResponse(
                text=result["text"],
                tokens=result.get("tokens", len(result["text"].split())),
                latency_ms=latency_ms,
                tier_used=tier,
                model=result.get("model", "unknown"),
                fallback=False,
                error=None
            )

        except Exception as e:
            logger.error(f"Execution on Tier {tier.value} failed: {e}")
            return LLMResponse(
                text="",
                tokens=0,
                latency_ms=int((time.time() - start_time) * 1000),
                tier_used=tier,
                model="unknown",
                fallback=False,
                error=str(e)
            )

    def _execute_tier0(self, request: LLMRequest) -> Dict[str, Any]:
        """Execute on Tier 0 (Device)"""
        if not self.tier0:
            raise RuntimeError("Tier 0 not available")

        result = self.tier0.generate(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop_sequences=request.stop_sequences
        )

        return {
            "text": result.text,
            "tokens": result.tokens,
            "model": result.model
        }

    async def _execute_tier1(self, request: LLMRequest) -> Dict[str, Any]:
        """Execute on Tier 1 (Edge)"""
        if not self.tier1:
            raise RuntimeError("Tier 1 not available")

        # TODO: Implement actual edge node RPC call
        # For now, return placeholder

        # Simulate edge node call
        await asyncio.sleep(0.5)  # Simulate network + inference

        return {
            "text": f"[Tier 1 response to: {request.prompt[:50]}...]",
            "tokens": request.max_tokens,
            "model": "edge-llama-70b"
        }

    def _execute_tier2(self, request: LLMRequest) -> Dict[str, Any]:
        """Execute on Tier 2 (Petals)"""
        if not self.tier2:
            raise RuntimeError("Tier 2 not available")

        result = self.tier2.generate(
            prompt=request.prompt,
            model_name=self.config["tier2"]["models"][0],  # Use first allowed model
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop_sequences=request.stop_sequences
        )

        if result.error:
            raise RuntimeError(result.error)

        return {
            "text": result.text,
            "tokens": result.tokens,
            "model": result.model
        }

    async def _fallback(self, failed_tier: ComputeTier, request: LLMRequest) -> LLMResponse:
        """
        Fallback to alternative tier if primary fails

        Fallback chain:
        - Tier 2 → Tier 1
        - Tier 1 → Tier 0
        - Tier 0 → return error (no fallback)
        """
        self.stats["fallbacks"] += 1

        # Determine fallback tier
        if failed_tier == ComputeTier.PETALS:
            fallback_tier = ComputeTier.EDGE
        elif failed_tier == ComputeTier.EDGE:
            fallback_tier = ComputeTier.DEVICE
        else:
            # No fallback for Tier 0
            return LLMResponse(
                text="",
                tokens=0,
                latency_ms=0,
                tier_used=failed_tier,
                model="unknown",
                fallback=True,
                error="All tiers failed"
            )

        logger.info(f"Falling back to Tier {fallback_tier.value}")

        response = await self._execute_on_tier(fallback_tier, request)
        response.fallback = True

        return response

    def get_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = self.stats.copy()

        if stats["total_requests"] > 0:
            stats["tier0_pct"] = stats["tier0_used"] / stats["total_requests"] * 100
            stats["tier1_pct"] = stats["tier1_used"] / stats["total_requests"] * 100
            stats["tier2_pct"] = stats["tier2_used"] / stats["total_requests"] * 100
            stats["fallback_rate"] = stats["fallbacks"] / stats["total_requests"]
        else:
            stats["tier0_pct"] = 0.0
            stats["tier1_pct"] = 0.0
            stats["tier2_pct"] = 0.0
            stats["fallback_rate"] = 0.0

        return stats

    def get_tier_status(self) -> Dict[str, Any]:
        """Get status of all tiers"""
        return {
            "tier0": {
                "available": self._is_tier_available(ComputeTier.DEVICE),
                "type": "device",
                "model": getattr(self.tier0, "model_name", None) if self.tier0 else None
            },
            "tier1": {
                "available": self._is_tier_available(ComputeTier.EDGE),
                "type": "edge",
                "host": self.config.get("tier1", {}).get("host")
            },
            "tier2": {
                "available": self._is_tier_available(ComputeTier.PETALS),
                "type": "petals",
                "enabled": self.config.get("tier2", {}).get("enabled", False)
            }
        }


def create_llm_router(config: Dict[str, Any]) -> LLMRouter:
    """
    Factory function to create LLM router from config

    Args:
        config: {
            "tier0": {
                "enabled": bool,
                "model": str
            },
            "tier1": {
                "enabled": bool,
                "host": str,
                "port": int
            },
            "tier2": {
                "enabled": bool,
                "models": List[str],
                "sanitize_data": bool
            }
        }

    Returns:
        Configured LLMRouter instance
    """
    return LLMRouter(config)


async def example_usage():
    """Example usage of LLMRouter"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Configure router
    config = {
        "tier0": {
            "enabled": True,
            "model": "Llama-3.2-1B"
        },
        "tier1": {
            "enabled": True,
            "host": "localhost",
            "port": 8080
        },
        "tier2": {
            "enabled": False,  # Disabled by default
            "models": ["meta-llama/Llama-3.1-70b-hf"],
            "sanitize_data": True
        }
    }

    router = create_llm_router(config)

    # Example 1: Fast, sensitive query → Tier 0
    request1 = LLMRequest(
        prompt="What's my schedule today?",
        max_tokens=100,
        latency_requirement_ms=150,
        sensitive=True
    )

    response1 = await router.route(request1)
    print(f"Example 1: Used Tier {response1.tier_used.value} ({response1.latency_ms}ms)")

    # Example 2: Complex query → Tier 1
    request2 = LLMRequest(
        prompt="Explain quantum computing in detail",
        max_tokens=500,
        latency_requirement_ms=2000,
        sensitive=False,
        quality_requirement=0.8
    )

    response2 = await router.route(request2)
    print(f"Example 2: Used Tier {response2.tier_used.value} ({response2.latency_ms}ms)")

    # Get stats
    stats = router.get_stats()
    print(f"\nRouter stats: {stats}")

    # Get tier status
    status = router.get_tier_status()
    print(f"Tier status: {status}")


if __name__ == "__main__":
    asyncio.run(example_usage())
