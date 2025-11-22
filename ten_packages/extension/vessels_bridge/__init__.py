"""
Vessels Bridge Extension for TEN Framework

This extension integrates the Vessels agentic platform with the TEN Framework
real-time audio graph, enabling voice-first agent interactions.
"""

from .extension import VesselsBridgeExtension, register_addon_as_extension

__version__ = "0.1.0"
__all__ = ["VesselsBridgeExtension", "register_addon_as_extension"]
