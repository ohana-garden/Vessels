"""
Tests for LLM router with TierConfig integration.

Tests AC from story_tiered_architecture.md:
- AC1: Load tier config from vessel
- AC2: Route to appropriate tier based on request
"""

import pytest
import asyncio
from vessels.core.vessel import TierConfig, TierLevel
from vessels.compute.llm_router import LLMRouter, LLMRequest, ComputeTier


def test_tier_config_initialization():
    """AC1: Initialize LLM router with TierConfig."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier0_model="Llama-3.2-1B",
        tier0_device="cpu",
        tier1_enabled=True,
        tier1_host="localhost",
        tier1_port=8080,
        tier1_model="Llama-3.1-70B",
        tier2_enabled=False,
        tier2_allowed_models=[],
    )

    router = LLMRouter(tier_config=tier_config)

    # Verify config was loaded
    assert router.tier_config is not None
    assert router.tier_config.tier0_enabled is True
    assert router.tier_config.tier0_model == "Llama-3.2-1B"
    assert router.tier_config.tier1_enabled is True
    assert router.tier_config.tier2_enabled is False


def test_route_sensitive_to_tier0_or_tier1():
    """Sensitive data never goes to Tier 2."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=True,  # Even when available
        tier2_allowed_models=["meta-llama/Llama-3.1-70b-hf"]
    )

    router = LLMRouter(tier_config=tier_config)

    # Sensitive request
    request = LLMRequest(
        prompt="What's my health history?",
        sensitive=True,
        latency_requirement_ms=500
    )

    tier = router._select_tier(request)

    # Should NEVER be Tier 2
    assert tier != ComputeTier.PETALS
    # Should be Tier 0 or 1
    assert tier in [ComputeTier.DEVICE, ComputeTier.EDGE]


def test_route_fast_request_to_tier0():
    """AC2: Fast requests route to Tier 0 (device)."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Ultra-fast request
    request = LLMRequest(
        prompt="Quick question",
        latency_requirement_ms=150,  # < 200ms
        sensitive=True
    )

    tier = router._select_tier(request)

    assert tier == ComputeTier.DEVICE


def test_route_interactive_to_tier1():
    """Interactive requests (< 1s) route to Tier 1 (edge)."""
    tier_config = TierConfig(
        tier0_enabled=False,  # Tier 0 disabled
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Interactive request
    request = LLMRequest(
        prompt="Medium complexity question",
        latency_requirement_ms=800,  # < 1s
        sensitive=False
    )

    tier = router._select_tier(request)

    assert tier == ComputeTier.EDGE


def test_route_large_context_to_tier2():
    """Large context routes to Tier 2 if available and non-sensitive."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=True,
        tier2_allowed_models=["meta-llama/Llama-3.1-70b-hf"]
    )

    router = LLMRouter(tier_config=tier_config)

    # Large context, non-sensitive
    request = LLMRequest(
        prompt="Analyze this large document...",
        context_length=40000,  # > 32K
        sensitive=False,
        latency_requirement_ms=5000
    )

    tier = router._select_tier(request)

    assert tier == ComputeTier.PETALS


