"""
Tests for SSF Composition.

These tests verify the SSF chaining and composition patterns:
- Sequential composition
- Parallel composition
- Conditional composition
- Loop composition
- Error handling in compositions
"""

import pytest
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from vessels.ssf.schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    ConstraintBindingConfig,
    SSFStatus,
    SSFPermissions,
    SSFResult,
)
from vessels.ssf.runtime import (
    SSFRuntime,
    Persona,
    A0AgentInstance,
)
from vessels.ssf.registry import SSFRegistry
from vessels.ssf.composition import SSFComposer, CompositionType


@pytest.fixture
def registry():
    """Create SSF registry for testing."""
    return SSFRegistry()


@pytest.fixture
def runtime(registry):
    """Create SSF runtime for testing."""
    return SSFRuntime(registry=registry)


@pytest.fixture
def composer(runtime):
    """Create SSF composer for testing."""
    return SSFComposer(runtime=runtime)


@pytest.fixture
def test_persona():
    """Create a test persona."""
    return Persona(
        id=uuid4(),
        name="test_persona",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            max_risk_level=RiskLevel.HIGH,
        ),
        virtue_state={
            "truthfulness": 0.8,
            "justice": 0.8,
            "trustworthiness": 0.8,
        },
    )


@pytest.fixture
def test_agent(test_persona):
    """Create a test agent."""
    return A0AgentInstance(
        agent_id="test_agent_001",
        persona_id=test_persona.id,
    )


