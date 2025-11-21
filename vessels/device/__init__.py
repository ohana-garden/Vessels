"""
Vessels On-Device AI Layer (Tier 0)

Handles local speech recognition, synthesis, LLM inference, and emotional intelligence.
All processing happens on-device for maximum privacy and offline capability.
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "WhisperSTT",
    "VesselsTTS",
    "DeviceLLM",
    "EmotionalIntelligence",
    "DeviceAPI"
]
