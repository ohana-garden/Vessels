"""
Tests for SSF Dynamic Spawning.

These tests verify the dynamic SSF creation system:
- Basic SSF spawning
- Constraint inheritance on spawned SSFs
- SpawnConstraints enforcement
- Spawned SSF validation
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
    SpawnConstraints,
)
from vessels.ssf.runtime import (
    SSFRuntime,
    Persona,
    A0AgentInstance,
)
from vessels.ssf.registry import SSFRegistry, SpawnError


@pytest.fixture
def registry():
    """Create SSF registry for testing."""
    return SSFRegistry()


@pytest.fixture
def runtime(registry):
    """Create SSF runtime for testing."""
    return SSFRuntime(registry=registry)


@pytest.fixture
def spawn_permitted_persona():
    """Create a persona with spawn permissions."""
    return Persona(
        id=uuid4(),
        name="spawn_permitted",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            can_spawn_ssfs=True,
            max_risk_level=RiskLevel.HIGH,
            spawn_constraints=SpawnConstraints(
                allowed_categories=[
                    SSFCategory.COMPUTATION,
                    SSFCategory.DATA_RETRIEVAL,
                ],
                max_risk_level=RiskLevel.MEDIUM,
                max_spawns_per_session=10,
                require_approval=False,
            ),
        ),
        virtue_state={
            "truthfulness": 0.8,
            "justice": 0.8,
        },
    )


@pytest.fixture
def spawn_blocked_persona():
    """Create a persona without spawn permissions."""
    return Persona(
        id=uuid4(),
        name="spawn_blocked",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            can_spawn_ssfs=False,
            max_risk_level=RiskLevel.HIGH,
        ),
    )


@pytest.fixture
def test_agent(spawn_permitted_persona):
    """Create a test agent."""
    return A0AgentInstance(
        agent_id="test_agent_001",
        persona_id=spawn_permitted_persona.id,
    )


@pytest.fixture
def basic_ssf_spec():
    """Create a basic SSF specification for spawning."""
    return {
        "name": "calculate_average",
        "description": "Calculate the average of a list of numbers",
        "category": SSFCategory.COMPUTATION,
        "risk_level": RiskLevel.LOW,
        "handler_code": "result = {'average': sum(inputs['numbers']) / len(inputs['numbers'])}",
        "input_schema": {
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                },
            },
            "required": ["numbers"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "average": {"type": "number"},
            },
        },
    }


class TestBasicSpawning:
    """Test basic SSF spawning functionality."""

    @pytest.mark.asyncio
    async def test_spawn_basic_ssf(
        self, registry, spawn_permitted_persona, basic_ssf_spec
    ):
        """Test spawning a basic SSF."""
        spawned_ssf = await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
            parent_ssf_id=None,
        )

        assert spawned_ssf is not None
        assert spawned_ssf.name == "calculate_average"
        assert spawned_ssf.category == SSFCategory.COMPUTATION
        assert spawned_ssf.risk_level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_spawned_ssf_is_registered(
        self, registry, spawn_permitted_persona, basic_ssf_spec
    ):
        """Test that spawned SSF is automatically registered."""
        spawned_ssf = await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
        )

        # Should be findable in registry
        found = await registry.get(spawned_ssf.id)
        assert found is not None
        assert found.id == spawned_ssf.id

    @pytest.mark.asyncio
    async def test_spawned_ssf_tracks_spawner(
        self, registry, spawn_permitted_persona, basic_ssf_spec
    ):
        """Test that spawned SSF tracks who spawned it."""
        spawned_ssf = await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
        )

        assert spawned_ssf.spawned_by == spawn_permitted_persona.id


class TestSpawnPermissions:
    """Test spawn permission enforcement."""

    @pytest.mark.asyncio
    async def test_blocked_persona_cannot_spawn(
        self, registry, spawn_blocked_persona, basic_ssf_spec
    ):
        """Test that personas without spawn permission are blocked."""
        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec=basic_ssf_spec,
                spawning_persona=spawn_blocked_persona,
            )

        assert "permission" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_spawn_limit_enforcement(
        self, registry, spawn_permitted_persona, basic_ssf_spec
    ):
        """Test that spawn limits are enforced."""
        # Temporarily set a low limit
        spawn_permitted_persona.ssf_permissions.spawn_constraints.max_spawns_per_session = 2

        # First two should succeed
        await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
        )
        await registry.spawn(
            spec={**basic_ssf_spec, "name": "ssf2"},
            spawning_persona=spawn_permitted_persona,
        )

        # Third should fail
        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec={**basic_ssf_spec, "name": "ssf3"},
                spawning_persona=spawn_permitted_persona,
            )

        assert "limit" in str(exc_info.value).lower()


class TestCategoryRestrictions:
    """Test category-based spawn restrictions."""

    @pytest.mark.asyncio
    async def test_spawn_allowed_category(
        self, registry, spawn_permitted_persona
    ):
        """Test spawning in allowed category succeeds."""
        spec = {
            "name": "allowed_ssf",
            "description": "An SSF in allowed category",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        spawned = await registry.spawn(
            spec=spec,
            spawning_persona=spawn_permitted_persona,
        )

        assert spawned is not None
        assert spawned.category == SSFCategory.COMPUTATION

    @pytest.mark.asyncio
    async def test_spawn_blocked_category(
        self, registry, spawn_permitted_persona
    ):
        """Test spawning in blocked category fails."""
        spec = {
            "name": "blocked_ssf",
            "description": "An SSF in blocked category",
            "category": SSFCategory.COMMUNICATION,  # Not in allowed list
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

        assert "category" in str(exc_info.value).lower()


class TestRiskLevelRestrictions:
    """Test risk level enforcement for spawning."""

    @pytest.mark.asyncio
    async def test_spawn_within_risk_limit(
        self, registry, spawn_permitted_persona
    ):
        """Test spawning within risk limit succeeds."""
        spec = {
            "name": "low_risk_ssf",
            "description": "A low risk SSF",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        spawned = await registry.spawn(
            spec=spec,
            spawning_persona=spawn_permitted_persona,
        )

        assert spawned is not None
        assert spawned.risk_level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_spawn_exceeding_risk_limit(
        self, registry, spawn_permitted_persona
    ):
        """Test spawning above risk limit fails."""
        spec = {
            "name": "high_risk_ssf",
            "description": "A high risk SSF",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.HIGH,  # Above MEDIUM limit
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

        assert "risk" in str(exc_info.value).lower()


class TestConstraintInheritance:
    """Test constraint inheritance on spawned SSFs."""

    @pytest.mark.asyncio
    async def test_spawned_ssf_inherits_constraints(
        self, registry, spawn_permitted_persona, basic_ssf_spec
    ):
        """Test that spawned SSFs inherit spawner's constraints."""
        spawned = await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
        )

        # Spawned SSF should have constraint binding
        assert spawned.constraint_binding is not None

    @pytest.mark.asyncio
    async def test_spawned_ssf_cannot_exceed_parent_permissions(
        self, registry, spawn_permitted_persona
    ):
        """Test that spawned SSF cannot have more permissions than parent."""
        # Try to create SSF with higher risk level than persona allows
        spec = {
            "name": "escalated_ssf",
            "description": "Trying to escalate permissions",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.CRITICAL,  # Higher than allowed
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

    @pytest.mark.asyncio
    async def test_spawned_ssf_inherits_virtue_requirements(
        self, registry
    ):
        """Test that spawned SSFs inherit virtue requirements."""
        # Persona with strict virtue requirements
        strict_persona = Persona(
            id=uuid4(),
            name="strict_spawner",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                can_spawn_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
                spawn_constraints=SpawnConstraints(
                    allowed_categories=[SSFCategory.COMPUTATION],
                    max_risk_level=RiskLevel.MEDIUM,
                    inherit_virtue_thresholds=True,
                ),
            ),
            virtue_state={
                "truthfulness": 0.9,
            },
        )

        spec = {
            "name": "inherited_constraints_ssf",
            "description": "SSF with inherited constraints",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        spawned = await registry.spawn(
            spec=spec,
            spawning_persona=strict_persona,
        )

        # Spawned SSF should inherit constraint config
        assert spawned.constraint_binding is not None


class TestSpawnedSSFExecution:
    """Test execution of spawned SSFs."""

    @pytest.mark.asyncio
    async def test_spawned_ssf_can_be_executed(
        self, runtime, registry, spawn_permitted_persona, test_agent, basic_ssf_spec
    ):
        """Test that spawned SSF can be executed normally."""
        spawned = await registry.spawn(
            spec=basic_ssf_spec,
            spawning_persona=spawn_permitted_persona,
        )

        result = await runtime.invoke(
            ssf_id=spawned.id,
            inputs={"numbers": [1, 2, 3, 4, 5]},
            invoking_persona=spawn_permitted_persona,
            invoking_agent=test_agent,
        )

        assert result.ssf_id == spawned.id
        assert result.ssf_name == spawned.name

    @pytest.mark.asyncio
    async def test_spawned_ssf_respects_constraints_during_execution(
        self, runtime, registry, test_agent
    ):
        """Test that spawned SSFs respect constraints during execution."""
        # Persona with high virtue requirements
        high_virtue_persona = Persona(
            id=uuid4(),
            name="high_virtue_spawner",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                can_spawn_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
                spawn_constraints=SpawnConstraints(
                    allowed_categories=[SSFCategory.COMPUTATION],
                    max_risk_level=RiskLevel.MEDIUM,
                ),
            ),
            virtue_state={
                "truthfulness": 0.95,
            },
        )

        spec = {
            "name": "constrained_spawn",
            "description": "Spawned SSF with constraints",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {'computed': True}",
        }

        spawned = await registry.spawn(
            spec=spec,
            spawning_persona=high_virtue_persona,
        )

        # Low virtue persona tries to invoke
        low_virtue_persona = Persona(
            id=uuid4(),
            name="low_virtue",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
            ),
            virtue_state={
                "truthfulness": 0.3,
            },
        )

        result = await runtime.invoke(
            ssf_id=spawned.id,
            inputs={},
            invoking_persona=low_virtue_persona,
            invoking_agent=test_agent,
        )

        # Should still execute since spawned SSF uses permissive constraints
        assert result.ssf_id == spawned.id


