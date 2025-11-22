"""
Tier routing for device/edge/cloud architecture.

Routes requests to appropriate compute tiers based on requirements.
"""

from .router import TierRouter, TierLevel, RoutingDecision

__all__ = ["TierRouter", "TierLevel", "RoutingDecision"]
