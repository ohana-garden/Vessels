"""
MCP Explorer: Proactive agent for discovering and understanding MCP servers.

The MCP Explorer continuously:
- Discovers new MCP servers from known sources
- Builds semantic understanding of what each server provides
- Tests connectivity and monitors health
- Matches vessel capability needs to available servers
- Anticipates what vessels might need

This is a system-level agent (not vessel-scoped) that serves all of Vessels.
"""

import asyncio
import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TrustLevel(str, Enum):
    """Trust level for MCP servers."""
    VERIFIED = "verified"      # Officially verified, high trust
    COMMUNITY = "community"    # Community-vetted, moderate trust
    UNKNOWN = "unknown"        # Not yet evaluated
    UNTRUSTED = "untrusted"    # Known issues or suspicious


class CostModel(str, Enum):
    """Cost model for MCP server usage."""
    FREE = "free"
    FREE_TIER = "free_tier"    # Free up to limits
    PER_CALL = "per_call"
    SUBSCRIPTION = "subscription"
    UNKNOWN = "unknown"


class ServerStatus(str, Enum):
    """Current status of an MCP server."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class MCPServerInfo:
    """Information about an MCP server."""
    server_id: str
    name: str
    description: str
    endpoint: str

    # What it provides (semantic understanding)
    capabilities: List[str]           # High-level: ["weather", "forecasting", "climate"]
    tools_provided: List[str]         # Actual tool names: ["get_forecast", "get_current"]
    problems_it_solves: List[str]     # "need weather data", "forecast planning"
    domains: List[str]                # "agriculture", "planning", "outdoor activities"

    # Trust and reliability
    trust_level: TrustLevel = TrustLevel.UNKNOWN
    status: ServerStatus = ServerStatus.UNKNOWN
    reliability_score: float = 0.0    # 0-1 based on uptime history
    avg_latency_ms: float = 0.0

    # Cost
    cost_model: CostModel = CostModel.UNKNOWN
    cost_details: Optional[str] = None

    # Auth
    auth_required: bool = False
    auth_type: Optional[str] = None   # "api_key", "oauth", etc.

    # Discovery metadata
    source: str = ""                  # Where we found it: "npm", "github", "manual"
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    last_successful_call: Optional[datetime] = None

    # Rich understanding (built over time)
    usage_notes: str = ""             # "Best for US weather, slow for historical"
    recommended_for: List[str] = field(default_factory=list)  # Vessel types
    not_recommended_for: List[str] = field(default_factory=list)

    def matches_need(self, need: str) -> float:
        """
        Score how well this server matches a capability need.
        Returns 0-1 confidence score.
        """
        need_lower = need.lower()
        score = 0.0

        # Check capabilities
        for cap in self.capabilities:
            if cap.lower() in need_lower or need_lower in cap.lower():
                score += 0.3

        # Check problems it solves
        for problem in self.problems_it_solves:
            if any(word in need_lower for word in problem.lower().split()):
                score += 0.4

        # Check domains
        for domain in self.domains:
            if domain.lower() in need_lower:
                score += 0.2

        # Adjust by reliability
        score *= (0.5 + 0.5 * self.reliability_score)

        return min(score, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "tools_provided": self.tools_provided,
            "problems_it_solves": self.problems_it_solves,
            "domains": self.domains,
            "trust_level": self.trust_level.value,
            "status": self.status.value,
            "reliability_score": self.reliability_score,
            "avg_latency_ms": self.avg_latency_ms,
            "cost_model": self.cost_model.value,
            "cost_details": self.cost_details,
            "auth_required": self.auth_required,
            "auth_type": self.auth_type,
            "source": self.source,
            "discovered_at": self.discovered_at.isoformat(),
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
            "usage_notes": self.usage_notes,
            "recommended_for": self.recommended_for,
        }


@dataclass
class MCPConnection:
    """Active connection from a vessel to an MCP server."""
    connection_id: str
    vessel_id: str
    server_id: str
    connected_at: datetime
    tools_provisioned: List[str]
    status: str = "active"
    call_count: int = 0
    last_call: Optional[datetime] = None


# Prompt for understanding what an MCP server provides
UNDERSTAND_MCP_PROMPT = """Analyze this MCP server and describe what it provides.

Server name: {name}
Description: {description}
Tools available: {tools}

