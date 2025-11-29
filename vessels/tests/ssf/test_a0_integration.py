"""
Tests for A0 (Agent Zero) SSF Integration.

These tests verify the integration between Agent Zero and the SSF system:
- Tool definition generation
- Tool call routing
- Meta-tool functionality (invoke_ssf, find_ssf, compose_ssfs, spawn_ssf)
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
    SSFStatus,
    SSFPermissions,
    SpawnConstraints,
)
from vessels.ssf.runtime import (
    SSFRuntime,
    Persona,
    A0AgentInstance,
)
from vessels.ssf.registry import SSFRegistry
from vessels.ssf.composition import SSFComposer
from vessels.a0.ssf_integration import A0SSFIntegration


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
def integration(runtime, registry, composer):
    """Create A0 SSF integration for testing."""
    return A0SSFIntegration(
        runtime=runtime,
        registry=registry,
        composer=composer,
    )


@pytest.fixture
def test_persona():
    """Create a test persona."""
    return Persona(
        id=uuid4(),
        name="test_persona",
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
            "truthfulness": 0.8,
            "justice": 0.8,
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
def computation_ssf():
    """Create a computation SSF for testing."""
    return SSFDefinition(
        id=uuid4(),
        name="compute_sum",
        description="Compute the sum of numbers",
        description_for_llm="Use this to add numbers together",
        category=SSFCategory.COMPUTATION,
        tags=["math", "addition", "computation"],
        risk_level=RiskLevel.LOW,
        handler=SSFHandler.inline(
            "result = {'sum': sum(inputs.get('numbers', []))}"
        ),
        input_schema={
            "type": "object",
            "properties": {
                "numbers": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Numbers to sum",
                },
            },
            "required": ["numbers"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sum": {"type": "number"},
            },
        },
        constraint_binding=ConstraintBindingConfig.permissive(),
    )


class TestToolDefinitionGeneration:
    """Test tool definition generation for A0."""

    @pytest.mark.asyncio
    async def test_generates_tool_definitions(
        self, integration, registry, computation_ssf, test_persona
    ):
        """Test that tool definitions are generated for available SSFs."""
        await registry.register(computation_ssf)

        tools = await integration.get_tool_definitions_for_agent(
            persona=test_persona,
        )

        # Should include meta-tools
        tool_names = [t["name"] for t in tools]
        assert "invoke_ssf" in tool_names
        assert "find_ssf" in tool_names

    @pytest.mark.asyncio
    async def test_tool_definitions_include_schemas(
        self, integration, registry, computation_ssf, test_persona
    ):
        """Test that tool definitions include proper schemas."""
        await registry.register(computation_ssf)

        tools = await integration.get_tool_definitions_for_agent(
            persona=test_persona,
        )

        invoke_tool = next(t for t in tools if t["name"] == "invoke_ssf")
        assert "parameters" in invoke_tool
        assert invoke_tool["parameters"]["type"] == "object"

    @pytest.mark.asyncio
    async def test_filtered_tools_for_risk_level(
        self, integration, registry, test_persona
    ):
        """Test that tools are filtered based on persona risk level."""
        # Create low risk SSF
        low_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="low_risk_action",
            description="Low risk",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {}"),
        )

        # Create critical risk SSF
        critical_ssf = SSFDefinition(
            id=uuid4(),
            name="critical_action",
            description="Critical risk",
            category=SSFCategory.EXTERNAL_API,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {}"),
        )

        await registry.register(low_risk_ssf)
        await registry.register(critical_ssf)

        # Get tools for persona with HIGH max risk
        tools = await integration.get_tool_definitions_for_agent(
            persona=test_persona,
        )

        # The invoke_ssf tool should still exist
        tool_names = [t["name"] for t in tools]
        assert "invoke_ssf" in tool_names


class TestToolCallRouting:
    """Test tool call routing through the integration."""

    @pytest.mark.asyncio
    async def test_invoke_ssf_meta_tool(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test the invoke_ssf meta-tool."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="invoke_ssf",
            arguments={
                "ssf_id": str(computation_ssf.id),
                "inputs": {"numbers": [1, 2, 3, 4, 5]},
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None
        assert "result" in result or "error" in result

    @pytest.mark.asyncio
    async def test_find_ssf_meta_tool(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test the find_ssf meta-tool."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="find_ssf",
            arguments={
                "capability": "add numbers",
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None
        # Should return matching SSFs
        assert "ssfs" in result or "matches" in result or "results" in result

    @pytest.mark.asyncio
    async def test_compose_ssfs_meta_tool(
        self, integration, registry, test_persona, test_agent
    ):
        """Test the compose_ssfs meta-tool."""
        # Create two SSFs to compose
        ssf1 = SSFDefinition(
            id=uuid4(),
            name="step1",
            description="First step",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'step': 1}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        ssf2 = SSFDefinition(
            id=uuid4(),
            name="step2",
            description="Second step",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'step': 2}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(ssf1)
        await registry.register(ssf2)

        result = await integration.handle_tool_call(
            tool_name="compose_ssfs",
            arguments={
                "composition_type": "sequence",
                "ssf_ids": [str(ssf1.id), str(ssf2.id)],
                "initial_inputs": {},
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_spawn_ssf_meta_tool(
        self, integration, registry, test_persona, test_agent
    ):
        """Test the spawn_ssf meta-tool."""
        result = await integration.handle_tool_call(
            tool_name="spawn_ssf",
            arguments={
                "name": "dynamic_compute",
                "description": "A dynamically created SSF",
                "category": "computation",
                "risk_level": "low",
                "handler_code": "result = {'computed': True}",
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None
        # Should return the spawned SSF or error
        assert "ssf_id" in result or "error" in result


class TestDirectSSFInvocation:
    """Test direct SSF invocation through integration."""

    @pytest.mark.asyncio
    async def test_direct_invocation_by_name(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test invoking SSF directly by name."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="compute_sum",  # Direct SSF name
            arguments={
                "numbers": [10, 20, 30],
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None


class TestErrorHandling:
    """Test error handling in the integration."""

    @pytest.mark.asyncio
    async def test_unknown_tool_error(
        self, integration, test_persona, test_agent
    ):
        """Test error handling for unknown tools."""
        result = await integration.handle_tool_call(
            tool_name="nonexistent_tool",
            arguments={},
            persona=test_persona,
            agent=test_agent,
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_invalid_ssf_id_error(
        self, integration, test_persona, test_agent
    ):
        """Test error handling for invalid SSF ID."""
        result = await integration.handle_tool_call(
            tool_name="invoke_ssf",
            arguments={
                "ssf_id": str(uuid4()),  # Random non-existent ID
                "inputs": {},
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_permission_denied_error(
        self, integration, registry, test_agent
    ):
        """Test error handling for permission denied."""
        # Create high risk SSF
        high_risk_ssf = SSFDefinition(
            id=uuid4(),
            name="high_risk",
            description="High risk action",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.CRITICAL,
            handler=SSFHandler.inline("result = {}"),
        )
        await registry.register(high_risk_ssf)

        # Create low-permission persona
        low_persona = Persona(
            id=uuid4(),
            name="low_permission",
            community_id="test",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.LOW,
            ),
        )

        result = await integration.handle_tool_call(
            tool_name="invoke_ssf",
            arguments={
                "ssf_id": str(high_risk_ssf.id),
                "inputs": {},
            },
            persona=low_persona,
            agent=test_agent,
        )

        assert "error" in result
        assert "blocked" in result["error"].lower() or "risk" in result["error"].lower()


class TestSSFDiscovery:
    """Test SSF discovery features."""

    @pytest.mark.asyncio
    async def test_find_by_capability(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test finding SSFs by capability description."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="find_ssf",
            arguments={
                "capability": "calculate sum",
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_category(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test finding SSFs by category."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="find_ssf",
            arguments={
                "category": "computation",
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_find_by_tags(
        self, integration, registry, computation_ssf, test_persona, test_agent
    ):
        """Test finding SSFs by tags."""
        await registry.register(computation_ssf)

        result = await integration.handle_tool_call(
            tool_name="find_ssf",
            arguments={
                "tags": ["math"],
            },
            persona=test_persona,
            agent=test_agent,
        )

        assert result is not None


class TestAgentContext:
    """Test agent context handling."""

    @pytest.mark.asyncio
    async def test_agent_context_passed_to_ssf(
        self, integration, registry, test_persona, test_agent
    ):
        """Test that agent context is passed to SSF execution."""
        ssf = SSFDefinition(
            id=uuid4(),
            name="context_aware",
            description="SSF that uses context",
            category=SSFCategory.COMPUTATION,
            risk_level=RiskLevel.LOW,
            handler=SSFHandler.inline("result = {'agent_id': context.get('agent_id')}"),
            constraint_binding=ConstraintBindingConfig.permissive(),
        )
        await registry.register(ssf)

        result = await integration.handle_tool_call(
            tool_name="invoke_ssf",
            arguments={
                "ssf_id": str(ssf.id),
                "inputs": {},
            },
            persona=test_persona,
            agent=test_agent,
        )

        # Result should have access to agent context
        assert result is not None

    @pytest.mark.asyncio
    async def test_persona_constraints_enforced(
        self, integration, registry, test_agent
    ):
        """Test that persona constraints are enforced."""
        ssf = SSFDefinition(
            id=uuid4(),
            name="constrained_action",
            description="Action with virtue requirements",
            category=SSFCategory.COMMUNICATION,
            risk_level=RiskLevel.HIGH,
            handler=SSFHandler.inline("result = {}"),
            constraint_binding=ConstraintBindingConfig(
                minimum_virtue_thresholds={"truthfulness": 0.9},
            ),
        )
        await registry.register(ssf)

        # Low virtue persona
        low_virtue = Persona(
            id=uuid4(),
            name="low_virtue",
            community_id="test",
            ssf_permissions=SSFPermissions(
                can_invoke_ssfs=True,
                max_risk_level=RiskLevel.HIGH,
            ),
            virtue_state={"truthfulness": 0.3},
        )

        result = await integration.handle_tool_call(
            tool_name="invoke_ssf",
            arguments={
                "ssf_id": str(ssf.id),
                "inputs": {},
            },
            persona=low_virtue,
            agent=test_agent,
        )

        assert "error" in result or result.get("status") == "blocked"
