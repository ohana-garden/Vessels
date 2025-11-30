"""
Agent Orchestrator - Coordinates multi-agent pipelines for complex tasks.

The orchestrator manages agent workflows that involve multiple specialized agents:
- Planner: Breaks down tasks into steps
- Architect: Designs solutions
- Developer: Implements solutions
- Tester: Validates implementations
- Deployer: Deploys completed work

Supports:
- Sequential pipelines (A -> B -> C)
- Parallel fan-out (A -> [B, C, D] -> E)
- Conditional routing (if X then A else B)
- Error handling and recovery

REQUIRES AgentZeroCore - all agent operations go through A0.
- Orchestrator registers with AgentZeroCore as a system-level coordinator
- Uses A0's spawn_agents for creating pipeline agents

DEPRECATED: Standalone operation without A0 is no longer supported.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING
import asyncio
import uuid

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore, AgentSpecification

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Standard agent types in the orchestration pipeline."""
    PLANNER = "planner"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    DEPLOYER = "deployer"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """Status of a task in the pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent_id: str
    agent_type: AgentType
    success: bool
    output: Any
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineTask:
    """A task in the orchestration pipeline."""
    task_id: str
    agent_type: AgentType
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[AgentResult] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class PipelineDefinition:
    """Definition of an orchestration pipeline."""
    pipeline_id: str
    name: str
    description: str
    stages: List[Dict[str, Any]]  # List of stage definitions
    error_handling: str = "stop"  # stop, continue, retry
    max_retries: int = 2
    timeout_seconds: int = 300


@dataclass
class PipelineExecution:
    """An execution instance of a pipeline."""
    execution_id: str
    pipeline_id: str
    status: TaskStatus
    tasks: List[PipelineTask]
    started_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Dict[str, AgentResult] = field(default_factory=dict)


class AgentFactory:
    """
    DEPRECATED: Use AgentZeroCore.spawn_agents() instead.

    This factory is no longer used - all agents are spawned through A0.
    Kept for backward compatibility but will be removed in future versions.
    """

    def __init__(self):
        import warnings
        warnings.warn(
            "AgentFactory is deprecated. Use AgentZeroCore.spawn_agents() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self._agent_classes: Dict[AgentType, type] = {}
        self._agent_configs: Dict[AgentType, Dict[str, Any]] = {}

    def register(
        self,
        agent_type: AgentType,
        agent_class: type,
        config: Optional[Dict[str, Any]] = None
    ):
        """Register an agent class for a type."""
        self._agent_classes[agent_type] = agent_class
        self._agent_configs[agent_type] = config or {}
        logger.info(f"Registered agent: {agent_type.value}")

    def create(
        self,
        agent_type: AgentType,
        agent_id: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create an agent instance."""
        if agent_type not in self._agent_classes:
            raise ValueError(f"No agent registered for type: {agent_type}")

        agent_class = self._agent_classes[agent_type]
        config = {**self._agent_configs[agent_type], **kwargs}

        agent_id = agent_id or f"{agent_type.value}_{uuid.uuid4().hex[:8]}"

        return agent_class(agent_id=agent_id, **config)


