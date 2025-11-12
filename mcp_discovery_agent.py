#!/usr/bin/env python3
"""
MCP DISCOVERY AGENT

Automatically discovers Model Context Protocol (MCP) servers and updates the
universal connector catalog with context-sensitive recommendations.

FEATURES:
- Discovers MCP servers from multiple sources (registries, GitHub, local config)
- Analyzes server capabilities and converts to connector specifications
- Provides context-aware recommendations based on current task
- Maintains a dynamic catalog that updates automatically
- Integrates seamlessly with universal_connector

MCP PROTOCOL:
Model Context Protocol (MCP) is Anthropic's standard for connecting AI assistants
to external data sources and tools. Servers expose resources, tools, and prompts
through a standardized JSON-RPC interface.

DISCOVERY SOURCES:
1. Official MCP registry (if available)
2. GitHub topics: #mcp-server, #model-context-protocol
3. Local configuration files (~/.mcp/servers.json)
4. Environment variables (MCP_SERVERS_PATH)
5. User-provided URLs/repositories

USAGE:
    from mcp_discovery_agent import mcp_agent

    # Discover servers
    servers = mcp_agent.discover_servers()

    # Get context-sensitive recommendations
    recommendations = mcp_agent.recommend_for_context(
        "I need to search for grants in Hawaii"
    )

    # Update universal connector catalog
    mcp_agent.update_connector_catalog()
"""

import json
import logging
import os
import re
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from urllib.parse import urlparse
import requests

# Import universal connector types
try:
    from universal_connector import (
        ConnectorSpecification,
        ConnectorType,
        AuthenticationType,
        universal_connector
    )
    CONNECTOR_AVAILABLE = True
except ImportError:
    CONNECTOR_AVAILABLE = False
    logging.warning("universal_connector not available, running in standalone mode")

logger = logging.getLogger(__name__)


class MCPServerType(Enum):
    """Types of MCP servers"""
    DATA_SOURCE = "data_source"  # Databases, APIs, files
    TOOL_PROVIDER = "tool_provider"  # Actions, operations
    RESOURCE_PROVIDER = "resource_provider"  # Documents, templates
    MIXED = "mixed"  # Combination


class DiscoveryStatus(Enum):
    """Status of server discovery"""
    PENDING = "pending"
    DISCOVERING = "discovering"
    ACTIVE = "active"
    FAILED = "failed"
    DEPRECATED = "deprecated"


@dataclass
class MCPCapability:
    """Represents a capability exposed by an MCP server"""
    name: str
    type: str  # "tool", "resource", "prompt"
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class MCPServer:
    """Represents a discovered MCP server"""
    id: str
    name: str
    description: str
    server_type: MCPServerType
    url: str
    version: str
    capabilities: List[MCPCapability]
    authentication: Dict[str, Any]
    metadata: Dict[str, Any]
    discovery_date: datetime
    status: DiscoveryStatus
    relevance_score: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class ContextRecommendation:
    """Context-aware server recommendation"""
    server: MCPServer
    relevance_score: float
    matching_capabilities: List[str]
    reasoning: str
    suggested_operations: List[str]


