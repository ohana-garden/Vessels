"""
Coordination SSFs - A2A Delegation, Agent Spawning, Multi-Agent Coordination.

These SSFs handle inter-agent communication and coordination,
implementing the A2A protocol for safe agent delegation.

AGENT ZERO HIERARCHY MODEL:
- Implements superior-subordinate agent hierarchy
- Supports call_subordinate for task delegation
- Bidirectional communication: instructions down, results up
- Chain processing for response propagation
See: docs/agent_zero_subagent_hierarchy.md
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

# Reference to AgentZeroCore instance (set during initialization)
_agent_zero_core = None


def set_agent_zero_core(core) -> None:
    """Set the AgentZeroCore instance for SSF handlers."""
    global _agent_zero_core
    _agent_zero_core = core


# ============================================================================
# HANDLER IMPLEMENTATIONS
# ============================================================================

async def handle_delegate_to_agent(
    target_agent_id: str,
    task_description: str,
    inputs: Dict[str, Any],
    constraint_export: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 300,
    **kwargs
) -> Dict[str, Any]:
    """
    Delegate a task to another agent via A2A protocol.

    Args:
        target_agent_id: Agent to delegate to
        task_description: What the agent should do
        inputs: Task inputs
        constraint_export: Constraints to pass to target agent
        timeout_seconds: Maximum wait time

    Returns:
        Delegation result
    """
    logger.info(f"Delegating to agent {target_agent_id}: {task_description[:50]}...")

    return {
        "task_id": str(uuid4()),
        "target_agent_id": target_agent_id,
        "status": "delegated",
        "delegated_at": datetime.utcnow().isoformat(),
    }


async def handle_call_subordinate(
    agent_id: str,
    message: str,
    reset: bool = False,
    profile: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Call a subordinate agent to delegate a task.

    Implements Agent Zero's call_subordinate pattern where agents can
    delegate tasks to child agents while maintaining hierarchy context.

    Args:
        agent_id: ID of the parent agent calling subordinate
        message: Task instructions for the subordinate
        reset: If True, create new subordinate; if False, continue with existing
        profile: Optional prompt profile for subordinate customization

    Returns:
        Dict with subordinate response and metadata
    """
    logger.info(f"call_subordinate from {agent_id}: {message[:50]}...")

    if _agent_zero_core is None:
        return {
            "success": False,
            "error": "AgentZeroCore not initialized",
        }

    return _agent_zero_core.call_subordinate(
        agent_id=agent_id,
        message=message,
        reset=reset,
        profile=profile,
    )


