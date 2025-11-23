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
                 default_memory=None, default_tools=None):
        """
        Initialize AgentZeroCore.

        Args:
            vessel_registry: Optional VesselRegistry for vessel-native coordination
            default_memory: Fallback memory system (used if no vessel provided)
            default_tools: Fallback tool system (used if no vessel provided)
        """
        self.vessel_registry = vessel_registry
        self.agents: Dict[str, AgentInstance] = {}
        self.agent_specifications: Dict[str, AgentSpecification] = {}
        self.message_bus = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.running = False
        self.coordination_thread = None

        # Legacy fallback systems (used when no vessel is provided)
        self.system_memory = default_memory or {}
        self.memory_system = default_memory
        self.tool_system = default_tools
        self.gate = None  # Global gate (fallback, vessel gates preferred)

        # Village consensus and interface
        self.consensus_engine = None  # Village consensus engine (optional)
        self.interface = None  # Interface for sending messages to users
        
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
        logger.info("Agent Zero Core initialized")

    def set_vessel_registry(self, registry: Any) -> None:
        """
        Set or update the vessel registry.

        Args:
            registry: VesselRegistry instance for vessel-native coordination
        """
        self.vessel_registry = registry
        logger.info("Vessel registry configured for AgentZeroCore")
        
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
        """Assign available tools to agent"""
        available_tools = []
        
        # Map tool names to actual implementations
        tool_mapping = {
            "web_scraper": "web_scraping_tool",
            "search_engine": "search_tool",
            "document_generator": "document_generation_tool",
            "database_query": "database_tool",
            "calendar_system": "calendar_tool",
            "notification_system": "notification_tool",
            "compliance_checker": "compliance_tool",
            "template_system": "template_tool",
            "messaging_system": "messaging_tool",
            "resource_tracker": "resource_tool",
            "volunteer_database": "volunteer_tool",
            "task_manager": "task_tool",
            "assessment_tools": "assessment_tool",
            "program_templates": "program_tool",
            "care_tracker": "care_tool",
            "resource_database": "resource_db_tool",
            "benefits_calculator": "benefits_tool",
            "service_directory": "service_tool"
        }
        
        for tool in tools_needed:
            if tool in tool_mapping:
                available_tools.append(tool_mapping[tool])
                
        return available_tools
    
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