#!/usr/bin/env python3
"""
AGENT ZERO CORE - Meta-Coordination Engine
Spawns agents dynamically from natural language descriptions
Self-organizes based on community needs
Coordinates entire agent ecosystem

VESSEL-NATIVE DESIGN:
- Accepts VesselRegistry for multi-vessel agent coordination
- Each agent spawned within a vessel gets vessel-scoped resources:
  * Memory backend (namespaced per agent)
  * Action gate (enforcing privacy/moral constraints)
  * Tools (with permission-based access)
- No global memory/tool system - all resources come from vessels
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
import inspect

# Avoid circular imports
if TYPE_CHECKING:
    from vessels.core.registry import VesselRegistry
    from vessels.core.vessel import Vessel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    PAUSED_FOR_CONSULTATION = "paused_for_consultation"
    WAITING_ASYNC = "waiting_async"

@dataclass
class AgentSpecification:
    """Dynamic agent specification from natural language"""
    name: str
    description: str
    capabilities: List[str]
    tools_needed: List[str]
    communication_style: str = "collaborative"
    autonomy_level: str = "high"
    memory_type: str = "shared"
    specialization: str = "general"
    
@dataclass
class AgentInstance:
    """Live agent instance with vessel-scoped resources"""
    id: str
    specification: AgentSpecification
    status: AgentStatus
    created_at: datetime
    last_active: datetime
    vessel_id: Optional[str] = None  # Vessel this agent belongs to
    memory: Dict[str, Any] = field(default_factory=dict)
    memory_backend: Optional[Any] = None  # Vessel-injected memory backend
    action_gate: Optional[Any] = None  # Vessel-injected action gate
    tools: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)
    message_queue: queue.Queue = field(default_factory=queue.Queue)
    active_consultation: Optional[Any] = None
    
class AgentZeroCore:
    """
    Meta-coordination engine that spawns and manages agents.

    VESSEL-NATIVE ARCHITECTURE:
    - Accepts VesselRegistry to coordinate agents across multiple vessels
    - Each agent is spawned within a specific vessel and gets vessel-scoped:
      * Memory backend (namespaced per agent)
      * Action gate (privacy/moral constraints from vessel)
      * Tools (permission-controlled from vessel)
    - Backward compatible: works without VesselRegistry (legacy mode)
    """

    def __init__(self, vessel_registry: Optional[Any] = None, *,
                 default_memory=None, default_tools=None,
                 llm_call: Optional[Callable[[str], str]] = None):
        """
        Initialize AgentZeroCore.

        Args:
            vessel_registry: Optional VesselRegistry for vessel-native coordination
            default_memory: Fallback memory system (used if no vessel provided)
            default_tools: Fallback tool system (used if no vessel provided)
            llm_call: Function to call LLM for agent thinking (prompt -> response)
        """
        self.vessel_registry = vessel_registry
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_specifications: Dict[str, AgentSpecification] = {}
        self.message_bus = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.running = False
        self.coordination_thread = None

        # LLM interface for agent thinking
        self.llm_call = llm_call

        # Legacy fallback systems (used when no vessel is provided)
        self.system_memory = default_memory or {}
        self.memory_system = default_memory
        self.tool_system = default_tools
        self.gate = None  # Global gate (fallback, vessel gates preferred)

        # Village consensus and interface
        self.consensus_engine = None  # Village consensus engine (optional)
        self.interface = None  # Interface for sending messages to users

        # Specialized agents (not spawned, but coordinated through A0)
        self.birth_agent = None  # Birth Agent for vessel creation
        self.mcp_explorer = None  # MCP Explorer for capability discovery
        self.ambassador_factory = None  # Factory for MCP Ambassador agents

        # Track MCP Ambassadors (server_id -> ambassador)
        self.mcp_ambassadors: Dict[str, Any] = {}

        # Tool Registry - graph-based tool management (no hardcoding!)
        self.tool_registry = None

        # A2A (Agent-to-Agent) Protocol - vessel-to-vessel communication
        self.a2a_service = None
        self.a2a_registry = None
        self.a2a_discovery = None
        
    def initialize(self, memory_system=None, tool_system=None):
        """
        Initialize the coordination system.

        Note: When using vessel_registry, memory/tools come from vessels.
        This method is primarily for backward compatibility.
        """
        if memory_system:
            self.memory_system = memory_system
        if tool_system:
            self.tool_system = tool_system
        self.running = True
        self.coordination_thread = threading.Thread(target=self._coordination_loop)
        self.coordination_thread.daemon = True
        self.coordination_thread.start()

        # Initialize Tool Registry - graph-based tool management
        self._initialize_tool_registry()

        # Initialize Birth Agent with A0's LLM interface
        self._initialize_birth_agent()

        # Initialize MCP Explorer for capability discovery
        self._initialize_mcp_explorer()

        # Initialize Ambassador Factory for MCP server personification
        self._initialize_ambassador_factory()

        # Initialize A2A Protocol for vessel-to-vessel communication
        self._initialize_a2a()

        logger.info("Agent Zero Core initialized")

    def _initialize_tool_registry(self):
        """Initialize the Tool Registry for graph-based tool management."""
        try:
            from vessels.core.tool_registry import ToolRegistry
            self.tool_registry = ToolRegistry(
                graph_client=self.memory_system,  # Use memory system as graph client
                llm_call=self.llm_call,
            )
            logger.info("Tool Registry initialized - no more hardcoded tool mappings!")
        except ImportError as e:
            logger.warning(f"Could not initialize Tool Registry: {e}")
            self.tool_registry = None

    def _initialize_birth_agent(self):
        """Initialize the Birth Agent for vessel creation."""
        try:
            from vessels.agents.birth_agent import BirthAgent
            self.birth_agent = BirthAgent(
                vessel_registry=self.vessel_registry,
                memory_backend=self.memory_system,
                llm_call=self.llm_call
            )
            logger.info("Birth Agent initialized through A0")
        except ImportError as e:
            logger.warning(f"Could not initialize Birth Agent: {e}")
            self.birth_agent = None

    def _initialize_mcp_explorer(self):
        """Initialize the MCP Explorer for capability discovery."""
        try:
            from vessels.agents.mcp_explorer import MCPExplorer
            self.mcp_explorer = MCPExplorer(
                llm_call=self.llm_call,
                memory_backend=self.memory_system,
            )
            # Start background exploration
            self.mcp_explorer.start()

            # Register seeded MCP server tools in tool registry
            if self.tool_registry:
                for server in self.mcp_explorer.servers.values():
                    self._register_mcp_server_tools(server)

            logger.info("MCP Explorer initialized and exploring")
        except ImportError as e:
            logger.warning(f"Could not initialize MCP Explorer: {e}")
            self.mcp_explorer = None

    def _initialize_ambassador_factory(self):
        """Initialize the Ambassador Factory for MCP server personification."""
        try:
            from vessels.agents.mcp_ambassador import MCPAmbassadorFactory
            self.ambassador_factory = MCPAmbassadorFactory(
                llm_call=self.llm_call,
            )

            # Create ambassadors for all seeded MCP servers
            if self.mcp_explorer:
                for server in self.mcp_explorer.servers.values():
                    self._birth_mcp_ambassador(server)

            logger.info(
                f"Ambassador Factory initialized with "
                f"{len(self.mcp_ambassadors)} ambassadors"
            )
        except ImportError as e:
            logger.warning(f"Could not initialize Ambassador Factory: {e}")
            self.ambassador_factory = None

    def set_llm_call(self, llm_call: Callable[[str], str]) -> None:
        """
        Set or update the LLM call function.

        Args:
            llm_call: Function to call LLM (prompt -> response)
        """
        self.llm_call = llm_call
        # Update Birth Agent if it exists
        if self.birth_agent:
            self.birth_agent.llm_call = llm_call
        # Update MCP Explorer if it exists
        if self.mcp_explorer:
            self.mcp_explorer.llm_call = llm_call
        # Update Tool Registry if it exists
        if self.tool_registry:
            self.tool_registry.llm_call = llm_call
        # Update Ambassador Factory if it exists
        if self.ambassador_factory:
            self.ambassador_factory.llm_call = llm_call
        logger.info("LLM call function configured for AgentZeroCore")

    def _initialize_a2a(self):
        """Initialize A2A Protocol components for agent-to-agent communication."""
        try:
            from vessels.a2a import A2AService, AgentRegistry, A2ADiscovery, AgentCard, AgentSkill

            # Create agent registry for tracking known agents
            self.a2a_registry = AgentRegistry(
                graphiti_client=self.memory_system
            )

            # Create A0's own agent card
            a0_skills = [
                AgentSkill(
                    skill_id="vessel-orchestration",
                    name="Vessel Orchestration",
                    description="Spawn, manage, and coordinate vessels and agents",
                    tags=["orchestration", "coordination", "management"],
                    examples=["Create a vessel for my garden", "Spawn an agent to help with grants"],
                ),
                AgentSkill(
                    skill_id="capability-discovery",
                    name="Capability Discovery",
                    description="Discover and provision capabilities from MCP servers",
                    tags=["mcp", "discovery", "tools"],
                    examples=["Find tools for weather forecasting", "Connect to a calendar service"],
                ),
                AgentSkill(
                    skill_id="task-delegation",
                    name="Task Delegation",
                    description="Delegate tasks to appropriate agents or vessels",
                    tags=["delegation", "coordination", "routing"],
                    examples=["Route this request to a specialist agent", "Find help for grant writing"],
                ),
            ]

            a0_card = AgentCard(
                agent_id="agent-zero",
                name="Agent Zero",
                description="The universal builder and coordinator for the Vessels ecosystem",
                skills=a0_skills,
                provider_name="Vessels",
                domains=["orchestration", "coordination", "meta-agent"],
            )

            # Get Nostr adapter if available
            nostr_adapter = None
            # (Will be connected when Nostr is configured)

            # Create A2A service
            self.a2a_service = A2AService(
                agent_card=a0_card,
                nostr_adapter=nostr_adapter,
                graphiti_client=self.memory_system,
            )

            # Create discovery service
            self.a2a_discovery = A2ADiscovery(
                registry=self.a2a_registry,
                nostr_adapter=nostr_adapter,
                graphiti_client=self.memory_system,
            )

            logger.info("A2A Protocol initialized - vessels can now communicate!")

        except ImportError as e:
            logger.warning(f"Could not initialize A2A Protocol: {e}")
            self.a2a_service = None
            self.a2a_registry = None
            self.a2a_discovery = None

    def process_birth_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process a message for vessel birth through A0.

        Args:
            user_id: User ID
            message: User message

        Returns:
            Response dict with message and metadata
        """
        if not self.birth_agent:
            self._initialize_birth_agent()

        if self.birth_agent:
            return self.birth_agent.process_message(user_id, message)
        else:
            return {
                "response": "Birth Agent not available",
                "phase": "error",
                "follow_up_needed": False
            }

    def detect_creation_intent(self, message: str) -> Dict[str, Any]:
        """
        Detect vessel creation intent through A0.

        Args:
            message: User message

        Returns:
            Intent detection result
        """
        if not self.birth_agent:
            self._initialize_birth_agent()

        if self.birth_agent:
            return self.birth_agent.detect_creation_intent(message)
        else:
            return {
                "wants_to_create": False,
                "confidence": 0.0,
                "subject": None,
                "reasoning": "Birth Agent not available"
            }

    def has_active_birth_session(self, user_id: str) -> bool:
        """Check if user has an active birth session."""
        if self.birth_agent:
            return self.birth_agent.has_active_session(user_id)
        return False

    def set_vessel_registry(self, registry: Any) -> None:
        """
        Set or update the vessel registry.

        Args:
            registry: VesselRegistry instance for vessel-native coordination
        """
        self.vessel_registry = registry
        logger.info("Vessel registry configured for AgentZeroCore")

    # =========================================================================
    # UNIVERSAL BUILDER METHODS
    # A0 is THE main core - everything is built through these methods
    # =========================================================================

    def build_project(
        self,
        name: str,
        owner_id: str,
        description: str = "",
        privacy_level: str = "private",
        governance: str = "solo",
    ) -> Dict[str, Any]:
        """
        Build a new project (community/bounded collaborative space).

        A project provides:
        - Shared knowledge graph namespace for all vessels within
        - Memory scope that vessels can access
        - Privacy boundaries for external access
        - Governance model

        Args:
            name: Project name
            owner_id: User ID of the project owner
            description: Project description
            privacy_level: "private", "shared", "public", or "federated"
            governance: "solo", "collaborative", or "federated"

        Returns:
            Dict with project details including project_id
        """
        from vessels.core.project import Project, GovernanceModel
        from vessels.knowledge.schema import CommunityPrivacy

        # Map string to enums
        privacy_enum = CommunityPrivacy(privacy_level)
        governance_enum = GovernanceModel(governance)

        # Create the project
        project = Project.create(
            name=name,
            owner_id=owner_id,
            description=description,
            privacy_level=privacy_enum,
            governance=governance_enum,
        )

        # Wire up memory backend if available
        if self.memory_system:
            project.set_memory_backend(self.memory_system)

        # Store in registry if we have one that supports projects
        # (For now, projects are tracked separately - can add ProjectRegistry later)
        if not hasattr(self, '_projects'):
            self._projects: Dict[str, Any] = {}
        self._projects[project.project_id] = project

        logger.info(f"A0 built project '{name}' ({project.project_id}) for {owner_id}")

        return {
            "project_id": project.project_id,
            "name": project.name,
            "description": project.description,
            "owner_id": project.owner_id,
            "graph_namespace": project.graph_namespace,
            "privacy_level": privacy_level,
            "governance": governance,
        }

    def build_vessel(
        self,
        name: str,
        project_id: str,
        description: str = "",
        persona: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a new vessel within a project.

        A vessel is a personified digital twin that:
        - Lives within a project (inherits project context)
        - Has its own persona (voice, values, relationship mode)
        - Can spawn agents to do work
        - Collaborates with other vessels in the same project

        Args:
            name: Vessel name
            project_id: ID of project this vessel belongs to
            description: Vessel description
            persona: Optional persona configuration (voice, values, etc.)

        Returns:
            Dict with vessel details including vessel_id
        """
        from vessels.core.vessel import Vessel, PrivacyLevel
        from vessels.knowledge.schema import CommunityPrivacy

        # Get the project
        project = self._projects.get(project_id) if hasattr(self, '_projects') else None
        if not project:
            # Create default project if none exists
            logger.warning(f"Project {project_id} not found, creating default")
            project_result = self.build_project(
                name=f"Project for {name}",
                owner_id="system",
                description=f"Auto-created project for vessel {name}",
            )
            project_id = project_result["project_id"]
            project = self._projects[project_id]

        # Create the vessel
        vessel = Vessel.create(
            name=name,
            community_id=project.graph_namespace,  # Use project's namespace
            description=description,
            privacy_level=PrivacyLevel(project.config.privacy_level.value),
        )

        # Wire up vessel resources from project
        if project._memory_backend:
            vessel.set_memory_backend(project._memory_backend)
        elif self.memory_system:
            vessel.set_memory_backend(self.memory_system)

        # Store persona if provided
        if persona:
            vessel.connectors["persona"] = persona

        # Register vessel with project
        project.add_vessel(vessel.vessel_id)

        # Register in vessel registry if available
        if self.vessel_registry:
            try:
                self.vessel_registry.register_vessel(vessel)
            except Exception as e:
                logger.warning(f"Could not register vessel in registry: {e}")

        logger.info(f"A0 built vessel '{name}' ({vessel.vessel_id}) in project {project_id}")

        # Proactively inform vessel of available capabilities
        capability_recommendations = None
        vessel_type = None
        if self.mcp_explorer and persona:
            vessel_type = persona.get("subject", name)
            capability_recommendations = self.mcp_explorer.recommend_capabilities_for_vessel(
                vessel_id=vessel.vessel_id,
                vessel_type=vessel_type,
            )
            logger.info(
                f"Recommended {len(capability_recommendations.get('recommendations', {}).get('essential', []))} "
                f"essential capabilities for vessel '{name}'"
            )

            # Register vessel interests for ongoing capability notifications
            # As new MCP servers emerge, this vessel will be informed of relevant ones
            vessel_domains = persona.get("domains", [])
            self.mcp_explorer.register_vessel_interest(
                vessel_id=vessel.vessel_id,
                vessel_type=vessel_type,
                domains=vessel_domains,
            )
            logger.info(f"Registered vessel '{name}' for ongoing capability notifications")

        return {
            "vessel_id": vessel.vessel_id,
            "name": vessel.name,
            "description": vessel.description,
            "project_id": project_id,
            "graph_namespace": vessel.graph_namespace,
            "persona": persona,
            "capability_recommendations": capability_recommendations,
        }

    def build_agent(
        self,
        name: str,
        vessel_id: str,
        specialization: str = "general",
        capabilities: Optional[List[str]] = None,
        tools_needed: Optional[List[str]] = None,
    ) -> str:
        """
        Build a new agent for a vessel.

        Agents are workers that do things on behalf of vessels.
        They inherit vessel-scoped resources (memory, tools, action gate).

        Args:
            name: Agent name
            vessel_id: ID of vessel this agent works for
            specialization: Agent specialization type
            capabilities: List of agent capabilities
            tools_needed: List of tools the agent needs

        Returns:
            Agent ID
        """
        spec = AgentSpecification(
            name=name,
            description=f"Agent for vessel {vessel_id}",
            capabilities=capabilities or [],
            tools_needed=tools_needed or [],
            specialization=specialization,
        )

        # Spawn through existing method which handles vessel integration
        agent_ids = self.spawn_agents([spec], vessel_id=vessel_id)

        if agent_ids:
            logger.info(f"A0 built agent '{name}' ({agent_ids[0]}) for vessel {vessel_id}")
            return agent_ids[0]
        else:
            raise RuntimeError(f"Failed to build agent '{name}' for vessel {vessel_id}")

    def build_tool(
        self,
        name: str,
        description: str,
        vessel_id: Optional[str] = None,
        implementation: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Build a new tool, optionally scoped to a vessel.

        Tools are capabilities that agents can use. When built through A0,
        tools are properly integrated with the system.

        Args:
            name: Tool name
            description: What the tool does
            vessel_id: Optional vessel to scope tool to
            implementation: Optional callable implementation

        Returns:
            Dict with tool details
        """
        tool_id = str(uuid.uuid4())

        tool_spec = {
            "tool_id": tool_id,
            "name": name,
            "description": description,
            "vessel_id": vessel_id,
            "created_at": datetime.now().isoformat(),
        }

        # If vessel specified, add tool to vessel
        if vessel_id and self.vessel_registry:
            vessel = self.vessel_registry.get_vessel(vessel_id)
            if vessel and implementation:
                vessel.add_tool(name, implementation)
                logger.info(f"A0 built tool '{name}' for vessel {vessel_id}")

        # Store in tool system if available
        if self.tool_system and hasattr(self.tool_system, 'register_tool'):
            self.tool_system.register_tool(tool_spec)

        return tool_spec

    def get_project(self, project_id: str) -> Optional[Any]:
        """Get a project by ID."""
        if hasattr(self, '_projects'):
            return self._projects.get(project_id)
        return None

    def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all projects owned by or accessible to a user."""
        if not hasattr(self, '_projects'):
            return []

        results = []
        for project in self._projects.values():
            if project.is_member(user_id):
                results.append(project.to_dict())
        return results

    def get_project_vessels(self, project_id: str) -> List[str]:
        """Get all vessel IDs in a project."""
        project = self.get_project(project_id)
        if project:
            return list(project.vessel_ids)
        return []

    # =========================================================================
    # MCP CAPABILITY PROVISIONING
    # Dynamic tool provisioning from MCP servers
    # =========================================================================

    def provision_capability(
        self,
        vessel_id: str,
        capability_need: str,
        auto_connect: bool = True,
    ) -> Dict[str, Any]:
        """
        Provision a capability for a vessel by connecting to appropriate MCP server.

        When a vessel needs a capability (e.g., "weather forecasting"), A0:
        1. Asks MCP Explorer to find matching servers
        2. Selects the best match
        3. Connects vessel to that server
        4. Returns the tools now available

        Args:
            vessel_id: Vessel that needs the capability
            capability_need: Natural language description of what's needed
            auto_connect: Automatically connect to recommended server

        Returns:
            Dict with server info, tools provisioned, and status
        """
        if not self.mcp_explorer:
            self._initialize_mcp_explorer()

        if not self.mcp_explorer:
            return {
                "success": False,
                "error": "MCP Explorer not available",
                "tools_provisioned": []
            }

        # Get vessel type for better matching
        vessel_type = None
        if self.vessel_registry:
            vessel = self.vessel_registry.get_vessel(vessel_id)
            if vessel and vessel.connectors.get("persona"):
                vessel_type = vessel.connectors["persona"].get("subject")

        # Get recommendation from MCP Explorer
        recommendation = self.mcp_explorer.get_recommendation(
            capability_need=capability_need,
            vessel_id=vessel_id,
            vessel_type=vessel_type,
        )

        if not recommendation.get("recommended_server_id"):
            return {
                "success": False,
                "error": recommendation.get("reasoning", "No matching MCP server found"),
                "tools_provisioned": []
            }

        server_id = recommendation["recommended_server_id"]

        if auto_connect:
            # Connect vessel to server
            connection = self.mcp_explorer.connect_vessel_to_server(vessel_id, server_id)

            logger.info(
                f"Provisioned capability '{capability_need}' for vessel {vessel_id} "
                f"via MCP server {server_id}"
            )

            return {
                "success": True,
                "server_id": server_id,
                "server_name": self.mcp_explorer.get_server(server_id).name,
                "confidence": recommendation["confidence"],
                "reasoning": recommendation["reasoning"],
                "tools_provisioned": connection.tools_provisioned,
                "alternatives": recommendation.get("alternatives", [])
            }
        else:
            # Just return recommendation without connecting
            server = self.mcp_explorer.get_server(server_id)
            return {
                "success": True,
                "server_id": server_id,
                "server_name": server.name if server else server_id,
                "confidence": recommendation["confidence"],
                "reasoning": recommendation["reasoning"],
                "tools_available": server.tools_provided if server else [],
                "auto_connect": False,
                "alternatives": recommendation.get("alternatives", [])
            }

    def get_vessel_mcp_tools(self, vessel_id: str) -> List[str]:
        """Get all MCP tools currently available to a vessel."""
        if self.mcp_explorer:
            return self.mcp_explorer.get_vessel_tools(vessel_id)
        return []

    def discover_capabilities(
        self,
        capability_need: str,
        trust_minimum: str = "unknown",
    ) -> List[Dict[str, Any]]:
        """
        Discover MCP servers that can provide a capability.

        Args:
            capability_need: What capability is needed
            trust_minimum: Minimum trust level ("verified", "community", "unknown")

        Returns:
            List of matching servers with scores
        """
        if not self.mcp_explorer:
            return []

        from vessels.agents.mcp_explorer import TrustLevel
        trust_level = TrustLevel(trust_minimum)

        return self.mcp_explorer.find_servers_for_need(
            capability_need=capability_need,
            trust_minimum=trust_level,
        )

    def get_mcp_stats(self) -> Dict[str, Any]:
        """Get statistics about the MCP ecosystem."""
        if self.mcp_explorer:
            return self.mcp_explorer.get_stats()
        return {"error": "MCP Explorer not initialized"}

    def get_vessel_capability_options(self, vessel_id: str) -> Dict[str, Any]:
        """
        Let a vessel ask "what can I do?" - returns all available capabilities.

        Vessels don't know what they don't know. This lets them (or their users)
        discover what capabilities are available to connect to.

        Args:
            vessel_id: The vessel asking

        Returns:
            Dict with connected and available capabilities
        """
        if self.mcp_explorer:
            return self.mcp_explorer.get_capability_options(vessel_id)
        return {
            "vessel_id": vessel_id,
            "currently_connected": [],
            "available_to_add": [],
            "message": "MCP Explorer not available"
        }

    def recommend_capabilities(
        self,
        vessel_id: str,
        vessel_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get proactive capability recommendations for a vessel.

        Can be called at any time to get updated recommendations based on
        what the vessel is and what's available.

        Args:
            vessel_id: The vessel to recommend for
            vessel_type: Optional vessel type (will lookup from registry if not provided)

        Returns:
            Dict with categorized recommendations and human-readable message
        """
        if not self.mcp_explorer:
            return {"error": "MCP Explorer not available", "recommendations": {}}

        # Try to get vessel type from registry if not provided
        if not vessel_type and self.vessel_registry:
            vessel = self.vessel_registry.get_vessel(vessel_id)
            if vessel and vessel.connectors.get("persona"):
                vessel_type = vessel.connectors["persona"].get("subject", "general")

        vessel_type = vessel_type or "general"

        return self.mcp_explorer.recommend_capabilities_for_vessel(
            vessel_id=vessel_id,
            vessel_type=vessel_type,
        )

    # =========================================================================
    # ONGOING CAPABILITY NOTIFICATIONS
    # Vessels are informed when new relevant MCP servers emerge
    # =========================================================================

    def get_vessel_notifications(
        self,
        vessel_id: str,
        mark_as_read: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get pending capability notifications for a vessel.

        Called when a vessel checks in or when user asks about new capabilities.

        Args:
            vessel_id: The vessel to check
            mark_as_read: Mark notifications as read

        Returns:
            List of pending notifications about new MCP servers
        """
        if not self.mcp_explorer:
            return []
        return self.mcp_explorer.get_pending_notifications(vessel_id, mark_as_read)

    def get_vessel_notification_summary(self, vessel_id: str) -> Dict[str, Any]:
        """
        Get a summary of notification status for a vessel.

        Args:
            vessel_id: The vessel to check

        Returns:
            Summary with counts and human-readable message
        """
        if not self.mcp_explorer:
            return {
                "vessel_id": vessel_id,
                "registered": False,
                "total_notifications": 0,
                "unread": 0,
                "message": "MCP Explorer not available"
            }
        return self.mcp_explorer.get_notification_summary(vessel_id)

    def check_all_vessels_for_new_capabilities(self) -> Dict[str, int]:
        """
        Trigger a sweep to notify all vessels of new capabilities.

        Called periodically or when new MCP servers are added to ensure
        all vessels are informed of relevant new capabilities.

        Returns:
            Dict mapping vessel_id to number of new notifications
        """
        if not self.mcp_explorer:
            return {}
        return self.mcp_explorer.check_for_new_capabilities()

    def dismiss_vessel_notification(
        self,
        vessel_id: str,
        server_id: str,
    ) -> bool:
        """
        Dismiss a capability notification (vessel chose not to use it).

        Args:
            vessel_id: The vessel
            server_id: The server to dismiss

        Returns:
            True if dismissed
        """
        if not self.mcp_explorer:
            return False
        return self.mcp_explorer.dismiss_notification(vessel_id, server_id)

    def add_mcp_server(self, server_info: Dict[str, Any]) -> bool:
        """
        Add a new MCP server to the ecosystem and notify interested vessels.

        Called when a new MCP server is discovered or submitted by the community.
        Also registers the server's tools in A0's tool registry.

        Args:
            server_info: Dictionary with server details (server_id, name, description, etc.)

        Returns:
            True if server was added (new), False if already exists
        """
        if not self.mcp_explorer:
            return False

        from vessels.agents.mcp_explorer import MCPServerInfo, TrustLevel, CostModel

        # Build MCPServerInfo from dict
        server = MCPServerInfo(
            server_id=server_info.get("server_id", str(uuid.uuid4())),
            name=server_info.get("name", "Unknown Server"),
            description=server_info.get("description", ""),
            endpoint=server_info.get("endpoint", ""),
            capabilities=server_info.get("capabilities", []),
            tools_provided=server_info.get("tools_provided", []),
            problems_it_solves=server_info.get("problems_it_solves", []),
            domains=server_info.get("domains", []),
            trust_level=TrustLevel(server_info.get("trust_level", "unknown")),
            cost_model=CostModel(server_info.get("cost_model", "unknown")),
            recommended_for=server_info.get("recommended_for", []),
            source=server_info.get("source", "manual"),
        )

        # Add to MCP catalog - this will automatically notify interested vessels
        added = self.mcp_explorer.add_discovered_server(server)

        if added:
            # Register tools in A0's tool registry for unified tool management
            if self.tool_registry:
                self._register_mcp_server_tools(server)

            # Birth an ambassador for this MCP server
            self._birth_mcp_ambassador(server)

        return added

    def _register_mcp_server_tools(self, server) -> None:
        """Register an MCP server's tools in the tool registry."""
        if not self.tool_registry:
            return

        from vessels.knowledge.schema import ToolTrustLevel, ToolCostModel

        # Map MCP trust/cost to tool registry enums
        trust_map = {
            "verified": ToolTrustLevel.VERIFIED,
            "community": ToolTrustLevel.COMMUNITY,
            "unknown": ToolTrustLevel.UNKNOWN,
            "untrusted": ToolTrustLevel.UNTRUSTED,
        }
        cost_map = {
            "free": ToolCostModel.FREE,
            "free_tier": ToolCostModel.FREE_TIER,
            "per_call": ToolCostModel.PER_CALL,
            "subscription": ToolCostModel.SUBSCRIPTION,
            "unknown": ToolCostModel.UNKNOWN,
        }

        trust_level = trust_map.get(server.trust_level.value, ToolTrustLevel.UNKNOWN)
        cost_model = cost_map.get(server.cost_model.value, ToolCostModel.UNKNOWN)

        # Create tool definitions for each tool the server provides
        tools_to_register = []
        for tool_name in server.tools_provided:
            tools_to_register.append({
                "name": tool_name,
                "description": f"{tool_name} from {server.name}",
                "capabilities": server.capabilities,
                "problems_it_solves": server.problems_it_solves,
                "domains": server.domains,
                "recommended_for": server.recommended_for,
            })

        # Register via tool registry
        self.tool_registry.register_mcp_tools(
            server_id=server.server_id,
            server_name=server.name,
            tools=tools_to_register,
            trust_level=trust_level,
            cost_model=cost_model,
        )

        logger.info(
            f"Registered {len(tools_to_register)} tools from MCP server "
            f"'{server.name}' in tool registry"
        )

    def _birth_mcp_ambassador(self, server) -> Optional[Dict[str, Any]]:
        """
        Birth an ambassador vessel for an MCP server.

        Each MCP server gets a personified ambassador that can be talked to.
        The ambassador explains capabilities, helps use tools, and makes
        the MCP ecosystem conversational.

        Args:
            server: MCPServerInfo object

        Returns:
            Ambassador info dict or None if failed
        """
        if not self.ambassador_factory:
            logger.warning("Ambassador factory not initialized, cannot birth ambassador")
            return None

        try:
            # Create the ambassador through the factory
            ambassador = self.ambassador_factory.create_ambassador(
                server_id=server.server_id,
                server_name=server.name,
                description=server.description,
                capabilities=server.capabilities,
                tools_provided=server.tools_provided,
                problems_it_solves=server.problems_it_solves,
                domains=server.domains,
            )

            # Track the ambassador
            self.mcp_ambassadors[server.server_id] = ambassador

            logger.info(
                f"Birthed ambassador '{ambassador.persona.friendly_name}' "
                f"({ambassador.persona.emoji}) for MCP server '{server.name}'"
            )

            return ambassador.to_dict()

        except Exception as e:
            logger.error(f"Failed to birth ambassador for {server.name}: {e}")
            return None

    # =========================================================================
    # MCP AMBASSADOR API - Talk to your MCP servers
    # =========================================================================

    def talk_to_ambassador(
        self,
        server_id: str,
        message: str,
    ) -> Dict[str, Any]:
        """
        Have a conversation with an MCP server's ambassador.

        Instead of reading docs, just ask the ambassador!

        Args:
            server_id: ID of the MCP server
            message: Your message/question

        Returns:
            Dict with ambassador's response
        """
        if server_id not in self.mcp_ambassadors:
            # Try to find ambassador by friendly name
            ambassador = self._find_ambassador_by_name(message)
            if ambassador:
                server_id = ambassador.persona.server_id
            else:
                return {
                    "success": False,
                    "error": f"No ambassador found for '{server_id}'",
                    "available_ambassadors": self.list_ambassadors(),
                }

        if not self.ambassador_factory:
            return {
                "success": False,
                "error": "Ambassador factory not initialized",
            }

        response = self.ambassador_factory.converse(server_id, message)
        ambassador = self.mcp_ambassadors[server_id]

        return {
            "success": True,
            "ambassador": ambassador.persona.friendly_name,
            "emoji": ambassador.persona.emoji,
            "response": response,
            "server_id": server_id,
        }

    def _find_ambassador_by_name(self, name: str) -> Optional[Any]:
        """Find an ambassador by friendly name or address."""
        if not self.ambassador_factory:
            return None
        return self.ambassador_factory.get_ambassador_by_name(name)

    def get_ambassador(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get info about a specific ambassador."""
        ambassador = self.mcp_ambassadors.get(server_id)
        if ambassador:
            return ambassador.to_dict()
        return None

    def get_ambassador_intro(self, server_id: str) -> str:
        """Get an ambassador's self-introduction."""
        if not self.ambassador_factory:
            return "Ambassador system not available"
        return self.ambassador_factory.get_ambassador_intro(server_id)

    def list_ambassadors(self) -> List[Dict[str, Any]]:
        """List all MCP ambassadors."""
        results = []
        for server_id, ambassador in self.mcp_ambassadors.items():
            results.append({
                "server_id": server_id,
                "ambassador_id": ambassador.ambassador_id,
                "friendly_name": ambassador.persona.friendly_name,
                "emoji": ambassador.persona.emoji,
                "self_intro": ambassador.persona.self_intro,
                "capabilities": ambassador.persona.capabilities[:3],
            })
        return results

    def meet_ambassadors(self) -> str:
        """
        Get a friendly introduction to all ambassadors.

        Great for first-time users to see what's available.
        """
        if not self.ambassador_factory:
            return "Ambassador system not available"
        return self.ambassador_factory.list_ambassador_intros()

    def ask_ambassador_about_tool(
        self,
        server_id: str,
        tool_name: str,
    ) -> Dict[str, Any]:
        """
        Ask an ambassador to explain how to use a specific tool.

        Args:
            server_id: ID of the MCP server
            tool_name: Name of the tool to explain

        Returns:
            Dict with explanation
        """
        if server_id not in self.mcp_ambassadors:
            return {
                "success": False,
                "error": f"No ambassador for '{server_id}'",
            }

        if not self.ambassador_factory:
            return {
                "success": False,
                "error": "Ambassador factory not initialized",
            }

        ambassador = self.mcp_ambassadors[server_id]

        # Get tool info if available
        tool_description = ""
        tool_params = None

        if self.mcp_explorer:
            server = self.mcp_explorer.get_server(server_id)
            if server and tool_name in server.tools_provided:
                tool_description = f"Tool from {server.name}"

        explanation = self.ambassador_factory.explain_tool(
            server_id=server_id,
            tool_name=tool_name,
            tool_description=tool_description,
            tool_params=tool_params,
        )

        return {
            "success": True,
            "ambassador": ambassador.persona.friendly_name,
            "tool_name": tool_name,
            "explanation": explanation,
        }

    def find_ambassador_for_need(
        self,
        need: str,
    ) -> Dict[str, Any]:
        """
        Find which ambassador can help with a specific need.

        Args:
            need: Natural language description of what you need

        Returns:
            Dict with recommended ambassador and reasoning
        """
        if not self.mcp_ambassadors:
            return {
                "success": False,
                "error": "No ambassadors available",
            }

        # Score each ambassador
        scores = []
        need_lower = need.lower()

        for server_id, ambassador in self.mcp_ambassadors.items():
            score = 0
            persona = ambassador.persona

            # Check capabilities
            for cap in persona.capabilities:
                if cap.lower() in need_lower or need_lower in cap.lower():
                    score += 2

            # Check problems it solves
            for problem in persona.problems_it_solves:
                if any(word in need_lower for word in problem.lower().split()):
                    score += 3

            # Check domains
            for domain in persona.domains:
                if domain.lower() in need_lower:
                    score += 1

            if score > 0:
                scores.append((server_id, ambassador, score))

        if not scores:
            return {
                "success": False,
                "error": f"No ambassador found for need: {need}",
                "available_ambassadors": self.list_ambassadors(),
            }

        # Sort by score
        scores.sort(key=lambda x: x[2], reverse=True)

        best = scores[0]
        ambassador = best[1]

        return {
            "success": True,
            "server_id": best[0],
            "ambassador": ambassador.persona.friendly_name,
            "emoji": ambassador.persona.emoji,
            "intro": ambassador.persona.self_intro,
            "confidence": min(best[2] / 6, 1.0),  # Normalize score
            "alternatives": [
                {
                    "server_id": s[0],
                    "ambassador": s[1].persona.friendly_name,
                    "emoji": s[1].persona.emoji,
                }
                for s in scores[1:3]  # Top 2 alternatives
            ],
        }

    # =========================================================================
    # A2A PROTOCOL - Agent-to-Agent Communication
    # Implements Google's A2A protocol for vessel interoperability
    # =========================================================================

    def delegate_to_vessel(
        self,
        target_vessel_id: str,
        request: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Delegate a task to another vessel using A2A protocol.

        This enables vessel-to-vessel collaboration where one vessel
        can ask another for help.

        Args:
            target_vessel_id: ID of the vessel to delegate to
            request: Natural language task request
            context: Optional context data

        Returns:
            Dict with task info and status
        """
        if not self.a2a_service:
            self._initialize_a2a()

        if not self.a2a_service:
            return {
                "success": False,
                "error": "A2A Protocol not available",
            }

        # Create task
        task = self.a2a_service.delegate_task(
            target_agent_id=target_vessel_id,
            request=request,
            context=context,
        )

        logger.info(f"Delegated task to vessel {target_vessel_id}: {task.task_id[:8]}...")

        return {
            "success": True,
            "task_id": task.task_id,
            "target_vessel_id": target_vessel_id,
            "state": task.state.value,
            "request": request,
        }

    def find_vessel_for_task(
        self,
        task_description: str,
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Find a vessel that can handle a specific task.

        Uses A2A discovery to find vessels with matching capabilities.

        Args:
            task_description: What needs to be done
            domains: Optional domain filters

        Returns:
            Dict with recommended vessel and alternatives
        """
        if not self.a2a_discovery:
            return {
                "success": False,
                "error": "A2A Discovery not available",
                "recommendations": [],
            }

        # Find matching agents
        matches = self.a2a_discovery.find_for_need(
            need=task_description,
            domains=domains,
            limit=5,
        )

        if not matches:
            return {
                "success": False,
                "error": f"No vessels found for: {task_description}",
                "recommendations": [],
            }

        # Format results
        recommendations = []
        for card in matches:
            recommendations.append({
                "vessel_id": card.vessel_id,
                "name": card.name,
                "description": card.description,
                "skills": [s.name for s in card.skills[:3]],
                "domains": card.domains,
            })

        return {
            "success": True,
            "best_match": recommendations[0] if recommendations else None,
            "recommendations": recommendations,
            "query": task_description,
        }

    def open_vessel_channel(
        self,
        from_vessel_id: str,
        to_vessel_id: str,
    ) -> Dict[str, Any]:
        """
        Open a direct communication channel between two vessels.

        Channels enable ongoing conversations without creating
        new tasks for each message.

        Args:
            from_vessel_id: Source vessel
            to_vessel_id: Target vessel

        Returns:
            Dict with channel info
        """
        if not self.a2a_service:
            return {
                "success": False,
                "error": "A2A Protocol not available",
            }

        # Get target's agent card if known
        target_card = None
        if self.a2a_registry:
            entry = self.a2a_registry.get(to_vessel_id)
            if entry:
                target_card = entry.agent_card

        channel = self.a2a_service.open_channel(
            remote_agent_id=to_vessel_id,
            remote_agent_card=target_card,
        )

        logger.info(f"Opened A2A channel {channel.channel_id[:8]}... between vessels")

        return {
            "success": True,
            "channel_id": channel.channel_id,
            "from_vessel_id": from_vessel_id,
            "to_vessel_id": to_vessel_id,
        }

    def send_vessel_message(
        self,
        channel_id: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a message on a vessel communication channel.

        Args:
            channel_id: ID of the channel
            message: Message text
            data: Optional structured data

        Returns:
            Dict with message status
        """
        if not self.a2a_service:
            return {
                "success": False,
                "error": "A2A Protocol not available",
            }

        msg = self.a2a_service.send_message(channel_id, message, data)

        if msg:
            return {
                "success": True,
                "message_id": msg.message_id,
                "channel_id": channel_id,
            }
        else:
            return {
                "success": False,
                "error": f"Failed to send message on channel {channel_id}",
            }

    def get_vessel_agent_card(self, vessel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the A2A Agent Card for a vessel.

        Agent Cards describe a vessel's identity and capabilities
        in a standard format for interoperability.

        Args:
            vessel_id: ID of the vessel

        Returns:
            Agent Card as dictionary, or None if not found
        """
        if not self.vessel_registry:
            return None

        vessel = self.vessel_registry.get_vessel(vessel_id)
        if not vessel:
            return None

        # Generate Agent Card from vessel
        from vessels.a2a.discovery import vessel_to_agent_card
        card = vessel_to_agent_card(vessel)

        return card.to_dict()

    def register_vessel_for_discovery(self, vessel_id: str) -> Dict[str, Any]:
        """
        Register a vessel in the A2A discovery system.

        Makes the vessel discoverable by other vessels that need
        its capabilities.

        Args:
            vessel_id: ID of the vessel to register

        Returns:
            Registration status
        """
        if not self.vessel_registry:
            return {
                "success": False,
                "error": "Vessel registry not available",
            }

        if not self.a2a_registry:
            return {
                "success": False,
                "error": "A2A registry not available",
            }

        vessel = self.vessel_registry.get_vessel(vessel_id)
        if not vessel:
            return {
                "success": False,
                "error": f"Vessel {vessel_id} not found",
            }

        # Generate Agent Card
        from vessels.a2a.discovery import vessel_to_agent_card
        card = vessel_to_agent_card(vessel)

        # Register in A2A registry
        entry = self.a2a_registry.register(card)

        # Also register in A2A service for coordination
        if self.a2a_service:
            self.a2a_service.register_known_agent(card)

        logger.info(f"Registered vessel {vessel.name} for A2A discovery")

        return {
            "success": True,
            "vessel_id": vessel_id,
            "agent_id": card.agent_id,
            "skills": [s.name for s in card.skills],
            "discoverable": True,
        }

    def discover_external_agents(
        self,
        domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Discover external A2A-compatible agents.

        Searches via Nostr network and known URIs for agents
        that can collaborate with Vessels.

        Args:
            domains: Optional domain filters

        Returns:
            Dict with discovered agents
        """
        if not self.a2a_discovery:
            return {
                "success": False,
                "error": "A2A Discovery not available",
                "agents": [],
            }

        # Trigger Nostr discovery
        self.a2a_discovery.discover_from_nostr(domains=domains)

        # Return currently known agents
        known = self.a2a_discovery.get_all_known()

        return {
            "success": True,
            "agents": [
                {
                    "agent_id": card.agent_id,
                    "name": card.name,
                    "description": card.description,
                    "vessel_id": card.vessel_id,
                    "domains": card.domains,
                    "external": card.vessel_id is None,
                }
                for card in known
            ],
            "total": len(known),
        }

    def get_a2a_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an A2A task."""
        if not self.a2a_service:
            return None

        task = self.a2a_service.get_task(task_id)
        if task:
            return task.to_dict()
        return None

    def list_a2a_tasks(
        self,
        vessel_id: Optional[str] = None,
        state: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List A2A tasks, optionally filtered by vessel or state."""
        if not self.a2a_service:
            return []

        from vessels.a2a import TaskState

        task_state = TaskState(state) if state else None
        tasks = self.a2a_service.list_tasks(state=task_state, agent_id=vessel_id)

        return [t.to_dict() for t in tasks]

    def get_a2a_stats(self) -> Dict[str, Any]:
        """Get A2A protocol statistics."""
        stats = {
            "enabled": self.a2a_service is not None,
            "registered_agents": 0,
            "active_tasks": 0,
            "open_channels": 0,
        }

        if self.a2a_registry:
            stats["registered_agents"] = self.a2a_registry.count()

        if self.a2a_service:
            service_stats = self.a2a_service.to_dict()
            stats["active_tasks"] = service_stats.get("activeTasks", 0)
            stats["open_channels"] = service_stats.get("openChannels", 0)

        return stats

    # =========================================================================
    # TOOL REGISTRY - Graph-based tool management
    # All tools are data in the knowledge graph, not hardcoded
    # =========================================================================

    def register_tool(
        self,
        name: str,
        description: str,
        capabilities: List[str],
        problems_it_solves: Optional[List[str]] = None,
        domains: Optional[List[str]] = None,
        recommended_for: Optional[List[str]] = None,
        provider_type: str = "custom",
        implementation: Optional[Callable] = None,
    ) -> str:
        """
        Register a tool in A0's tool registry.

        Tools become queryable in the knowledge graph - A0 finds them
        semantically when agents need capabilities.

        Args:
            name: Tool name
            description: What the tool does
            capabilities: High-level capabilities ["scheduling", "communication"]
            problems_it_solves: Natural language problems ["need to send email"]
            domains: Relevant domains ["business", "agriculture"]
            recommended_for: Vessel types this is good for
            provider_type: "native", "mcp", "custom", "vessel"
            implementation: Optional callable for custom tools

        Returns:
            Tool ID
        """
        if not self.tool_registry:
            self._initialize_tool_registry()

        if not self.tool_registry:
            raise RuntimeError("Tool Registry not available")

        from vessels.core.tool_registry import ToolDefinition
        from vessels.knowledge.schema import ToolProviderType, ToolTrustLevel, ToolCostModel

        tool = ToolDefinition(
            tool_id=f"{provider_type}_{name.lower().replace(' ', '_')}",
            name=name,
            description=description,
            capabilities=capabilities,
            problems_it_solves=problems_it_solves or [],
            domains=domains or [],
            recommended_for=recommended_for or [],
            provider_type=ToolProviderType(provider_type),
            trust_level=ToolTrustLevel.COMMUNITY,
            cost_model=ToolCostModel.FREE,
            implementation=implementation,
        )

        tool_id = self.tool_registry.register_tool(tool)

        if implementation:
            self.tool_registry.register_implementation(tool_id, implementation)

        logger.info(f"A0 registered tool: {name} ({tool_id})")
        return tool_id

    def find_tools_for_purpose(
        self,
        purpose: str,
        vessel_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find tools that would help with a purpose.

        Uses semantic search through the tool registry - no hardcoded mappings.

        Args:
            purpose: What the agent/vessel needs to do
            vessel_type: Type of vessel for better matching

        Returns:
            List of matching tools with scores
        """
        if not self.tool_registry:
            return []

        return self.tool_registry.find_tools_for_need(
            capability_need=purpose,
            vessel_type=vessel_type,
            max_results=10,
        )

    def get_vessel_tools(self, vessel_id: str) -> List[str]:
        """
        Get all tools available to a vessel.

        Combines:
        - Tools bound directly to vessel
        - Tools from connected MCP servers
        - Native tools

        Args:
            vessel_id: Vessel to get tools for

        Returns:
            List of tool IDs
        """
        tools = set()

        # Tools from registry binding
        if self.tool_registry:
            tools.update(self.tool_registry.get_vessel_tool_ids(vessel_id))

        # MCP tools
        if self.mcp_explorer:
            mcp_tools = self.mcp_explorer.get_vessel_tools(vessel_id)
            tools.update(mcp_tools)

        return list(tools)

    def bind_tool_to_vessel(self, vessel_id: str, tool_id: str) -> bool:
        """Bind a tool to a vessel."""
        if not self.tool_registry:
            return False
        return self.tool_registry.bind_tool_to_vessel(vessel_id, tool_id)

    def get_tool_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        if self.tool_registry:
            return self.tool_registry.get_stats()
        return {"error": "Tool Registry not initialized"}

    # =========================================================================
    # END UNIVERSAL BUILDER METHODS
    # =========================================================================

    def interpret_community_needs(self, need_description: str) -> List[AgentSpecification]:
        """Interpret natural language community needs into agent specifications"""
        
        # Parse the need description and determine required capabilities
        needs_analysis = self._analyze_community_needs(need_description)
        
        # Generate appropriate agent specifications
        agents_needed = []
        
        if "grant" in need_description.lower() or "funding" in need_description.lower():
            agents_needed.extend(self._create_grant_management_agents())
            
        if "coordinate" in need_description.lower() or "volunteer" in need_description.lower():
            agents_needed.extend(self._create_coordination_agents())
            
        if "elder" in need_description.lower() or "care" in need_description.lower():
            agents_needed.extend(self._create_elder_care_agents())
            
        # Always include general coordination agents
        agents_needed.extend(self._create_general_coordination_agents())
        
        return agents_needed
    
    def _analyze_community_needs(self, description: str) -> Dict[str, Any]:
        """Analyze community needs from description"""
        analysis = {
            "primary_focus": "",
            "secondary_needs": [],
            "urgency_level": "medium",
            "target_population": "",
            "geographic_area": "",
            "resource_requirements": [],
            "coordination_complexity": "medium"
        }
        
        # Simple but effective need analysis
        desc_lower = description.lower()
        
        if "elder" in desc_lower or "senior" in desc_lower:
            analysis["primary_focus"] = "elder_care"
            analysis["target_population"] = "elderly"
            
        if "grant" in desc_lower or "funding" in desc_lower:
            analysis["primary_focus"] = "grant_management"
            analysis["resource_requirements"].append("funding")
            
        if "puna" in desc_lower or "hawaii" in desc_lower:
            analysis["geographic_area"] = "puna_hawaii"
            
        if "urgent" in desc_lower or "emergency" in desc_lower:
            analysis["urgency_level"] = "high"
            
        return analysis
    
    def _create_grant_management_agents(self) -> List[AgentSpecification]:
        """Create grant management agent specifications"""
        return [
            AgentSpecification(
                name="GrantFinder",
                description="Discovers and analyzes grant opportunities",
                capabilities=["web_search", "data_analysis", "opportunity_matching"],
                tools_needed=["web_scraper", "search_engine", "database_query"],
                specialization="grant_discovery"
            ),
            AgentSpecification(
                name="GrantWriter",
                description="Writes complete grant applications automatically",
                capabilities=["document_generation", "compliance_checking", "narrative_writing"],
                tools_needed=["document_generator", "template_system", "compliance_checker"],
                specialization="grant_writing"
            ),
            AgentSpecification(
                name="GrantTracker",
                description="Tracks grant applications and manages deadlines",
                capabilities=["deadline_management", "status_tracking", "report_generation"],
                tools_needed=["calendar_system", "notification_system", "report_generator"],
                specialization="grant_tracking"
            )
        ]
    
    def _create_coordination_agents(self) -> List[AgentSpecification]:
        """Create coordination agent specifications"""
        return [
            AgentSpecification(
                name="CommunityCoordinator",
                description="Coordinates community activities and resources",
                capabilities=["resource_allocation", "scheduling", "communication"],
                tools_needed=["calendar_system", "messaging_system", "resource_tracker"],
                specialization="community_coordination"
            ),
            AgentSpecification(
                name="VolunteerManager",
                description="Manages volunteer recruitment and coordination",
                capabilities=["volunteer_matching", "task_assignment", "progress_tracking"],
                tools_needed=["volunteer_database", "task_manager", "communication_hub"],
                specialization="volunteer_management"
            )
        ]
    
    def _create_elder_care_agents(self) -> List[AgentSpecification]:
        """Create elder care specific agents"""
        return [
            AgentSpecification(
                name="ElderCareSpecialist",
                description="Specializes in elder care program development",
                capabilities=["needs_assessment", "program_design", "care_coordination"],
                tools_needed=["assessment_tools", "program_templates", "care_tracker"],
                specialization="elder_care"
            ),
            AgentSpecification(
                name="ResourceNavigator",
                description="Navigates community resources for elder care",
                capabilities=["resource_mapping", "benefit_calculation", "service_coordination"],
                tools_needed=["resource_database", "benefits_calculator", "service_directory"],
                specialization="resource_navigation"
            )
        ]
    
    def _create_general_coordination_agents(self) -> List[AgentSpecification]:
        """Create general coordination agents"""
        return [
            AgentSpecification(
                name="SystemOrchestrator",
                description="Orchestrates all agents and coordinates system-wide activities",
                capabilities=["orchestration", "monitoring", "optimization"],
                tools_needed=["monitoring_system", "performance_analyzer", "resource_manager"],
                specialization="system_orchestration",
                autonomy_level="full"
            ),
            AgentSpecification(
                name="CommunicationHub",
                description="Manages all inter-agent communication",
                capabilities=["message_routing", "protocol_management", "conflict_resolution"],
                tools_needed=["message_bus", "routing_system", "conflict_resolver"],
                specialization="communication"
            )
        ]
    
    def spawn_agents(self, specifications: List[AgentSpecification],
                     vessel_id: Optional[str] = None, **kwargs) -> List[str]:
        """
        Spawn agents from specifications within a vessel.

        Args:
            specifications: List of agent specifications to spawn
            vessel_id: ID of vessel to spawn agents in (vessel-native mode)
            **kwargs: Additional parameters for agent spawning

        Returns:
            List of spawned agent IDs

        Raises:
            ValueError: If vessel_id provided but vessel not found in registry
        """
        # Get vessel if vessel_id provided
        vessel = None
        if vessel_id:
            if not self.vessel_registry:
                raise ValueError("vessel_id provided but no vessel_registry configured")
            vessel = self.vessel_registry.get_vessel(vessel_id)
            if not vessel:
                raise ValueError(f"Vessel {vessel_id} not found in registry")

        spawned_ids = []
        for spec in specifications:
            agent_id = self._spawn_agent(spec, vessel=vessel, **kwargs)
            spawned_ids.append(agent_id)

        logger.info(f"Spawned {len(spawned_ids)} agents" +
                   (f" in vessel {vessel_id}" if vessel_id else ""))
        return spawned_ids
    
    def _spawn_agent(self, specification: AgentSpecification,
                     vessel: Optional[Any] = None, **kwargs) -> str:
        """
        Spawn a single agent with vessel-scoped resources.

        Args:
            specification: Agent specification
            vessel: Optional Vessel instance providing scoped resources
            **kwargs: Additional parameters

        Returns:
            Agent ID
        """
        agent_id = str(uuid.uuid4())

        # Determine resource sources: vessel or fallback
        action_gate = vessel.action_gate if vessel else self.gate
        memory_backend = vessel.memory_backend if vessel else self.memory_system
        vessel_id = vessel.vessel_id if vessel else None

        # Create agent instance with vessel-scoped resources
        agent = AgentInstance(
            id=agent_id,
            specification=specification,
            status=AgentStatus.IDLE,
            created_at=datetime.now(),
            last_active=datetime.now(),
            vessel_id=vessel_id,
            action_gate=action_gate,
            memory_backend=memory_backend
        )

        # Assign tools based on specification and vessel
        if vessel and vessel.tools:
            # Resolve tools from vessel with permission checks
            agent.tools = self._resolve_vessel_tools(
                specification.tools_needed, vessel
            )
        else:
            # Fallback to legacy tool assignment
            agent.tools = self._assign_tools(specification.tools_needed)

        # Initialize agent memory namespace
        if memory_backend and hasattr(memory_backend, 'create_namespace'):
            # Create namespaced memory for this agent
            agent_memory = memory_backend.create_namespace(agent_id)
            agent.memory = agent_memory
        else:
            # Fallback to in-memory dict
            agent.memory = {
                "specification": specification,
                "interaction_history": [],
                "learned_patterns": [],
                "active_tasks": []
            }

        self.agents[agent_id] = agent
        self.agent_specifications[agent_id] = specification

        # Start agent processing loop
        agent_thread = threading.Thread(
            target=self._agent_processing_loop, args=(agent_id,)
        )
        agent_thread.daemon = True
        agent_thread.start()

        logger.info(
            f"Spawned agent {specification.name} with ID {agent_id}" +
            (f" in vessel {vessel_id}" if vessel_id else "")
        )
        return agent_id

    def _resolve_vessel_tools(self, tools_needed: List[str],
                             vessel: Any) -> List[str]:
        """
        Resolve tool names to vessel-scoped implementations.

        Args:
            tools_needed: List of tool names from specification
            vessel: Vessel instance with tool bindings

        Returns:
            List of resolved tool identifiers
        """
        resolved = []
        for tool_name in tools_needed:
            tool_impl = vessel.get_tool(tool_name)
            if tool_impl:
                resolved.append(tool_name)
            else:
                logger.warning(
                    f"Tool '{tool_name}' not found in vessel {vessel.vessel_id}"
                )
        return resolved
    
    def _assign_tools(self, tools_needed: List[str]) -> List[str]:
        """
        Assign tools to an agent using the Tool Registry.

        Queries the knowledge graph semantically - no hardcoded mappings!
        """
        if not self.tool_registry:
            # Fallback if registry not initialized
            logger.warning("Tool Registry not available, returning empty tool list")
            return []

        assigned_tools = []

        for tool_need in tools_needed:
            # Query registry for tools matching this need
            matches = self.tool_registry.find_tools_for_need(
                capability_need=tool_need,
                max_results=1,
            )

            if matches:
                best_match = matches[0]
                assigned_tools.append(best_match["tool_id"])
                logger.debug(f"Assigned tool '{best_match['tool_id']}' for need '{tool_need}'")
            else:
                # No exact match - try semantic search with the tool need as description
                semantic_matches = self.tool_registry.find_tools_for_purpose(tool_need)
                if semantic_matches:
                    assigned_tools.extend(semantic_matches[:2])  # Top 2 semantic matches
                else:
                    logger.warning(f"No tools found for need: {tool_need}")

        return list(set(assigned_tools))  # Dedupe
    
    def _agent_processing_loop(self, agent_id: str):
        """
        Main processing loop for each agent.

        Uses vessel-injected memory backend if available, otherwise falls back
        to legacy memory system.
        """
        agent = self.agents[agent_id]

        while self.running:
            try:
                # Check for messages
                if not agent.message_queue.empty():
                    message = agent.message_queue.get_nowait()
                    self._process_agent_message(agent_id, message)

                # Process active tasks
                active_tasks = None
                if isinstance(agent.memory, dict):
                    active_tasks = agent.memory.get("active_tasks")
                elif hasattr(agent.memory, 'get_active_tasks'):
                    active_tasks = agent.memory.get_active_tasks()

                if active_tasks:
                    agent.status = AgentStatus.PROCESSING
                    self._process_agent_tasks(agent_id)
                    agent.last_active = datetime.now()
                else:
                    agent.status = AgentStatus.IDLE

                # Share learnings with memory backend (vessel-native or legacy)
                memory_backend = agent.memory_backend or self.memory_system
                learned_patterns = None

                if isinstance(agent.memory, dict):
                    learned_patterns = agent.memory.get("learned_patterns", [])
                elif hasattr(agent.memory, 'get_learned_patterns'):
                    learned_patterns = agent.memory.get_learned_patterns()

                if memory_backend and learned_patterns:
                    if hasattr(memory_backend, 'store_experience'):
                        memory_backend.store_experience(
                            agent_id, learned_patterns
                        )
                    # Clear learned patterns after storing
                    if isinstance(agent.memory, dict):
                        agent.memory["learned_patterns"] = []
                    elif hasattr(agent.memory, 'clear_learned_patterns'):
                        agent.memory.clear_learned_patterns()

            except Exception as e:
                logger.error(f"Agent {agent_id} processing error: {e}")
                agent.status = AgentStatus.ERROR

            threading.Event().wait(1)  # Brief pause
    
    def _process_agent_message(self, agent_id: str, message: Dict[str, Any]):
        """Process message for specific agent"""
        agent = self.agents[agent_id]
        
        if message.get("type") == "task":
            agent.memory["active_tasks"].append(message.get("content"))
            
        elif message.get("type") == "query":
            response = self._generate_agent_response(agent_id, message.get("content"))
            self.send_message(message.get("sender_id"), {
                "type": "response",
                "content": response,
                "sender_id": agent_id
            })
    
    def _process_agent_tasks(self, agent_id: str):
        """Process active tasks for agent"""
        agent = self.agents[agent_id]
        
        if agent.memory["active_tasks"]:
            task = agent.memory["active_tasks"].pop(0)
            
            # Execute task based on agent specialization
            result = self._execute_agent_task(agent_id, task)
            
            # Store result and learning
            agent.memory["interaction_history"].append({
                "task": task,
                "result": result,
                "timestamp": datetime.now()
            })
            
            agent.memory["learned_patterns"].append({
                "task_type": task.get("type"),
                "success": result.get("success", False),
                "approach": result.get("approach", "")
            })
    
    def _execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific task for agent"""
        agent = self.agents[agent_id]
        spec = agent.specification
        
        result = {"success": False, "approach": spec.specialization}
        
        try:
            if spec.specialization == "grant_discovery":
                result = self._execute_grant_discovery_task(task)
            elif spec.specialization == "grant_writing":
                result = self._execute_grant_writing_task(task)
            elif spec.specialization == "community_coordination":
                result = self._execute_coordination_task(task)
            elif spec.specialization == "elder_care":
                result = self._execute_elder_care_task(task)
            else:
                result = self._execute_general_task(task)
                
        except Exception as e:
            logger.error(f"Task execution error for agent {agent_id}: {e}")
            result["error"] = str(e)
            
        return result
    
    def _execute_grant_discovery_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grant discovery task"""
        # This would integrate with the grant coordination system
        return {
            "success": True,
            "discovered_grants": [
                {"title": "Elder Care Innovation Grant", "amount": "$50,000", "deadline": "2025-12-15"},
                {"title": "Community Health Initiative", "amount": "$25,000", "deadline": "2025-11-30"}
            ],
            "approach": "web_search_and_analysis"
        }
    
    def _execute_grant_writing_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute grant writing task"""
        return {
            "success": True,
            "application_draft": "Generated comprehensive grant application...",
            "compliance_score": 0.95,
            "approach": "template_based_generation"
        }
    
    def _execute_coordination_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute coordination task"""
        return {
            "success": True,
            "coordination_plan": "Generated community coordination strategy...",
            "resource_allocation": "Optimized resource distribution...",
            "approach": "collaborative_planning"
        }
    
    def _execute_elder_care_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute elder care task"""
        return {
            "success": True,
            "care_plan": "Generated elder care program framework...",
            "resource_needs": "Identified required resources...",
            "approach": "needs_based_design"
        }
    
    def _execute_general_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general task"""
        return {
            "success": True,
            "task_result": f"Completed task: {task}",
            "approach": "general_processing"
        }
    
    def _generate_agent_response(self, agent_id: str, query: str) -> str:
        """Generate response from agent based on query"""
        agent = self.agents[agent_id]
        spec = agent.specification
        
        return f"Agent {spec.name} ({spec.specialization}) received query: {query}"
    
    def send_message(self, agent_id: str, message: Dict[str, Any]):
        """Send message to specific agent"""
        if agent_id in self.agents:
            self.agents[agent_id].message_queue.put(message)
    
    def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all agents"""
        for agent_id in self.agents:
            self.send_message(agent_id, message)
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            return {
                "id": agent.id,
                "name": agent.specification.name,
                "status": agent.status.value,
                "specialization": agent.specification.specialization,
                "last_active": agent.last_active.isoformat(),
                "active_tasks": len(agent.memory.get("active_tasks", [])),
                "tools": agent.tools
            }
        return None
    
    def get_all_agents_status(self) -> List[Dict[str, Any]]:
        """Get status of all agents"""
        return [self.get_agent_status(agent_id) for agent_id in self.agents]
    
    def _coordination_loop(self):
        """Main coordination system loop"""
        while self.running:
            try:
                # Monitor agent health
                self._monitor_agents()
                
                # Optimize agent connections
                self._optimize_connections()
                
                # Handle system-level tasks
                self._handle_system_tasks()
                
            except Exception as e:
                logger.error(f"Coordination loop error: {e}")
                
            threading.Event().wait(5)  # Coordination interval
    
    def _monitor_agents(self):
        """Monitor agent health and performance"""
        for agent_id, agent in self.agents.items():
            # Check if agent is responsive
            time_since_active = (datetime.now() - agent.last_active).seconds
            
            if time_since_active > 300 and agent.status != AgentStatus.IDLE:  # 5 minutes
                logger.warning(f"Agent {agent_id} may be unresponsive")
                
            # Restart agents in error state
            if agent.status == AgentStatus.ERROR:
                logger.info(f"Restarting agent {agent_id}")
                agent.status = AgentStatus.IDLE
    
    def _optimize_connections(self):
        """Optimize agent connections based on workload"""
        # Simple connection optimization
        for agent_id, agent in self.agents.items():
            # Connect agents with complementary specializations
            for other_id, other_agent in self.agents.items():
                if agent_id != other_id:
                    if (agent.specification.specialization != other_agent.specification.specialization and
                        other_id not in agent.connections):
                        agent.connections.append(other_id)
    
    def _handle_system_tasks(self):
        """Handle system-level coordination tasks"""
        # Distribute workload among agents
        active_agents = [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]
        idle_agents = [a for a in self.agents.values() if a.status == AgentStatus.IDLE]
        
        # Balance load if needed
        if len(active_agents) > len(idle_agents) * 2:
            # Redistribute tasks to idle agents
            for agent in idle_agents[:2]:  # Activate up to 2 idle agents
                agent.status = AgentStatus.ACTIVE
    
    def execute_gated_action(
        self,
        agent_id: str,
        action: Any,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an action through the gate with consultation support.

        Uses the agent's vessel-scoped action gate if available, otherwise
        falls back to the global gate.

        Args:
            agent_id: ID of the agent attempting the action
            action: The action to execute
            action_metadata: Optional metadata about the action

        Returns:
            Dictionary with execution result
        """
        if agent_id not in self.agents:
            return {
                "success": False,
                "error": f"Agent {agent_id} not found"
            }

        agent = self.agents[agent_id]

        # Use vessel-scoped action gate if available, otherwise global gate
        action_gate = agent.action_gate or self.gate

        # If no gate is configured, execute directly
        if not action_gate:
            logger.warning(
                f"No gate configured for agent {agent_id}, "
                "executing action without gating"
            )
            result = self._execute_agent_task(
                agent_id, {"type": "action", "action": action}
            )
            return {"success": result.get("success", False), "result": result}

        # Gate the action using vessel-scoped or global gate
        gate_result = action_gate.gate_action(agent_id, action, action_metadata)

        if not gate_result.allowed:
            # Check if this is a consultation request
            if gate_result.meta.get("type") == "CONSULTATION_REQUIRED":
                # Extract the consultation request
                consultation_req = gate_result.meta["consultation_request"]

                # Store consultation in agent
                agent.active_consultation = consultation_req

                # Trigger the UI/Interface
                if self.interface and self.consensus_engine:
                    prompt = self.consensus_engine.initiate_check_in(consultation_req)
                    self.send_message_to_user(agent_id, prompt)

                # Pause agent state
                agent.status = AgentStatus.PAUSED_FOR_CONSULTATION
                logger.info(f"Agent {agent_id} paused for consultation: {gate_result.reason}")

                return {
                    "success": False,
                    "blocked": True,
                    "reason": gate_result.reason,
                    "consultation_required": True,
                    "consultation_request": consultation_req
                }
            else:
                # Standard block
                logger.warning(f"Action blocked for agent {agent_id}: {gate_result.reason}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": gate_result.reason
                }

        # Action allowed - execute it
        result = self._execute_agent_task(agent_id, {"type": "action", "action": action})
        return {"success": result.get("success", False), "result": result}

    def send_message_to_user(self, agent_id: str, message: str):
        """
        Send a message to the user/interface.

        Args:
            agent_id: ID of the agent sending the message
            message: Message content
        """
        if self.interface:
            try:
                # If interface has a send_message method, use it
                if hasattr(self.interface, 'send_message'):
                    self.interface.send_message(agent_id, message)
                else:
                    logger.warning(f"Interface does not have send_message method")
                    print(f"\n[Agent {agent_id}]\n{message}\n")
            except Exception as e:
                logger.error(f"Error sending message to user: {e}")
                print(f"\n[Agent {agent_id}]\n{message}\n")
        else:
            # Fallback: print to console
            print(f"\n[Agent {agent_id}]\n{message}\n")

    def handle_consultation_response(
        self,
        agent_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Handle user response to a consultation request.

        Args:
            agent_id: ID of the agent in consultation
            user_response: User's response

        Returns:
            Dictionary with handling result
        """
        if agent_id not in self.agents:
            return {"success": False, "error": f"Agent {agent_id} not found"}

        agent = self.agents[agent_id]

        # Check if agent is in consultation mode
        if agent.status != AgentStatus.PAUSED_FOR_CONSULTATION:
            return {
                "success": False,
                "error": f"Agent {agent_id} is not in consultation mode"
            }

        if not agent.active_consultation:
            return {
                "success": False,
                "error": f"No active consultation for agent {agent_id}"
            }

        if not self.consensus_engine:
            return {
                "success": False,
                "error": "No consensus engine configured"
            }

        consultation_req = agent.active_consultation
        response_lower = user_response.lower()

        # Case A: User says "Use Precedent"
        if "precedent" in response_lower:
            if consultation_req.relevant_precedents:
                precedent = consultation_req.relevant_precedents[0]
                self.consensus_engine.resolve_consultation(
                    consultation_req.request_id,
                    resolution_summary=f"Applied precedent: {precedent.title}",
                    consensus_action=precedent.resolution_principle,
                    principle=precedent.resolution_principle,
                    store_as_parable=False
                )
                agent.status = AgentStatus.ACTIVE
                agent.active_consultation = None
                return {
                    "success": True,
                    "message": "Precedent applied. Resuming action.",
                    "action": "precedent_applied"
                }
            else:
                return {
                    "success": False,
                    "error": "No precedents available for this consultation"
                }

        # Case B: User says "Async"
        elif "async" in response_lower:
            self.consensus_engine.set_async_mode(consultation_req.request_id)
            agent.status = AgentStatus.WAITING_ASYNC
            return {
                "success": True,
                "message": "Understood. Switching to async mode.",
                "action": "async_mode"
            }

        # Case C: User provides a decision
        else:
            # Extract principle if provided (simple heuristic)
            principle = user_response if len(user_response) < 200 else "User guidance provided"

            self.consensus_engine.resolve_consultation(
                consultation_req.request_id,
                resolution_summary=user_response,
                consensus_action="Proceed based on user input",
                principle=principle
            )
            agent.status = AgentStatus.ACTIVE
            agent.active_consultation = None
            return {
                "success": True,
                "message": "Wisdom received. Action unblocked.",
                "action": "resolved"
            }

    def shutdown(self):
        """Shutdown the coordination system"""
        self.running = False
        if self.coordination_thread:
            self.coordination_thread.join(timeout=10)
        self.executor.shutdown(wait=True)
        logger.info("Agent Zero Core shutdown complete")

# Global instance for easy access
agent_zero = AgentZeroCore()