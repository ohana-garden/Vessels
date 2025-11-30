"""
SSF Runtime - The Execution Engine.

ALL agent actions flow through this runtime. It is responsible for:
1. Validating inputs against persona's constraint manifold
2. Binding constraints to execution context
3. Executing the SSF
4. Validating outputs against constraints
5. Logging execution to shared memory

This is the PRIMARY SAFETY MECHANISM - there are no backdoors.
"""

import asyncio
import importlib
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID

from .schema import (
    SSFDefinition,
    SSFHandler,
    HandlerType,
    SSFResult,
    SSFStatus,
    SSFCategory,
    RiskLevel,
    ConstraintBindingMode,
    BoundaryBehavior,
    ManifoldValidation,
    ExecutionContext,
    SSFPermissions,
)

if TYPE_CHECKING:
    from ..constraints.manifold import Manifold
    from .registry import SSFRegistry

logger = logging.getLogger(__name__)


class SSFExecutionError(Exception):
    """Error during SSF execution."""
    pass


class SSFTimeoutError(SSFExecutionError):
    """SSF execution timed out."""
    pass


class SSFNotFoundError(SSFExecutionError):
    """SSF not found in registry."""
    pass


class SSFPermissionDeniedError(SSFExecutionError):
    """Persona lacks permission to invoke SSF."""
    pass


class SSFConstraintViolationError(SSFExecutionError):
    """Input or output violates ethical constraints."""
    pass


@dataclass
class BoundConstraintContext:
    """
    Execution context with bound constraints.

    Created for each SSF invocation, binding the invoking persona's
    constraints to the execution.
    """
    ssf: SSFDefinition
    persona_id: UUID
    agent_id: str
    constraints: List[str]  # Names of constraints that apply
    virtue_state: Dict[str, float]
    forbidden_patterns: Dict[str, List[re.Pattern]]
    execution_context: ExecutionContext

    # Runtime tracking
    started_at: datetime = field(default_factory=datetime.utcnow)
    timeout_seconds: int = 30


@dataclass
class Persona:
    """
    Minimal persona interface for SSF runtime.

    In practice, this would be imported from the vessels.core module,
    but we define a minimal interface here for typing.
    """
    id: UUID
    name: str
    community_id: str
    ssf_permissions: SSFPermissions = field(default_factory=SSFPermissions)
    virtue_state: Dict[str, float] = field(default_factory=dict)
    manifold_position: Optional[str] = None  # Reference to manifold position


@dataclass
class A0AgentInstance:
    """
    Minimal A0 agent interface for SSF runtime.
    """
    agent_id: str
    persona_id: UUID
    vessel_id: Optional[str] = None


