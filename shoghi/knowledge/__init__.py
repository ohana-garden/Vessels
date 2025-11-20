"""
Shoghi Knowledge Graph and Vector Store Management

This package provides the knowledge layer for Shoghi, including:
- Graphiti/FalkorDB integration for temporal knowledge graphs
- Vector embeddings and semantic search
- Project-specific and shared vector stores
- Graph backup and restore utilities
"""

from .schema import ShorghiGraphSchema
from .graphiti_client import ShorghiGraphitiClient
from .embeddings import ShorghiEmbedder
from .vector_stores import ProjectVectorStore, SharedVectorStore

__all__ = [
    "ShorghiGraphSchema",
    "ShorghiGraphitiClient",
    "ShorghiEmbedder",
    "ProjectVectorStore",
    "SharedVectorStore",
]
