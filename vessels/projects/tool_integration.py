"""
Tool Integration Layer - Connects AdaptiveTools with ServantProject Policies

This module bridges the gap between:
1. AdaptiveTools (adaptive_tools.py) - Python function-based tool system
2. ServantProject.get_allowed_tools() - Policy-driven tool permissions

Key responsibilities:
- Enforce project-level tool policies
- Map allowed tool names to AdaptiveTools instances
- Create Run nodes for every tool execution
- Provide audit trail through Graphiti
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from adaptive_tools import AdaptiveTools, ToolType, ToolSpecification
from vessels.projects.project import ServantProject

logger = logging.getLogger(__name__)


class ProjectToolGateway:
    """
    Gateway that enforces project-level tool policies

    Usage:
        gateway = ProjectToolGateway(project)
        result = gateway.execute_tool("search_web", {"query": "grants for elders"})
    """

    def __init__(self, project: ServantProject):
        """
        Initialize tool gateway for a project

        Args:
            project: ServantProject with allowed tools policy
        """
        self.project = project
        self.adaptive_tools = AdaptiveTools()
        self._tool_registry: Dict[str, str] = {}  # tool_name -> tool_id

        # Register project-allowed tools
        self._register_project_tools()

    def _register_project_tools(self):
        """Register tools that this project is allowed to use"""
        allowed_tools = self.project.get_allowed_tools()

        # Map tool names to ToolType and create specifications
        tool_type_mapping = {
            "read_file": ToolType.GENERIC,
            "write_file": ToolType.GENERIC,
            "search_web": ToolType.WEB_SCRAPING,
            "query_memory": ToolType.GENERIC,
            "store_memory": ToolType.GENERIC,
            "map_api": ToolType.API_INTEGRATION,
            "schedule_api": ToolType.API_INTEGRATION,
            "nutrition_api": ToolType.API_INTEGRATION,
            "recipe_search": ToolType.WEB_SCRAPING,
            "medical_facility_api": ToolType.API_INTEGRATION,
            "grant_database_api": ToolType.API_INTEGRATION,
            "document_generator": ToolType.DOCUMENT_GENERATION,
        }

        for tool_name in allowed_tools:
            tool_type = tool_type_mapping.get(tool_name, ToolType.GENERIC)

            spec = ToolSpecification(
                name=tool_name,
                description=f"Project-scoped {tool_name} tool",
                tool_type=tool_type,
                parameters={},
                returns={},
                capabilities=[tool_name]
            )

            tool_id = self.adaptive_tools.create_tool(spec)
            self._tool_registry[tool_name] = tool_id

            logger.debug(f"Registered tool '{tool_name}' for project {self.project.id}")

    def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a tool with project-level policy enforcement

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            agent_id: Optional agent ID for audit trail

        Returns:
            Tool execution result with success/error status
        """
        # 1. Check if tool is allowed by project policy
        if tool_name not in self._tool_registry:
            logger.warning(
                f"Tool '{tool_name}' not allowed for project {self.project.id} "
                f"(type: {self.project.servant_type.value})"
            )
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not allowed by project policy",
                "allowed_tools": list(self._tool_registry.keys())
            }

        tool_id = self._tool_registry[tool_name]

        # 2. Create Run node BEFORE execution
        run_id = self._create_run_node(
            tool_name=tool_name,
            inputs=params,
            agent_id=agent_id or self.project.id
        )

        # 3. Execute tool
        try:
            result = self.adaptive_tools.execute_tool(
                tool_id,
                params,
                agent_id=agent_id or self.project.id,
                gate_metadata={
                    "project_id": self.project.id,
                    "servant_type": self.project.servant_type.value,
                    "community_id": self.project.community_id,
                    "run_id": run_id
                }
            )

            # 4. Update Run node with result
            self._update_run_node(run_id, result)

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            error_result = {"success": False, "error": str(e)}
            self._update_run_node(run_id, error_result)
            return error_result

    def _create_run_node(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        agent_id: str
    ) -> str:
        """Create Run node in Graphiti for audit trail"""
        try:
            import uuid

            run_id = str(uuid.uuid4())
            self.project.graphiti.create_node(
                node_type="Run",
                properties={
                    "tool_name": tool_name,
                    "inputs": json.dumps(inputs),
                    "timestamp": datetime.utcnow().isoformat(),
                    "servant_id": self.project.id,
                    "agent_id": agent_id,
                    "community_id": self.project.community_id,
                    "status": "executing"
                },
                node_id=run_id
            )
            logger.debug(f"Created Run node {run_id} for tool '{tool_name}'")
            return run_id

        except Exception as e:
            logger.error(f"Failed to create Run node: {e}")
            return "run_node_failed"

    def _update_run_node(self, run_id: str, result: Dict[str, Any]):
        """Update Run node with execution result"""
        if run_id == "run_node_failed":
            return

        try:
            # Update the Run node with outputs
            self.project.graphiti.update_node(
                run_id,
                {
                    "outputs": json.dumps(result),
                    "status": "completed" if result.get("success") else "failed",
                    "completed_at": datetime.utcnow().isoformat()
                }
            )
            logger.debug(f"Updated Run node {run_id} with result")

        except Exception as e:
            logger.error(f"Failed to update Run node: {e}")

    def get_allowed_tools(self) -> List[str]:
        """Get list of tools allowed for this project"""
        return list(self._tool_registry.keys())

    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get statistics about tool usage for this project"""
        # Query Graphiti for Run nodes associated with this project
        try:
            # This would query the graph for Run nodes
            # For now, return basic info
            return {
                "project_id": self.project.id,
                "servant_type": self.project.servant_type.value,
                "allowed_tools": self.get_allowed_tools(),
                "tool_count": len(self._tool_registry)
            }
        except Exception as e:
            logger.error(f"Failed to get tool usage stats: {e}")
            return {}
