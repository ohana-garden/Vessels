"""
Adaptive Tools - Dynamically created and gated tool execution.

Tools that can be created at runtime and executed through the moral gating
system. All tool executions must pass through the ActionGate.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ToolType(str, Enum):
    """Categories of adaptive tools."""
    GENERIC = "generic"
    DATA_RETRIEVAL = "data_retrieval"
    DATA_MUTATION = "data_mutation"
    EXTERNAL_API = "external_api"
    COMPUTATION = "computation"
    COMMUNICATION = "communication"


@dataclass
class ToolSpecification:
    """Specification for creating a new tool."""
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, Any]
    returns: Dict[str, Any]
    capabilities: List[str] = field(default_factory=list)
    risk_level: str = "low"
    requires_approval: bool = False


@dataclass
class Tool:
    """A registered tool instance."""
    tool_id: str
    specification: ToolSpecification
    handler: Optional[Callable] = None
    created_at: str = ""
    invocations: int = 0


class AdaptiveTools:
    """
    Runtime tool creation and execution with moral gating.

    All tool executions pass through the ActionGate to ensure
    they comply with moral constraints.
    """

    def __init__(
        self,
        gate=None,
        tracker=None,
        vessel_id: str = "default"
    ):
        """
        Initialize adaptive tools.

        Args:
            gate: ActionGate for moral constraint checking
            tracker: TrajectoryTracker for observability
            vessel_id: ID of the vessel this tools instance belongs to
        """
        self.gate = gate
        self.tracker = tracker
        self.vessel_id = vessel_id
        self.tools: Dict[str, Tool] = {}
        self.handlers: Dict[str, Callable] = {}

    def create_tool(
        self,
        spec: ToolSpecification,
        handler: Optional[Callable] = None
    ) -> str:
        """
        Create a new tool from specification.

        Args:
            spec: Tool specification
            handler: Optional handler function for the tool

        Returns:
            Tool ID
        """
        from datetime import datetime

        tool_id = f"tool_{spec.name}_{uuid4().hex[:8]}"

        tool = Tool(
            tool_id=tool_id,
            specification=spec,
            handler=handler,
            created_at=datetime.utcnow().isoformat()
        )

        self.tools[tool_id] = tool
        if handler:
            self.handlers[tool_id] = handler

        logger.info(f"Created tool: {tool_id} ({spec.name})")
        return tool_id

    def register_handler(self, tool_id: str, handler: Callable):
        """Register a handler function for a tool."""
        if tool_id not in self.tools:
            raise ValueError(f"Tool not found: {tool_id}")

        self.handlers[tool_id] = handler
        self.tools[tool_id].handler = handler

    def execute_tool(
        self,
        tool_id: str,
        params: Dict[str, Any],
        agent_id: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Execute a tool with moral gating.

        Args:
            tool_id: ID of the tool to execute
            params: Parameters for the tool
            agent_id: ID of the agent executing the tool

        Returns:
            Execution result
        """
        if tool_id not in self.tools:
            return {"success": False, "error": f"Tool not found: {tool_id}"}

        tool = self.tools[tool_id]

        # Build action for moral gating
        action = {
            "type": "tool_execution",
            "tool_id": tool_id,
            "tool_name": tool.specification.name,
            "tool_type": tool.specification.tool_type.value,
            "parameters": params,
            "vessel_id": self.vessel_id,
            "service_value": 0.5,  # Default service value for tool use
        }

        # Apply moral gating if available
        if self.gate:
            gating_result = self.gate.gate_action(
                agent_id=agent_id,
                action=action,
                action_metadata={"tool_spec": tool.specification.__dict__}
            )

            if not gating_result.allowed:
                logger.warning(f"Tool execution blocked: {gating_result.reason}")
                return {
                    "success": False,
                    "blocked": True,
                    "reason": gating_result.reason
                }

        # Execute the tool
        tool.invocations += 1

        if tool_id not in self.handlers:
            # Default behavior: return params
            return {"success": True, "output": params}

        try:
            handler = self.handlers[tool_id]
            result = handler(params)
            return {"success": True, "output": result}
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {"success": False, "error": str(e)}

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools."""
        return [
            {
                "tool_id": tool.tool_id,
                "name": tool.specification.name,
                "type": tool.specification.tool_type.value,
                "invocations": tool.invocations
            }
            for tool in self.tools.values()
        ]

    def get_tool(self, tool_id: str) -> Optional[Tool]:
        """Get a tool by ID."""
        return self.tools.get(tool_id)

    def delete_tool(self, tool_id: str) -> bool:
        """Delete a tool."""
        if tool_id in self.tools:
            del self.tools[tool_id]
            if tool_id in self.handlers:
                del self.handlers[tool_id]
            return True
        return False
