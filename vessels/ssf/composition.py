"""
SSF Composition - Chaining and Parallel Execution.

Composes multiple SSFs into workflows:
- Sequential composition (pipelines)
- Parallel composition (concurrent execution)
- Conditional composition (branching logic)

All SSFs in a composition share the same constraint binding from
the invoking persona.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
from uuid import UUID, uuid4

from .schema import (
    SSFResult,
    SSFStatus,
    ExecutionContext,
    SSFPermissions,
)
from .runtime import SSFRuntime, Persona, A0AgentInstance

logger = logging.getLogger(__name__)


class CompositionStatus(str, Enum):
    """Status of a composition execution."""
    COMPLETE = "complete"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SSFStep:
    """A single step in an SSF composition."""
    ssf_id: UUID
    inputs: Dict[str, Any] = field(default_factory=dict)

    # Optional: reference previous outputs using template syntax
    # e.g., {"data": "{{step_0.output.result}}"}
    input_templates: Dict[str, str] = field(default_factory=dict)

    # Step metadata
    name: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ssf_id": str(self.ssf_id),
            "inputs": self.inputs,
            "input_templates": self.input_templates,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SSFStep":
        """Create from dictionary."""
        return cls(
            ssf_id=UUID(d["ssf_id"]) if isinstance(d["ssf_id"], str) else d["ssf_id"],
            inputs=d.get("inputs", {}),
            input_templates=d.get("input_templates", {}),
            name=d.get("name"),
            description=d.get("description"),
        )


@dataclass
class SSFStepResult:
    """Result of executing a single step."""
    step_index: int
    ssf_id: UUID
    ssf_name: Optional[str]
    result: SSFResult
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_index": self.step_index,
            "ssf_id": str(self.ssf_id),
            "ssf_name": self.ssf_name,
            "result": self.result.to_dict(),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class CompositionResult:
    """Result of a composition execution."""
    status: CompositionStatus
    completed_steps: int
    total_steps: int
    results: List[SSFStepResult] = field(default_factory=list)
    final_output: Optional[Dict[str, Any]] = None
    failure_reason: Optional[str] = None
    execution_time_seconds: float = 0.0

    # Composition metadata
    composition_id: UUID = field(default_factory=uuid4)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "status": self.status.value,
            "completed_steps": self.completed_steps,
            "total_steps": self.total_steps,
            "results": [r.to_dict() for r in self.results],
            "final_output": self.final_output,
            "failure_reason": self.failure_reason,
            "execution_time_seconds": self.execution_time_seconds,
            "composition_id": str(self.composition_id),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @property
    def success(self) -> bool:
        """Check if composition completed successfully."""
        return self.status == CompositionStatus.COMPLETE


@dataclass
class ConditionalBranch:
    """A conditional branch in a composition."""
    condition_ssf_id: UUID
    condition_inputs: Dict[str, Any]
    true_branch: List[SSFStep]
    false_branch: List[SSFStep]


class SSFComposer:
    """
    Composes multiple SSFs into workflows.

    A0 agents use this to chain SSF invocations for complex tasks.
    All SSFs in a composition share the same constraint binding.

    Composition patterns:
    - Sequential: Steps execute one after another, outputs flow forward
    - Parallel: Steps execute concurrently, results collected
    - Conditional: Branch based on SSF output
    """

    def __init__(
        self,
        runtime: SSFRuntime,
        max_parallel: int = 5,
    ):
        """
        Initialize the SSF composer.

        Args:
            runtime: SSF runtime for execution
            max_parallel: Maximum concurrent SSF executions
        """
        self.runtime = runtime
        self.max_parallel = max_parallel

        # Execution statistics
        self._total_compositions = 0
        self._completed_compositions = 0
        self._failed_compositions = 0

    async def compose_sequence(
        self,
        steps: List[SSFStep],
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
        execution_context: Optional[ExecutionContext] = None,
    ) -> CompositionResult:
        """
        Execute a sequence of SSFs where each output can feed into the next.

        If any step fails or is blocked by constraints, the composition stops.

        Args:
            steps: List of SSF steps to execute
            invoking_persona: Persona for constraint binding
            invoking_agent: Agent instance
            execution_context: Optional execution context

        Returns:
            CompositionResult with execution details
        """
        self._total_compositions += 1
        start_time = datetime.utcnow()
        execution_context = execution_context or ExecutionContext()

        # Check composition permissions
        permissions = invoking_persona.ssf_permissions
        if not permissions.can_compose_ssfs:
            return CompositionResult(
                status=CompositionStatus.FAILED,
                completed_steps=0,
                total_steps=len(steps),
                failure_reason="Persona lacks composition permission",
            )

        if len(steps) > permissions.max_composition_length:
            return CompositionResult(
                status=CompositionStatus.FAILED,
                completed_steps=0,
                total_steps=len(steps),
                failure_reason=f"Composition exceeds max length ({len(steps)} > {permissions.max_composition_length})",
            )

        results: List[SSFStepResult] = []
        previous_output: Optional[Dict[str, Any]] = None

        for i, step in enumerate(steps):
            step_start = datetime.utcnow()

            # Resolve inputs (may reference previous outputs)
            resolved_inputs = self._resolve_inputs(
                step.inputs,
                step.input_templates,
                previous_output,
                results,
            )

            # Invoke the SSF
            result = await self.runtime.invoke(
                ssf_id=step.ssf_id,
                inputs=resolved_inputs,
                invoking_persona=invoking_persona,
                invoking_agent=invoking_agent,
                execution_context=execution_context,
            )

            step_result = SSFStepResult(
                step_index=i,
                ssf_id=step.ssf_id,
                ssf_name=result.ssf_name,
                result=result,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )
            results.append(step_result)

            # Stop on failure
            if result.status != SSFStatus.SUCCESS:
                self._failed_compositions += 1
                return CompositionResult(
                    status=CompositionStatus.PARTIAL,
                    completed_steps=i,
                    total_steps=len(steps),
                    results=results,
                    failure_reason=result.error or result.status.value,
                    execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
                    completed_at=datetime.utcnow(),
                )

            previous_output = result.output

        self._completed_compositions += 1
        return CompositionResult(
            status=CompositionStatus.COMPLETE,
            completed_steps=len(steps),
            total_steps=len(steps),
            results=results,
            final_output=previous_output,
            execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
            completed_at=datetime.utcnow(),
        )

    async def compose_parallel(
        self,
        steps: List[SSFStep],
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
        execution_context: Optional[ExecutionContext] = None,
        fail_fast: bool = True,
    ) -> CompositionResult:
        """
        Execute multiple SSFs in parallel.

        All SSFs share the same constraint binding from the invoking persona.

        Args:
            steps: List of SSF steps to execute concurrently
            invoking_persona: Persona for constraint binding
            invoking_agent: Agent instance
            execution_context: Optional execution context
            fail_fast: If True, cancel remaining SSFs on first failure

        Returns:
            CompositionResult with all execution results
        """
        self._total_compositions += 1
        start_time = datetime.utcnow()
        execution_context = execution_context or ExecutionContext()

        # Check permissions
        permissions = invoking_persona.ssf_permissions
        if not permissions.can_parallel_compose:
            return CompositionResult(
                status=CompositionStatus.FAILED,
                completed_steps=0,
                total_steps=len(steps),
                failure_reason="Persona lacks parallel composition permission",
            )

        if len(steps) > permissions.max_parallel_ssfs:
            return CompositionResult(
                status=CompositionStatus.FAILED,
                completed_steps=0,
                total_steps=len(steps),
                failure_reason=f"Too many parallel SSFs ({len(steps)} > {permissions.max_parallel_ssfs})",
            )

        # Create tasks for parallel execution
        async def execute_step(index: int, step: SSFStep) -> SSFStepResult:
            step_start = datetime.utcnow()
            result = await self.runtime.invoke(
                ssf_id=step.ssf_id,
                inputs=step.inputs,
                invoking_persona=invoking_persona,
                invoking_agent=invoking_agent,
                execution_context=execution_context,
            )
            return SSFStepResult(
                step_index=index,
                ssf_id=step.ssf_id,
                ssf_name=result.ssf_name,
                result=result,
                started_at=step_start,
                completed_at=datetime.utcnow(),
            )

        # Execute with concurrency limit
        semaphore = asyncio.Semaphore(self.max_parallel)

        async def limited_execute(index: int, step: SSFStep) -> SSFStepResult:
            async with semaphore:
                return await execute_step(index, step)

        # Run all tasks
        if fail_fast:
            # Use gather with return_exceptions=False to fail fast
            try:
                tasks = [limited_execute(i, step) for i, step in enumerate(steps)]
                results = await asyncio.gather(*tasks)
            except Exception as e:
                self._failed_compositions += 1
                return CompositionResult(
                    status=CompositionStatus.FAILED,
                    completed_steps=0,
                    total_steps=len(steps),
                    failure_reason=str(e),
                    execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
                )
        else:
            # Run all even if some fail
            tasks = [limited_execute(i, step) for i, step in enumerate(steps)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        step_results: List[SSFStepResult] = []
        failed_count = 0
        outputs: List[Dict[str, Any]] = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Task raised an exception
                step_results.append(SSFStepResult(
                    step_index=i,
                    ssf_id=steps[i].ssf_id,
                    ssf_name=None,
                    result=SSFResult(
                        status=SSFStatus.ERROR,
                        error=str(result),
                    ),
                ))
                failed_count += 1
            else:
                step_results.append(result)
                if result.result.status == SSFStatus.SUCCESS:
                    outputs.append(result.result.output or {})
                else:
                    failed_count += 1

        # Determine overall status
        if failed_count == 0:
            status = CompositionStatus.COMPLETE
            self._completed_compositions += 1
        elif failed_count < len(steps):
            status = CompositionStatus.PARTIAL
        else:
            status = CompositionStatus.FAILED
            self._failed_compositions += 1

        return CompositionResult(
            status=status,
            completed_steps=len(steps) - failed_count,
            total_steps=len(steps),
            results=step_results,
            final_output={"results": outputs} if outputs else None,
            execution_time_seconds=(datetime.utcnow() - start_time).total_seconds(),
            completed_at=datetime.utcnow(),
        )

    async def compose_conditional(
        self,
        condition_ssf: UUID,
        condition_inputs: Dict[str, Any],
        true_branch: List[SSFStep],
        false_branch: List[SSFStep],
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
        execution_context: Optional[ExecutionContext] = None,
    ) -> CompositionResult:
        """
        Conditional composition based on SSF output.

        The condition SSF should return a boolean-coercible value in its output.
        If output["result"] or output["condition"] is truthy, true_branch executes.

        Args:
            condition_ssf: UUID of SSF to evaluate condition
            condition_inputs: Inputs for condition SSF
            true_branch: Steps to execute if condition is true
            false_branch: Steps to execute if condition is false
            invoking_persona: Persona for constraint binding
            invoking_agent: Agent instance
            execution_context: Optional execution context

        Returns:
            CompositionResult from the chosen branch
        """
        execution_context = execution_context or ExecutionContext()

        # First, evaluate the condition
        condition_result = await self.runtime.invoke(
            ssf_id=condition_ssf,
            inputs=condition_inputs,
            invoking_persona=invoking_persona,
            invoking_agent=invoking_agent,
            execution_context=execution_context,
        )

        if condition_result.status != SSFStatus.SUCCESS:
            return CompositionResult(
                status=CompositionStatus.FAILED,
                completed_steps=0,
                total_steps=1 + max(len(true_branch), len(false_branch)),
                failure_reason=f"Condition evaluation failed: {condition_result.error}",
            )

        # Determine which branch to execute
        output = condition_result.output or {}
        condition_value = output.get("result", output.get("condition", False))

        if condition_value:
            branch = true_branch
            branch_name = "true"
        else:
            branch = false_branch
            branch_name = "false"

        logger.debug(f"Conditional composition taking {branch_name} branch")

        # Execute the chosen branch
        return await self.compose_sequence(
            steps=branch,
            invoking_persona=invoking_persona,
            invoking_agent=invoking_agent,
            execution_context=execution_context,
        )

    async def compose_loop(
        self,
        steps: List[SSFStep],
        condition_ssf: UUID,
        condition_inputs_template: Dict[str, str],
        invoking_persona: Persona,
        invoking_agent: A0AgentInstance,
        execution_context: Optional[ExecutionContext] = None,
        max_iterations: int = 10,
    ) -> CompositionResult:
        """
        Execute steps repeatedly while a condition is true.

        Args:
            steps: Steps to execute each iteration
            condition_ssf: SSF to check loop continuation
            condition_inputs_template: Template for condition inputs
            invoking_persona: Persona for constraint binding
            invoking_agent: Agent instance
            execution_context: Optional execution context
            max_iterations: Safety limit on iterations

        Returns:
            CompositionResult with all iteration results
        """
        execution_context = execution_context or ExecutionContext()
        all_results: List[SSFStepResult] = []
        iteration = 0
        last_output: Optional[Dict[str, Any]] = None

        while iteration < max_iterations:
            # Check condition
            condition_inputs = self._resolve_templates(
                condition_inputs_template,
                last_output,
                all_results,
            )

            condition_result = await self.runtime.invoke(
                ssf_id=condition_ssf,
                inputs=condition_inputs,
                invoking_persona=invoking_persona,
                invoking_agent=invoking_agent,
                execution_context=execution_context,
            )

            if condition_result.status != SSFStatus.SUCCESS:
                return CompositionResult(
                    status=CompositionStatus.FAILED,
                    completed_steps=len(all_results),
                    total_steps=len(all_results) + 1,
                    results=all_results,
                    failure_reason=f"Loop condition failed: {condition_result.error}",
                )

            # Check if we should continue
            output = condition_result.output or {}
            if not output.get("result", output.get("continue", False)):
                break

            # Execute iteration
            iteration_result = await self.compose_sequence(
                steps=steps,
                invoking_persona=invoking_persona,
                invoking_agent=invoking_agent,
                execution_context=execution_context,
            )

            all_results.extend(iteration_result.results)

            if not iteration_result.success:
                return CompositionResult(
                    status=CompositionStatus.PARTIAL,
                    completed_steps=len(all_results),
                    total_steps=len(all_results),
                    results=all_results,
                    failure_reason=iteration_result.failure_reason,
                )

            last_output = iteration_result.final_output
            iteration += 1

        return CompositionResult(
            status=CompositionStatus.COMPLETE,
            completed_steps=len(all_results),
            total_steps=len(all_results),
            results=all_results,
            final_output=last_output,
        )

    def _resolve_inputs(
        self,
        static_inputs: Dict[str, Any],
        templates: Dict[str, str],
        previous_output: Optional[Dict[str, Any]],
        all_results: List[SSFStepResult],
    ) -> Dict[str, Any]:
        """
        Resolve inputs from static values and templates.

        Templates can reference:
        - {{previous.key}} - Value from previous step output
        - {{step_N.output.key}} - Value from step N's output
        - {{step_N.result.status}} - Status from step N
        """
        resolved = dict(static_inputs)

        for key, template in templates.items():
            value = self._resolve_template(template, previous_output, all_results)
            if value is not None:
                resolved[key] = value

        return resolved

    def _resolve_templates(
        self,
        templates: Dict[str, str],
        previous_output: Optional[Dict[str, Any]],
        all_results: List[SSFStepResult],
    ) -> Dict[str, Any]:
        """Resolve all templates to values."""
        resolved = {}
        for key, template in templates.items():
            value = self._resolve_template(template, previous_output, all_results)
            if value is not None:
                resolved[key] = value
        return resolved

    def _resolve_template(
        self,
        template: str,
        previous_output: Optional[Dict[str, Any]],
        all_results: List[SSFStepResult],
    ) -> Any:
        """Resolve a single template string."""
        import re

        # Match {{path.to.value}}
        match = re.match(r'\{\{(.+?)\}\}', template.strip())
        if not match:
            return template

        path = match.group(1).strip()
        parts = path.split('.')

        if parts[0] == 'previous':
            # Reference previous step output
            if previous_output and len(parts) > 1:
                return self._get_nested(previous_output, parts[1:])
        elif parts[0].startswith('step_'):
            # Reference specific step
            try:
                step_index = int(parts[0].split('_')[1])
                if step_index < len(all_results):
                    result = all_results[step_index]
                    if len(parts) > 1:
                        if parts[1] == 'output':
                            return self._get_nested(result.result.output or {}, parts[2:])
                        elif parts[1] == 'result':
                            return getattr(result.result, parts[2], None)
            except (ValueError, IndexError):
                pass

        return None

    def _get_nested(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get a nested value from a dictionary."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def get_stats(self) -> Dict[str, Any]:
        """Get composer statistics."""
        total = self._total_compositions or 1
        return {
            "total_compositions": self._total_compositions,
            "completed_compositions": self._completed_compositions,
            "failed_compositions": self._failed_compositions,
            "success_rate": self._completed_compositions / total,
        }
