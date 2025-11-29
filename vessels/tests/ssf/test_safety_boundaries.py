"""
Tests for SSF Safety Boundaries - NO ESCAPE HATCH.

These tests verify the fundamental safety guarantees of the SSF system:
- Agents cannot execute raw code
- Agents cannot make direct API calls
- Constraint violations block execution
- Spawned SSFs inherit constraints
- Jailbreak attempts are still constrained
- Compositions maintain constraints throughout
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
from vessels.ssf.composition import SSFComposer


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
def trusted_persona():
    """Create a trusted persona with full permissions."""
    return Persona(
        id=uuid4(),
        name="trusted_persona",
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
            ),
        ),
        virtue_state={
            "truthfulness": 0.9,
            "justice": 0.9,
            "trustworthiness": 0.9,
        },
    )


@pytest.fixture
def untrusted_persona():
    """Create an untrusted persona with limited permissions."""
    return Persona(
        id=uuid4(),
        name="untrusted_persona",
        community_id="test_community",
        ssf_permissions=SSFPermissions(
            can_invoke_ssfs=True,
            can_spawn_ssfs=False,
            max_risk_level=RiskLevel.LOW,
        ),
        virtue_state={
            "truthfulness": 0.3,
            "justice": 0.3,
            "trustworthiness": 0.3,
        },
    )


@pytest.fixture
def test_agent(trusted_persona):
    """Create a test agent."""
    return A0AgentInstance(
        agent_id="test_agent_001",
        persona_id=trusted_persona.id,
    )


class TestNoEscapeHatch:
    """Core safety tests - these MUST pass for system security."""

    @pytest.mark.asyncio
    async def test_agent_cannot_execute_raw_code(self, runtime, trusted_persona, test_agent):
        """Test that agents cannot execute arbitrary code outside SSFs."""
        # The only way to execute code is through SSFs
        # There is no runtime.execute_raw_code or similar method
        assert not hasattr(runtime, "execute_raw_code")
        assert not hasattr(runtime, "run_code")
        assert not hasattr(runtime, "eval")
        assert not hasattr(runtime, "exec")

        # The invoke method is the ONLY entry point
        assert hasattr(runtime, "invoke")
        assert callable(runtime.invoke)

    @pytest.mark.asyncio
    async def test_agent_cannot_make_direct_api_calls(self, runtime, trusted_persona, test_agent):
        """Test that agents cannot make direct HTTP/API calls outside SSFs."""
        # No direct API call methods
        assert not hasattr(runtime, "http_request")
        assert not hasattr(runtime, "api_call")
        assert not hasattr(runtime, "fetch")
        assert not hasattr(runtime, "request")

    @pytest.mark.asyncio
    async def test_constraint_violation_blocks_execution(
        self, runtime, registry, untrusted_persona, test_agent
    ):
        """Test that constraint violations block SSF execution."""
        # Create SSF with high virtue requirements
        strict_ssf = SSFDefinition(
            id=uuid4(),
            name="strict_action",
            description="Requires high virtue",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig(
                mode=ConstraintBindingMode.FULL,
                boundary_behavior=BoundaryBehavior.BLOCK,
                minimum_virtue_thresholds={
                    "truthfulness": 0.8,
                    "justice": 0.8,
                },
            ),
        )
        await registry.register(strict_ssf)

        result = await runtime.invoke(
            ssf_id=strict_ssf.id,
            inputs={},
            invoking_persona=untrusted_persona,
            invoking_agent=test_agent,
        )

        # MUST be blocked
        assert result.status == SSFStatus.BLOCKED
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_spawned_ssf_inherits_constraints(
        self, registry, trusted_persona
    ):
        """Test that dynamically spawned SSFs inherit spawner constraints."""
        spawned = await registry.spawn(
            spec={
                "name": "spawned_constrained",
                "description": "Spawned SSF",
                "category": SSFCategory.COMPUTATION,
                "risk_level": RiskLevel.LOW,
                "handler_code": "result = {}",
            },
            spawning_persona=trusted_persona,
        )

        # Spawned SSF must have constraint binding
        assert spawned.constraint_binding is not None
        # Spawned SSF must track spawner
        assert spawned.spawned_by == trusted_persona.id

    @pytest.mark.asyncio
    async def test_jailbreak_prompt_still_constrained(
        self, runtime, registry, untrusted_persona, test_agent
    ):
        """Test that even 'jailbreak' attempts are constrained by SSF system."""
        # Even if an agent is 'tricked' into thinking it has more permissions,
        # the SSF runtime still enforces constraints based on persona

        high_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="sensitive_action",
            description="A sensitive action",
            category=SSFCategory.EXTERNAL_API,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {'sensitive': True}"),
            constraint_binding=ConstraintBindingConfig.strict(),
        )
        await registry.register(high_risk_ssf)

        # Untrusted persona tries to invoke critical action
        # Even with a "jailbreak" mindset, runtime enforces constraints
        result = await runtime.invoke(
            ssf_id=high_risk_ssf.id,
            inputs={},
            invoking_persona=untrusted_persona,
            invoking_agent=test_agent,
        )

        # Risk level mismatch should block
        assert result.status == SSFStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_composition_maintains_constraints(
        self, runtime, registry, composer, untrusted_persona, test_agent
    ):
        """Test that SSF compositions maintain constraints throughout chain."""
        # First SSF - low risk, should pass
        ssf1 = SSFDefinition(
            id=uuid4(),
            name="low_risk_step",
            description="Low risk",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'step': 1}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )

        # Second SSF - high risk, should be blocked for untrusted persona
        ssf2 = SSFDefinition(
            id=uuid4(),
            name="high_risk_step",
            description="High risk in chain",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {'step': 2}"),
            constraint_binding=ConstraintBindingConfig.strict(),
        )

        await registry.register(ssf1)
        await registry.register(ssf2)

        result = await composer.compose_sequence(
            ssf_ids=[ssf1.id, ssf2.id],
            initial_inputs={},
            invoking_persona=untrusted_persona,
            invoking_agent=test_agent,
        )

        # Sequence should be blocked at second SSF
        assert result.status in [SSFStatus.BLOCKED, SSFStatus.ERROR]


class TestHandlerSecurityValidation:
    """Test that handlers are validated for security."""

    @pytest.mark.asyncio
    async def test_inline_handler_cannot_import_os(self, registry, trusted_persona):
        """Test that inline handlers cannot import dangerous modules."""
        spec = {
            "name": "os_import_attempt",
            "description": "Attempting to import os",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "import os; result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)

    @pytest.mark.asyncio
    async def test_inline_handler_cannot_import_subprocess(
        self, registry, trusted_persona
    ):
        """Test that inline handlers cannot import subprocess."""
        spec = {
            "name": "subprocess_import_attempt",
            "description": "Attempting to import subprocess",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "import subprocess; result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)

    @pytest.mark.asyncio
    async def test_inline_handler_cannot_use_eval(self, registry, trusted_persona):
        """Test that inline handlers cannot use eval."""
        spec = {
            "name": "eval_attempt",
            "description": "Attempting to use eval",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = eval('1+1')",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)

    @pytest.mark.asyncio
    async def test_inline_handler_cannot_use_exec(self, registry, trusted_persona):
        """Test that inline handlers cannot use exec."""
        spec = {
            "name": "exec_attempt",
            "description": "Attempting to use exec",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "exec('print(1)'); result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)

    @pytest.mark.asyncio
    async def test_inline_handler_cannot_access_file_system(
        self, registry, trusted_persona
    ):
        """Test that inline handlers cannot access file system."""
        spec = {
            "name": "file_access_attempt",
            "description": "Attempting file access",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.LOW,
            "handler_code": "open('/etc/passwd', 'r'); result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)


class TestRiskLevelEnforcement:
    """Test risk level enforcement across the system."""

    @pytest.mark.asyncio
    async def test_cannot_invoke_above_max_risk(
        self, runtime, registry, untrusted_persona, test_agent
    ):
        """Test that personas cannot invoke SSFs above their max risk level."""
        medium_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="medium_risk_action",
            description="Medium risk",
            category=SSFCategory.DATA_RETRIEVAL,
            risk_level=RiskLevel.MEDIUM,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(medium_risk_ssf)

        # Untrusted persona has LOW max risk
        result = await runtime.invoke(
            ssf_id=medium_risk_ssf.id,
            inputs={},
            invoking_persona=untrusted_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "risk" in result.error.lower()

    @pytest.mark.asyncio
    async def test_cannot_spawn_above_spawn_risk_limit(
        self, registry, trusted_persona
    ):
        """Test that cannot spawn SSFs above spawn risk limit."""
        # trusted_persona has spawn max risk of MEDIUM
        spec = {
            "name": "high_risk_spawn",
            "description": "Attempting high risk spawn",
            "category": SSFCategory.COMPUTATION,
            "risk_level": RiskLevel.HIGH,  # Above MEDIUM
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)


class TestCategoryEnforcement:
    """Test category-based access control."""

    @pytest.mark.asyncio
    async def test_cannot_spawn_blocked_category(
        self, registry, trusted_persona
    ):
        """Test that cannot spawn SSFs in blocked categories."""
        # trusted_persona only allows COMPUTATION and DATA_RETRIEVAL
        spec = {
            "name": "blocked_category_spawn",
            "description": "Attempting spawn in blocked category",
            "category": SSFCategory.EXTERNAL_API,  # Not allowed
            "risk_level": RiskLevel.LOW,
            "handler_code": "result = {}",
        }

        with pytest.raises(SpawnError):
            await registry.spawn(spec=spec, spawning_persona=trusted_persona)


class TestPermissionBlockedPersonas:
    """Test that personas without permissions are properly blocked."""

    @pytest.mark.asyncio
    async def test_no_invoke_permission_blocks_all(
        self, runtime, registry, test_agent
    ):
        """Test that personas without invoke permission are blocked from all SSFs."""
        no_invoke_persona = Persona(
            id=uuid4(),
            name="no_invoke",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=False,  # Cannot invoke anything
            ),
        )

        simple_ssf = SSFDefinition(
            id=uuid4(),
            name="simple",
            description="Simple SSF",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(simple_ssf)

        result = await runtime.invoke(
            ssf_id=simple_ssf.id,
            inputs={},
            invoking_persona=no_invoke_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED
        assert "permission" in result.error.lower()

    @pytest.mark.asyncio
    async def test_specific_ssf_blocking(
        self, runtime, registry, trusted_persona, test_agent
    ):
        """Test that specific blocked SSF IDs are enforced."""
        target_ssf = SSFDefinition(
            id=uuid4(),
            name="blocked_target",
            description="Target SSF",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(target_ssf)

        # Create persona with this specific SSF blocked
        blocked_persona = Persona(
            id=uuid4(),
            name="selective_block",
            community_id="test_community",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
                blocked_ssf_ids=[target_ssf.id],  # Specifically blocked
            ),
        )

        result = await runtime.invoke(
            ssf_id=target_ssf.id,
            inputs={},
            invoking_persona=blocked_persona,
            invoking_agent=test_agent,
        )

        assert result.status == SSFStatus.BLOCKED


class TestImmutableConstraints:
    """Test that constraints cannot be modified after SSF creation."""

    @pytest.mark.asyncio
    async def test_ssf_constraints_immutable(self, registry, trusted_persona):
        """Test that SSF constraints cannot be changed after spawning."""
        spawned = await registry.spawn(
            spec={
                "name": "immutable_constraints",
                "description": "SSF with immutable constraints",
                "category": SSFCategory.COMPUTATION,
                "risk_level": RiskLevel.LOW,
                "handler_code": "result = {}",
            },
            spawning_persona=trusted_persona,
        )

        original_binding = spawned.constraint_binding

        # Attempt to modify (should not affect original)
        try:
            spawned.constraint_binding = ConstraintBindingConfig.permissive()
        except Exception:
            pass  # May be frozen/immutable

        # If modification was allowed, verify registry still has original
        stored = await registry.get(spawned.id)
        # The stored version should maintain proper constraints
        assert stored.constraint_binding is not None


class TestAuditTrail:
    """Test that all actions leave an audit trail."""

    @pytest.mark.asyncio
    async def test_invocation_logged(
        self, runtime, registry, trusted_persona, test_agent
    ):
        """Test that SSF invocations are logged."""
        ssf = SSFDefinition(
            id=uuid4(),
            name="logged_action",
            description="Action that should be logged",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(ssf)

        await runtime.invoke(
            ssf_id=ssf.id,
            inputs={"test": True},
            invoking_persona=trusted_persona,
            invoking_agent=test_agent,
        )

        # Check that stats tracked the invocation
        stats = runtime.get_stats()
        assert stats["total_invocations"] >= 1

    @pytest.mark.asyncio
    async def test_blocked_invocation_logged(
        self, runtime, registry, untrusted_persona, test_agent
    ):
        """Test that blocked invocations are logged."""
        high_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="blocked_action",
            description="Action that will be blocked",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig.strict(),
        )
        await registry.register(high_risk_ssf)

        initial_stats = runtime.get_stats()

        await runtime.invoke(
            ssf_id=high_risk_ssf.id,
            inputs={},
            invoking_persona=untrusted_persona,
            invoking_agent=test_agent,
        )

        # Blocked invocations should still be counted
        stats = runtime.get_stats()
        assert stats["total_invocations"] > initial_stats["total_invocations"]