class MCPDiscoveryAgent:
    """
    Agent that discovers MCP servers and provides context-sensitive recommendations.
    """

    def __init__(self):
        self.discovered_servers: Dict[str, MCPServer] = {}
        self.discovery_sources: List[Dict[str, Any]] = []
        self.context_cache: Dict[str, List[ContextRecommendation]] = {}
        self.running = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.last_discovery: Optional[datetime] = None

        # Context analysis patterns
        self.context_patterns = self._load_context_patterns()

        self._initialize_discovery_sources()
        logger.info("MCP Discovery Agent initialized")

    def _initialize_discovery_sources(self):
        """Initialize discovery sources"""
        self.discovery_sources = [
            {
                "name": "MCP Official Registry",
                "type": "registry",
                "url": "https://registry.modelcontextprotocol.io/servers",
                "enabled": True,
                "priority": 1
            },
            {
                "name": "GitHub MCP Servers",
                "type": "github",
                "search_query": "topic:mcp-server language:python",
                "enabled": True,
                "priority": 2
            },
            {
                "name": "Local Configuration",
                "type": "local",
                "path": os.path.expanduser("~/.mcp/servers.json"),
                "enabled": True,
                "priority": 3
            },
            {
                "name": "Environment Variables",
                "type": "env",
                "variable": "MCP_SERVERS_PATH",
                "enabled": True,
                "priority": 4
            }
        ]

    def _load_context_patterns(self) -> Dict[str, List[str]]:
        """
        Load patterns for context analysis.

        Maps intent keywords to relevant capability tags.
        """
        return {
            "search": ["search", "query", "find", "lookup", "discover"],
            "grants": ["grants", "funding", "foundation", "government", "financial"],
            "database": ["database", "sql", "query", "data", "records"],
            "files": ["files", "filesystem", "documents", "read", "write"],
            "api": ["api", "rest", "http", "endpoint", "request"],
            "email": ["email", "mail", "smtp", "send", "notification"],
            "calendar": ["calendar", "schedule", "event", "meeting", "appointment"],
            "finance": ["finance", "accounting", "budget", "transaction", "payment"],
            "weather": ["weather", "forecast", "climate", "temperature"],
            "location": ["location", "maps", "geography", "geocoding", "address"],
            "health": ["health", "medical", "patient", "healthcare", "wellness"],
            "social": ["social", "twitter", "facebook", "linkedin", "post"],
            "analytics": ["analytics", "metrics", "statistics", "data analysis"],
            "ai": ["ai", "ml", "machine learning", "llm", "model"],
        }

    def discover_servers(self, force_refresh: bool = False) -> List[MCPServer]:
        """
        Discover MCP servers from all configured sources.

        Args:
            force_refresh: Force rediscovery even if cached

        Returns:
            List of discovered MCP servers
        """
        # Check cache
        if not force_refresh and self.last_discovery:
            cache_age = datetime.now() - self.last_discovery
            if cache_age < timedelta(hours=6):
                logger.info(f"Using cached discovery results (age: {cache_age})")
                return list(self.discovered_servers.values())

        logger.info("Starting MCP server discovery...")
        discovered_count = 0

        # Sort sources by priority
        sorted_sources = sorted(
            self.discovery_sources,
            key=lambda s: s.get("priority", 999)
        )

        for source in sorted_sources:
            if not source.get("enabled", False):
                continue

            try:
                logger.info(f"Discovering from {source['name']}...")
                servers = self._discover_from_source(source)

                for server in servers:
                    self.discovered_servers[server.id] = server
                    discovered_count += 1

                logger.info(f"Found {len(servers)} servers from {source['name']}")

            except Exception as e:
                logger.error(f"Error discovering from {source['name']}: {e}")

        self.last_discovery = datetime.now()
        logger.info(f"Discovery complete: {discovered_count} total servers")

        return list(self.discovered_servers.values())

    def _discover_from_source(self, source: Dict[str, Any]) -> List[MCPServer]:
        """Discover servers from a specific source"""
        source_type = source.get("type")

        if source_type == "registry":
            return self._discover_from_registry(source)
        elif source_type == "github":
            return self._discover_from_github(source)
        elif source_type == "local":
            return self._discover_from_local(source)
        elif source_type == "env":
            return self._discover_from_env(source)
        else:
            logger.warning(f"Unknown source type: {source_type}")
            return []

    def _discover_from_registry(self, source: Dict[str, Any]) -> List[MCPServer]:
        """
        Discover from official MCP registry.

        Note: This is currently a mock implementation. Replace with actual
        registry API calls when the official registry is available.
        """
        # TODO: Implement actual registry API calls when available
        logger.warning("Official MCP registry not yet available, using sample data")

        # Sample servers for demonstration
        return [
            MCPServer(
                id="mcp-server-sqlite",
                name="SQLite MCP Server",
                description="Query SQLite databases through MCP",
                server_type=MCPServerType.DATA_SOURCE,
                url="mcp://localhost:3000/sqlite",
                version="1.0.0",
                capabilities=[
                    MCPCapability(
                        name="query",
                        type="tool",
                        description="Execute SQL queries",
                        input_schema={"type": "object", "properties": {"sql": {"type": "string"}}},
                        tags=["database", "query", "sql"]
                    )
                ],
                authentication={"type": "none"},
                metadata={"category": "database", "language": "python"},
                discovery_date=datetime.now(),
                status=DiscoveryStatus.ACTIVE,
                tags=["database", "sqlite", "sql"]
            ),
            MCPServer(
                id="mcp-server-filesystem",
                name="Filesystem MCP Server",
                description="Read and write files through MCP",
                server_type=MCPServerType.TOOL_PROVIDER,
                url="mcp://localhost:3001/filesystem",
                version="1.0.0",
                capabilities=[
                    MCPCapability(
                        name="read_file",
                        type="tool",
                        description="Read file contents",
                        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
                        tags=["files", "read"]
                    ),
                    MCPCapability(
                        name="write_file",
                        type="tool",
                        description="Write file contents",
                        input_schema={
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            }
                        },
                        tags=["files", "write"]
                    )
                ],
                authentication={"type": "none"},
                metadata={"category": "filesystem", "language": "python"},
                discovery_date=datetime.now(),
                status=DiscoveryStatus.ACTIVE,
                tags=["filesystem", "files", "io"]
            )
        ]

    def _discover_from_github(self, source: Dict[str, Any]) -> List[MCPServer]:
        """
        Discover MCP servers from GitHub.

        Searches for repositories with MCP server topic.
        """
        servers = []
        search_query = source.get("search_query", "topic:mcp-server")

        try:
            # GitHub API search
            response = requests.get(
                "https://api.github.com/search/repositories",
                params={"q": search_query, "sort": "stars", "per_page": 10},
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=10
            )

            if response.status_code == 200:
                repos = response.json().get("items", [])

                for repo in repos:
                    try:
                        server = self._parse_github_repo_to_server(repo)
                        if server:
                            servers.append(server)
                    except Exception as e:
                        logger.warning(f"Error parsing repo {repo.get('name')}: {e}")

            else:
                logger.warning(f"GitHub API returned {response.status_code}")

        except Exception as e:
            logger.error(f"Error discovering from GitHub: {e}")

        return servers

    def _parse_github_repo_to_server(self, repo: Dict[str, Any]) -> Optional[MCPServer]:
        """Convert GitHub repository to MCP server representation"""
        # This is a simplified parser. Real implementation would:
        # 1. Check for MCP manifest file
        # 2. Parse capability definitions
        # 3. Extract authentication requirements

        repo_name = repo.get("name", "")
        repo_url = repo.get("html_url", "")
        description = repo.get("description", "")

        # Basic server definition from repository
        return MCPServer(
            id=f"github-{repo.get('id')}",
            name=repo_name,
            description=description,
            server_type=MCPServerType.MIXED,
            url=repo_url,
            version="unknown",
            capabilities=[],  # Would parse from repo
            authentication={"type": "unknown"},
            metadata={
                "source": "github",
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language", "")
            },
            discovery_date=datetime.now(),
            status=DiscoveryStatus.PENDING,
            tags=repo.get("topics", [])
        )

    def _discover_from_local(self, source: Dict[str, Any]) -> List[MCPServer]:
        """Discover servers from local configuration file"""
        servers = []
        config_path = source.get("path")

        if not config_path or not os.path.exists(config_path):
            logger.debug(f"Local config not found: {config_path}")
            return servers

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)

            for server_config in config.get("servers", []):
                try:
                    server = self._parse_config_to_server(server_config)
                    if server:
                        servers.append(server)
                except Exception as e:
                    logger.warning(f"Error parsing local config: {e}")

        except Exception as e:
            logger.error(f"Error reading local config: {e}")

        return servers

    def _parse_config_to_server(self, config: Dict[str, Any]) -> Optional[MCPServer]:
        """Parse configuration dictionary to MCP server"""
        try:
            capabilities = []
            for cap_config in config.get("capabilities", []):
                capabilities.append(MCPCapability(
                    name=cap_config["name"],
                    type=cap_config["type"],
                    description=cap_config.get("description", ""),
                    input_schema=cap_config.get("input_schema", {}),
                    tags=cap_config.get("tags", [])
                ))

            return MCPServer(
                id=config["id"],
                name=config["name"],
                description=config.get("description", ""),
                server_type=MCPServerType(config.get("type", "mixed")),
                url=config["url"],
                version=config.get("version", "1.0.0"),
                capabilities=capabilities,
                authentication=config.get("authentication", {"type": "none"}),
                metadata=config.get("metadata", {}),
                discovery_date=datetime.now(),
                status=DiscoveryStatus.ACTIVE,
                tags=config.get("tags", [])
            )
        except KeyError as e:
            logger.error(f"Missing required field in config: {e}")
            return None

    def _discover_from_env(self, source: Dict[str, Any]) -> List[MCPServer]:
        """Discover servers from environment variable"""
        servers = []
        env_var = source.get("variable")

        if not env_var:
            return servers

        servers_path = os.getenv(env_var)
        if not servers_path:
            logger.debug(f"Environment variable {env_var} not set")
            return servers

        # Parse comma-separated paths
        for path in servers_path.split(":"):
            path = path.strip()
            if os.path.exists(path):
                # Load from this path
                local_source = {"type": "local", "path": path}
                servers.extend(self._discover_from_local(local_source))

        return servers

    def recommend_for_context(
        self,
        context: str,
        max_recommendations: int = 5
    ) -> List[ContextRecommendation]:
        """
        Provide context-sensitive server recommendations.

        Args:
            context: Description of current task or query
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommended servers with relevance scoring
        """
        # Check cache
        cache_key = context.lower().strip()
        if cache_key in self.context_cache:
            cached_time = self.context_cache.get(f"{cache_key}_time")
            if cached_time and (datetime.now() - cached_time) < timedelta(minutes=10):
                return self.context_cache[cache_key][:max_recommendations]

        logger.info(f"Analyzing context: {context[:100]}...")

        # Extract keywords and intent
        keywords = self._extract_keywords(context)
        intent_tags = self._map_intent_to_tags(keywords)

        recommendations = []

        for server in self.discovered_servers.values():
            if server.status != DiscoveryStatus.ACTIVE:
                continue

            # Calculate relevance score
            score, matching_caps, reasoning = self._calculate_relevance(
                server, keywords, intent_tags
            )

            if score > 0.3:  # Relevance threshold
                recommendations.append(ContextRecommendation(
                    server=server,
                    relevance_score=score,
                    matching_capabilities=[cap.name for cap in matching_caps],
                    reasoning=reasoning,
                    suggested_operations=self._suggest_operations(server, context)
                ))

        # Sort by relevance
        recommendations.sort(key=lambda r: r.relevance_score, reverse=True)

        # Cache results
        self.context_cache[cache_key] = recommendations
        self.context_cache[f"{cache_key}_time"] = datetime.now()

        return recommendations[:max_recommendations]

    def _extract_keywords(self, context: str) -> Set[str]:
        """Extract keywords from context"""
        # Simple keyword extraction (could use NLP libraries for better results)
        words = re.findall(r'\b\w+\b', context.lower())
        # Filter common words
        stop_words = {"the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by", "from", "i", "need", "want", "how", "what", "where", "when", "why"}
        return set(word for word in words if word not in stop_words and len(word) > 2)

    def _map_intent_to_tags(self, keywords: Set[str]) -> Set[str]:
        """Map keywords to intent tags"""
        intent_tags = set()

        for intent, patterns in self.context_patterns.items():
            for pattern in patterns:
                if pattern in keywords:
                    intent_tags.add(intent)

        return intent_tags

    def _calculate_relevance(
        self,
        server: MCPServer,
        keywords: Set[str],
        intent_tags: Set[str]
    ) -> tuple[float, List[MCPCapability], str]:
        """
        Calculate relevance score for a server given context.

        Returns:
            (score, matching_capabilities, reasoning)
        """
        score = 0.0
        matching_capabilities = []
        reasoning_parts = []

        # Check server tags
        server_tag_matches = len(set(server.tags) & (keywords | intent_tags))
        if server_tag_matches > 0:
            tag_score = min(server_tag_matches * 0.2, 0.6)
            score += tag_score
            reasoning_parts.append(f"Server tags match ({server_tag_matches} matches)")

        # Check capability tags
        for capability in server.capabilities:
            cap_tag_matches = len(set(capability.tags) & (keywords | intent_tags))
            if cap_tag_matches > 0:
                cap_score = min(cap_tag_matches * 0.15, 0.4)
                score += cap_score
                matching_capabilities.append(capability)
                reasoning_parts.append(f"Capability '{capability.name}' matches")

        # Check description
        desc_lower = (server.description + " " + server.name).lower()
        desc_matches = sum(1 for kw in keywords if kw in desc_lower)
        if desc_matches > 0:
            desc_score = min(desc_matches * 0.1, 0.3)
            score += desc_score
            reasoning_parts.append(f"Description contains relevant keywords")

        # Normalize score
        score = min(score, 1.0)

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Low relevance"

        return score, matching_capabilities, reasoning

    def _suggest_operations(self, server: MCPServer, context: str) -> List[str]:
        """Suggest specific operations based on context"""
        suggestions = []

        # Simple heuristic: suggest capabilities with highest tag overlap
        keywords = self._extract_keywords(context)

        for capability in server.capabilities:
            cap_tags = set(capability.tags)
            overlap = len(cap_tags & keywords)
            if overlap > 0:
                suggestions.append(capability.name)

        return suggestions[:3]  # Top 3 suggestions

    def update_connector_catalog(self) -> int:
        """
        Update universal connector catalog with discovered MCP servers.

        Converts MCP servers to ConnectorSpecifications and adds them to
        the universal connector.

        Returns:
            Number of servers added to catalog
        """
        if not CONNECTOR_AVAILABLE:
            logger.error("universal_connector not available, cannot update catalog")
            return 0

        added_count = 0

        for server in self.discovered_servers.values():
            if server.status != DiscoveryStatus.ACTIVE:
                continue

            try:
                # Convert MCP server to connector specification
                connector_spec = self._mcp_to_connector_spec(server)

                # Add to universal connector catalog
                universal_connector.connector_specs[server.id] = connector_spec
                added_count += 1

                logger.info(f"Added {server.name} to connector catalog")

            except Exception as e:
                logger.error(f"Error converting {server.name}: {e}")

        logger.info(f"Updated connector catalog: {added_count} servers added")
        return added_count

    def _mcp_to_connector_spec(self, server: MCPServer) -> 'ConnectorSpecification':
        """Convert MCP server to ConnectorSpecification"""
        # Map MCP authentication to connector authentication
        auth_mapping = {
            "none": AuthenticationType.NONE,
            "api_key": AuthenticationType.API_KEY,
            "oauth": AuthenticationType.OAUTH,
            "basic": AuthenticationType.BASIC
        }

        auth_type = auth_mapping.get(
            server.authentication.get("type", "none"),
            AuthenticationType.CUSTOM
        )

        # Map server type to connector type
        type_mapping = {
            MCPServerType.DATA_SOURCE: ConnectorType.DATABASE,
            MCPServerType.TOOL_PROVIDER: ConnectorType.API,
            MCPServerType.RESOURCE_PROVIDER: ConnectorType.DOCUMENT,
            MCPServerType.MIXED: ConnectorType.API
        }

        connector_type = type_mapping.get(server.server_type, ConnectorType.API)

        # Build endpoints from capabilities
        endpoints = {}
        for capability in server.capabilities:
            endpoints[capability.name] = f"/{capability.name}"

        # Extract parameters from capabilities
        parameters = {}
        for capability in server.capabilities:
            if capability.input_schema:
                props = capability.input_schema.get("properties", {})
                parameters.update({k: v.get("type", "string") for k, v in props.items()})

        return ConnectorSpecification(
            name=server.id,
            description=server.description,
            connector_type=connector_type,
            base_url=server.url,
            authentication=auth_type,
            endpoints=endpoints,
            parameters=parameters,
            rate_limits={"requests_per_minute": 60, "requests_per_hour": 1000},
            capabilities=[cap.name for cap in server.capabilities]
        )

    def start_background_discovery(self, interval_hours: int = 24):
        """
        Start background thread for periodic server discovery.

        Args:
            interval_hours: Hours between discovery runs
        """
        if self.running:
            logger.warning("Background discovery already running")
            return

        self.running = True

        def discovery_loop():
            while self.running:
                try:
                    logger.info("Starting background discovery...")
                    self.discover_servers(force_refresh=True)
                    self.update_connector_catalog()
                except Exception as e:
                    logger.error(f"Error in background discovery: {e}")

                # Sleep for interval
                sleep_seconds = interval_hours * 3600
                for _ in range(int(sleep_seconds)):
                    if not self.running:
                        break
                    time.sleep(1)

        self.discovery_thread = threading.Thread(target=discovery_loop, daemon=True)
        self.discovery_thread.start()
        logger.info(f"Background discovery started (interval: {interval_hours}h)")

    def stop_background_discovery(self):
        """Stop background discovery thread"""
        if not self.running:
            return

        logger.info("Stopping background discovery...")
        self.running = False

        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=10)
            if self.discovery_thread.is_alive():
                logger.warning("Discovery thread did not stop within timeout")

        logger.info("Background discovery stopped")

    def get_discovery_status(self) -> Dict[str, Any]:
        """Get current discovery status"""
        return {
            "total_servers": len(self.discovered_servers),
            "active_servers": len([s for s in self.discovered_servers.values() if s.status == DiscoveryStatus.ACTIVE]),
            "last_discovery": self.last_discovery.isoformat() if self.last_discovery else None,
            "background_running": self.running,
            "servers_by_type": self._count_by_type(),
            "discovery_sources": [
                {"name": s["name"], "enabled": s["enabled"]}
                for s in self.discovery_sources
            ]
        }

    def _count_by_type(self) -> Dict[str, int]:
        """Count servers by type"""
        counts = {}
        for server in self.discovered_servers.values():
            type_name = server.server_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts


# Global instance
mcp_agent = MCPDiscoveryAgent()


# Convenience functions
def discover_and_recommend(context: str) -> List[ContextRecommendation]:
    """
    One-shot function: discover servers and get recommendations for context.

    Args:
        context: Description of current task

    Returns:
        Context-sensitive recommendations
    """
    mcp_agent.discover_servers()
    return mcp_agent.recommend_for_context(context)


def auto_discover_and_update(interval_hours: int = 24):
    """
    Start automatic discovery and catalog updates.

    Args:
        interval_hours: Hours between discovery runs
    """
    mcp_agent.start_background_discovery(interval_hours)
    # Do initial discovery and update
    mcp_agent.discover_servers()
    mcp_agent.update_connector_catalog()
