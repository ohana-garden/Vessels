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
        # For now, just log that we're exploring
        logger.debug("MCP Explorer: scanning for new servers...")

        # This is where we'd implement actual discovery:
        # - Query npm for packages matching @mcp/ or mcp-server
        # - Search GitHub for repos with mcp-server topic
        # - Check community registries
        # - For each found, call _understand_server() to build semantic model

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


# Singleton instance
mcp_explorer = MCPExplorer()
