"""
Vessels Knowledge Graph and Vector Store Management

This package provides the knowledge layer for Vessels, including:
- Graphiti/FalkorDB integration for temporal knowledge graphs
- Vector embeddings and semantic search
- Project-specific and shared vector stores
- Graph backup and restore utilities
- Fast context assembly pipeline
- Parable system for moral precedent memory
"""

from .schema import VesselsGraphSchema, CommunityPrivacy
from .parable import Parable, ParableLibrary

__all__ = [
    "VesselsGraphSchema",
    "CommunityPrivacy",
    "Parable",
    "ParableLibrary",
]