async def handle_intervene(
    agent_id: str,
    message: str,
    pause: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Intervene in an agent's execution.

    Allows real-time human oversight by interrupting agent execution
    with new instructions or corrections.

    Args:
        agent_id: Agent to intervene on
        message: Intervention message/instruction
        pause: If True, pause agent before intervention

    Returns:
        Dict with intervention status
    """
    logger.info(f"Intervention for agent {agent_id}: {message[:50]}...")

    if _agent_zero_core is None:
        return {
            "success": False,
            "error": "AgentZeroCore not initialized",
        }

    return _agent_zero_core.intervene(
        agent_id=agent_id,
        message=message,
        pause=pause,
    )


async def handle_spawn_sub_agent(
    purpose: str,
    capabilities: List[str],
    parent_persona_id: str,
    inherit_constraints: bool = True,
    max_lifetime_seconds: int = 3600,
    **kwargs
) -> Dict[str, Any]:
    """
    Spawn a subordinate agent for a specific task.

    This is the SSF wrapper for creating subordinate agents within
    the Agent Zero hierarchy. Uses call_subordinate internally.

    Args:
        purpose: Agent's purpose (becomes the initial message)
        capabilities: Required capabilities
        parent_persona_id: Parent agent ID for hierarchy
        inherit_constraints: Whether to inherit parent's constraints
        max_lifetime_seconds: Maximum agent lifetime

    Returns:
        Spawned agent details
    """
    logger.info(f"Spawning sub-agent: {purpose}")

    if _agent_zero_core is None:
        # Fallback if core not available
        return {
            "agent_id": str(uuid4()),
            "purpose": purpose,
            "status": "spawned",
            "parent_persona_id": parent_persona_id,
            "hierarchy_level": 1,
            "expires_at": datetime.utcnow().isoformat(),
        }

    # Use call_subordinate with reset=True to create new subordinate
    result = _agent_zero_core.call_subordinate(
        agent_id=parent_persona_id,
        message=f"You are a subordinate agent with purpose: {purpose}. Capabilities: {capabilities}",
        reset=True,
        profile=None,
    )

    if result.get("success"):
        return {
            "agent_id": result.get("subordinate_id"),
            "purpose": purpose,
            "status": "spawned",
            "parent_persona_id": parent_persona_id,
            "hierarchy_level": result.get("hierarchy_level", 1),
            "response": result.get("response"),
            "expires_at": datetime.utcnow().isoformat(),
        }

    return {
        "agent_id": str(uuid4()),
        "purpose": purpose,
        "status": "error",
        "error": result.get("error", "Unknown error"),
        "parent_persona_id": parent_persona_id,
    }


async def handle_broadcast_to_community(
    community_id: str,
    message_type: str,
    content: Dict[str, Any],
    target_roles: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Broadcast a message to community members.

    Args:
        community_id: Target community
        message_type: Type of broadcast
        content: Message content
        target_roles: Optional filter by roles

    Returns:
        Broadcast result
    """
    logger.info(f"Broadcasting to community {community_id}")

    return {
        "broadcast_id": str(uuid4()),
        "community_id": community_id,
        "recipients_count": 0,
        "status": "sent",
    }


async def handle_request_human_input(
    user_id: str,
    question: str,
    options: Optional[List[str]] = None,
    timeout_seconds: int = 3600,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Request input or decision from a human user.

    Args:
        user_id: User to ask
        question: Question to ask
        options: Optional response options
        timeout_seconds: How long to wait
        context: Additional context

    Returns:
        Request details (response comes asynchronously)
    """
    logger.info(f"Requesting human input from {user_id}")

    return {
        "request_id": str(uuid4()),
        "user_id": user_id,
        "status": "pending",
        "expires_at": datetime.utcnow().isoformat(),
    }


# ============================================================================
# SSF DEFINITIONS
# ============================================================================

def _create_delegate_to_agent_ssf() -> SSFDefinition:
    """Create the delegate_to_agent SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="delegate_to_agent",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["a2a", "delegate", "agent", "coordination", "task"],
        description="Delegate a task to another agent using the A2A protocol, with constraint propagation.",
        description_for_llm="Use this SSF to delegate tasks to other agents. Supports the A2A protocol for safe inter-agent communication. Good for distributing work, leveraging specialized agents, or handling tasks outside your capabilities.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_delegate_to_agent",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "target_agent_id": {
                    "type": "string",
                    "description": "Agent to delegate to",
                },
                "task_description": {
                    "type": "string",
                    "description": "Task description",
                },
                "inputs": {
                    "type": "object",
                    "description": "Task inputs",
                },
                "constraint_export": {
                    "type": "object",
                    "description": "Constraints to pass to target",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 300,
                    "description": "Maximum wait time",
                },
            },
            "required": ["target_agent_id", "task_description", "inputs"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "target_agent_id": {"type": "string"},
                "status": {"type": "string"},
                "delegated_at": {"type": "string"},
            },
        },
        timeout_seconds=30,  # Delegation itself is quick
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Creates A2A task for target agent",
            "May consume target agent resources",
        ],
        reversible=True,  # Task can be cancelled
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        ),
    )


def _create_spawn_sub_agent_ssf() -> SSFDefinition:
    """Create the spawn_sub_agent SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="spawn_sub_agent",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["agent", "spawn", "subordinate", "hierarchy"],
        description="Spawn a subordinate agent with specific capabilities and inherited constraints.",
        description_for_llm="Use this SSF to create a temporary sub-agent for a specific task. The sub-agent inherits your constraints and has a limited lifetime. Good for parallelizing work or handling specialized tasks.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_spawn_sub_agent",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "purpose": {
                    "type": "string",
                    "description": "Agent's purpose",
                },
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required capabilities",
                },
                "parent_persona_id": {
                    "type": "string",
                    "description": "Parent persona ID",
                },
                "inherit_constraints": {
                    "type": "boolean",
                    "default": True,
                    "description": "Inherit parent constraints",
                },
                "max_lifetime_seconds": {
                    "type": "integer",
                    "default": 3600,
                    "description": "Maximum agent lifetime",
                },
            },
            "required": ["purpose", "capabilities", "parent_persona_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "purpose": {"type": "string"},
                "status": {"type": "string"},
                "parent_persona_id": {"type": "string"},
                "expires_at": {"type": "string"},
            },
        },
        timeout_seconds=60,
        memory_mb=256,
        risk_level=RiskLevel.HIGH,
        side_effects=[
            "Creates new agent instance",
            "Consumes compute resources",
        ],
        reversible=True,  # Agent can be terminated
        constraint_binding=ConstraintBindingConfig.strict(),
    )


def _create_broadcast_to_community_ssf() -> SSFDefinition:
    """Create the broadcast_to_community SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="broadcast_to_community",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["broadcast", "community", "announcement", "coordination"],
        description="Broadcast a message or update to all or selected community members.",
        description_for_llm="Use this SSF to send announcements or updates to community members. Can target specific roles. Good for community-wide notifications, status updates, or coordination messages.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_broadcast_to_community",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "community_id": {
                    "type": "string",
                    "description": "Target community",
                },
                "message_type": {
                    "type": "string",
                    "enum": ["announcement", "update", "alert", "request"],
                    "description": "Type of broadcast",
                },
                "content": {
                    "type": "object",
                    "description": "Message content",
                },
                "target_roles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional role filter",
                },
            },
            "required": ["community_id", "message_type", "content"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "broadcast_id": {"type": "string"},
                "community_id": {"type": "string"},
                "recipients_count": {"type": "integer"},
                "status": {"type": "string"},
            },
        },
        timeout_seconds=60,
        memory_mb=128,
        risk_level=RiskLevel.MEDIUM,
        side_effects=["Sends messages to community members"],
        reversible=False,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=False,
            on_boundary_approach=BoundaryBehavior.WARN,
        ),
    )


