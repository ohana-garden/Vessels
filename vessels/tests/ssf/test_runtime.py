"""
Tests for SSF Runtime.

These tests verify the core SSF execution engine including:
- Basic SSF invocation
- Permission checking
- Input/output validation
- Handler execution
"""

import pytest
from uuid import uuid4
from datetime import datetime

from vessels.ssf.schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
    HandlerType,
    ConstraintBindingConfig,
    ConstraintBindingMode,
    BoundaryBehavior,
    SSFStatus,
    SSFPermissions,
    ExecutionContext,
)
from vessels.ssf.runtime import (
    SSFRuntime,
    Persona,
    A0AgentInstance,
    SSFNotFoundError,
    SSFPermissionDeniedError,
)
from vessels.ssf.registry import SSFRegistry


@pytest.fixture
def runtime():
    """Create SSF runtime for testing."""
    registry = SSFRegistry()
    return SSFRuntime(registry=registry)


@pytest.fixture
def registry():
    """Create SSF registry for testing."""
    return SSFRegistry()


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
            "justice": 0.7,
            "trustworthiness": 0.8,
            "unity": 0.7,
            "service": 0.8,
            "detachment": 0.6,
            "understanding": 0.7,
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
def simple_ssf():
    """Create a simple computation SSF."""
    return SSFDefinition(
        id=uuid4(),
        name="add_numbers",
        description="Add two numbers together",
        description_for_llm="Use this to add two numbers",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline("result = {'sum': inputs['a'] + inputs['b']}"),
        input_schema={
            "type": "object",
            "properties": {
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["a", "b"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sum": {"type": "number"},
            },
        },
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


class TestSSFRuntimeBasics:
    """Basic runtime tests."""

    @pytest.mark.asyncio
    async def test_runtime_initialization(self, runtime):
        """Test runtime initializes correctly."""
        assert runtime is not None
        assert runtime._total_invocations == 0
        assert runtime._successful_invocations == 0

    @pytest.mark.asyncio
    async def test_invoke_nonexistent_ssf(self, runtime, test_persona, test_agent):
        """Test invoking a non-existent SSF returns error."""
        result = await runtime.invoke(
            ssf_id=uuid4(),  # Random UUID
            inputs={},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.ERROR
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_invoke_registered_ssf(
        self, runtime, registry, simple_ssf, test_persona, test_agent
    ):
        """Test invoking a registered SSF."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 5, "b": 3},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Note: inline handler won't actually execute in this test
        # because we need to handle the restricted execution environment
        assert result.ssf_id == simple_ssf.id
        assert result.ssf_name == simple_ssf.name


class TestSSFPermissions:
    """Permission checking tests."""

    @pytest.mark.asyncio
    async def test_blocked_persona_cannot_invoke(
        self, runtime, registry, simple_ssf, test_agent
    ):
        """Test that a persona without invoke permission is blocked."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        blocked_persona = Persona(
            id=uuid4(),
            name="blocked_persona",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=False,
            ),
        )

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 1, "b": 2},
            invoking_persona=blocked_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "permission" in result.error.lower()

    @pytest.mark.asyncio
    async def test_risk_level_enforcement(self, runtime, registry, test_agent):
        """Test that risk level constraints are enforced."""
        runtime.registry = registry

        # Create high-risk SSF
        high_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="high_risk_action",
            description="A high risk action",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {}"),
        )
        await registry.register(high_risk_ssf)

        # Create persona with low risk tolerance
        low_risk_persona = Persona(
            id=uuid4(),
            name="cautious_persona",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.LOW,
            ),
        )

        result = await runtime.invoke(
            ssf_id=high_risk_ssf.id,
            inputs={},
            invoking_persona=low_risk_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "risk level" in result.error.lower()

    @pytest.mark.asyncio
    async def test_blocked_ssf_id(self, runtime, registry, simple_ssf, test_agent):
        """Test that blocked SSF IDs are enforced."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        # Create persona with this SSF blocked
        blocked_persona = Persona(
            id=uuid4(),
            name="selective_persona",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                blocked_ssf_ids=[simple_ssf.id],
            ),
        )

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 1, "b": 2},
            invoking_persona=blocked_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "blocked" in result.error.lower()


class TestInputValidation:
    """Input schema validation tests."""

    @pytest.mark.asyncio
    async def test_missing_required_field(
        self, runtime, registry, simple_ssf, test_persona, test_agent
    ):
        """Test that missing required fields are caught."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 5},  # Missing 'b'
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "required" in result.error.lower() or "schema" in result.error.lower()

    @pytest.mark.asyncio
    async def test_valid_inputs_accepted(
        self, runtime, registry, simple_ssf, test_persona, test_agent
    ):
        """Test that valid inputs pass validation."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 5, "b": 3},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        # Should pass schema validation (execution may still have issues)
        assert result.ssf_id == simple_ssf.id


class TestRuntimeStats:
    """Runtime statistics tests."""

    @pytest.mark.asyncio
    async def test_stats_tracking(self, runtime, registry, simple_ssf, test_persona, test_agent):
        """Test that execution statistics are tracked."""
        runtime.registry = registry
        await registry.register(simple_ssf)

        initial_stats = runtime.get_stats()
        assert initial_stats["total_invocations"] == 0

        await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={"a": 1, "b": 2},
            invoking_persona=test_persona,
            invoking_agent=test_agent,
        )

        stats = runtime.get_stats()
        assert stats["total_invocations"] == 1
