"""
Vessels Compute Layer

Manages LLM inference across three tiers:
- Tier 0: On-device (phone/tablet)
- Tier 1: Local edge (home server)
- Tier 2: Petals network (optional, distributed)
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "PetalsGateway",
    "LLMRouter",
    "LocalEdgeLLM"
]
