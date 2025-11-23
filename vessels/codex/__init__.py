"""
The Vessels Codex: The Village Protocol

A meta-awareness layer for Vessels that implements:
- Tension detection (value collisions, ambiguity, low confidence)
- Check protocol (requesting village guidance)
- Parable system (learning from decisions)
- Safety guardrails (non-negotiable constraints)

"We learn together, or we do not learn at all."
"""

from .tension_detector import TensionDetector, Tension, TensionType
from .check_protocol import CheckProtocol, CheckRequest, CheckResponse
from .parable import Parable, ParableStorage
from .council import VillageCouncil, CouncilDecision
from .codex_gate import CodexGate

__all__ = [
    "TensionDetector",
    "Tension",
    "TensionType",
    "CheckProtocol",
    "CheckRequest",
    "CheckResponse",
    "Parable",
    "ParableStorage",
    "VillageCouncil",
    "CouncilDecision",
    "CodexGate",
]
