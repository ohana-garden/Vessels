"""
External service integrations for Vessels.

Includes:
- NanoBanana: AI image generation from conversation entities
"""

from vessels.services.nanobanana_client import (
    NanoBananaClient,
    GeneratedImage,
    AspectRatio,
    ImageStyle,
    get_nanobanana_client,
)

__all__ = [
    "NanoBananaClient",
    "GeneratedImage",
    "AspectRatio",
    "ImageStyle",
    "get_nanobanana_client",
]
