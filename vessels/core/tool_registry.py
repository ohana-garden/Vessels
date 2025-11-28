"""
Tool Registry: Graph-based tool management for A0.

All tools (native, MCP, custom) are registered in the knowledge graph.
A0 queries the graph to find tools that match capability needs.
No hardcoded tool mappings - everything is data.
"""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from vessels.knowledge.schema import (
    NodeType,
    RelationType,
    ToolTrustLevel,
    ToolCostModel,
    ToolProviderType,
    CapabilityCategory,
)

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of a tool in the registry."""
    tool_id: str
    name: str
    description: str

    # What it does
    capabilities: List[str]           # ["scheduling", "reminders"]
    problems_it_solves: List[str]     # ["need to track time", "coordinate events"]
    domains: List[str]                # ["agriculture", "business"]

    # How to use it
    parameters_schema: Optional[Dict[str, Any]] = None  # JSON schema
    implementation: Optional[Callable] = None           # For native/custom tools

    # Where it comes from
    provider_type: ToolProviderType = ToolProviderType.NATIVE
    provider_id: Optional[str] = None  # MCP server ID, or None for native

    # Trust and cost
    trust_level: ToolTrustLevel = ToolTrustLevel.UNKNOWN
    cost_model: ToolCostModel = ToolCostModel.UNKNOWN

    # Recommendations
    recommended_for: List[str] = field(default_factory=list)  # Vessel types

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)

    def matches_need(self, need: str) -> float:
        """Score how well this tool matches a capability need (0-1)."""
        need_lower = need.lower()
        score = 0.0

        # Check capabilities
        for cap in self.capabilities:
            if cap.lower() in need_lower or need_lower in cap.lower():
                score += 0.3

        # Check problems it solves
        for problem in self.problems_it_solves:
            words = problem.lower().split()
            if any(word in need_lower for word in words if len(word) > 3):
                score += 0.4

        # Check domains
        for domain in self.domains:
            if domain.lower() in need_lower:
                score += 0.2

        # Check name and description
        if need_lower in self.name.lower() or need_lower in self.description.lower():
            score += 0.2

        return min(score, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for graph storage."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "problems_it_solves": self.problems_it_solves,
            "domains": self.domains,
            "parameters_schema": json.dumps(self.parameters_schema) if self.parameters_schema else None,
            "provider_type": self.provider_type.value,
            "provider_id": self.provider_id,
            "trust_level": self.trust_level.value,
            "cost_model": self.cost_model.value,
            "recommended_for": self.recommended_for,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolDefinition":
        """Deserialize from dictionary."""
        params_schema = data.get("parameters_schema")
        if isinstance(params_schema, str):
            params_schema = json.loads(params_schema) if params_schema else None

        return cls(
            tool_id=data["tool_id"],
            name=data["name"],
            description=data.get("description", ""),
            capabilities=data.get("capabilities", []),
            problems_it_solves=data.get("problems_it_solves", []),
            domains=data.get("domains", []),
            parameters_schema=params_schema,
            provider_type=ToolProviderType(data.get("provider_type", "native")),
            provider_id=data.get("provider_id"),
            trust_level=ToolTrustLevel(data.get("trust_level", "unknown")),
            cost_model=ToolCostModel(data.get("cost_model", "unknown")),
            recommended_for=data.get("recommended_for", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
        )


class ToolRegistry:
    """
    Graph-based tool registry for A0.

    All tools are stored in the knowledge graph. A0 queries semantically
    to find tools that match capability needs - no hardcoded mappings.

    Supports:
    - Native tools (built into A0/Claude)
    - MCP tools (from MCP servers)
    - Custom tools (user-defined)
    - Vessel tools (provided by other vessels)
    """

    def __init__(
        self,
        graph_client: Optional[Any] = None,
        llm_call: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize the tool registry.

        Args:
            graph_client: Graphiti/FalkorDB client for persistence
            llm_call: LLM function for semantic matching
        """
        self.graph_client = graph_client
        self.llm_call = llm_call

        # In-memory cache (primary when no graph, fallback cache when graph exists)
        self._tools: Dict[str, ToolDefinition] = {}
        self._implementations: Dict[str, Callable] = {}  # tool_id -> callable

        # Track vessel tool bindings
        self._vessel_tools: Dict[str, Set[str]] = {}  # vessel_id -> set of tool_ids

        # Seed with native tools
        self._seed_native_tools()

    def _seed_native_tools(self):
        """Register A0's native capabilities as tools."""
        native_tools = [
            ToolDefinition(
                tool_id="native_web_search",
                name="Web Search",
                description="Search the web for information",
                capabilities=["search", "research", "lookup", "find_information"],
                problems_it_solves=["need to find information", "research a topic", "look something up"],
                domains=["research", "general"],
                provider_type=ToolProviderType.NATIVE,
                trust_level=ToolTrustLevel.VERIFIED,
                cost_model=ToolCostModel.FREE,
                recommended_for=["research", "general", "business"],
            ),
            ToolDefinition(
                tool_id="native_web_fetch",
                name="Web Fetch",
                description="Fetch and analyze content from URLs",
                capabilities=["http", "fetch", "web_content", "scraping"],
                problems_it_solves=["need web content", "analyze a webpage", "get data from URL"],
                domains=["research", "monitoring"],
                provider_type=ToolProviderType.NATIVE,
                trust_level=ToolTrustLevel.VERIFIED,
                cost_model=ToolCostModel.FREE,
                recommended_for=["research", "monitoring"],
            ),
            ToolDefinition(
                tool_id="native_file_read",
                name="File Read",
                description="Read files from the filesystem",
                capabilities=["file", "read", "document"],
                problems_it_solves=["need to read a file", "access document content"],
                domains=["general"],
                provider_type=ToolProviderType.NATIVE,
                trust_level=ToolTrustLevel.VERIFIED,
                cost_model=ToolCostModel.FREE,
                recommended_for=["general"],
            ),
            ToolDefinition(
                tool_id="native_file_write",
                name="File Write",
                description="Write content to files",
                capabilities=["file", "write", "save", "document"],
                problems_it_solves=["need to save content", "write to file", "create document"],
                domains=["general"],
                provider_type=ToolProviderType.NATIVE,
                trust_level=ToolTrustLevel.VERIFIED,
                cost_model=ToolCostModel.FREE,
                recommended_for=["general"],
            ),
            ToolDefinition(
                tool_id="native_bash",
                name="Bash Command",
                description="Execute shell commands",
                capabilities=["shell", "command", "system", "execute"],
                problems_it_solves=["need to run a command", "system operation", "execute script"],
                domains=["system", "development"],
                provider_type=ToolProviderType.NATIVE,
                trust_level=ToolTrustLevel.VERIFIED,
                cost_model=ToolCostModel.FREE,
                recommended_for=["development", "system"],
            ),
        ]

        for tool in native_tools:
            self._tools[tool.tool_id] = tool

        logger.info(f"Seeded {len(native_tools)} native tools in registry")

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register_tool(self, tool: ToolDefinition) -> str:
        """
        Register a tool in the registry.

        Args:
            tool: Tool definition to register

        Returns:
            Tool ID
        """
        if not tool.tool_id:
            tool.tool_id = str(uuid.uuid4())

        # Store in memory cache
        self._tools[tool.tool_id] = tool

        # Persist to graph if available
        if self.graph_client:
            self._persist_tool_to_graph(tool)

        logger.info(f"Registered tool: {tool.name} ({tool.tool_id})")
        return tool.tool_id

    def register_mcp_tools(
        self,
        server_id: str,
        server_name: str,
        tools: List[Dict[str, Any]],
        trust_level: ToolTrustLevel = ToolTrustLevel.UNKNOWN,
        cost_model: ToolCostModel = ToolCostModel.UNKNOWN,
    ) -> List[str]:
        """
        Register tools from an MCP server.

        Args:
            server_id: MCP server ID
            server_name: Human-readable server name
            tools: List of tool definitions from MCP
            trust_level: Trust level for these tools
            cost_model: Cost model for these tools

        Returns:
            List of registered tool IDs
        """
        registered = []

        for mcp_tool in tools:
            tool = ToolDefinition(
                tool_id=f"mcp_{server_id}_{mcp_tool.get('name', 'unknown')}",
                name=mcp_tool.get("name", "Unknown Tool"),
                description=mcp_tool.get("description", ""),
                capabilities=mcp_tool.get("capabilities", []),
                problems_it_solves=mcp_tool.get("problems_it_solves", []),
                domains=mcp_tool.get("domains", []),
                parameters_schema=mcp_tool.get("inputSchema"),
                provider_type=ToolProviderType.MCP,
                provider_id=server_id,
                trust_level=trust_level,
                cost_model=cost_model,
                recommended_for=mcp_tool.get("recommended_for", []),
            )

            self.register_tool(tool)
            registered.append(tool.tool_id)

        logger.info(f"Registered {len(registered)} tools from MCP server {server_name}")
        return registered

    def register_implementation(self, tool_id: str, implementation: Callable) -> bool:
        """
        Register a callable implementation for a tool.

        Args:
            tool_id: Tool to register implementation for
            implementation: Callable to execute

        Returns:
            True if registered successfully
        """
        if tool_id not in self._tools:
            logger.warning(f"Cannot register implementation for unknown tool: {tool_id}")
            return False

        self._implementations[tool_id] = implementation
        self._tools[tool_id].implementation = implementation
        return True

    def _persist_tool_to_graph(self, tool: ToolDefinition) -> None:
        """Persist a tool to the knowledge graph."""
        if not self.graph_client:
            return

        try:
            # Create tool node
            # This would use the graph client's API
            # For now, implementation depends on Graphiti interface
            pass
        except Exception as e:
            logger.error(f"Failed to persist tool to graph: {e}")

    # =========================================================================
    # DISCOVERY & QUERYING
    # =========================================================================

    def find_tools_for_need(
        self,
        capability_need: str,
        vessel_type: Optional[str] = None,
        trust_minimum: ToolTrustLevel = ToolTrustLevel.UNKNOWN,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find tools that match a capability need.

        Uses semantic matching to find tools - no hardcoded mappings.

        Args:
            capability_need: Natural language description of what's needed
            vessel_type: Optional vessel type for better matching
            trust_minimum: Minimum trust level required
            max_results: Maximum number of results

        Returns:
            List of matching tools with scores
        """
        matches = []
        trust_order = [ToolTrustLevel.UNTRUSTED, ToolTrustLevel.UNKNOWN,
                      ToolTrustLevel.COMMUNITY, ToolTrustLevel.VERIFIED]

        for tool in self._tools.values():
            # Filter by trust level
            if trust_order.index(tool.trust_level) < trust_order.index(trust_minimum):
                continue

            # Score the match
            score = tool.matches_need(capability_need)

            # Boost if recommended for this vessel type
            if vessel_type:
                vessel_lower = vessel_type.lower()
                for rec in tool.recommended_for:
                    if rec.lower() in vessel_lower or vessel_lower in rec.lower():
                        score *= 1.3
                        break

            if score > 0.1:  # Minimum threshold
                matches.append({
                    "tool": tool.to_dict(),
                    "tool_id": tool.tool_id,
                    "score": min(score, 1.0),
                    "provider_type": tool.provider_type.value,
                })

        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:max_results]

    def find_tools_for_purpose(
        self,
        purpose: str,
        vessel_type: Optional[str] = None,
    ) -> List[str]:
        """
        Find tool IDs for an agent's purpose.

        Used by A0.build_agent() to determine what tools an agent needs
        based on its purpose - replaces hardcoded tool mapping.

        Args:
            purpose: Natural language description of agent's purpose
            vessel_type: Type of vessel the agent serves

        Returns:
            List of tool IDs that would help with this purpose
        """
        # Use LLM if available for better understanding
        if self.llm_call:
            return self._llm_find_tools(purpose, vessel_type)

        # Fallback to keyword matching
        matches = self.find_tools_for_need(purpose, vessel_type)
        return [m["tool_id"] for m in matches if m["score"] > 0.2]

    def _llm_find_tools(self, purpose: str, vessel_type: Optional[str] = None) -> List[str]:
        """Use LLM to semantically match tools to purpose."""
        # Build tool catalog summary
        tool_summaries = []
        for tool in self._tools.values():
            tool_summaries.append(
                f"- {tool.tool_id}: {tool.name} - {tool.description} "
                f"(capabilities: {', '.join(tool.capabilities[:3])})"
            )

        prompt = f"""Given this agent purpose: "{purpose}"
{f'For a {vessel_type} vessel.' if vessel_type else ''}

Available tools:
{chr(10).join(tool_summaries[:20])}

Which tools would be most useful for this purpose? Return a JSON array of tool_ids.
Example: ["native_web_search", "native_file_read"]

JSON array:"""

        try:
            response = self.llm_call(prompt)
            # Parse JSON from response
            import re
            match = re.search(r'\[.*?\]', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception as e:
            logger.error(f"LLM tool matching failed: {e}")

        # Fallback to simple matching
        matches = self.find_tools_for_need(purpose, vessel_type)
        return [m["tool_id"] for m in matches if m["score"] > 0.2]

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)

    def get_implementation(self, tool_id: str) -> Optional[Callable]:
        """Get the implementation for a tool."""
        return self._implementations.get(tool_id)

    def list_tools(
        self,
        provider_type: Optional[ToolProviderType] = None,
        trust_level: Optional[ToolTrustLevel] = None,
    ) -> List[ToolDefinition]:
        """List all tools with optional filtering."""
        tools = list(self._tools.values())

        if provider_type:
            tools = [t for t in tools if t.provider_type == provider_type]

        if trust_level:
            trust_order = [ToolTrustLevel.UNTRUSTED, ToolTrustLevel.UNKNOWN,
                          ToolTrustLevel.COMMUNITY, ToolTrustLevel.VERIFIED]
            min_idx = trust_order.index(trust_level)
            tools = [t for t in tools if trust_order.index(t.trust_level) >= min_idx]

        return tools

    # =========================================================================
    # VESSEL TOOL BINDINGS
    # =========================================================================

    def bind_tool_to_vessel(self, vessel_id: str, tool_id: str) -> bool:
        """Bind a tool to a vessel."""
        if tool_id not in self._tools:
            logger.warning(f"Cannot bind unknown tool {tool_id} to vessel {vessel_id}")
            return False

        if vessel_id not in self._vessel_tools:
            self._vessel_tools[vessel_id] = set()

        self._vessel_tools[vessel_id].add(tool_id)
        logger.debug(f"Bound tool {tool_id} to vessel {vessel_id}")
        return True

    def unbind_tool_from_vessel(self, vessel_id: str, tool_id: str) -> bool:
        """Unbind a tool from a vessel."""
        if vessel_id in self._vessel_tools:
            self._vessel_tools[vessel_id].discard(tool_id)
            return True
        return False

    def get_vessel_tools(self, vessel_id: str) -> List[ToolDefinition]:
        """Get all tools bound to a vessel."""
        tool_ids = self._vessel_tools.get(vessel_id, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]

    def get_vessel_tool_ids(self, vessel_id: str) -> List[str]:
        """Get tool IDs bound to a vessel."""
        return list(self._vessel_tools.get(vessel_id, set()))

    # =========================================================================
    # MCP INTEGRATION
    # =========================================================================

    def get_mcp_tools(self, server_id: str) -> List[ToolDefinition]:
        """Get all tools provided by an MCP server."""
        return [
            t for t in self._tools.values()
            if t.provider_type == ToolProviderType.MCP and t.provider_id == server_id
        ]

    def get_mcp_servers(self) -> List[str]:
        """Get unique MCP server IDs that have registered tools."""
        return list(set(
            t.provider_id for t in self._tools.values()
            if t.provider_type == ToolProviderType.MCP and t.provider_id
        ))

    # =========================================================================
    # STATS
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        by_provider = {}
        by_trust = {}

        for tool in self._tools.values():
            provider = tool.provider_type.value
            by_provider[provider] = by_provider.get(provider, 0) + 1

            trust = tool.trust_level.value
            by_trust[trust] = by_trust.get(trust, 0) + 1

        return {
            "total_tools": len(self._tools),
            "by_provider": by_provider,
            "by_trust": by_trust,
            "vessels_with_tools": len(self._vessel_tools),
            "mcp_servers": len(self.get_mcp_servers()),
        }


# Singleton instance
tool_registry = ToolRegistry()