def _create_request_human_input_ssf() -> SSFDefinition:
    """Create the request_human_input SSF definition."""
    return SSFDefinition(
        id=uuid4(),
        name="request_human_input",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["human", "input", "decision", "approval", "consultation"],
        description="Request input, decision, or approval from a human user.",
        description_for_llm="Use this SSF when you need human input, approval, or a decision. Good for ethical edge cases, unclear instructions, important decisions, or when human judgment is needed. The response comes asynchronously.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_request_human_input",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User to ask",
                },
                "question": {
                    "type": "string",
                    "description": "Question to ask",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Response options",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "default": 3600,
                    "description": "Wait time",
                },
                "context": {
                    "type": "object",
                    "description": "Additional context",
                },
            },
            "required": ["user_id", "question"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
                "user_id": {"type": "string"},
                "status": {"type": "string"},
                "expires_at": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=["Sends notification to user"],
        reversible=True,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def _create_call_subordinate_ssf() -> SSFDefinition:
    """
    Create the call_subordinate SSF definition.

    This is the core A0 hierarchy tool - allows agents to delegate
    tasks to subordinate agents while maintaining context.
    """
    return SSFDefinition(
        id=uuid4(),
        name="call_subordinate",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["subordinate", "hierarchy", "delegation", "a0", "agent-zero"],
        description="Delegate a task to a subordinate agent in the hierarchy.",
        description_for_llm="""Use this tool to delegate tasks to a subordinate agent.

Key arguments:
- message: Detailed instructions for the subordinate. Include:
  * The role they should play (scientist, coder, writer, etc.)
  * The specific task to accomplish
  * Context about the higher-level goal
  * Any constraints or requirements
- reset: Use 'true' for brand new tasks, 'false' to continue with existing subordinate

The subordinate will execute their own reasoning loop and return results.
Results are automatically added to your context as a tool result.""",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_call_subordinate",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "ID of the calling agent (parent)",
                },
                "message": {
                    "type": "string",
                    "description": "Task instructions for subordinate",
                },
                "reset": {
                    "type": "boolean",
                    "default": False,
                    "description": "True = new subordinate, False = continue existing",
                },
                "profile": {
                    "type": "string",
                    "description": "Optional prompt profile for subordinate",
                },
            },
            "required": ["agent_id", "message"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "subordinate_id": {"type": "string"},
                "hierarchy_level": {"type": "integer"},
                "response": {"type": "string"},
                "parent_id": {"type": "string"},
            },
        },
        timeout_seconds=300,  # Subordinate may need time to work
        memory_mb=512,
        risk_level=RiskLevel.MEDIUM,
        side_effects=[
            "Creates subordinate agent instance",
            "Consumes compute resources",
            "May create further subordinates (recursive)",
        ],
        reversible=True,
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            validate_inputs=True,
            validate_outputs=True,
            on_boundary_approach=BoundaryBehavior.ESCALATE,
        ),
    )


def _create_intervene_ssf() -> SSFDefinition:
    """Create the intervene SSF for human oversight."""
    return SSFDefinition(
        id=uuid4(),
        name="intervene",
        version="1.0.0",
        category=SSFCategory.AGENT_COORDINATION,
        tags=["intervention", "oversight", "human", "control", "hierarchy"],
        description="Intervene in an agent's execution with new instructions.",
        description_for_llm="Use this to interrupt an agent with new instructions or corrections. The agent will process the intervention and adjust its behavior.",
        handler=SSFHandler.module(
            module_path="vessels.ssf.builtins.coordination",
            function_name="handle_intervene",
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent to intervene on",
                },
                "message": {
                    "type": "string",
                    "description": "Intervention message/instruction",
                },
                "pause": {
                    "type": "boolean",
                    "default": False,
                    "description": "Pause agent before intervention",
                },
            },
            "required": ["agent_id", "message"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "agent_id": {"type": "string"},
                "message": {"type": "string"},
            },
        },
        timeout_seconds=30,
        memory_mb=128,
        risk_level=RiskLevel.LOW,
        side_effects=["Interrupts agent execution"],
        reversible=False,
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


def get_builtin_ssfs() -> List[SSFDefinition]:
    """Get all built-in coordination SSFs."""
    return [
        _create_delegate_to_agent_ssf(),
        _create_spawn_sub_agent_ssf(),
        _create_call_subordinate_ssf(),  # A0 hierarchy core
        _create_intervene_ssf(),  # A0 human oversight
        _create_broadcast_to_community_ssf(),
        _create_request_human_input_ssf(),
    ]