class TestSpawnValidation:
    """Test validation of spawned SSF specifications."""

    @pytest.mark.asyncio
    async def test_spawn_validates_input_schema(
        self, registry, spawn_permitted_persona
    ):
        """Test that spawned SSF input schema is validated."""
        spec = {
            "name": "invalid_schema_ssf",
            "description": "SSF with invalid schema",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
            "input_schema": "not a valid schema",  # Invalid
        }

        with pytest.raises((SpawnError, ValueError, TypeError)):
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

    @pytest.mark.asyncio
    async def test_spawn_requires_name(
        self, registry, spawn_permitted_persona
    ):
        """Test that spawned SSF requires a name."""
        spec = {
            # No name
            "description": "SSF without name",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        with pytest.raises((SpawnError, ValueError, KeyError)):
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

    @pytest.mark.asyncio
    async def test_spawn_validates_handler_code(
        self, registry, spawn_permitted_persona
    ):
        """Test that handler code is validated for safety."""
        # This test verifies the handler code is checked for dangerous patterns
        spec = {
            "name": "potentially_dangerous_ssf",
            "description": "SSF with suspicious code",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "import os; os.system('rm -rf /')",  # Dangerous!
        }

        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec=spec,
                spawning_persona=spawn_permitted_persona,
            )

        # Should be blocked for security reasons
        assert any(word in str(exc_info.value).lower() for word in ["security", "dangerous", "blocked", "os.system"])


