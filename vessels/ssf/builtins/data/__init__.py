"""
Data SSFs - Graphiti Queries, Memory Operations.

These SSFs handle data retrieval and storage operations
through the Graphiti/FalkorDB knowledge graph.
"""

from typing import Dict, Any, List, Optional
from uuid import uuid4
from datetime import datetime
import logging

from ...schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
)

logger = logging.getLogger(__name__)


# ============================================================================
# HANDLER IMPLEMENTATIONS
# ============================================================================

async def handle_query_graph(
    query: str,
    community_id: str,
    parameters: Optional[Dict[str, Any]] = None,
    limit: int = 100,
    **kwargs
) -> Dict[str, Any]:
    """
    Query the knowledge graph.

    Args:
        query: Cypher-like query string
        community_id: Community to query
        parameters: Optional query parameters
        limit: Maximum results

    Returns:
        Query results
    """
    logger.info(f"Graph query in {community_id}: {query[:50]}...")

    # Placeholder - actual implementation would use Graphiti client
    return {
        "results": [],
        "count": 0,
        "query": query,
        "execution_time_ms": 10,
    }


async def handle_store_memory(
    content: str,
    memory_type: str,
    community_id: str,
    entity_ids: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    valid_until: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Store a memory in the knowledge graph.

    Args:
        content: Memory content
        memory_type: Type of memory (experience, fact, pattern)
        community_id: Community to store in
        entity_ids: Related entity IDs
        metadata: Additional metadata
        valid_until: Optional expiration timestamp

    Returns:
        Stored memory details
    """
    logger.info(f"Storing {memory_type} memory in {community_id}")

    return {
        "memory_id": str(uuid4()),
        "type": memory_type,
        "stored_at": datetime.utcnow().isoformat(),
        "community_id": community_id,
    }


async def handle_retrieve_memories(
    query: str,
    community_id: str,
    memory_types: Optional[List[str]] = None,
    limit: int = 10,
    include_related: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Retrieve memories from the knowledge graph.

    Args:
        query: Semantic search query
        community_id: Community to search
        memory_types: Filter by memory types
        limit: Maximum results
        include_related: Include related entities

    Returns:
        Retrieved memories
    """
    logger.info(f"Retrieving memories: {query[:50]}...")

    return {
        "memories": [],
        "count": 0,
        "query": query,
    }


async def handle_search_knowledge(
    query: str,
    community_id: str,
    node_types: Optional[List[str]] = None,
    include_cross_community: bool = False,
    limit: int = 20,
    **kwargs
) -> Dict[str, Any]:
    """
    Search the knowledge graph with RAG retrieval.

    Args:
        query: Natural language search query
        community_id: Primary community to search
        node_types: Filter by node types
        include_cross_community: Include shared community data
        limit: Maximum results

    Returns:
        Search results with relevance scores
    """
    logger.info(f"Searching knowledge: {query[:50]}...")

    return {
        "results": [],
        "count": 0,
        "query": query,
        "communities_searched": [community_id],
    }


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_query_graph_ssf() -> SSFDefinition:
    """Create the query_graph SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="query_graph",
        version="1.0.0",
        category=SSFCategory.DATA_RETRIEVAL,
        tags=["graph", "query", "knowledge", "graphiti", "cypher"],
        description="Execute a query against the knowledge graph to retrieve nodes, relationships, and patterns.",
        description_for_llm="Use this SSF when you need to query the knowledge graph directly. Supports Cypher-like queries for complex graph traversals. Good for finding relationships between entities, patterns, and specific node data.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.data",
            function_name="handle_query_graph",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Cypher-like query string",
                },
                "community_id": {
                    "type": "string",
                    "description": "Community to query",
                },
                "parameters": {
                    "type": "object",
                    "description": "Query parameters",
                },
                "limit": {
                    "type": "integer",
                    "default": 100,
                    "maximum": 1000,
                    "description": "Maximum results",
                },
            },
            "required": ["query", "community_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "count": {"type": "integer"},
                "query": {"type": "string"},
                "execution_time_ms": {"type": "number"},
            },
        },
        timeout_seconds=60,
        memory_mb=256,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_store_memory_ssf() -> SSFDefinition:
    """Create the store_memory SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="store_memory",
        version="1.0.0",
        category=SSFCategory.MEMORY_OPERATIONS,
        tags=["memory", "store", "knowledge", "graphiti", "write"],
        description="Store a new memory (experience, fact, or pattern) in the knowledge graph.",
        description_for_llm="Use this SSF to persist information to the knowledge graph. Good for storing learned facts, recording experiences, or noting patterns. Memories are scoped to communities and can have expiration dates.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.data",
            function_name="handle_store_memory",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Memory content",
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["experience", "fact", "pattern"],
                    "description": "Type of memory",
                },
                "community_id": {
                    "type": "string",
                    "description": "Community to store in",
                },
                "entity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Related entity IDs",
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata",
                },
                "valid_until": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Optional expiration",
                },
            },
            "required": ["content", "memory_type", "community_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "type": {"type": "string"},
                "stored_at": {"type": "string"},
                "community_id": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=["Creates new node in knowledge graph"],
        reversible=True,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.WARN,
        ),
    )


def _create_retrieve_memories_ssf() -> SSFDefinition:
    """Create the retrieve_memories SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="retrieve_memories",
        version="1.0.0",
        category=SSFCategory.DATA_RETRIEVAL,
        tags=["memory", "retrieve", "search", "recall", "graphiti"],
        description="Retrieve memories from the knowledge graph using semantic search.",
        description_for_llm="Use this SSF to recall stored memories using natural language queries. Searches experiences, facts, and patterns. Good for remembering past interactions, learned information, or recognized patterns.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.data",
            function_name="handle_retrieve_memories",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query",
                },
                "community_id": {
                    "type": "string",
                    "description": "Community to search",
                },
                "memory_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by memory types",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "maximum": 100,
                    "description": "Maximum results",
                },
                "include_related": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include related entities",
                },
            },
            "required": ["query", "community_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "memories": {"type": "array"},
                "count": {"type": "integer"},
                "query": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=256,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_search_knowledge_ssf() -> SSFDefinition:
    """Create the search_knowledge SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="search_knowledge",
        version="1.0.0",
        category=SSFCategory.DATA_RETRIEVAL,
        tags=["search", "rag", "knowledge", "semantic", "retrieval"],
        description="Search the knowledge graph with semantic RAG retrieval for relevant information.",
        description_for_llm="Use this SSF for general knowledge search using natural language. Combines semantic search with graph traversal for comprehensive results. Good for answering questions, finding related information, or exploring topics.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.data",
            function_name="handle_search_knowledge",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                },
                "community_id": {
                    "type": "string",
                    "description": "Primary community to search",
                },
                "node_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by node types",
                },
                "include_cross_community": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include shared community data",
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "maximum": 100,
                    "description": "Maximum results",
                },
            },
            "required": ["query", "community_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "count": {"type": "integer"},
                "query": {"type": "string"},
                "communities_searched": {"type": "array"},
            },
        },
        timeout_seconds=45,
        memory_mb=512,
        risk_level=RiskLevel.LOW,
        side_effects=[],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in data SSFs."""
    return [
        _create_query_graph_ssf(),
        _create_store_memory_ssf(),
        _create_retrieve_memories_ssf(),
        _create_search_knowledge_ssf(),
    ]
