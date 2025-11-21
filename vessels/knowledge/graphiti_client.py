"""
Vessels Graphiti Client

Wrapper around Graphiti for Vessels-specific functionality:
- Community graph namespacing
- Privacy-filtered cross-community queries
- Temporal knowledge tracking
- Integration with 12D phase space and moral constraints
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .schema import (
    NodeType, RelationType, PropertyName,
    VesselsGraphSchema, CommunityPrivacy
)

logger = logging.getLogger(__name__)


class VesselsGraphitiClient:
    """
    Vessels-specific wrapper around Graphiti/FalkorDB

    Provides:
    - Namespace isolation per community
    - Privacy-filtered queries
    - Temporal validity tracking
    - Simplified API for Vessels patterns
    """

    def __init__(
        self,
        community_id: str,
        servant_id: Optional[str] = None,
        host: str = "localhost",
        port: int = 6379,
        read_only_communities: Optional[List[str]] = None,
        allow_mock: bool = False,
    ):
        """
        Initialize Graphiti client for a community

        Args:
            community_id: Primary community this client operates in (read/write access)
            servant_id: ID of the servant using this client (for audit trail)
            host: FalkorDB host
            port: FalkorDB port
            read_only_communities: Communities this client can read (privacy-filtered)
        """
        self.community_id = community_id
        self.servant_id = servant_id
        self.host = host
        self.port = port
        self.read_only_communities = read_only_communities or []
        self.allow_mock = allow_mock

        # Graph name for this community
        self.graph_name = VesselsGraphSchema.create_community_graph_name(community_id)

        # Lazy-load Graphiti client
        self._graphiti = None
        self._driver = None

    @property
    def graphiti(self):
        """Lazy-load Graphiti client."""
        if self._graphiti is None:
            try:
                from graphiti_core import Graphiti
            except ImportError as exc:  # pragma: no cover - dependency check
                message = (
                    "graphiti-core not installed. Install graphiti-core to use the "
                    "Graphiti/FalkorDB backend or set VESSELS_GRAPHITI_ALLOW_MOCK=1 "
                    "to continue with the mock client."
                )
                logger.error(message)
                if not self.allow_mock:
                    raise RuntimeError(message) from exc
                self._graphiti = MockGraphitiClient(self.graph_name)
                return self._graphiti

            try:
                from falkordb import FalkorDB
            except ImportError as exc:  # pragma: no cover - dependency check
                message = (
                    "falkordb not installed. Install falkordb to connect to the "
                    "graph backend or set VESSELS_GRAPHITI_ALLOW_MOCK=1 to proceed "
                    "with the mock client."
                )
                logger.error(message)
                if not self.allow_mock:
                    raise RuntimeError(message) from exc
                self._graphiti = MockGraphitiClient(self.graph_name)
                return self._graphiti

            try:
                self._driver = FalkorDB(host=self.host, port=self.port)
                logger.info(f"Connected to FalkorDB at {self.host}:{self.port}")

                self._graphiti = Graphiti(
                    graph_name=self.graph_name,
                    driver=self._driver,
                )
                logger.info(f"Initialized Graphiti for community: {self.community_id}")
            except Exception as exc:  # pragma: no cover - runtime connectivity issues
                message = (
                    f"Failed to initialize Graphiti for {self.community_id}: {exc}. "
                    "Set VESSELS_GRAPHITI_ALLOW_MOCK=1 to continue with the mock "
                    "client while you provision FalkorDB/Graphiti."
                )
                logger.error(message)
                if not self.allow_mock:
                    raise RuntimeError(message) from exc
                self._graphiti = MockGraphitiClient(self.graph_name)

        return self._graphiti

    def health_check(self) -> bool:
        """Return True if the Graphiti backend is available."""
        client = self.graphiti
        if isinstance(client, MockGraphitiClient):
            return False
        try:
            client.execute_query("RETURN 1", {})
            return True
        except Exception as exc:  # pragma: no cover - real backend path
            logger.error(f"Graphiti health check failed: {exc}")
            return False

    def create_node(
        self,
        node_type: NodeType,
        properties: Dict[str, Any],
        node_id: Optional[str] = None
    ) -> str:
        """
        Create a node in the knowledge graph

        Args:
            node_type: Type of node (from NodeType enum)
            properties: Node properties (must include required properties)
            node_id: Optional node ID (generated if not provided)

        Returns:
            Node ID
        """
        # Add community_id if not present
        if PropertyName.COMMUNITY_ID not in properties:
            properties[PropertyName.COMMUNITY_ID] = self.community_id

        # Add created_by if servant_id present
        if self.servant_id and PropertyName.CREATED_BY not in properties:
            properties[PropertyName.CREATED_BY] = self.servant_id

        # Add created_at timestamp
        if PropertyName.CREATED_AT not in properties:
            properties[PropertyName.CREATED_AT] = datetime.utcnow().isoformat()

        # Validate properties
        if not VesselsGraphSchema.validate_node_properties(node_type, properties):
            missing = set(VesselsGraphSchema.get_required_properties(node_type)) - set(properties.keys())
            raise ValueError(f"Missing required properties for {node_type}: {missing}")

        # Generate ID if not provided
        if node_id is None:
            node_id = f"{node_type.value}_{datetime.utcnow().timestamp()}"

        try:
            # Use Graphiti to create node
            # This is a simplified version - actual implementation depends on Graphiti API
            result = self.graphiti.create_node(
                node_type=node_type.value,
                node_id=node_id,
                properties=properties
            )
            logger.debug(f"Created {node_type} node: {node_id}")
            return node_id

        except Exception as e:
            logger.error(f"Error creating node: {e}")
            raise

    def create_relationship(
        self,
        source_id: str,
        rel_type: RelationType,
        target_id: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between two nodes

        Args:
            source_id: Source node ID
            rel_type: Relationship type
            target_id: Target node ID
            properties: Optional relationship properties
        """
        properties = properties or {}

        # Add created_by if servant_id present
        if self.servant_id and PropertyName.CREATED_BY not in properties:
            properties[PropertyName.CREATED_BY] = self.servant_id

        # Add created_at
        if PropertyName.CREATED_AT not in properties:
            properties[PropertyName.CREATED_AT] = datetime.utcnow().isoformat()

        try:
            self.graphiti.create_relationship(
                source_id=source_id,
                rel_type=rel_type.value,
                target_id=target_id,
                properties=properties
            )
            logger.debug(f"Created {rel_type} relationship: {source_id} -> {target_id}")

        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            raise

    def query(self, cypher: str, **params) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query on the graph

        Args:
            cypher: Cypher query string
            **params: Query parameters

        Returns:
            List of result records
        """
        try:
            # TODO: Add privacy filtering for cross-community queries
            results = self.graphiti.execute_query(cypher, params)
            return results

        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def get_neighbors(
        self,
        node_id: str,
        rel_types: Optional[List[RelationType]] = None,
        max_depth: int = 1
    ) -> Dict[str, Any]:
        """
        Get neighboring nodes connected to a node

        Args:
            node_id: ID of the node
            rel_types: Optional list of relationship types to follow
            max_depth: Maximum traversal depth

        Returns:
            Dict with neighbors organized by relationship type
        """
        rel_filter = ""
        if rel_types:
            rel_types_str = "|".join([r.value for r in rel_types])
            rel_filter = f":{rel_types_str}"

        cypher = f"""
        MATCH (n {{id: $node_id}})-[r{rel_filter}*1..{max_depth}]-(neighbor)
        RETURN type(r) as rel_type, neighbor
        """

        try:
            results = self.query(cypher, node_id=node_id)

            # Organize by relationship type
            neighbors = {}
            for record in results:
                rel_type = record.get("rel_type")
                neighbor = record.get("neighbor")
                if rel_type not in neighbors:
                    neighbors[rel_type] = []
                neighbors[rel_type].append(neighbor)

            return neighbors

        except Exception as e:
            logger.error(f"Error getting neighbors: {e}")
            return {}

    def add_episode(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Add an episodic memory to the graph (Graphiti will extract entities)

        Args:
            text: Episode text (conversation, action, observation)
            metadata: Optional metadata (timestamp, source, etc.)
        """
        metadata = metadata or {}

        # Add community context
        metadata["community_id"] = self.community_id
        if self.servant_id:
            metadata["servant_id"] = self.servant_id

        try:
            # Graphiti will automatically extract entities and relationships
            self.graphiti.add_episode(text, metadata=metadata)
            logger.debug(f"Added episode: {text[:50]}...")

        except Exception as e:
            logger.error(f"Error adding episode: {e}")
            raise

    def search_semantic(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search across graph entities

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching entities/episodes
        """
        try:
            results = self.graphiti.search(query, limit=top_k)
            return results

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []


class MockGraphitiClient:
    """
    Mock Graphiti client for testing when FalkorDB is not available

    This allows development and testing without requiring FalkorDB running.
    """

    def __init__(self, graph_name: str):
        self.graph_name = graph_name
        self.nodes = {}
        self.relationships = []
        logger.info(f"Initialized mock Graphiti client for {graph_name}")

    def create_node(self, node_type: str, node_id: str, properties: Dict[str, Any]) -> str:
        """Create a node in the mock graph"""
        self.nodes[node_id] = {
            "type": node_type,
            "id": node_id,
            "properties": properties
        }
        return node_id

    def create_relationship(
        self,
        source_id: str,
        rel_type: str,
        target_id: str,
        properties: Dict[str, Any]
    ):
        """Create a relationship in the mock graph"""
        self.relationships.append({
            "source": source_id,
            "type": rel_type,
            "target": target_id,
            "properties": properties
        })

    def execute_query(self, cypher: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute a query on the mock graph"""
        logger.warning("Mock client: Query execution not fully implemented")
        return []

    def add_episode(self, text: str, metadata: Dict[str, Any]):
        """Add an episode to the mock graph"""
        episode_id = f"episode_{len(self.nodes)}"
        self.create_node("Episode", episode_id, {"text": text, **metadata})
        logger.debug(f"Mock: Added episode {episode_id}")

    def search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search the mock graph"""
        logger.warning("Mock client: Search not implemented")
        return []
