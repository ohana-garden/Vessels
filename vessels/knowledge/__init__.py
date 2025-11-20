"""
Vessels Knowledge Graph and Vector Store Management

This package provides the knowledge layer for Vessels, including:
- Graphiti/FalkorDB integration for temporal knowledge graphs
- Vector embeddings and semantic search
- Project-specific and shared vector stores
- Graph backup and restore utilities
- Fast context assembly pipeline
"""

from .schema import VesselsGraphSchema
from .graphiti_client import VesselsGraphitiClient
from .embeddings import VesselsEmbedder
from .vector_stores import ProjectVectorStore, SharedVectorStore
from .context_assembly import ContextAssembler

__all__ = [
    "VesselsGraphSchema",
    "VesselsGraphitiClient",
    "VesselsEmbedder",
    "ProjectVectorStore",
    "SharedVectorStore",
    "ContextAssembler",
]