class SSFRuntime:
    """
    The SSF execution engine.

    ALL agent actions flow through this runtime. It is responsible for:
    1. Validating inputs against persona's constraint manifold
    2. Binding constraints to execution context
    3. Executing the SSF
    4. Validating outputs against constraints
    5. Logging execution to shared memory

    There are NO backdoors - this is the only entry point for execution.
    """

    def __init__(
        self,
        manifold: Optional["Manifold"] = None,
        memory_client: Optional[Any] = None,
        registry: Optional["SSFRegistry"] = None,
        default_timeout_seconds: int = 30,
        latency_budget_ms: float = 50.0,
    ):
        """
        Initialize the SSF runtime.

        Args:
            manifold: Moral manifold for constraint validation
            memory_client: Client for logging executions (Graphiti)
            registry: SSF registry for lookups
            default_timeout_seconds: Default execution timeout
            latency_budget_ms: Max overhead for SSF system (target <50ms)
        """
        self.manifold = manifold
        self.memory_client = memory_client
        self.registry = registry
        self.default_timeout_seconds = default_timeout_seconds
        self.latency_budget_ms = latency_budget_ms

        # Execution statistics
        self._total_invocations = 0
        self._blocked_invocations = 0
        self._successful_invocations = 0
        self._total_execution_time = 0.0

        # Handler cache
        self._handler_cache: Dict[str, Callable] = {}

    async def invoke(
        self,
        ssf_id: UUID,
        inputs: Dict[str, Any],
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
        execution_context: Optional[ExecutionContext] = None,
    ) -> SSFResult:
        """
        Invoke an SSF with full constraint binding.

        This is the ONLY entry point for execution. There are no backdoors.

        Args:
            ssf_id: UUID of the SSF to invoke
            inputs: Input parameters for the SSF
            invoking_persona: Persona invoking the SSF
            invoking_agent: Agent instance invoking the SSF
            execution_context: Optional execution context

        Returns:
            SSFResult with execution outcome
        """
        start_time = time.time()
        self._total_invocations += 1
        execution_context = execution_context or ExecutionContext()

        try:
            # 1. Resolve SSF definition
            ssf = await self._resolve_ssf(ssf_id)
            if not ssf:
                return SSFResult(
                    status=SSFStatus.ERROR,
                    error=f"SSF not found: {ssf_id}",
                    ssf_id=ssf_id,
                )

            # 2. Check persona permissions
            permission_error = await self._check_permissions(ssf, invoking_persona)
            if permission_error:
                self._blocked_invocations += 1
                return SSFResult(
                    status=SSFStatus.BLOCKED,
                    error=permission_error,
                    ssf_id=ssf_id,
                    ssf_name=ssf.name,
                )

            # 3. Validate inputs against schema
            schema_error = await self._validate_input_schema(ssf, inputs)
            if schema_error:
                self._blocked_invocations += 1
                return SSFResult(
                    status=SSFStatus.BLOCKED,
                    error=f"Input schema validation failed: {schema_error}",
                    ssf_id=ssf_id,
                    ssf_name=ssf.name,
                )

            # 4. Validate inputs against ethical manifold
            if ssf.constraint_binding.validate_inputs:
                input_validation = await self._validate_against_manifold(
                    ssf=ssf,
                    data=inputs,
                    direction="input",
                    persona=invoking_persona,
                )

                if input_validation.blocked:
                    self._blocked_invocations += 1
                    await self._log_blocked_execution(
                        ssf, inputs, None, invoking_persona, invoking_agent,
                        input_validation, "input"
                    )
                    return SSFResult(
                        status=SSFStatus.BLOCKED,
                        error=f"Input violates constraint: {input_validation.violation}",
                        constraint_violation=input_validation,
                        ssf_id=ssf_id,
                        ssf_name=ssf.name,
                    )

                if input_validation.boundary_warning:
                    if ssf.constraint_binding.on_boundary_approach == BoundaryBehavior.ESCALATE:
                        return SSFResult(
                            status=SSFStatus.ESCALATED,
                            escalation_reason=input_validation.boundary_warning,
                            escalation_target=ssf.constraint_binding.escalation_target,
                            ssf_id=ssf_id,
                            ssf_name=ssf.name,
                        )
                    elif ssf.constraint_binding.on_boundary_approach == BoundaryBehavior.BLOCK:
                        self._blocked_invocations += 1
                        return SSFResult(
                            status=SSFStatus.BLOCKED,
                            error=f"Input approaches constraint boundary: {input_validation.boundary_warning}",
                            constraint_violation=input_validation,
                            ssf_id=ssf_id,
                            ssf_name=ssf.name,
                        )

            # 5. Create execution context with bound constraints
            bound_context = await self._bind_constraints(
                ssf=ssf,
                persona=invoking_persona,
                agent=invoking_agent,
                execution_context=execution_context,
            )

            # 6. Execute the SSF
            execution_start = time.time()
            try:
                raw_output = await self._execute(ssf, inputs, bound_context)
            except asyncio.TimeoutError:
                return SSFResult(
                    status=SSFStatus.TIMEOUT,
                    error=f"SSF execution timed out after {ssf.timeout_seconds}s",
                    execution_time_seconds=time.time() - execution_start,
                    ssf_id=ssf_id,
                    ssf_name=ssf.name,
                )
            except Exception as e:
                logger.error(f"SSF execution error: {e}", exc_info=True)
                return SSFResult(
                    status=SSFStatus.ERROR,
                    error=str(e),
                    execution_time_seconds=time.time() - execution_start,
                    ssf_id=ssf_id,
                    ssf_name=ssf.name,
                )

            execution_duration = time.time() - execution_start

            # 7. Validate outputs against ethical manifold
            if ssf.constraint_binding.validate_outputs:
                output_validation = await self._validate_against_manifold(
                    ssf=ssf,
                    data=raw_output or {},
                    direction="output",
                    persona=invoking_persona,
                )

                if output_validation.blocked:
                    self._blocked_invocations += 1
                    await self._log_blocked_execution(
                        ssf, inputs, raw_output, invoking_persona, invoking_agent,
                        output_validation, "output"
                    )
                    return SSFResult(
                        status=SSFStatus.OUTPUT_BLOCKED,
                        error=f"Output violates constraint: {output_validation.violation}",
                        constraint_violation=output_validation,
                        execution_time_seconds=execution_duration,
                        ssf_id=ssf_id,
                        ssf_name=ssf.name,
                    )

            # 8. Log successful execution
            await self._log_execution(
                ssf=ssf,
                inputs=inputs,
                output=raw_output,
                persona=invoking_persona,
                agent=invoking_agent,
                duration=execution_duration,
                context=execution_context,
            )

            self._successful_invocations += 1
            total_time = time.time() - start_time
            self._total_execution_time += total_time

            return SSFResult(
                status=SSFStatus.SUCCESS,
                output=raw_output,
                execution_time_seconds=execution_duration,
                ssf_id=ssf_id,
                ssf_name=ssf.name,
            )

        except Exception as e:
            logger.error(f"Unexpected error in SSF invocation: {e}", exc_info=True)
            return SSFResult(
                status=SSFStatus.ERROR,
                error=f"Unexpected error: {str(e)}",
                ssf_id=ssf_id,
            )

    async def _resolve_ssf(self, ssf_id: UUID) -> Optional[SSFDefinition]:
        """Resolve SSF definition from registry."""
        if self.registry:
            return await self.registry.get(ssf_id)
        return None

    async def _check_permissions(
        self,
        ssf: SSFDefinition,
        persona: Persona
    ) -> Optional[str]:
        """
        Check if persona has permission to invoke the SSF.

        Returns error message if permission denied, None if allowed.
        """
        permissions = persona.ssf_permissions

        # Check if SSF invocation is allowed at all
        if not permissions.can_invoke_ssfs:
            return "Persona does not have SSF invocation permission"

        # Check if SSF is explicitly blocked
        if ssf.id in permissions.blocked_ssf_ids:
            return f"SSF {ssf.name} is explicitly blocked for this persona"

        # Check category permissions
        if permissions.permitted_categories and ssf.category not in permissions.permitted_categories:
            return f"Persona not permitted to invoke {ssf.category.value} SSFs"

        # Check risk level
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        if risk_order.index(ssf.risk_level) > risk_order.index(permissions.max_risk_level):
            return f"SSF risk level {ssf.risk_level.value} exceeds persona's max {permissions.max_risk_level.value}"

        return None

    async def _validate_input_schema(
        self,
        ssf: SSFDefinition,
        inputs: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate inputs against SSF's JSON schema.

        Returns error message if validation fails, None if valid.
        """
        if not ssf.input_schema:
            return None

        try:
            # Basic schema validation
            schema = ssf.input_schema
            properties = schema.get("properties", {})
            required = schema.get("required", [])

            # Check required fields
            for field_name in required:
                if field_name not in inputs:
                    return f"Missing required field: {field_name}"

            # Check additional properties
            if not schema.get("additionalProperties", True):
                for key in inputs:
                    if key not in properties:
                        return f"Unknown field: {key}"

            # Type checking for provided values
            for key, value in inputs.items():
                if key in properties:
                    prop_schema = properties[key]
                    expected_type = prop_schema.get("type")
                    if expected_type:
                        if not self._check_type(value, expected_type):
                            return f"Field {key} has wrong type, expected {expected_type}"

            return None

        except Exception as e:
            return f"Schema validation error: {str(e)}"

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None),
        }
        expected = type_mapping.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True

    async def _validate_against_manifold(
        self,
        ssf: SSFDefinition,
        data: Dict[str, Any],
        direction: str,  # "input" or "output"
        persona: Persona,
    ) -> ManifoldValidation:
        """
        Check if data violates the persona's position in virtue space.

        This is where topological ethics are enforced.
        """
        validation = ManifoldValidation()

        # Get constraint binding config
        binding = ssf.constraint_binding

        # Check forbidden patterns first (hard-coded safety rails)
        forbidden_patterns = (
            binding.forbidden_input_patterns if direction == "input"
            else binding.forbidden_output_patterns
        )

        for pattern in forbidden_patterns:
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                data_str = str(data)
                if regex.search(data_str):
                    validation.blocked = True
                    validation.violation = f"Data matches forbidden pattern: {pattern}"
                    validation.violations.append(validation.violation)
                    return validation
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")

        # If we have a manifold, validate against virtue constraints
        if self.manifold:
            virtue_state = persona.virtue_state or {}

            # Get constraints to apply based on binding mode
            if binding.mode == ConstraintBindingMode.FULL:
                constraints = self.manifold.get_all_constraints()
            elif binding.mode == ConstraintBindingMode.FILTERED:
                constraints = self._get_category_constraints(ssf.category)
            else:  # EXPLICIT
                constraints = self._get_explicit_constraints(binding.explicit_constraints or [])

            # Check each constraint
            for constraint in constraints:
                validation.checked_constraints.append(constraint.name)

                # Create combined state for constraint checking
                combined_state = {**virtue_state}

                # Add operational hints based on SSF category
                if ssf.category == SSFCategory.COMMUNICATION:
                    combined_state["coordination"] = 0.8
                elif ssf.category == SSFCategory.DATA_MUTATION:
                    combined_state["activity"] = 0.6

                try:
                    if not constraint(combined_state):
                        validation.blocked = True
                        validation.violation = f"Constraint violated: {constraint.name}"
                        validation.violations.append(constraint.name)
                except Exception as e:
                    logger.warning(f"Constraint check error for {constraint.name}: {e}")

        return validation

    def _get_category_constraints(self, category: SSFCategory) -> List[Any]:
        """Get constraints relevant to an SSF category."""
        if not self.manifold:
            return []

        # Map categories to relevant constraint names
        category_constraints = {
            SSFCategory.COMMUNICATION: [
                "truthfulness_required_06",
                "low_truthfulness_high_coordination",
            ],
            SSFCategory.DATA_MUTATION: [
                "low_justice_high_activity",
                "low_service_high_resource",
            ],
            SSFCategory.AGENT_COORDINATION: [
                "unity_requires_understanding",
                "unity_requires_detachment",
            ],
        }

        relevant_names = category_constraints.get(category, [])
        all_constraints = self.manifold.get_all_constraints()

        return [c for c in all_constraints if c.name in relevant_names]

    def _get_explicit_constraints(self, constraint_names: List[str]) -> List[Any]:
        """Get constraints by explicit names."""
        if not self.manifold:
            return []

        all_constraints = self.manifold.get_all_constraints()
        return [c for c in all_constraints if c.name in constraint_names]

    async def _bind_constraints(
        self,
        ssf: SSFDefinition,
        persona: Persona,
        agent: A0AgentInstance,
        execution_context: ExecutionContext,
    ) -> BoundConstraintContext:
        """Create execution context with bound constraints."""
        binding = ssf.constraint_binding

        # Compile forbidden patterns
        forbidden_patterns = {
            "input": [re.compile(p, re.IGNORECASE) for p in binding.forbidden_input_patterns],
            "output": [re.compile(p, re.IGNORECASE) for p in binding.forbidden_output_patterns],
        }

        # Get constraint names
        if binding.mode == ConstraintBindingMode.FULL and self.manifold:
            constraint_names = [c.name for c in self.manifold.get_all_constraints()]
        elif binding.mode == ConstraintBindingMode.FILTERED:
            constraint_names = [c.name for c in self._get_category_constraints(ssf.category)]
        else:
            constraint_names = binding.explicit_constraints or []

        return BoundConstraintContext(
            ssf=ssf,
            persona_id=persona.id,
            agent_id=agent.agent_id,
            constraints=constraint_names,
            virtue_state=persona.virtue_state or {},
            forbidden_patterns=forbidden_patterns,
            execution_context=execution_context,
            timeout_seconds=execution_context.timeout_override or ssf.timeout_seconds,
        )

    async def _execute(
        self,
        ssf: SSFDefinition,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute the SSF handler.

        This is the actual execution of the SSF logic.
        """
        if not ssf.handler:
            raise SSFExecutionError("SSF has no handler defined")

        handler = ssf.handler

        # Execute with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_handler(handler, inputs, context),
                timeout=context.timeout_seconds,
            )
            return result
        except asyncio.TimeoutError:
            raise SSFTimeoutError(f"Execution timed out after {context.timeout_seconds}s")

    async def _execute_handler(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute a specific handler type."""
        if handler.type == HandlerType.INLINE:
            return await self._execute_inline(handler, inputs, context)
        elif handler.type == HandlerType.MODULE:
            return await self._execute_module(handler, inputs, context)
        elif handler.type == HandlerType.MCP:
            return await self._execute_mcp(handler, inputs, context)
        elif handler.type == HandlerType.REMOTE:
            return await self._execute_remote(handler, inputs, context)
        elif handler.type == HandlerType.CONTAINER:
            return await self._execute_container(handler, inputs, context)
        else:
            raise SSFExecutionError(f"Unknown handler type: {handler.type}")

    async def _execute_inline(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute inline Python code handler."""
        if not handler.inline_code:
            raise SSFExecutionError("Inline handler has no code")

        # Create restricted execution environment
        local_vars = {"inputs": inputs, "result": None}

        # Execute the code
        try:
            exec(handler.inline_code, {"__builtins__": {}}, local_vars)
            return local_vars.get("result")
        except Exception as e:
            raise SSFExecutionError(f"Inline execution error: {str(e)}")

    async def _execute_module(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute Python module handler."""
        if not handler.module_path or not handler.function_name:
            raise SSFExecutionError("Module handler missing path or function name")

        # Check cache first
        cache_key = f"{handler.module_path}.{handler.function_name}"
        func = self._handler_cache.get(cache_key)

        if not func:
            try:
                module = importlib.import_module(handler.module_path)
                func = getattr(module, handler.function_name)
                self._handler_cache[cache_key] = func
            except (ImportError, AttributeError) as e:
                raise SSFExecutionError(f"Failed to load module handler: {str(e)}")

        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(**inputs)
            else:
                return func(**inputs)
        except Exception as e:
            raise SSFExecutionError(f"Module execution error: {str(e)}")

    async def _execute_mcp(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute MCP tool handler."""
        if not handler.mcp_server or not handler.mcp_tool:
            raise SSFExecutionError("MCP handler missing server or tool name")

        # This would integrate with the MCP client
        # For now, return a placeholder
        logger.info(f"MCP call: {handler.mcp_server}/{handler.mcp_tool}")
        return {"status": "mcp_not_implemented", "server": handler.mcp_server, "tool": handler.mcp_tool}

    async def _execute_remote(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute remote HTTP handler."""
        if not handler.remote_url:
            raise SSFExecutionError("Remote handler missing URL")

        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                headers = handler.remote_headers or {}
                headers["Content-Type"] = "application/json"

                async with session.request(
                    method=handler.remote_method,
                    url=handler.remote_url,
                    json=inputs,
                    headers=headers,
                ) as response:
                    if response.status >= 400:
                        text = await response.text()
                        raise SSFExecutionError(f"Remote call failed: {response.status} - {text}")
                    return await response.json()

        except ImportError:
            raise SSFExecutionError("aiohttp not available for remote handlers")
        except Exception as e:
            raise SSFExecutionError(f"Remote execution error: {str(e)}")

    async def _execute_container(
        self,
        handler: SSFHandler,
        inputs: Dict[str, Any],
        context: BoundConstraintContext,
    ) -> Optional[Dict[str, Any]]:
        """Execute container handler (placeholder)."""
        logger.info(f"Container call: {handler.container_image}")
        return {"status": "container_not_implemented", "image": handler.container_image}

    async def _log_execution(
        self,
        ssf: SSFDefinition,
        inputs: Dict[str, Any],
        output: Optional[Dict[str, Any]],
        persona: Persona,
        agent: A0AgentInstance,
        duration: float,
        context: ExecutionContext,
    ) -> None:
        """Log successful execution to shared memory."""
        if not self.memory_client:
            return

        try:
            # Build record for future storage (depends on Graphiti interface)
            _execution_record = {  # noqa: F841
                "type": "ssf_execution",
                "ssf_id": str(ssf.id),
                "ssf_name": ssf.name,
                "category": ssf.category.value,
                "risk_level": ssf.risk_level.value,
                "persona_id": str(persona.id),
                "agent_id": agent.agent_id,
                "community_id": persona.community_id,
                "inputs_summary": self._summarize_data(inputs),
                "output_summary": self._summarize_data(output) if output else None,
                "duration_seconds": duration,
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": str(context.request_id),
            }
            # TODO: Store _execution_record to memory_client when interface is ready
            logger.debug(f"SSF execution logged: {ssf.name} ({duration:.3f}s)")

        except Exception as e:
            logger.error(f"Failed to log SSF execution: {e}")

    async def _log_blocked_execution(
        self,
        ssf: SSFDefinition,
        inputs: Dict[str, Any],
        output: Optional[Dict[str, Any]],
        persona: Persona,
        agent: A0AgentInstance,
        validation: ManifoldValidation,
        direction: str,
    ) -> None:
        """Log blocked execution to shared memory."""
        if not self.memory_client:
            return

        try:
            # Build record for future storage
            _blocked_record = {  # noqa: F841
                "type": "ssf_blocked",
                "ssf_id": str(ssf.id),
                "ssf_name": ssf.name,
                "category": ssf.category.value,
                "risk_level": ssf.risk_level.value,
                "persona_id": str(persona.id),
                "agent_id": agent.agent_id,
                "direction": direction,
                "violations": validation.violations,
                "violation": validation.violation,
                "timestamp": datetime.utcnow().isoformat(),
            }
            # TODO: Store _blocked_record to memory_client when interface is ready
            logger.warning(f"SSF blocked: {ssf.name} - {validation.violation}")

        except Exception as e:
            logger.error(f"Failed to log blocked SSF execution: {e}")

    def _summarize_data(self, data: Any, max_length: int = 200) -> str:
        """Create a safe summary of data for logging."""
        if data is None:
            return "null"

        try:
            import json
            text = json.dumps(data)
            if len(text) > max_length:
                return text[:max_length] + "..."
            return text
        except Exception:
            return str(data)[:max_length]

    def get_stats(self) -> Dict[str, Any]:
        """Get runtime statistics."""
        avg_time = (
            self._total_execution_time / self._successful_invocations
            if self._successful_invocations > 0
            else 0
        )

        return {
            "total_invocations": self._total_invocations,
            "successful_invocations": self._successful_invocations,
            "blocked_invocations": self._blocked_invocations,
            "success_rate": self._successful_invocations / max(self._total_invocations, 1),
            "average_execution_time_seconds": avg_time,
            "total_execution_time_seconds": self._total_execution_time,
            "cached_handlers": len(self._handler_cache),
        }

    def clear_handler_cache(self) -> None:
        """Clear the handler cache."""
        self._handler_cache.clear()
