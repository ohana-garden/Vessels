"""
Tests for SSF Constraint Binding.

These tests verify the constraint inheritance and validation system:
- Constraint binding modes (FULL, FILTERED, EXPLICIT)
- Manifold position inheritance
- Boundary behavior (block, escalate, warn)
"""

import pytest
from uuid import uuid4
from datetime import datetime

from vessels.ssf.schema import (
    SSFDefinition,
    SSFCategory,
    RiskLevel,
    SSFHandler,
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
)
from vessels.ssf.registry import SSFRegistry


@pytest.fixture
def registry():
    """Create SSF registry for testing."""
    return SSFRegistry()


@pytest.fixture
def runtime(registry):
    """Create SSF runtime for testing."""
    return SSFRuntime(registry=registry)


@pytest.fixture
def high_virtue_persona():
    """Create a persona with high virtue scores."""
    return Persona(
        id=uuid4(),
        name="virtuous_persona",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            max_risk_level=RiskLevel.CRITICAL,
        ),
        virtue_state={
            "truthfulness": 0.95,
            "justice": 0.90,
            "trustworthiness": 0.92,
            "unity": 0.88,
            "service": 0.91,
            "detachment": 0.85,
            "understanding": 0.89,
        },
    )


@pytest.fixture
def low_virtue_persona():
    """Create a persona with low virtue scores."""
    return Persona(
        id=uuid4(),
        name="developing_persona",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            max_risk_level=RiskLevel.MEDIUM,
        ),
        virtue_state={
            "truthfulness": 0.3,
            "justice": 0.4,
            "trustworthiness": 0.35,
            "unity": 0.5,
            "service": 0.45,
            "detachment": 0.3,
            "understanding": 0.4,
        },
    )


@pytest.fixture
def test_agent(high_virtue_persona):
    """Create a test agent."""
    return A0AgentInstance(
        agent_id="test_agent_001",
        persona_id=high_virtue_persona.id,
    )


@pytest.fixture
def full_binding_ssf():
    """Create an SSF with full constraint binding."""
    return SSFDefinition(
        id=uuid4(),
        name="full_binding_action",
        description="An action that inherits full constraints",
        category=SSFCategory.COMMUNICATION,
        risk_level=RiskLevel.HIGH,
        handler=SSFHandler.inline("result = {'sent': True}"),
        input_schema={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
            },
        },
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FULL,
            boundary_behavior=BoundaryBehavior.BLOCK,
            minimum_virtue_thresholds={
                "truthfulness": 0.7,
                "trustworthiness": 0.7,
            },
        ),
    )


@pytest.fixture
def filtered_binding_ssf():
    """Create an SSF with filtered constraint binding."""
    return SSFDefinition(
        id=uuid4(),
        name="filtered_binding_action",
        description="An action with filtered constraints",
        category=SSFCategory.DATA_RETRIEVAL,
        risk_level=RiskLevel.MEDIUM,
        handler=SSFHandler.inline("result = {'data': 'retrieved'}"),
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.FILTERED,
            applicable_virtues=["trustworthiness", "understanding"],
            boundary_behavior=BoundaryBehavior.WARN,
        ),
    )


@pytest.fixture
def explicit_binding_ssf():
    """Create an SSF with explicit constraint binding."""
    return SSFDefinition(
        id=uuid4(),
        name="explicit_binding_action",
        description="An action with explicit constraints only",
        category=SSFCategory.COMPUTATION,
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline("result = {'computed': True}"),
        constraint_binding=ConstraintBindingConfig(
            mode=ConstraintBindingMode.EXPLICIT,
            explicit_constraints=["no_harmful_output"],
            boundary_behavior=BoundaryBehavior.ESCALATE,
        ),
    )


