"""
Vessels CLI - Command-line interface for vessel management.

Provides commands for:
- Loading vessels from manifest files
- Listing and inspecting vessels
- Starting and stopping vessels
- Managing vessel configurations
"""

from .manifest import load_manifest, validate_manifest, ManifestLoader
from .commands import main

__all__ = [
    "load_manifest",
    "validate_manifest",
    "ManifestLoader",
    "main",
]