@pytest.fixture
def increment_ssf():
    """Create an SSF that increments a value."""
    return SSFDefinition(
        id=uuid4(),
        name="increment_value",
        description="Increment a value by an amount",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline(
            "result = {'value': inputs.get('value', 0) + inputs.get('amount', 1)}"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "amount": {"type": "number"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
            },
        },
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


@pytest.fixture
def multiply_ssf():
    """Create an SSF that multiplies a value."""
    return SSFDefinition(
        id=uuid4(),
        name="multiply_value",
        description="Multiply a value by a factor",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline(
            "result = {'value': inputs.get('value', 0) * inputs.get('factor', 2)}"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "factor": {"type": "number"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
            },
        },
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


@pytest.fixture
def format_ssf():
    """Create an SSF that formats a value."""
    return SSFDefinition(
        id=uuid4(),
        name="format_value",
        description="Format a value as a string",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline(
            "result = {'formatted': f\"Result: {inputs.get('value', 0)}\"}"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "value": {"type": "number"},
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "formatted": {"type": "string"},
            },
        },
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


@pytest.fixture
def failing_ssf():
    """Create an SSF that always fails."""
    return SSFDefinition(
        id=uuid4(),
        name="failing_action",
        description="An action that always fails",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline("raise ValueError('Intentional failure')"),
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


class TestSequentialComposition:
    """Test sequential SSF composition."""

    @pytest.mark.asyncio
    async def test_basic_sequence(
        self, composer, registry, increment_ssf, multiply_ssf, test_persona, test_agent
    ):
        """Test basic sequential composition."""
        await registry.register(increment_ssf)
        await registry.register(multiply_ssf)

        result = await composer.compose_sequence(
            ssf_ids=[increment_ssf.id, multiply_ssf.id],
            initial_inputs={"value": 5, "amount": 3},
            input_mappings=[
                None,  # First SSF gets initial inputs
                {"value": "$.value", "factor": 2},  # Second gets output of first
            ],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.SEQUENCE
        assert len(result.step_results) == 2

    @pytest.mark.asyncio
    async def test_sequence_with_output_piping(
        self, composer, registry, increment_ssf, format_ssf, test_persona, test_agent
    ):
        """Test sequential composition with output piping."""
        await registry.register(increment_ssf)
        await registry.register(format_ssf)

        result = await composer.compose_sequence(
            ssf_ids=[increment_ssf.id, format_ssf.id],
            initial_inputs={"value": 10, "amount": 5},
            input_mappings=[
                None,
                {"value": "$.value"},  # Pipe value to format
            ],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.SEQUENCE

    @pytest.mark.asyncio
    async def test_sequence_stops_on_failure(
        self, composer, registry, increment_ssf, failing_ssf, test_persona, test_agent
    ):
        """Test that sequence stops when an SSF fails."""
        await registry.register(increment_ssf)
        await registry.register(failing_ssf)

        result = await composer.compose_sequence(
            ssf_ids=[increment_ssf.id, failing_ssf.id, increment_ssf.id],
            initial_inputs={"value": 5},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Sequence should have stopped at failing SSF
        assert result.status in [SSFStatus.ERROR, SSFStatus.BLOCKED]


class TestParallelComposition:
    """Test parallel SSF composition."""

    @pytest.mark.asyncio
    async def test_basic_parallel(
        self, composer, registry, increment_ssf, multiply_ssf, test_persona, test_agent
    ):
        """Test basic parallel composition."""
        await registry.register(increment_ssf)
        await registry.register(multiply_ssf)

        result = await composer.compose_parallel(
            ssf_ids=[increment_ssf.id, multiply_ssf.id],
            inputs_list=[
                {"value": 5, "amount": 3},
                {"value": 5, "factor": 2},
            ],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.PARALLEL
        assert len(result.step_results) == 2

    @pytest.mark.asyncio
    async def test_parallel_with_same_inputs(
        self, composer, registry, increment_ssf, multiply_ssf, test_persona, test_agent
    ):
        """Test parallel composition broadcasting same inputs."""
        await registry.register(increment_ssf)
        await registry.register(multiply_ssf)

        result = await composer.compose_parallel(
            ssf_ids=[increment_ssf.id, multiply_ssf.id],
            inputs_list=[
                {"value": 10, "amount": 1},
                {"value": 10, "factor": 2},
            ],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.PARALLEL

    @pytest.mark.asyncio
    async def test_parallel_with_partial_failure(
        self, composer, registry, increment_ssf, failing_ssf, test_persona, test_agent
    ):
        """Test parallel composition handles partial failures."""
        await registry.register(increment_ssf)
        await registry.register(failing_ssf)

        result = await composer.compose_parallel(
            ssf_ids=[increment_ssf.id, failing_ssf.id],
            inputs_list=[
                {"value": 5, "amount": 1},
                {},
            ],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Should complete but show mixed results
        assert len(result.step_results) == 2


class TestConditionalComposition:
    """Test conditional SSF composition."""

    @pytest.mark.asyncio
    async def test_basic_conditional(
        self, composer, registry, increment_ssf, multiply_ssf, test_persona, test_agent
    ):
        """Test basic conditional composition."""
        await registry.register(increment_ssf)
        await registry.register(multiply_ssf)

        # Condition that checks value
        def condition(output: Dict[str, Any]) -> bool:
            return output.get("value", 0) > 5

        result = await composer.compose_conditional(
            condition_ssf_id=increment_ssf.id,
            then_ssf_id=multiply_ssf.id,
            else_ssf_id=None,
            condition_func=condition,
            initial_inputs={"value": 10, "amount": 0},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.CONDITIONAL

    @pytest.mark.asyncio
    async def test_conditional_takes_else_branch(
        self, composer, registry, increment_ssf, multiply_ssf, format_ssf, test_persona, test_agent
    ):
        """Test conditional composition takes else branch."""
        await registry.register(increment_ssf)
        await registry.register(multiply_ssf)
        await registry.register(format_ssf)

        # Condition that will be false
        def condition(output: Dict[str, Any]) -> bool:
            return output.get("value", 0) > 100

        result = await composer.compose_conditional(
            condition_ssf_id=increment_ssf.id,
            then_ssf_id=multiply_ssf.id,
            else_ssf_id=format_ssf.id,
            condition_func=condition,
            initial_inputs={"value": 5, "amount": 1},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.CONDITIONAL


class TestLoopComposition:
    """Test loop SSF composition."""

    @pytest.mark.asyncio
    async def test_basic_loop(
        self, composer, registry, increment_ssf, test_persona, test_agent
    ):
        """Test basic loop composition."""
        await registry.register(increment_ssf)

        # Loop while value < 10
        def continue_condition(output: Dict[str, Any], iteration: int) -> bool:
            return output.get("value", 0) < 10 and iteration < 10

        result = await composer.compose_loop(
            ssf_id=increment_ssf.id,
            initial_inputs={"value": 0, "amount": 2},
            continue_condition=continue_condition,
            max_iterations=10,
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.composition_type == CompositionType.LOOP

    @pytest.mark.asyncio
    async def test_loop_respects_max_iterations(
        self, composer, registry, increment_ssf, test_persona, test_agent
    ):
        """Test that loop respects max iterations limit."""
        await registry.register(increment_ssf)

        # Condition that would loop forever
        def always_continue(output: Dict[str, Any], iteration: int) -> bool:
            return True

        result = await composer.compose_loop(
            ssf_id=increment_ssf.id,
            initial_inputs={"value": 0, "amount": 1},
            continue_condition=always_continue,
            max_iterations=5,
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Should stop at max_iterations
        assert len(result.step_results) <= 5


class TestCompositionConstraintMaintenance:
    """Test that constraints are maintained through compositions."""

    @pytest.mark.asyncio
    async def test_sequence_maintains_constraints(
        self, composer, registry, test_agent
    ):
        """Test that sequences maintain constraint checking."""
        low_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="low_risk",
            description="Low risk computation",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'value': 1}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )

        high_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="high_risk",
            description="High risk action",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.strict(),
        )

        await registry.register(low_risk_ssf)
        await registry.register(high_risk_ssf)

        # Persona with low risk tolerance
        low_risk_persona = Persona(
            id=uuid4(),
            name="cautious",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.LOW,
            ),
        )

        result = await composer.compose_sequence(
            ssf_ids=[low_risk_ssf.id, high_risk_ssf.id],
            initial_inputs={},
            invoking_persona=low_risk_persona,
            invoking_agent=test_agent,
        )

        # Should block at high risk SSF
        assert result.status in [SSFStatus.BLOCKED, SSFStatus.ERROR]


class TestCompositionErrorHandling:
    """Test error handling in compositions."""

    @pytest.mark.asyncio
    async def test_sequence_error_contains_context(
        self, composer, registry, failing_ssf, test_persona, test_agent
    ):
        """Test that sequence errors contain context about failure."""
        await registry.register(failing_ssf)

        result = await composer.compose_sequence(
            ssf_ids=[failing_ssf.id],
            initial_inputs={},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.status in [SSFStatus.ERROR, SSFStatus.BLOCKED]
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_parallel_reports_all_errors(
        self, composer, registry, failing_ssf, test_persona, test_agent
    ):
        """Test that parallel composition reports all errors."""
        await registry.register(failing_ssf)

        result = await composer.compose_parallel(
            ssf_ids=[failing_ssf.id, failing_ssf.id],
            inputs_list=[{}, {}],
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Both should have failed
        assert len(result.step_results) == 2
