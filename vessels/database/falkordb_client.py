"""
FalkorDB Client Configuration and Management

Provides centralized FalkorDB client with connection pooling,
health checks, and graph namespace management.
"""
import logging
import os
from typing import Optional, Dict, Any
from falkordb import FalkorDB, Graph

logger = logging.getLogger(__name__)


class FalkorDBClient:
    """
    Centralized FalkorDB client with graph management.

    Supports multiple graph namespaces for different data domains:
    - vessels_sessions: User session tracking with relationships
    - vessels_phase_space: Agent state trajectories and constraint violations
    - vessels_memory: Community memory with semantic relationships
    - vessels_kala: Contribution network and value flows
    - vessels_commercial: Commercial agent tracking and revenue flows
    - vessels_grants: Grant opportunities and application matching
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        password: Optional[str] = None,
        username: Optional[str] = None,
        ssl: bool = False,
        ssl_certfile: Optional[str] = None,
        ssl_keyfile: Optional[str] = None,
        ssl_ca_certs: Optional[str] = None
    ):
        """
        Initialize FalkorDB client.

        Args:
            host: FalkorDB host (default: localhost or env REDIS_HOST)
            port: FalkorDB port (default: 6379 or env REDIS_PORT)
            password: Authentication password (env REDIS_PASSWORD)
            username: Authentication username
            ssl: Enable SSL/TLS
            ssl_certfile: Path to SSL certificate file
            ssl_keyfile: Path to SSL key file
            ssl_ca_certs: Path to CA certificates
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = int(port or os.getenv("REDIS_PORT", 6379))
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.username = username

        # Connection parameters
        connection_kwargs = {
            "host": self.host,
            "port": self.port
        }

        if self.username:
            connection_kwargs["username"] = self.username

        if self.password:
            connection_kwargs["password"] = self.password

        if ssl:
            connection_kwargs["ssl"] = True
            if ssl_certfile:
                connection_kwargs["ssl_certfile"] = ssl_certfile
            if ssl_keyfile:
                connection_kwargs["ssl_keyfile"] = ssl_keyfile
            if ssl_ca_certs:
                connection_kwargs["ssl_ca_certs"] = ssl_ca_certs

        try:
            self.client = FalkorDB(**connection_kwargs)
            logger.info(f"FalkorDB client connected to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to FalkorDB: {e}")
            raise

        # Graph cache
        self._graphs: Dict[str, Graph] = {}

        # Initialize standard graphs
        self._initialize_graphs()

    def _initialize_graphs(self):
        """Initialize standard graph namespaces."""
        standard_graphs = [
            "vessels_sessions",
            "vessels_phase_space",
            "vessels_memory",
            "vessels_kala",
            "vessels_commercial",
            "vessels_grants",
            "vessels_registry"
        ]

        for graph_name in standard_graphs:
            try:
                self._graphs[graph_name] = self.client.select_graph(graph_name)
                logger.info(f"Initialized graph: {graph_name}")
            except Exception as e:
                logger.warning(f"Could not initialize graph {graph_name}: {e}")

    def get_graph(self, graph_name: str) -> Graph:
        """
        Get or create a graph by name.

        Args:
            graph_name: Name of the graph namespace

        Returns:
            Graph object for executing queries
        """
        if graph_name not in self._graphs:
            self._graphs[graph_name] = self.client.select_graph(graph_name)
            logger.info(f"Created new graph: {graph_name}")

        return self._graphs[graph_name]

    def health_check(self) -> bool:
        """
        Check FalkorDB connection health.

        Returns:
            True if connection is healthy
        """
        try:
            # Try a simple query on the default graph
            graph = self.get_graph("vessels_health_check")
            result = graph.query("RETURN 1")
            return result is not None
        except Exception as e:
            logger.error(f"FalkorDB health check failed: {e}")
            return False

    def create_indexes(self):
        """
        Create indexes for common query patterns.

        Indexes improve query performance for:
        - Session lookups by session_id
        - Agent state lookups by agent_id
        - Memory lookups by person_id and community_id
        - Contribution lookups by contributor_id
        """
        indexes = {
            "vessels_sessions": [
                "CREATE INDEX FOR (s:Session) ON (s.session_id)",
                "CREATE INDEX FOR (u:User) ON (u.user_id)",
                "CREATE INDEX FOR (i:Interaction) ON (i.timestamp)"
            ],
            "vessels_phase_space": [
                "CREATE INDEX FOR (a:AgentState) ON (a.agent_id)",
                "CREATE INDEX FOR (a:AgentState) ON (a.timestamp)",
                "CREATE INDEX FOR (c:Constraint) ON (c.name)",
                "CREATE INDEX FOR (e:SecurityEvent) ON (e.timestamp)"
            ],
            "vessels_memory": [
                "CREATE INDEX FOR (m:MemoryEntry) ON (m.memory_id)",
                "CREATE INDEX FOR (m:MemoryEntry) ON (m.agent_id)",
                "CREATE INDEX FOR (p:Person) ON (p.person_id)",
                "CREATE INDEX FOR (c:Community) ON (c.community_id)"
            ],
            "vessels_kala": [
                "CREATE INDEX FOR (p:Person) ON (p.person_id)",
                "CREATE INDEX FOR (c:Contribution) ON (c.contribution_id)",
                "CREATE INDEX FOR (c:Contribution) ON (c.timestamp)"
            ],
            "vessels_commercial": [
                "CREATE INDEX FOR (ca:CommercialAgent) ON (ca.agent_id)",
                "CREATE INDEX FOR (r:RevenueRecord) ON (r.timestamp)"
            ],
            "vessels_grants": [
                "CREATE INDEX FOR (g:Grant) ON (g.grant_id)",
                "CREATE INDEX FOR (g:Grant) ON (g.deadline)"
            ]
        }

        for graph_name, index_queries in indexes.items():
            try:
                graph = self.get_graph(graph_name)
                for query in index_queries:
                    try:
                        graph.query(query)
                        logger.info(f"Created index on {graph_name}: {query}")
                    except Exception as e:
                        # Index might already exist
                        logger.debug(f"Index creation skipped (may exist): {e}")
            except Exception as e:
                logger.error(f"Failed to create indexes on {graph_name}: {e}")

    def close(self):
        """Close FalkorDB connection."""
        try:
            if hasattr(self, 'client') and self.client:
                # FalkorDB client doesn't have explicit close, but clear cache
                self._graphs.clear()
                logger.info("FalkorDB client closed")
        except Exception as e:
            logger.error(f"Error closing FalkorDB client: {e}")


# Singleton instance
_falkordb_client: Optional[FalkorDBClient] = None


def get_falkordb_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    **kwargs
) -> FalkorDBClient:
    """
    Get or create singleton FalkorDB client.

    Args:
        host: FalkorDB host
        port: FalkorDB port
        **kwargs: Additional connection parameters

    Returns:
        FalkorDBClient instance
    """
    global _falkordb_client

    if _falkordb_client is None:
        _falkordb_client = FalkorDBClient(host=host, port=port, **kwargs)
        # Create indexes on initialization
        _falkordb_client.create_indexes()

    return _falkordb_client


def close_falkordb_client():
    """Close singleton FalkorDB client."""
    global _falkordb_client

    if _falkordb_client:
        _falkordb_client.close()
        _falkordb_client = None