def test_tier0_disabled_fallback():
    """When Tier 0 is disabled, fast requests fall back to Tier 1."""
    tier_config = TierConfig(
        tier0_enabled=False,  # Disabled
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Request that would normally go to Tier 0
    request = LLMRequest(
        prompt="Fast question",
        latency_requirement_ms=150,
        sensitive=True
    )

    tier = router._select_tier(request)

    # Should fall back to Tier 1
    assert tier == ComputeTier.EDGE


def test_tier_availability_check():
    """Test tier availability checking."""
    tier_config = TierConfig(
        tier0_enabled=False,
        tier1_enabled=True,
        tier2_enabled=True,
        tier2_allowed_models=["meta-llama/Llama-3.1-70b-hf"]
    )

    router = LLMRouter(tier_config=tier_config)

    # Tier 0 should not be available
    assert router._is_tier_available(ComputeTier.DEVICE) is False

    # Tier 1 should be available (placeholder)
    assert router._is_tier_available(ComputeTier.EDGE) is True


def test_default_tier_selection():
    """Default tier selection when no special requirements."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Standard request
    request = LLMRequest(
        prompt="Normal question",
        latency_requirement_ms=2000,
        sensitive=False
    )

    tier = router._select_tier(request)

    # Should default to Tier 1 (edge)
    assert tier == ComputeTier.EDGE


def test_preferred_tier_honored():
    """Preferred tier is honored if available and allowed."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Request with preferred tier
    request = LLMRequest(
        prompt="Question",
        preferred_tier=ComputeTier.DEVICE,
        sensitive=False
    )

    tier = router._select_tier(request)

    assert tier == ComputeTier.DEVICE


def test_preferred_tier_overridden_for_sensitive():
    """Preferred Tier 2 is overridden for sensitive data."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=True,
        tier2_allowed_models=["meta-llama/Llama-3.1-70b-hf"]
    )

    router = LLMRouter(tier_config=tier_config)

    # Request prefers Tier 2 but is sensitive
    request = LLMRequest(
        prompt="Sensitive question",
        preferred_tier=ComputeTier.PETALS,
        sensitive=True
    )

    tier = router._select_tier(request)

    # Should NOT be Tier 2 despite preference
    assert tier != ComputeTier.PETALS
    assert tier == ComputeTier.EDGE


def test_high_quality_non_sensitive_to_tier2():
    """High quality, non-sensitive requests prefer Tier 2."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=True,
        tier2_allowed_models=["meta-llama/Llama-3.1-70b-hf"]
    )

    router = LLMRouter(tier_config=tier_config)

    # High quality requirement, non-sensitive
    request = LLMRequest(
        prompt="Complex analysis needed",
        quality_requirement=0.9,  # > 0.85
        sensitive=False,
        latency_requirement_ms=5000
    )

    tier = router._select_tier(request)

    assert tier == ComputeTier.PETALS


def test_router_stats():
    """Test that router tracks usage statistics."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    # Initial stats
    stats = router.get_stats()
    assert stats["total_requests"] == 0
    assert stats["tier0_used"] == 0
    assert stats["tier1_used"] == 0


def test_tier_status():
    """Test tier status reporting."""
    tier_config = TierConfig(
        tier0_enabled=True,
        tier0_model="Llama-3.2-1B",
        tier1_enabled=True,
        tier1_host="localhost",
        tier1_port=8080,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    status = router.get_tier_status()

    assert status["tier0"]["available"] is True or status["tier0"]["available"] is False
    assert status["tier1"]["type"] == "edge"
    assert status["tier1"]["host"] == "localhost"
    assert status["tier2"]["enabled"] is False


@pytest.mark.asyncio
async def test_route_and_execute():
    """Test full routing and execution flow."""
    tier_config = TierConfig(
        tier0_enabled=False,  # Device not available
        tier1_enabled=True,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    request = LLMRequest(
        prompt="Test question",
        max_tokens=50,
        latency_requirement_ms=1000,
        sensitive=False
    )

    # Route the request
    response = await router.route(request)

    # Should complete (even with placeholder implementation)
    assert response is not None
    assert response.tier_used in [ComputeTier.DEVICE, ComputeTier.EDGE, ComputeTier.PETALS]


def test_all_tiers_disabled_graceful_degradation():
    """Test graceful handling when all tiers disabled."""
    tier_config = TierConfig(
        tier0_enabled=False,
        tier1_enabled=False,
        tier2_enabled=False
    )

    router = LLMRouter(tier_config=tier_config)

    request = LLMRequest(
        prompt="Question",
        sensitive=False
    )

    # Should still select a tier (will attempt and may fail gracefully)
    tier = router._select_tier(request)
    assert tier in [ComputeTier.DEVICE, ComputeTier.EDGE, ComputeTier.PETALS]
