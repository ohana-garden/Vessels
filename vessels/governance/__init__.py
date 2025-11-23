"""
Governance module for Vessels.

This module contains the village consensus engine and related governance systems
for managing teachable moments and moral precedents.
"""

from .consensus import (
    VillageConsensusEngine,
    ConsultationRequest,
    ConsultationMode
)

__all__ = [
    "VillageConsensusEngine",
    "ConsultationRequest",
    "ConsultationMode",
]