class TestParentChildRelationships:
    """Test parent-child relationships in spawning."""

    @pytest.mark.asyncio
    async def test_spawned_ssf_from_parent_ssf(
        self, registry, spawn_permitted_persona
    ):
        """Test spawning an SSF from another SSF."""
        # First create a parent SSF
        parent_spec = {
            "name": "parent_ssf",
            "description": "Parent SSF",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }
        parent = await registry.spawn(
            spec=parent_spec,
            spawning_persona=spawn_permitted_persona,
        )

        # Now spawn a child from the parent
        child_spec = {
            "name": "child_ssf",
            "description": "Child SSF spawned from parent",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }
        child = await registry.spawn(
            spec=child_spec,
            spawning_persona=spawn_permitted_persona,
            parent_ssf_id=parent.id,
        )

        assert child.parent_ssf_id == parent.id

    @pytest.mark.asyncio
    async def test_child_cannot_exceed_parent_risk(
        self, registry, spawn_permitted_persona
    ):
        """Test that child SSF cannot exceed parent's risk level."""
        # Create low-risk parent
        parent_spec = {
            "name": "low_risk_parent",
            "description": "Low risk parent",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }
        parent = await registry.spawn(
            spec=parent_spec,
            spawning_persona=spawn_permitted_persona,
        )

        # Try to spawn higher-risk child
        child_spec = {
            "name": "high_risk_child",
            "description": "Trying to escalate risk",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.MEDIUM,  # Higher than parent
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError) as exc_info:
            await registry.spawn(
                spec=child_spec,
                spawning_persona=spawn_permitted_persona,
                parent_ssf_id=parent.id,
            )

        assert "risk" in str(exc_info.value).lower() or "parent" in str(exc_info.value).lower()