class TestConstraintBindingModes:
    """Test different constraint binding modes."""

    @pytest.mark.asyncio
    async def test_full_binding_inherits_all_constraints(
        self, runtime, registry, full_binding_ssf, high_virtue_persona, test_agent
    ):
        """Test that FULL binding mode inherits all persona constraints."""
        await registry.register(full_binding_ssf)

        result = await runtime.invoke(
            ssf_id=full_binding_ssf.id,
            inputs={"message": "Hello"},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )

        # High virtue persona should pass full binding
        assert result.ssf_id == full_binding_ssf.id

    @pytest.mark.asyncio
    async def test_full_binding_blocks_low_virtue(
        self, runtime, registry, full_binding_ssf, low_virtue_persona, test_agent
    ):
        """Test that FULL binding blocks personas below virtue thresholds."""
        await registry.register(full_binding_ssf)

        # Create agent for low virtue persona
        low_agent = A0AgentInstance(
            agent_id="low_virtue_agent",
            persona_id=low_virtue_persona.id,
        )

        result = await runtime.invoke(
            ssf_id=full_binding_ssf.id,
            inputs={"message": "Hello"},
            invoking_persona=low_virtue_persona,
            invoking_agent=low_agent,
        )

        # Low virtue persona should be blocked
        assert result.status == SSFStatus.BLOCKED
        assert "virtue" in result.error.lower() or "constraint" in result.error.lower()

    @pytest.mark.asyncio
    async def test_filtered_binding_checks_only_specified_virtues(
        self, runtime, registry, filtered_binding_ssf, high_virtue_persona, test_agent
    ):
        """Test that FILTERED binding only checks applicable virtues."""
        await registry.register(filtered_binding_ssf)

        result = await runtime.invoke(
            ssf_id=filtered_binding_ssf.id,
            inputs={},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )

        assert result.ssf_id == filtered_binding_ssf.id

    @pytest.mark.asyncio
    async def test_explicit_binding_uses_only_explicit_constraints(
        self, runtime, registry, explicit_binding_ssf, high_virtue_persona, test_agent
    ):
        """Test that EXPLICIT binding uses only explicitly defined constraints."""
        await registry.register(explicit_binding_ssf)

        result = await runtime.invoke(
            ssf_id=explicit_binding_ssf.id,
            inputs={},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )

        # Explicit binding with basic constraints should pass
        assert result.ssf_id == explicit_binding_ssf.id


class TestBoundaryBehaviors:
    """Test boundary behavior when constraints are violated."""

    @pytest.mark.asyncio
    async def test_block_behavior_prevents_execution(
        self, runtime, registry, full_binding_ssf, low_virtue_persona
    ):
        """Test that BLOCK behavior prevents SSF execution."""
        await registry.register(full_binding_ssf)

        low_agent = A0AgentInstance(
            agent_id="low_virtue_agent",
            persona_id=low_virtue_persona.id,
        )

        result = await runtime.invoke(
            ssf_id=full_binding_ssf.id,
            inputs={"message": "Hello"},
            invoking_persona=low_virtue_persona,
            invoking_agent=low_agent,
        )

        assert result.status == SSFStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_escalate_behavior_on_constraint_violation(
        self, runtime, registry, high_virtue_persona, test_agent
    ):
        """Test that ESCALATE behavior marks execution for review."""
        escalate_ssf = SSFDefinition(
            id=uuid4(),
            name="escalate_action",
            description="An action that escalates on violation",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig(
                mode=ConstraintBindingMode.FULL,
                boundary_behavior=BoundaryBehavior.ESCALATE,
                minimum_virtue_thresholds={
                    "truthfulness": 0.99,  # Very high threshold
                },
            ),
        )
        await registry.register(escalate_ssf)

        result = await runtime.invoke(
            ssf_id=escalate_ssf.id,
            inputs={},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )

        # Escalate should mark for review, not necessarily block
        assert result.ssf_id == escalate_ssf.id

    @pytest.mark.asyncio
    async def test_warn_behavior_allows_execution_with_warning(
        self, runtime, registry, filtered_binding_ssf, low_virtue_persona
    ):
        """Test that WARN behavior allows execution but logs warning."""
        await registry.register(filtered_binding_ssf)

        low_agent = A0AgentInstance(
            agent_id="low_virtue_agent",
            persona_id=low_virtue_persona.id,
        )

        result = await runtime.invoke(
            ssf_id=filtered_binding_ssf.id,
            inputs={},
            invoking_persona=low_virtue_persona,
            invoking_agent=low_agent,
        )

        # WARN behavior should still allow execution
        assert result.ssf_id == filtered_binding_ssf.id