class Orchestrator:
    """
    Coordinates multi-agent pipelines for complex tasks.

    The orchestrator:
    1. Accepts pipeline definitions (sequence of agent stages)
    2. Manages task execution order based on dependencies
    3. Routes outputs between agents
    4. Handles errors and retries
    5. Records results to community memory

    REQUIRES AgentZeroCore - all agent operations go through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        vessel_id: Optional[str] = None,
        community_memory=None
    ):
        """
        Initialize orchestrator.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            vessel_id: Vessel ID for spawning agents via A0
            community_memory: Community memory for storing results
        """
        if agent_zero is None:
            raise ValueError("Orchestrator requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.vessel_id = vessel_id
        self.community_memory = community_memory or agent_zero.memory_system

        self.pipelines: Dict[str, PipelineDefinition] = {}
        self.executions: Dict[str, PipelineExecution] = {}

        # A0 spawned agents (agent_type -> agent_id)
        self._a0_agents: Dict[AgentType, str] = {}

        # Register with A0
        self._register_with_a0()

    def register_pipeline(self, pipeline: PipelineDefinition):
        """Register a pipeline definition."""
        self.pipelines[pipeline.pipeline_id] = pipeline
        logger.info(f"Registered pipeline: {pipeline.name} ({pipeline.pipeline_id})")

    def register_handler(
        self,
        agent_type: AgentType,
        handler: Callable[[Dict[str, Any]], AgentResult]
    ):
        """
        Register a handler function for an agent type.

        Handlers are simpler alternatives to full agent classes.

        Args:
            agent_type: Type of agent
            handler: Function that takes input and returns AgentResult
        """
        self._default_handlers[agent_type] = handler
        logger.info(f"Registered handler for: {agent_type.value}")

    async def execute_pipeline(
        self,
        pipeline_id: str,
        initial_input: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> PipelineExecution:
        """
        Execute a pipeline with the given input.

        Args:
            pipeline_id: ID of pipeline to execute
            initial_input: Input data for the first stage
            context: Optional context to pass to all agents

        Returns:
            PipelineExecution with results
        """
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        pipeline = self.pipelines[pipeline_id]
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        # Create tasks from pipeline stages
        tasks = self._create_tasks(pipeline, initial_input)

        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_id=pipeline_id,
            status=TaskStatus.IN_PROGRESS,
            tasks=tasks,
            started_at=datetime.utcnow()
        )

        self.executions[execution_id] = execution
        logger.info(f"Starting pipeline execution: {execution_id}")

        try:
            # Execute tasks in dependency order
            await self._execute_tasks(execution, context or {})

            # Check if all tasks completed successfully
            all_completed = all(t.status == TaskStatus.COMPLETED for t in execution.tasks)
            execution.status = TaskStatus.COMPLETED if all_completed else TaskStatus.FAILED

        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            execution.status = TaskStatus.FAILED
            execution.error = str(e)

        execution.completed_at = datetime.utcnow()

        # Store results in community memory
        await self._store_results(execution)

        logger.info(f"Pipeline execution completed: {execution_id} ({execution.status.value})")
        return execution

    def _create_tasks(
        self,
        pipeline: PipelineDefinition,
        initial_input: Dict[str, Any]
    ) -> List[PipelineTask]:
        """Create tasks from pipeline stages."""
        tasks = []
        prev_task_id = None

        for i, stage in enumerate(pipeline.stages):
            task_id = f"task_{i}_{uuid.uuid4().hex[:8]}"

            # Parse agent type
            agent_type_str = stage.get("agent_type", "custom")
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                agent_type = AgentType.CUSTOM

            # Set input data
            if i == 0:
                input_data = initial_input
            else:
                # Will be filled from previous task output
                input_data = {"_from_previous": True}

            # Set dependencies
            dependencies = []
            if stage.get("depends_on"):
                dependencies = stage["depends_on"]
            elif prev_task_id:
                dependencies = [prev_task_id]

            task = PipelineTask(
                task_id=task_id,
                agent_type=agent_type,
                input_data=input_data,
                dependencies=dependencies
            )

            tasks.append(task)
            prev_task_id = task_id

        return tasks

    async def _execute_tasks(
        self,
        execution: PipelineExecution,
        context: Dict[str, Any]
    ):
        """Execute tasks in dependency order."""
        task_map = {t.task_id: t for t in execution.tasks}
        completed_tasks: Dict[str, AgentResult] = {}

        while True:
            # Find tasks ready to execute (all dependencies met)
            ready_tasks = [
                t for t in execution.tasks
                if t.status == TaskStatus.PENDING
                and all(
                    task_map.get(dep, PipelineTask(
                        task_id="", agent_type=AgentType.CUSTOM, input_data={}
                    )).status == TaskStatus.COMPLETED
                    for dep in t.dependencies
                )
            ]

            if not ready_tasks:
                # Check if we're stuck (pending tasks with unmet dependencies)
                pending = [t for t in execution.tasks if t.status == TaskStatus.PENDING]
                if pending:
                    logger.warning(f"Pipeline stuck with {len(pending)} pending tasks")
                    for t in pending:
                        t.status = TaskStatus.BLOCKED
                break

            # Execute ready tasks (could be parallel)
            for task in ready_tasks:
                # Prepare input
                if task.input_data.get("_from_previous"):
                    # Get output from dependencies
                    dep_outputs = {}
                    for dep_id in task.dependencies:
                        if dep_id in completed_tasks:
                            dep_outputs[dep_id] = completed_tasks[dep_id].output
                    task.input_data = {"dependencies": dep_outputs, **context}

                # Execute task
                result = await self._execute_single_task(task, context)
                task.result = result

                if result.success:
                    task.status = TaskStatus.COMPLETED
                    completed_tasks[task.task_id] = result
                    execution.results[task.task_id] = result
                else:
                    task.status = TaskStatus.FAILED
                    logger.error(f"Task {task.task_id} failed: {result.error}")

                    # Check error handling policy
                    pipeline = self.pipelines.get(execution.pipeline_id)
                    if pipeline and pipeline.error_handling == "stop":
                        raise RuntimeError(f"Task failed: {result.error}")

    async def _execute_single_task(
        self,
        task: PipelineTask,
        context: Dict[str, Any]
    ) -> AgentResult:
        """Execute a single task."""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        start_time = datetime.utcnow()

        try:
            # Try handler first
            if task.agent_type in self._default_handlers:
                handler = self._default_handlers[task.agent_type]
                result = handler({**task.input_data, **context})

                if not isinstance(result, AgentResult):
                    result = AgentResult(
                        agent_id=f"handler_{task.agent_type.value}",
                        agent_type=task.agent_type,
                        success=True,
                        output=result
                    )

            # Try agent factory
            elif task.agent_type in self.agent_factory._agent_classes:
                agent = self.agent_factory.create(task.agent_type)
                output = await self._run_agent(agent, task.input_data, context)
                result = AgentResult(
                    agent_id=agent.agent_id if hasattr(agent, 'agent_id') else str(id(agent)),
                    agent_type=task.agent_type,
                    success=True,
                    output=output
                )

            else:
                # No handler or agent - use passthrough
                logger.warning(f"No handler for {task.agent_type}, using passthrough")
                result = AgentResult(
                    agent_id="passthrough",
                    agent_type=task.agent_type,
                    success=True,
                    output=task.input_data
                )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.duration_ms = duration

        except Exception as e:
            logger.error(f"Task execution error: {e}")
            result = AgentResult(
                agent_id="error",
                agent_type=task.agent_type,
                success=False,
                output=None,
                error=str(e)
            )

        task.completed_at = datetime.utcnow()
        return result

    async def _run_agent(
        self,
        agent: Any,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Any:
        """Run an agent with input data."""
        # Try different execution methods
        if hasattr(agent, 'execute'):
            if asyncio.iscoroutinefunction(agent.execute):
                return await agent.execute(input_data, context)
            return agent.execute(input_data, context)

        if hasattr(agent, 'run'):
            if asyncio.iscoroutinefunction(agent.run):
                return await agent.run(input_data)
            return agent.run(input_data)

        if callable(agent):
            return agent(input_data, context)

        raise ValueError(f"Agent has no execute/run method: {type(agent)}")

    async def _store_results(self, execution: PipelineExecution):
        """Store pipeline results in community memory."""
        if not self.community_memory:
            return

        try:
            # Store execution summary
            summary = {
                "type": "pipeline_execution",
                "execution_id": execution.execution_id,
                "pipeline_id": execution.pipeline_id,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat(),
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "task_count": len(execution.tasks),
                "completed_count": sum(1 for t in execution.tasks if t.status == TaskStatus.COMPLETED),
                "failed_count": sum(1 for t in execution.tasks if t.status == TaskStatus.FAILED),
            }

            self.community_memory.store_knowledge(
                agent_id="orchestrator",
                knowledge={
                    "domain": "orchestration",
                    "summary": summary,
                    "tags": ["pipeline", "execution", execution.pipeline_id]
                }
            )

        except Exception as e:
            logger.warning(f"Failed to store results: {e}")

    def get_execution(self, execution_id: str) -> Optional[PipelineExecution]:
        """Get a pipeline execution by ID."""
        return self.executions.get(execution_id)

    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get status summary of an execution."""
        execution = self.executions.get(execution_id)
        if not execution:
            return None

        return {
            "execution_id": execution.execution_id,
            "pipeline_id": execution.pipeline_id,
            "status": execution.status.value,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "agent_type": t.agent_type.value,
                    "status": t.status.value,
                    "error": t.result.error if t.result else None
                }
                for t in execution.tasks
            ]
        }

    # =========================================================================
    # A0 Integration Methods
    # =========================================================================

    def _register_with_a0(self):
        """Register orchestrator with AgentZeroCore."""
        if not self.agent_zero:
            return

        try:
            # Register as system-level orchestrator
            self.agent_zero.orchestrator = self
            logger.info("Orchestrator registered with AgentZeroCore")
        except Exception as e:
            logger.warning(f"Failed to register with A0: {e}")

    def _spawn_a0_agent(self, agent_type: AgentType) -> Optional[str]:
        """
        Spawn an agent via A0 for pipeline execution.

        Args:
            agent_type: Type of agent to spawn

        Returns:
            Agent ID if successful, None otherwise
        """
        if not self.agent_zero:
            return None

        # Check if already spawned
        if agent_type in self._a0_agents:
            return self._a0_agents[agent_type]

        try:
            from agent_zero_core import AgentSpecification

            # Create specification for this agent type
            spec = AgentSpecification(
                name=f"Pipeline{agent_type.value.title()}",
                description=f"Pipeline agent for {agent_type.value} tasks",
                capabilities=[agent_type.value, "pipeline_execution"],
                tools_needed=self._get_tools_for_agent_type(agent_type),
                communication_style="collaborative",
                autonomy_level="medium",
                specialization=agent_type.value
            )

            # Spawn via A0
            agent_ids = self.agent_zero.spawn_agents(
                [spec],
                vessel_id=self.vessel_id
            )

            if agent_ids:
                self._a0_agents[agent_type] = agent_ids[0]
                logger.info(f"Spawned A0 agent for {agent_type.value}: {agent_ids[0]}")
                return agent_ids[0]

        except Exception as e:
            logger.warning(f"Failed to spawn A0 agent for {agent_type.value}: {e}")

        return None

    def _get_tools_for_agent_type(self, agent_type: AgentType) -> List[str]:
        """Get tools needed for a specific agent type."""
        tools_map = {
            AgentType.PLANNER: ["task_breakdown", "requirement_analysis"],
            AgentType.ARCHITECT: ["design_tools", "diagram_generation"],
            AgentType.DEVELOPER: ["code_editor", "git", "file_system"],
            AgentType.TESTER: ["test_runner", "coverage_analysis"],
            AgentType.DEPLOYER: ["deployment_tools", "environment_config"],
            AgentType.ANALYST: ["data_analysis", "visualization"],
            AgentType.RESEARCHER: ["web_search", "document_analysis"],
            AgentType.CUSTOM: []
        }
        return tools_map.get(agent_type, [])

    def _send_task_to_a0_agent(
        self,
        agent_id: str,
        task: "PipelineTask",
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Send a task to an A0-spawned agent.

        Args:
            agent_id: A0 agent ID
            task: Pipeline task to execute
            context: Execution context

        Returns:
            Agent output if successful
        """
        if not self.agent_zero:
            return None

        try:
            # Send message to agent via A0
            message = {
                "type": "pipeline_task",
                "task_id": task.task_id,
                "agent_type": task.agent_type.value,
                "input": task.input_data,
                "context": context
            }

            self.agent_zero.send_message(agent_id, message)

            # Wait for response (simplified - real impl would be async)
            # For now, return None to indicate A0 handling
            return {"status": "delegated_to_a0", "agent_id": agent_id}

        except Exception as e:
            logger.warning(f"Failed to send task to A0 agent: {e}")
            return None


# Convenience function for creating standard pipelines
def create_development_pipeline() -> PipelineDefinition:
    """Create a standard development pipeline."""
    return PipelineDefinition(
        pipeline_id="development_pipeline",
        name="Development Pipeline",
        description="Standard pipeline for software development tasks",
        stages=[
            {"agent_type": "planner", "name": "Plan"},
            {"agent_type": "architect", "name": "Design"},
            {"agent_type": "developer", "name": "Implement"},
            {"agent_type": "tester", "name": "Test"},
            {"agent_type": "deployer", "name": "Deploy"}
        ],
        error_handling="stop",
        max_retries=2,
        timeout_seconds=600
    )


def create_research_pipeline() -> PipelineDefinition:
    """Create a research pipeline."""
    return PipelineDefinition(
        pipeline_id="research_pipeline",
        name="Research Pipeline",
        description="Pipeline for research and analysis tasks",
        stages=[
            {"agent_type": "researcher", "name": "Research"},
            {"agent_type": "analyst", "name": "Analyze"},
            {"agent_type": "planner", "name": "Summarize"}
        ],
        error_handling="continue",
        max_retries=3,
        timeout_seconds=900
    )


def create_orchestrator_with_a0(
    agent_zero: "AgentZeroCore",
    vessel_id: Optional[str] = None,
    community_memory=None
) -> Orchestrator:
    """
    DEPRECATED: Just use Orchestrator(agent_zero, ...) directly.

    This factory function is no longer needed since Orchestrator
    now requires AgentZeroCore by default.

    Args:
        agent_zero: AgentZeroCore instance
        vessel_id: Optional vessel ID for agent spawning
        community_memory: Optional community memory for results

    Returns:
        Orchestrator instance registered with A0
    """
    import warnings
    warnings.warn(
        "create_orchestrator_with_a0 is deprecated. Use Orchestrator(agent_zero, ...) directly.",
        DeprecationWarning,
        stacklevel=2
    )
    return Orchestrator(
        agent_zero=agent_zero,
        vessel_id=vessel_id,
        community_memory=community_memory
    )
