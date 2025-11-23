"""
Adversarial testing framework for Vessels moral constraints.

This module implements "Trickster" agents that actively try to game
the moral geometry system. These adversarial tests help discover
loopholes and edge cases before they're exploited in production.

Test Categories:
- Activity Gaming: High activity to mask low service
- Coordination Manipulation: High coordination, low justice
- Truthfulness Gaming: Maintain truthfulness while violating other virtues
- Resource Hoarding: Low service, high resource consumption
- Service Shirking: Appear active while avoiding real service
"""

from vessels.tests.adversarial.trickster_agents import (
    TricksterAgent,
    ActivitySpammer,
    CoordinationManipulator,
    TruthfulnessGamer,
    ResourceHoarder,
    ServiceShirker,
    JusticeFaker,
)

__all__ = [
    "TricksterAgent",
    "ActivitySpammer",
    "CoordinationManipulator",
    "TruthfulnessGamer",
    "ResourceHoarder",
    "ServiceShirker",
    "JusticeFaker",
]