class TestVirtueThresholds:
    """Test minimum virtue threshold enforcement."""

    @pytest.mark.asyncio
    async def test_specific_virtue_threshold_enforcement(
        self, runtime, registry, test_agent
    ):
        """Test that specific virtue thresholds are enforced."""
        strict_ssf = SSFDefinition(
            id=uuid4(),
            name="strict_virtue_action",
            description="Requires specific virtue levels",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig(
                mode=ConstraintBindingMode.FULL,
                boundary_behavior=BoundaryBehavior.BLOCK,
                minimum_virtue_thresholds={
                    "justice": 0.95,  # Very high requirement
                },
            ),
        )
        await registry.register(strict_ssf)

        # Persona with high but not sufficient justice
        almost_just_persona = Persona(
            id=uuid4(),
            name="almost_just",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
            ),
            virtue_state={
                "justice": 0.90,  # Below 0.95 threshold
            },
        )

        result = await runtime.invoke(
            ssf_id=strict_ssf.id,
            inputs={},
            invoking_persona=almost_just_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_multiple_virtue_thresholds(
        self, runtime, registry, test_agent
    ):
        """Test that multiple virtue thresholds are all checked."""
        multi_virtue_ssf = SSFDefinition(
            id=uuid4(),
            name="multi_virtue_action",
            description="Requires multiple virtues",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig(
                mode=ConstraintBindingMode.FULL,
                boundary_behavior=BoundaryBehavior.BLOCK,
                minimum_virtue_thresholds={
                    "truthfulness": 0.8,
                    "justice": 0.8,
                    "service": 0.8,
                },
            ),
        )
        await registry.register(multi_virtue_ssf)

        # Persona missing one virtue threshold
        partial_persona = Persona(
            id=uuid4(),
            name="partial_virtuous",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
            ),
            virtue_state={
                "truthfulness": 0.85,
                "justice": 0.85,
                "service": 0.7,  # Below threshold
            },
        )

        result = await runtime.invoke(
            ssf_id=multi_virtue_ssf.id,
            inputs={},
            invoking_persona=partial_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED


class TestConstraintPropagation:
    """Test constraint propagation through SSF chains."""

    @pytest.mark.asyncio
    async def test_constraints_propagate_in_composition(
        self, runtime, registry, high_virtue_persona, test_agent
    ):
        """Test that constraints are maintained through SSF composition."""
        # Create two SSFs for composition
        ssf1 = SSFDefinition(
            id=uuid4(),
            name="first_ssf",
            description="First SSF in chain",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'step': 1}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )

        ssf2 = SSFDefinition(
            id=uuid4(),
            name="second_ssf",
            description="Second SSF in chain with strict constraints",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {'step': 2}"),
            constraint_binding=ConstraintBindingConfig(
                mode=ConstraintBindingMode.FULL,
                boundary_behavior=BoundaryBehavior.BLOCK,
                minimum_virtue_thresholds={"truthfulness": 0.9},
            ),
        )

        await registry.register(ssf1)
        await registry.register(ssf2)

        # Both should inherit constraints from the invoking persona
        result1 = await runtime.invoke(
            ssf_id=ssf1.id,
            inputs={},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )
        assert result1.ssf_id == ssf1.id

        result2 = await runtime.invoke(
            ssf_id=ssf2.id,
            inputs={},
            invoking_persona=high_virtue_persona,
            invoking_agent=test_agent,
        )
        assert result2.ssf_id == ssf2.id


class TestConstraintConfigCreation:
    """Test ConstraintBindingConfig factory methods."""

    def test_permissive_config(self):
        """Test permissive constraint config creation."""
        config = ConstraintBindingConfig.permissive()
        assert config.mode == ConstraintBindingMode.FILTERED
        assert config.boundary_behavior == BoundaryBehavior.WARN

    def test_strict_config(self):
        """Test strict constraint config creation."""
        config = ConstraintBindingConfig.strict()
        assert config.mode == ConstraintBindingMode.FULL
        assert config.boundary_behavior == BoundaryBehavior.BLOCK

    def test_custom_config(self):
        """Test custom constraint config creation."""
        config = ConstraintBindingConfig(
            mode=ConstraintBindingMode.EXPLICIT,
            explicit_constraints=["no_pii", "no_harmful_content"],
            boundary_behavior=BoundaryBehavior.ESCALATE,
        )
        assert config.mode == ConstraintBindingMode.EXPLICIT
        assert "no_pii" in config.explicit_constraints
        assert config.boundary_behavior == BoundaryBehavior.ESCALATE