Respond with JSON:
{{
  "capabilities": ["high-level capabilities like 'weather', 'email', 'calendar'"],
  "problems_it_solves": ["natural language problems like 'need to check weather', 'send notifications'"],
  "domains": ["relevant domains like 'agriculture', 'business', 'personal'],
  "recommended_for": ["types of vessels/use cases it's good for"],
  "usage_notes": "any important notes about using this server"
}}

JSON response:"""


# Prompt for matching capability needs to servers
MATCH_CAPABILITY_PROMPT = """A vessel needs this capability: "{need}"

Available MCP servers:
{servers_summary}

Which server(s) best match this need? Consider:
- How well capabilities match the need
- Reliability and trust level
- Cost (prefer free when quality is similar)

Respond with JSON:
{{
  "recommended_server_id": "best match server_id",
  "confidence": 0.0-1.0,
  "reasoning": "why this is the best match",
  "alternatives": ["other server_ids that could work"]
}}

JSON response:"""


class MCPExplorer:
    """
    Proactive agent for discovering and understanding MCP servers.

    Runs as a background process, continuously:
    - Discovering new MCP servers
    - Building understanding of capabilities
    - Monitoring health and reliability
    - Ready to match vessel needs instantly
    """

    # Known sources for MCP server discovery
    DISCOVERY_SOURCES = [
        {"type": "registry", "url": "https://mcp.registry.example/servers"},  # Hypothetical
        {"type": "npm", "search": "@mcp/ mcp-server"},
        {"type": "github", "topics": ["mcp-server", "model-context-protocol"]},
    ]

    def __init__(
        self,
        llm_call: Optional[Callable[[str], str]] = None,
        memory_backend: Optional[Any] = None,
    ):
        """
        Initialize MCP Explorer.

        Args:
            llm_call: Function to call LLM for semantic understanding
            memory_backend: For persisting discovered servers
        """
        self.llm_call = llm_call
        self.memory_backend = memory_backend

        # Server catalog
        self.servers: Dict[str, MCPServerInfo] = {}

        # Active connections (vessel_id -> server_id -> connection)
        self.connections: Dict[str, Dict[str, MCPConnection]] = {}

        # Vessel interests - for ongoing notifications when new MCPs emerge
        # vessel_id -> {type, domains, keywords} for matching new discoveries
        self.vessel_interests: Dict[str, Dict[str, Any]] = {}

        # Pending notifications - new capabilities relevant to specific vessels
        # vessel_id -> [list of new capability notifications]
        self.pending_notifications: Dict[str, List[Dict[str, Any]]] = {}

        # Background exploration
        self.running = False
        self.exploration_thread: Optional[threading.Thread] = None
        self.exploration_interval = 3600  # Check for new servers every hour

        # Health monitoring
        self.health_check_interval = 300  # Check health every 5 minutes
        self.last_health_check: Optional[datetime] = None

        # Seed with some well-known MCP servers
        self._seed_known_servers()

    def _seed_known_servers(self):
        """Seed the catalog with well-known MCP servers that EXTEND vessel capabilities.

        Note: We don't include servers that replace our tech stack (postgres, storage, etc.)
        Only servers that give vessels new capabilities they couldn't have otherwise.
        """
        known_servers = [
            # Weather - critical for garden/agriculture vessels
            MCPServerInfo(
                server_id="weather-mcp",
                name="Weather MCP",
                description="Weather forecasts, current conditions, and climate data",
                endpoint="npx @mcp/weather",
                capabilities=["weather", "forecasting", "climate", "temperature", "precipitation"],
                tools_provided=["get_forecast", "get_current_weather", "get_historical", "get_alerts"],
                problems_it_solves=["need weather data", "forecast planning", "climate information", "weather alerts"],
                domains=["agriculture", "gardening", "outdoor_activities", "planning", "events"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE_TIER,
                recommended_for=["garden", "farm", "outdoor", "events"],
                source="community",
            ),
            # Maps/Geocoding - location awareness for community vessels
            MCPServerInfo(
                server_id="maps-mcp",
                name="Maps & Geocoding MCP",
                description="Location services, geocoding, directions, and place information",
                endpoint="npx @mcp/maps",
                capabilities=["maps", "geocoding", "directions", "places", "location"],
                tools_provided=["geocode", "reverse_geocode", "get_directions", "search_places", "get_distance"],
                problems_it_solves=["need location data", "find places", "get directions", "distance calculation"],
                domains=["community", "logistics", "local_services", "navigation"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE_TIER,
                recommended_for=["community", "local", "logistics", "delivery"],
                source="community",
            ),
            # Calendar/Scheduling - coordination for any vessel
            MCPServerInfo(
                server_id="calendar-mcp",
                name="Calendar MCP",
                description="Calendar integration for scheduling, events, and availability",
                endpoint="npx @mcp/google-calendar",
                capabilities=["calendar", "scheduling", "events", "availability", "reminders"],
                tools_provided=["list_events", "create_event", "check_availability", "set_reminder"],
                problems_it_solves=["need to schedule", "check calendar", "coordinate timing", "event management"],
                domains=["coordination", "scheduling", "community", "business"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE,
                auth_required=True,
                auth_type="oauth",
                recommended_for=["coordinator", "community", "business", "project"],
                source="official",
            ),
            # Email/Communication - outreach for any vessel
            MCPServerInfo(
                server_id="email-mcp",
                name="Email MCP",
                description="Send and manage email communications",
                endpoint="npx @mcp/email",
                capabilities=["email", "communication", "notifications", "outreach"],
                tools_provided=["send_email", "list_emails", "search_emails", "create_draft"],
                problems_it_solves=["need to send email", "email notifications", "communication", "outreach"],
                domains=["communication", "business", "community", "coordination"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE,
                auth_required=True,
                auth_type="oauth",
                recommended_for=["business", "community", "coordinator"],
                source="official",
            ),
            # Web fetch - research capability for any vessel
            MCPServerInfo(
                server_id="fetch-mcp",
                name="Web Fetch MCP",
                description="Fetch and parse web content for research and monitoring",
                endpoint="npx @anthropics/mcp-server-fetch",
                capabilities=["http", "web_requests", "web_scraping", "research", "monitoring"],
                tools_provided=["fetch", "fetch_and_parse", "check_url"],
                problems_it_solves=["need web data", "research", "monitor websites", "fetch content"],
                domains=["research", "monitoring", "general"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE,
                recommended_for=["research", "monitoring", "general"],
                source="official",
            ),
            # SMS/Messaging - direct communication for urgent matters
            MCPServerInfo(
                server_id="sms-mcp",
                name="SMS MCP",
                description="Send SMS messages for alerts and direct communication",
                endpoint="npx @mcp/twilio-sms",
                capabilities=["sms", "messaging", "alerts", "notifications"],
                tools_provided=["send_sms", "check_status"],
                problems_it_solves=["need to text", "send alerts", "urgent notification", "direct contact"],
                domains=["communication", "alerts", "elder_care", "emergency"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.PER_CALL,
                cost_details="~$0.01 per SMS",
                auth_required=True,
                auth_type="api_key",
                recommended_for=["elder_care", "emergency", "coordinator", "alerts"],
                source="community",
            ),
            # Translation - accessibility for diverse communities
            MCPServerInfo(
                server_id="translate-mcp",
                name="Translation MCP",
                description="Language translation for multilingual communication",
                endpoint="npx @mcp/translate",
                capabilities=["translation", "language", "multilingual", "localization"],
                tools_provided=["translate", "detect_language", "list_languages"],
                problems_it_solves=["need translation", "multilingual support", "language barrier"],
                domains=["communication", "accessibility", "community", "international"],
                trust_level=TrustLevel.VERIFIED,
                cost_model=CostModel.FREE_TIER,
                recommended_for=["community", "international", "accessibility"],
                source="community",
            ),
        ]

        for server in known_servers:
            self.servers[server.server_id] = server

        logger.info(f"MCP Explorer seeded with {len(known_servers)} capability-extending servers")

    def start(self):
        """Start the background exploration process."""
        if self.running:
            return

        self.running = True
        self.exploration_thread = threading.Thread(target=self._exploration_loop, daemon=True)
        self.exploration_thread.start()
        logger.info("MCP Explorer started")

    def stop(self):
        """Stop the background exploration process."""
        self.running = False
        if self.exploration_thread:
            self.exploration_thread.join(timeout=5)
        logger.info("MCP Explorer stopped")

    def _exploration_loop(self):
        """Background loop for continuous exploration."""
        while self.running:
            try:
                # Discover new servers
                self._discover_servers()

                # Health check existing servers
                if self._should_health_check():
                    self._check_server_health()

            except Exception as e:
                logger.error(f"Exploration loop error: {e}")

            # Sleep between exploration cycles
            time.sleep(self.exploration_interval)

    def _should_health_check(self) -> bool:
        """Check if it's time for a health check."""
        if not self.last_health_check:
            return True
        return (datetime.utcnow() - self.last_health_check).seconds > self.health_check_interval

    def _discover_servers(self):
        """Discover new MCP servers from known sources."""
        # In production, this would crawl npm, github, registries
        logger.debug("MCP Explorer: scanning for new servers...")

        # This is where we'd implement actual discovery:
        # - Query npm for packages matching @mcp/ or mcp-server
        # - Search GitHub for repos with mcp-server topic
        # - Check community registries

        # Placeholder for actual discovery implementation
        discovered = self._fetch_from_sources()

        for server_info in discovered:
            if server_info.server_id not in self.servers:
                # New server! Understand it and add to catalog
                server = self._understand_server(server_info)
                self.servers[server.server_id] = server

                logger.info(f"Discovered new MCP server: {server.name}")

                # Notify interested vessels about this new capability
                self._notify_vessels_of_new_server(server)

    def _fetch_from_sources(self) -> List[MCPServerInfo]:
        """
        Fetch MCP servers from discovery sources.

        In production, this would:
        - Query npm registry for @mcp/* packages
        - Search GitHub for mcp-server topics
        - Check community MCP registries

        Returns:
            List of newly discovered servers (not yet in catalog)
        """
        # Placeholder - in production this would actually fetch
        # For now, returns empty list (seeded servers are added in __init__)
        return []

    def add_discovered_server(self, server: MCPServerInfo) -> bool:
        """
        Add a newly discovered server to the catalog and notify interested vessels.

        Called externally when a new MCP server is found (e.g., by community,
        user request, or automated discovery).

        Args:
            server: The server to add

        Returns:
            True if added (new), False if already exists
        """
        if server.server_id in self.servers:
            return False

        # Understand it if we have LLM
        server = self._understand_server(server)
        self.servers[server.server_id] = server

        logger.info(f"Added new MCP server: {server.name}")

        # Notify all interested vessels
        notified = self._notify_vessels_of_new_server(server)
        if notified > 0:
            logger.info(f"Notified {notified} vessels about new server '{server.name}'")

        return True

    def _check_server_health(self):
        """Check health of all known servers."""
        self.last_health_check = datetime.utcnow()

        for server_id, server in self.servers.items():
            try:
                # In production: actually ping the server
                # For now, just mark as checked
                server.last_checked = datetime.utcnow()

                # Simulate health check result
                # In reality: measure latency, check if tools respond
                server.status = ServerStatus.ONLINE
                server.reliability_score = min(1.0, server.reliability_score + 0.01)

            except Exception as e:
                logger.warning(f"Health check failed for {server_id}: {e}")
                server.status = ServerStatus.OFFLINE
                server.reliability_score = max(0.0, server.reliability_score - 0.1)

        logger.debug(f"Health checked {len(self.servers)} MCP servers")

    def _understand_server(self, server: MCPServerInfo) -> MCPServerInfo:
        """Use LLM to build semantic understanding of what a server provides."""
        if not self.llm_call:
            return server

        try:
            prompt = UNDERSTAND_MCP_PROMPT.format(
                name=server.name,
                description=server.description,
                tools=", ".join(server.tools_provided) if server.tools_provided else "unknown"
            )

            response = self.llm_call(prompt)
            result = self._parse_json(response)

            if result:
                server.capabilities = result.get("capabilities", server.capabilities)
                server.problems_it_solves = result.get("problems_it_solves", [])
                server.domains = result.get("domains", [])
                server.recommended_for = result.get("recommended_for", [])
                server.usage_notes = result.get("usage_notes", "")

        except Exception as e:
            logger.error(f"Error understanding server {server.name}: {e}")

        return server

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        import re

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    # =========================================================================
    # PUBLIC API - Called by A0 and vessels
    # =========================================================================

    def find_servers_for_need(
        self,
        capability_need: str,
        vessel_type: Optional[str] = None,
        trust_minimum: TrustLevel = TrustLevel.UNKNOWN,
        prefer_free: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Find MCP servers that can fulfill a capability need.

        Args:
            capability_need: Natural language description of what's needed
            vessel_type: Optional vessel type for better matching
            trust_minimum: Minimum trust level required
            prefer_free: Prefer free servers when quality is similar

        Returns:
            List of matching servers with scores, sorted by relevance
        """
        matches = []

        for server in self.servers.values():
            # Filter by trust level
            trust_order = [TrustLevel.UNTRUSTED, TrustLevel.UNKNOWN,
                          TrustLevel.COMMUNITY, TrustLevel.VERIFIED]
            if trust_order.index(server.trust_level) < trust_order.index(trust_minimum):
                continue

            # Score the match
            score = server.matches_need(capability_need)

            # Boost if recommended for this vessel type
            if vessel_type and vessel_type.lower() in [r.lower() for r in server.recommended_for]:
                score *= 1.2

            # Slight preference for free
            if prefer_free and server.cost_model == CostModel.FREE:
                score *= 1.1

            if score > 0.1:  # Minimum threshold
                matches.append({
                    "server": server.to_dict(),
                    "score": min(score, 1.0),
                    "server_id": server.server_id,
                })

        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)

        return matches[:5]  # Top 5 matches

    def get_recommendation(
        self,
        capability_need: str,
        vessel_id: Optional[str] = None,
        vessel_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a single recommended MCP server for a capability need.

        Uses LLM for sophisticated matching when available.

        Args:
            capability_need: What the vessel needs
            vessel_id: Optional vessel ID for context
            vessel_type: Optional vessel type

        Returns:
            Recommendation with server_id, confidence, and reasoning
        """
        matches = self.find_servers_for_need(capability_need, vessel_type)

        if not matches:
            return {
                "recommended_server_id": None,
                "confidence": 0.0,
                "reasoning": "No matching MCP servers found for this capability",
                "alternatives": []
            }

        # If we have LLM, use it for sophisticated matching
        if self.llm_call and len(matches) > 1:
            try:
                servers_summary = "\n".join([
                    f"- {m['server']['name']} ({m['server_id']}): {m['server']['description']} "
                    f"[trust: {m['server']['trust_level']}, cost: {m['server']['cost_model']}]"
                    for m in matches
                ])

                prompt = MATCH_CAPABILITY_PROMPT.format(
                    need=capability_need,
                    servers_summary=servers_summary
                )

                response = self.llm_call(prompt)
                result = self._parse_json(response)

                if result and result.get("recommended_server_id"):
                    return result

            except Exception as e:
                logger.error(f"LLM matching error: {e}")

        # Fallback: return top match
        top = matches[0]
        return {
            "recommended_server_id": top["server_id"],
            "confidence": top["score"],
            "reasoning": f"Best match based on capability alignment ({top['score']:.2f})",
            "alternatives": [m["server_id"] for m in matches[1:3]]
        }

    def connect_vessel_to_server(
        self,
        vessel_id: str,
        server_id: str,
    ) -> MCPConnection:
        """
        Connect a vessel to an MCP server.

        Args:
            vessel_id: Vessel to connect
            server_id: MCP server to connect to

        Returns:
            MCPConnection object
        """
        if server_id not in self.servers:
            raise ValueError(f"Unknown MCP server: {server_id}")

        server = self.servers[server_id]

        # Create connection
        connection = MCPConnection(
            connection_id=str(uuid.uuid4()),
            vessel_id=vessel_id,
            server_id=server_id,
            connected_at=datetime.utcnow(),
            tools_provisioned=server.tools_provided.copy(),
        )

        # Track connection
        if vessel_id not in self.connections:
            self.connections[vessel_id] = {}
        self.connections[vessel_id][server_id] = connection

        logger.info(f"Connected vessel {vessel_id} to MCP server {server_id}")

        return connection

    def disconnect_vessel_from_server(self, vessel_id: str, server_id: str) -> bool:
        """Disconnect a vessel from an MCP server."""
        if vessel_id in self.connections and server_id in self.connections[vessel_id]:
            del self.connections[vessel_id][server_id]
            logger.info(f"Disconnected vessel {vessel_id} from MCP server {server_id}")
            return True
        return False

    def get_vessel_connections(self, vessel_id: str) -> List[MCPConnection]:
        """Get all MCP connections for a vessel."""
        if vessel_id in self.connections:
            return list(self.connections[vessel_id].values())
        return []

    def get_vessel_tools(self, vessel_id: str) -> List[str]:
        """Get all tools available to a vessel from MCP connections."""
        tools = []
        for connection in self.get_vessel_connections(vessel_id):
            tools.extend(connection.tools_provisioned)
        return tools

    def register_server(self, server: MCPServerInfo) -> None:
        """Manually register an MCP server."""
        self.servers[server.server_id] = server
        logger.info(f"Registered MCP server: {server.name} ({server.server_id})")

    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        """Get info about a specific server."""
        return self.servers.get(server_id)

    def list_servers(
        self,
        capability_filter: Optional[str] = None,
        trust_filter: Optional[TrustLevel] = None,
    ) -> List[MCPServerInfo]:
        """List all known servers with optional filtering."""
        servers = list(self.servers.values())

        if capability_filter:
            servers = [s for s in servers if s.matches_need(capability_filter) > 0.1]

        if trust_filter:
            trust_order = [TrustLevel.UNTRUSTED, TrustLevel.UNKNOWN,
                          TrustLevel.COMMUNITY, TrustLevel.VERIFIED]
            min_idx = trust_order.index(trust_filter)
            servers = [s for s in servers if trust_order.index(s.trust_level) >= min_idx]

        return servers

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the MCP ecosystem."""
        return {
            "total_servers": len(self.servers),
            "servers_by_trust": {
                level.value: len([s for s in self.servers.values() if s.trust_level == level])
                for level in TrustLevel
            },
            "servers_by_status": {
                status.value: len([s for s in self.servers.values() if s.status == status])
                for status in ServerStatus
            },
            "total_connections": sum(len(c) for c in self.connections.values()),
            "vessels_connected": len(self.connections),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
        }

    # =========================================================================
    # PROACTIVE CAPABILITY AWARENESS
    # Vessels don't know what they don't know - we inform them of options
    # =========================================================================

    def recommend_capabilities_for_vessel(
        self,
        vessel_id: str,
        vessel_type: str,
        vessel_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Proactively recommend capabilities for a newly born vessel.

        Vessels don't know what's available to them. When a vessel is born,
        we analyze its type/domain and recommend relevant MCP servers
        it might want to use.

        Args:
            vessel_id: The vessel's ID
            vessel_type: What the vessel is for (garden, community, business, etc.)
            vessel_domains: Optional additional domains of interest

        Returns:
            Dict with categorized recommendations
        """
        vessel_type_lower = vessel_type.lower() if vessel_type else ""
        domains = [d.lower() for d in (vessel_domains or [])]

        # Categorize recommendations
        essential = []      # Highly recommended for this vessel type
        useful = []         # Might be useful
        available = []      # Available if needed

        for server in self.servers.values():
            # Check if this server is recommended for this vessel type
            recommended_for = [r.lower() for r in server.recommended_for]
            server_domains = [d.lower() for d in server.domains]

            # Score relevance
            relevance = 0

            # Direct vessel type match
            if vessel_type_lower in recommended_for:
                relevance += 3

            # Partial vessel type match
            for rec in recommended_for:
                if rec in vessel_type_lower or vessel_type_lower in rec:
                    relevance += 2

            # Domain match
            for domain in domains:
                if domain in server_domains:
                    relevance += 1

            # Check server capabilities against vessel type keywords
            vessel_keywords = self._extract_keywords(vessel_type_lower)
            for cap in server.capabilities:
                if any(kw in cap.lower() for kw in vessel_keywords):
                    relevance += 1

            if relevance >= 3:
                essential.append(self._format_recommendation(server, relevance))
            elif relevance >= 1:
                useful.append(self._format_recommendation(server, relevance))
            elif server.trust_level == TrustLevel.VERIFIED:
                available.append(self._format_recommendation(server, 0))

        # Sort by relevance
        essential.sort(key=lambda x: x["relevance"], reverse=True)
        useful.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "vessel_id": vessel_id,
            "vessel_type": vessel_type,
            "recommendations": {
                "essential": essential[:5],   # Top 5 highly recommended
                "useful": useful[:5],         # Top 5 potentially useful
                "available": available[:10],  # Up to 10 others available
            },
            "message": self._generate_recommendation_message(vessel_type, essential, useful),
        }

    def _extract_keywords(self, vessel_type: str) -> List[str]:
        """Extract relevant keywords from vessel type for matching."""
        # Common mappings
        keyword_map = {
            "garden": ["weather", "climate", "plants", "soil", "water", "irrigation"],
            "farm": ["weather", "climate", "agriculture", "crops", "irrigation", "soil"],
            "community": ["communication", "scheduling", "coordination", "local", "events"],
            "business": ["email", "calendar", "scheduling", "communication", "crm"],
            "elder": ["sms", "alerts", "emergency", "communication", "scheduling"],
            "care": ["sms", "alerts", "scheduling", "communication", "reminders"],
            "coordinator": ["calendar", "scheduling", "email", "communication"],
            "project": ["calendar", "scheduling", "communication", "coordination"],
        }

        keywords = []
        for key, words in keyword_map.items():
            if key in vessel_type:
                keywords.extend(words)

        return list(set(keywords))

    def _format_recommendation(self, server: MCPServerInfo, relevance: int) -> Dict[str, Any]:
        """Format a server as a recommendation."""
        return {
            "server_id": server.server_id,
            "name": server.name,
            "description": server.description,
            "capabilities": server.capabilities[:3],  # Top 3 capabilities
            "tools": server.tools_provided,
            "why": server.problems_it_solves[:2],     # Top 2 problems it solves
            "cost": server.cost_model.value,
            "auth_required": server.auth_required,
            "relevance": relevance,
        }

    def _generate_recommendation_message(
        self,
        vessel_type: str,
        essential: List[Dict],
        useful: List[Dict],
    ) -> str:
        """Generate a human-readable recommendation message."""
        if not essential and not useful:
            return f"I'm a {vessel_type} vessel. I can explore available capabilities as needs arise."

        parts = [f"As a {vessel_type} vessel, here are capabilities that might help me:"]

        if essential:
            parts.append("\n**Recommended:**")
            for rec in essential[:3]:
                parts.append(f"- {rec['name']}: {rec['description']}")

        if useful:
            parts.append("\n**Also available:**")
            for rec in useful[:3]:
                parts.append(f"- {rec['name']}: {rec['why'][0] if rec['why'] else rec['description']}")

        parts.append("\nWould you like me to connect to any of these?")

        return "\n".join(parts)

    def get_capability_options(self, vessel_id: str) -> Dict[str, Any]:
        """
        Let a vessel ask "what can I do?" - returns all available capabilities.

        Called when vessel or user wants to know what's possible.
        """
        connected = self.get_vessel_connections(vessel_id)
        connected_ids = {c.server_id for c in connected}

        connected_caps = []
        available_caps = []

        for server in self.servers.values():
            info = {
                "server_id": server.server_id,
                "name": server.name,
                "description": server.description,
                "tools": server.tools_provided,
                "cost": server.cost_model.value,
            }

            if server.server_id in connected_ids:
                connected_caps.append(info)
            else:
                available_caps.append(info)

        return {
            "vessel_id": vessel_id,
            "currently_connected": connected_caps,
            "available_to_add": available_caps,
            "message": f"You have {len(connected_caps)} capabilities connected. "
                       f"{len(available_caps)} more are available to add."
        }

    # =========================================================================
    # ONGOING NOTIFICATION SYSTEM
    # As new MCP servers emerge, vessels need to be informed of relevant ones
    # =========================================================================

    def register_vessel_interest(
        self,
        vessel_id: str,
        vessel_type: str,
        domains: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
    ) -> None:
        """
        Register a vessel's interests for ongoing capability notifications.

        Called when a vessel is born - tracks what types of MCP servers
        would be relevant so we can notify when new ones are discovered.

        Args:
            vessel_id: The vessel's ID
            vessel_type: What kind of vessel (garden, community, etc.)
            domains: Domains of interest (agriculture, communication, etc.)
            keywords: Specific capability keywords to watch for
        """
        # Build interest profile
        interest = {
            "vessel_type": vessel_type.lower() if vessel_type else "",
            "domains": [d.lower() for d in (domains or [])],
            "keywords": [k.lower() for k in (keywords or [])],
            "registered_at": datetime.utcnow().isoformat(),
            # Track which servers vessel already knows about (to avoid re-notifying)
            "known_servers": set(self.servers.keys()),
        }

        # Add auto-generated keywords based on vessel type
        interest["keywords"].extend(self._extract_keywords(interest["vessel_type"]))
        interest["keywords"] = list(set(interest["keywords"]))  # Dedupe

        self.vessel_interests[vessel_id] = interest

        # Initialize empty notification queue
        if vessel_id not in self.pending_notifications:
            self.pending_notifications[vessel_id] = []

        logger.info(
            f"Registered vessel {vessel_id} ({vessel_type}) for ongoing "
            f"capability notifications. Watching: {interest['keywords'][:5]}..."
        )

    def unregister_vessel_interest(self, vessel_id: str) -> bool:
        """Unregister a vessel from notifications (e.g., when vessel is archived)."""
        removed = False
        if vessel_id in self.vessel_interests:
            del self.vessel_interests[vessel_id]
            removed = True
        if vessel_id in self.pending_notifications:
            del self.pending_notifications[vessel_id]
        if removed:
            logger.info(f"Unregistered vessel {vessel_id} from capability notifications")
        return removed

    def _notify_vessels_of_new_server(self, server: MCPServerInfo) -> int:
        """
        Check if any registered vessels would be interested in a newly discovered server.

        Called when a new MCP server is discovered. Checks against all registered
        vessel interests and queues notifications for relevant vessels.

        Args:
            server: The newly discovered server

        Returns:
            Number of vessels notified
        """
        notified_count = 0

        for vessel_id, interest in self.vessel_interests.items():
            # Skip if vessel already knows about this server
            if server.server_id in interest.get("known_servers", set()):
                continue

            # Calculate relevance score
            relevance = self._calculate_server_relevance(server, interest)

            if relevance >= 2:  # Threshold for notification
                notification = {
                    "type": "new_capability",
                    "server_id": server.server_id,
                    "server_name": server.name,
                    "description": server.description,
                    "capabilities": server.capabilities[:3],
                    "why_relevant": self._explain_relevance(server, interest),
                    "relevance_score": relevance,
                    "discovered_at": datetime.utcnow().isoformat(),
                    "read": False,
                }

                self.pending_notifications[vessel_id].append(notification)

                # Mark this server as known to avoid re-notifying
                interest.setdefault("known_servers", set()).add(server.server_id)

                notified_count += 1
                logger.debug(
                    f"Queued notification for vessel {vessel_id}: "
                    f"new MCP server '{server.name}' (relevance: {relevance})"
                )

        if notified_count > 0:
            logger.info(
                f"New MCP server '{server.name}' relevant to {notified_count} vessels"
            )

        return notified_count

    def _calculate_server_relevance(
        self,
        server: MCPServerInfo,
        interest: Dict[str, Any],
    ) -> int:
        """Calculate how relevant a server is to a vessel's interests."""
        relevance = 0
        vessel_type = interest.get("vessel_type", "")
        domains = interest.get("domains", [])
        keywords = interest.get("keywords", [])

        # Check if server is recommended for this vessel type
        recommended_for = [r.lower() for r in server.recommended_for]
        if vessel_type in recommended_for:
            relevance += 3

        # Partial vessel type match
        for rec in recommended_for:
            if rec in vessel_type or vessel_type in rec:
                relevance += 2
                break

        # Domain match
        server_domains = [d.lower() for d in server.domains]
        for domain in domains:
            if domain in server_domains:
                relevance += 1

        # Keyword match against capabilities
        server_caps = [c.lower() for c in server.capabilities]
        for keyword in keywords:
            for cap in server_caps:
                if keyword in cap or cap in keyword:
                    relevance += 1
                    break

        # Keyword match against problems it solves
        for problem in server.problems_it_solves:
            problem_lower = problem.lower()
            for keyword in keywords:
                if keyword in problem_lower:
                    relevance += 1
                    break

        return relevance

    def _explain_relevance(
        self,
        server: MCPServerInfo,
        interest: Dict[str, Any],
    ) -> str:
        """Generate a human-readable explanation of why a server is relevant."""
        reasons = []
        vessel_type = interest.get("vessel_type", "")

        # Check recommendation match
        recommended_for = [r.lower() for r in server.recommended_for]
        if vessel_type in recommended_for:
            reasons.append(f"recommended for {vessel_type} vessels")

        # Check domain match
        domains = interest.get("domains", [])
        server_domains = [d.lower() for d in server.domains]
        matching_domains = [d for d in domains if d in server_domains]
        if matching_domains:
            reasons.append(f"matches your domains: {', '.join(matching_domains[:2])}")

        # Check capability match
        keywords = interest.get("keywords", [])
        server_caps = [c.lower() for c in server.capabilities]
        matching_caps = [k for k in keywords if any(k in c for c in server_caps)]
        if matching_caps:
            reasons.append(f"provides: {', '.join(matching_caps[:2])}")

        if reasons:
            return "This is " + " and ".join(reasons)
        return "May be useful for your work"

    def get_pending_notifications(
        self,
        vessel_id: str,
        mark_as_read: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get pending capability notifications for a vessel.

        Called when a vessel checks for new capabilities or during
        regular vessel activity.

        Args:
            vessel_id: The vessel's ID
            mark_as_read: Whether to mark notifications as read

        Returns:
            List of pending notifications
        """
        if vessel_id not in self.pending_notifications:
            return []

        notifications = self.pending_notifications[vessel_id]

        if mark_as_read:
            for n in notifications:
                n["read"] = True

        # Return unread or recently read notifications
        return [n for n in notifications if not n.get("dismissed", False)]

    def dismiss_notification(
        self,
        vessel_id: str,
        server_id: str,
    ) -> bool:
        """Dismiss a notification (vessel chose not to use this capability)."""
        if vessel_id not in self.pending_notifications:
            return False

        for notification in self.pending_notifications[vessel_id]:
            if notification.get("server_id") == server_id:
                notification["dismissed"] = True
                notification["dismissed_at"] = datetime.utcnow().isoformat()
                return True
        return False

    def clear_notifications(self, vessel_id: str) -> int:
        """Clear all notifications for a vessel."""
        if vessel_id not in self.pending_notifications:
            return 0

        count = len(self.pending_notifications[vessel_id])
        self.pending_notifications[vessel_id] = []
        return count

    def get_notification_summary(self, vessel_id: str) -> Dict[str, Any]:
        """Get a summary of notification status for a vessel."""
        if vessel_id not in self.pending_notifications:
            return {
                "vessel_id": vessel_id,
                "registered": vessel_id in self.vessel_interests,
                "total_notifications": 0,
                "unread": 0,
                "message": "No notifications"
            }

        notifications = self.pending_notifications[vessel_id]
        unread = [n for n in notifications if not n.get("read", False)]
        undismissed = [n for n in notifications if not n.get("dismissed", False)]

        message = ""
        if unread:
            message = f"You have {len(unread)} new capability notification(s)!"
        elif undismissed:
            message = f"{len(undismissed)} capability notification(s) pending review"
        else:
            message = "All caught up! No new capabilities to review."

        return {
            "vessel_id": vessel_id,
            "registered": vessel_id in self.vessel_interests,
            "total_notifications": len(notifications),
            "unread": len(unread),
            "pending_review": len(undismissed),
            "message": message,
        }

    def check_for_new_capabilities(self) -> Dict[str, int]:
        """
        Manually trigger a check for new capabilities against all registered vessels.

        Used by A0 or scheduled tasks to ensure vessels are informed of
        new MCP servers that have been added since they last checked.

        Returns:
            Dict mapping vessel_id to number of new notifications
        """
        results = {}

        for vessel_id, interest in self.vessel_interests.items():
            known_servers = interest.get("known_servers", set())
            new_count = 0

            for server_id, server in self.servers.items():
                if server_id not in known_servers:
                    # This is a server the vessel doesn't know about
                    relevance = self._calculate_server_relevance(server, interest)
                    if relevance >= 2:
                        self._notify_vessels_of_new_server(server)
                        new_count += 1

                    # Mark as known even if not relevant (to avoid re-checking)
                    interest.setdefault("known_servers", set()).add(server_id)

            if new_count > 0:
                results[vessel_id] = new_count

        return results


# Singleton instance
mcp_explorer = MCPExplorer()
