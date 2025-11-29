"""
A0 SSF Integration - Connecting Agent Zero to SSF Execution.

This module integrates SSF execution with Agent Zero's reasoning loop,
replacing A0's default code execution with constrained SSF invocation.

The agent can ONLY affect the world through SSFs - there is no direct
code execution, no raw API calls, no escape hatch.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from ..ssf.schema import (
    SSFDefinition,
    SSFResult,
    SSFStatus,
    SSFCategory,
    SSFHandler,
    HandlerType,
    ExecutionContext,
    SSFPermissions,
    SSFSpawnRequest,
)
from ..ssf.runtime import SSFRuntime, Persona, A0AgentInstance
from ..ssf.registry import SSFRegistry, SSFMatch
from ..ssf.composition import SSFComposer, SSFStep, CompositionResult

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """
    Tool definition for A0's prompt.

    This represents an SSF as a tool that A0 can call.
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    ssf_id: Optional[UUID] = None
    category: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for prompt injection."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "ssf_id": str(self.ssf_id) if self.ssf_id else None,
        }

    def to_function_spec(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": self.parameters,
                "required": list(self.parameters.keys()),
            },
        }


@dataclass
class ToolResult:
    """Result of a tool call from A0."""
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    ssf_result: Optional[SSFResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for response."""
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
        }


class UnknownToolError(Exception):
    """Raised when A0 calls an unknown tool."""
    pass


class A0SSFIntegration:
    """
    Integrates SSF execution with Agent Zero's reasoning loop.

    This replaces A0's default code execution with SSF invocation.
    The agent can ONLY affect the world through SSFs.

    Provides:
    - Tool definitions for A0's prompt
    - Tool call handling that routes through SSFs
    - SSF discovery for capability matching
    - Dynamic SSF spawning (with constraints)
    - SSF composition for complex tasks
    """

    # Core meta-tools that are always available
    META_TOOLS = ["invoke_ssf", "find_ssf", "compose_ssfs"]

    def __init__(
        self,
        runtime: SSFRuntime,
        registry: SSFRegistry,
        composer: SSFComposer,
    ):
        """
        Initialize the A0 SSF integration.

        Args:
            runtime: SSF runtime for execution
            registry: SSF registry for discovery
            composer: SSF composer for chaining
        """
        self.runtime = runtime
        self.registry = registry
        self.composer = composer

        # Cache of SSF -> tool mappings
        self._tool_cache: Dict[str, ToolDefinition] = {}

        # Statistics
        self._tool_calls = 0
        self._ssf_invocations = 0
        self._compositions = 0

    def get_tool_definitions_for_agent(
        self,
        persona: Persona,
        include_meta_tools: bool = True,
        include_ssfs: bool = True,
        max_ssfs: int = 50,
    ) -> List[ToolDefinition]:
        """
        Generate tool definitions for A0's prompt.

        This creates the interface between A0 reasoning and SSF execution.
        Each permitted SSF becomes a "tool" the agent can call.

        Args:
            persona: Persona to generate tools for
            include_meta_tools: Include invoke_ssf, find_ssf, etc.
            include_ssfs: Include individual SSFs as tools
            max_ssfs: Maximum number of SSFs to include

        Returns:
            List of tool definitions for the prompt
        """
        tools: List[ToolDefinition] = []

        # Add meta-tools
        if include_meta_tools:
            tools.extend(self._get_meta_tools(persona))

        # Add individual SSFs as tools
        if include_ssfs:
            ssf_tools = self._get_ssf_tools(persona, max_ssfs)
            tools.extend(ssf_tools)

        return tools

    def _get_meta_tools(self, persona: Persona) -> List[ToolDefinition]:
        """Get the core meta-tools."""
        tools = []

        # invoke_ssf - Direct SSF invocation
        tools.append(ToolDefinition(
            name="invoke_ssf",
            description="Execute a Serverless Smart Function by ID. Use this when you know the exact SSF to call.",
            parameters={
                "ssf_id": {
                    "type": "string",
                    "description": "UUID of the SSF to invoke",
                },
                "inputs": {
                    "type": "object",
                    "description": "Input parameters matching the SSF's input schema",
                },
            },
        ))

        # find_ssf - Capability search
        tools.append(ToolDefinition(
            name="find_ssf",
            description="Find SSFs that can accomplish a capability. Use this when you need to discover what SSFs are available for a task.",
            parameters={
                "capability": {
                    "type": "string",
                    "description": "Natural language description of what you need to do",
                },
                "required_inputs": {
                    "type": "object",
                    "description": "Optional: inputs you have available",
                },
            },
        ))

        # compose_ssfs - Sequential composition
        if persona.ssf_permissions.can_compose_ssfs:
            tools.append(ToolDefinition(
                name="compose_ssfs",
                description="Chain multiple SSFs into a workflow where outputs flow from one to the next. Use this for multi-step tasks.",
                parameters={
                    "steps": {
                        "type": "array",
                        "description": "List of {ssf_id, inputs} for sequential execution",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ssf_id": {"type": "string"},
                                "inputs": {"type": "object"},
                            },
                        },
                    },
                },
            ))

        # spawn_ssf - Dynamic SSF creation (if permitted)
        if persona.ssf_permissions.can_spawn_ssfs:
            tools.append(ToolDefinition(
                name="spawn_ssf",
                description="Create a new SSF for a capability not covered by existing SSFs. Subject to spawn constraints.",
                parameters={
                    "name": {
                        "type": "string",
                        "description": "Name for the new SSF (snake_case)",
                    },
                    "description": {
                        "type": "string",
                        "description": "What the SSF does",
                    },
                    "description_for_llm": {
                        "type": "string",
                        "description": "Description optimized for LLM tool selection",
                    },
                    "category": {
                        "type": "string",
                        "description": "SSF category",
                    },
                    "handler": {
                        "type": "object",
                        "description": "Handler specification",
                    },
                    "input_schema": {
                        "type": "object",
                        "description": "JSON Schema for inputs",
                    },
                    "output_schema": {
                        "type": "object",
                        "description": "JSON Schema for outputs",
                    },
                },
            ))

        return tools

    def _get_ssf_tools(self, persona: Persona, max_ssfs: int) -> List[ToolDefinition]:
        """Convert permitted SSFs to tool definitions."""
        tools = []
        ssfs = self.registry.list_all()

        for ssf in ssfs[:max_ssfs]:
            # Check if persona can invoke this SSF
            if not self._can_invoke(ssf, persona):
                continue

            # Create tool definition from SSF
            tool = ToolDefinition(
                name=f"ssf_{ssf.name}",
                description=ssf.description_for_llm or ssf.description,
                parameters=self._schema_to_params(ssf.input_schema),
                ssf_id=ssf.id,
                category=ssf.category.value,
            )

            tools.append(tool)
            self._tool_cache[tool.name] = tool

        return tools

    def _can_invoke(self, ssf: SSFDefinition, persona: Persona) -> bool:
        """Check if persona can invoke an SSF."""
        permissions = persona.ssf_permissions

        if not permissions.can_invoke_ssfs:
            return False

        if ssf.id in permissions.blocked_ssf_ids:
            return False

        if permissions.permitted_categories:
            if ssf.category not in permissions.permitted_categories:
                return False

        return True

    def _schema_to_params(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON Schema to parameter definitions."""
        properties = schema.get("properties", {})
        params = {}

        for name, prop in properties.items():
            params[name] = {
                "type": prop.get("type", "string"),
                "description": prop.get("description", ""),
            }
            if "enum" in prop:
                params[name]["enum"] = prop["enum"]
            if "default" in prop:
                params[name]["default"] = prop["default"]

        return params

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        persona: Persona,
        agent: A0AgentInstance,
        context: Optional[ExecutionContext] = None,
    ) -> ToolResult:
        """
        Handle a tool call from A0's reasoning loop.

        All tool calls route through SSFs - there is no direct execution.

        Args:
            tool_name: Name of the tool being called
            arguments: Arguments for the tool
            persona: Invoking persona
            agent: Invoking agent
            context: Execution context

        Returns:
            ToolResult with execution outcome
        """
        self._tool_calls += 1
        context = context or ExecutionContext()

        try:
            if tool_name == "invoke_ssf":
                return await self._handle_invoke_ssf(arguments, persona, agent, context)

            elif tool_name == "find_ssf":
                return await self._handle_find_ssf(arguments, persona)

            elif tool_name == "compose_ssfs":
                return await self._handle_compose_ssfs(arguments, persona, agent, context)

            elif tool_name == "spawn_ssf":
                return await self._handle_spawn_ssf(arguments, persona, agent)

            elif tool_name.startswith("ssf_"):
                # Direct SSF call via tool name
                return await self._handle_direct_ssf_call(
                    tool_name, arguments, persona, agent, context
                )

            else:
                raise UnknownToolError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool call error: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=str(e),
            )

    async def _handle_invoke_ssf(
        self,
        arguments: Dict[str, Any],
        persona: Persona,
        agent: A0AgentInstance,
        context: ExecutionContext,
    ) -> ToolResult:
        """Handle invoke_ssf tool call."""
        ssf_id = arguments.get("ssf_id")
        inputs = arguments.get("inputs", {})

        if not ssf_id:
            return ToolResult(success=False, error="ssf_id is required")

        try:
            ssf_uuid = UUID(ssf_id)
        except ValueError:
            return ToolResult(success=False, error=f"Invalid SSF ID: {ssf_id}")

        self._ssf_invocations += 1

        result = await self.runtime.invoke(
            ssf_id=ssf_uuid,
            inputs=inputs,
            invoking_persona=persona,
            invoking_agent=agent,
            execution_context=context,
        )

        return self._ssf_result_to_tool_result(result)

    async def _handle_find_ssf(
        self,
        arguments: Dict[str, Any],
        persona: Persona,
    ) -> ToolResult:
        """Handle find_ssf tool call."""
        capability = arguments.get("capability", "")
        required_inputs = arguments.get("required_inputs")

        if not capability:
            return ToolResult(success=False, error="capability description is required")

        matches = await self.registry.find_for_capability(
            capability_description=capability,
            invoking_persona=persona,
            required_inputs=required_inputs,
        )

        return ToolResult(
            success=True,
            output={
                "matches": [m.to_dict() for m in matches],
                "count": len(matches),
            },
        )

    async def _handle_compose_ssfs(
        self,
        arguments: Dict[str, Any],
        persona: Persona,
        agent: A0AgentInstance,
        context: ExecutionContext,
    ) -> ToolResult:
        """Handle compose_ssfs tool call."""
        steps_data = arguments.get("steps", [])

        if not steps_data:
            return ToolResult(success=False, error="steps are required")

        try:
            steps = [
                SSFStep(ssf_id=UUID(s["ssf_id"]), inputs=s.get("inputs", {}))
                for s in steps_data
            ]
        except (KeyError, ValueError) as e:
            return ToolResult(success=False, error=f"Invalid step format: {e}")

        self._compositions += 1

        result = await self.composer.compose_sequence(
            steps=steps,
            invoking_persona=persona,
            invoking_agent=agent,
            execution_context=context,
        )

        return self._composition_result_to_tool_result(result)

    async def _handle_spawn_ssf(
        self,
        arguments: Dict[str, Any],
        persona: Persona,
        agent: A0AgentInstance,
    ) -> ToolResult:
        """Handle spawn_ssf tool call."""
        try:
            # Build handler from arguments
            handler_data = arguments.get("handler", {})
            handler_type = HandlerType(handler_data.get("type", "module"))

            handler = SSFHandler(
                type=handler_type,
                module_path=handler_data.get("module_path"),
                function_name=handler_data.get("function_name"),
                inline_code=handler_data.get("inline_code"),
            )

            # Build spawn request
            request = SSFSpawnRequest(
                name=arguments.get("name", "spawned_ssf"),
                description=arguments.get("description", ""),
                description_for_llm=arguments.get("description_for_llm", ""),
                category=SSFCategory(arguments.get("category", "computation")),
                handler=handler,
                input_schema=arguments.get("input_schema", {}),
                output_schema=arguments.get("output_schema", {}),
            )

            ssf = await self.registry.spawn(
                request=request,
                invoking_persona=persona,
                invoking_agent=agent,
            )

            return ToolResult(
                success=True,
                output={
                    "ssf_id": str(ssf.id),
                    "name": ssf.name,
                    "status": "spawned",
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _handle_direct_ssf_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        persona: Persona,
        agent: A0AgentInstance,
        context: ExecutionContext,
    ) -> ToolResult:
        """Handle direct SSF call via tool name (ssf_<name>)."""
        # Look up from cache
        tool_def = self._tool_cache.get(tool_name)
        if not tool_def or not tool_def.ssf_id:
            return ToolResult(
                success=False,
                error=f"Unknown SSF tool: {tool_name}",
            )

        self._ssf_invocations += 1

        result = await self.runtime.invoke(
            ssf_id=tool_def.ssf_id,
            inputs=arguments,
            invoking_persona=persona,
            invoking_agent=agent,
            execution_context=context,
        )

        return self._ssf_result_to_tool_result(result)

    def _ssf_result_to_tool_result(self, result: SSFResult) -> ToolResult:
        """Convert SSF result to tool result."""
        return ToolResult(
            success=result.status == SSFStatus.SUCCESS,
            output=result.output,
            error=result.error,
            ssf_result=result,
        )

    def _composition_result_to_tool_result(self, result: CompositionResult) -> ToolResult:
        """Convert composition result to tool result."""
        return ToolResult(
            success=result.success,
            output={
                "status": result.status.value,
                "completed_steps": result.completed_steps,
                "total_steps": result.total_steps,
                "final_output": result.final_output,
            },
            error=result.failure_reason,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        return {
            "tool_calls": self._tool_calls,
            "ssf_invocations": self._ssf_invocations,
            "compositions": self._compositions,
            "cached_tools": len(self._tool_cache),
        }

    def clear_tool_cache(self) -> None:
        """Clear the tool definition cache."""
        self._tool_cache.clear()


def create_a0_integration(
    manifold: Optional[Any] = None,
    memory_client: Optional[Any] = None,
) -> A0SSFIntegration:
    """
    Factory function to create a fully configured A0 SSF integration.

    Args:
        manifold: Moral manifold for constraint validation
        memory_client: Memory client for logging

    Returns:
        Configured A0SSFIntegration instance
    """
    runtime = SSFRuntime(
        manifold=manifold,
        memory_client=memory_client,
    )

    registry = SSFRegistry()
    composer = SSFComposer(runtime)

    # Set runtime's registry reference
    runtime.registry = registry

    return A0SSFIntegration(
        runtime=runtime,
        registry=registry,
        composer=composer,
    )
