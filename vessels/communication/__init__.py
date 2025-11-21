"""
Vessels Communication Layer

Handles decentralized communication protocols for cross-community coordination.
Supports local RPC and optional Nostr integration.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "NostrAdapter",
    "ProtocolRegistry",
    "DataSanitizer",
]


class CommunicationError(Exception):
    """Base exception for communication errors"""
    pass


class ProtocolNotEnabled(CommunicationError):
    """Raised when attempting to use a disabled protocol"""
    pass


class SanitizationError(CommunicationError):
    """Raised when data cannot be safely sanitized"""
    pass
