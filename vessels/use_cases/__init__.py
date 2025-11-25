"""
Vessels Use Cases

This module contains domain-specific use cases built on top of the Vessels platform.
Each use case operates within a Vessel context, leveraging:
- Knowledge graphs for data storage
- Action gating for moral/privacy enforcement
- Measurement systems for tracking
- Community memory for learning

Available use cases:
- grants: Grant discovery, writing, and coordination
"""

from .grants import GrantsUseCase

__all__ = ["GrantsUseCase"]
