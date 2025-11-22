"""
Tests for vessel context propagation.

Tests AC from story_vessel_context.md:
- AC1: Resolve vessel from user_id
- AC2: Resolve vessel from explicit name
- AC3: Use default vessel
- AC4: AdaptiveTools receives vessel context
- AC5: Gate events include vessel_id
- AC6: GraphitiClient uses vessel namespace
"""

import pytest
from vessels.core import (
    Vessel, VesselRegistry, VesselContext,
    PrivacyLevel, map_user_to_vessel, clear_user_vessel_mappings
)
from vessels.knowledge.schema import CommunityPrivacy
from adaptive_tools import AdaptiveTools, ToolSpecification, ToolType


def test_vessel_context_from_vessel_id(tmp_path):
    """AC1: Resolve vessel from vessel ID."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="v1",
        name="Test Vessel",
        description="Test",
        community_ids=["c1"],
        graph_namespace="c1_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Resolve context
    context = VesselContext.from_vessel_id("v1", registry)

    assert context is not None
    assert context.vessel_id == "v1"
    assert context.graph_namespace == "c1_graph"
    assert context.community_ids == ["c1"]


def test_vessel_context_from_name(tmp_path):
    """AC2: Resolve vessel from explicit name."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="v1",
        name="Lower Puna Elders Care",
        description="Elder care vessel",
        community_ids=["lower_puna"],
        graph_namespace="lower_puna_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Resolve by name
    context = VesselContext.from_vessel_name("Lower Puna Elders Care", registry)

    assert context is not None
    assert context.vessel.name == "Lower Puna Elders Care"
    assert context.vessel_id == "v1"


def test_vessel_context_from_user_id(tmp_path):
    """AC1 Extended: Resolve vessel from user_id mapping."""
    clear_user_vessel_mappings()  # Clean slate

    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="v1",
        name="User Vessel",
        description="Test",
        community_ids=["c1"],
        graph_namespace="c1_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Map user to vessel
    map_user_to_vessel("user_123", "v1")

    # Resolve context from user
    context = VesselContext.from_user_id("user_123", registry)

    assert context is not None
    assert context.vessel_id == "v1"

    # Cleanup
    clear_user_vessel_mappings()


def test_vessel_context_default(tmp_path):
    """AC3: Use default vessel when none specified."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Get default (will create one if none exist)
    context = VesselContext.get_default(registry)

    assert context is not None
    assert context.vessel is not None


def test_vessel_context_metadata(tmp_path):
    """Test metadata extraction from vessel context."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="v1",
        name="Test Vessel",
        description="Test",
        community_ids=["c1", "c2"],
        graph_namespace="c1_graph",
        privacy_level=CommunityPrivacy.SHARED,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    context = VesselContext.from_vessel_id("v1", registry)
    metadata = context.get_metadata()

    assert metadata["vessel_id"] == "v1"
    assert metadata["graph_namespace"] == "c1_graph"
    assert metadata["community_ids"] == ["c1", "c2"]
    assert metadata["privacy_level"] == "shared"


def test_vessel_context_graphiti_client(tmp_path):
    """AC6: GraphitiClient uses vessel namespace."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="v1",
        name="Test Vessel",
        description="Test",
        community_ids=["test_community"],
        graph_namespace="test_community_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    context = VesselContext.from_vessel_id("v1", registry)

    # Get graphiti client with mock enabled
    graphiti = context.get_graphiti_client(allow_mock=True)

    # Should use the community_id from the vessel
    assert graphiti.community_id == "test_community"
    assert graphiti.graph_name == "test_community_graph"


def test_adaptive_tools_with_vessel_context():
    """AC4: AdaptiveTools receives and uses vessel context."""
    tools = AdaptiveTools(vessel_id="test_vessel_1")

    assert tools.vessel_id == "test_vessel_1"

    # Create and execute a tool
    spec = ToolSpecification(
        name="test_tool",
        description="Test tool",
        tool_type=ToolType.GENERIC,
        parameters={},
        returns={},
        capabilities=[]
    )

    tool_id = tools.create_tool(spec)

    # Execute tool - vessel_id should be in gate metadata
    result = tools.execute_tool(
        tool_id,
        {},
        agent_id="agent_1",
        gate_metadata={}
    )

    # Tool should execute successfully
    assert result["success"] is True


def test_gate_events_include_vessel_id(tmp_path):
    """AC5: Gate events include vessel_id from action_metadata."""
    from vessels.gating.gate import ActionGate, GatingResult
    from vessels.measurement.operational import OperationalMetrics
    from vessels.measurement.virtue_inference import VirtueInferenceEngine
    from vessels.constraints.manifold import Manifold
    from vessels.phase_space.tracker import TrajectoryTracker

    # Create gate components
    manifold = Manifold.servant_default()
    operational = OperationalMetrics()
    virtue_engine = VirtueInferenceEngine()
    tracker = TrajectoryTracker(db_path=str(tmp_path / "tracker.db"))

    gate = ActionGate(
        manifold=manifold,
        operational_metrics=operational,
        virtue_engine=virtue_engine,
        tracker=tracker
    )

    # Gate an action with vessel_id in metadata
    result = gate.gate_action(
        agent_id="test_agent",
        action={"type": "test_action"},
        action_metadata={"vessel_id": "test_vessel_123", "tool_name": "test_tool"}
    )

    # Verify action was processed
    assert isinstance(result, GatingResult)

    # Verify state transition was created with vessel_id
    assert len(gate.state_transitions) > 0
    transition = gate.state_transitions[-1]
    assert transition.action_metadata.get("vessel_id") == "test_vessel_123"
    assert transition.action_metadata.get("tool_name") == "test_tool"

    # If there's a security event, it should also have vessel_id
    if gate.security_events:
        event = gate.security_events[-1]
        assert event.metadata.get("vessel_id") == "test_vessel_123"


def test_vessel_context_tier_config(tmp_path):
    """Test that tier config is accessible from vessel context."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    from vessels.core.vessel import TierConfig

    tier_config = TierConfig(
        tier0_enabled=True,
        tier0_model="Llama-3.2-1B",
        tier1_enabled=False,
        tier2_enabled=True
    )

    vessel = Vessel(
        vessel_id="v1",
        name="Test Vessel",
        description="Test",
        community_ids=["c1"],
        graph_namespace="c1_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
        tier_config=tier_config
    )
    registry.create_vessel(vessel)

    context = VesselContext.from_vessel_id("v1", registry)

    assert context.tier_config.tier0_enabled is True
    assert context.tier_config.tier1_enabled is False
    assert context.tier_config.tier2_enabled is True
    assert context.tier_config.tier0_model == "Llama-3.2-1B"


def test_vessel_context_not_found(tmp_path):
    """Test graceful handling when vessel not found."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Try to get non-existent vessel
    context = VesselContext.from_vessel_id("nonexistent", registry)

    assert context is None


def test_vessel_context_user_not_mapped(tmp_path):
    """Test fallback when user has no vessel mapping."""
    clear_user_vessel_mappings()

    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Create a vessel to use as default
    vessel = Vessel(
        vessel_id="default_v",
        name="Default",
        description="Default vessel",
        community_ids=["default"],
        graph_namespace="default_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # User with no mapping, but with explicit default
    context = VesselContext.from_user_id(
        "unmapped_user",
        registry,
        default_vessel_id="default_v"
    )

    assert context is not None
    assert context.vessel_id == "default_v"

    # Cleanup
    clear_user_vessel_mappings()


def test_vessel_context_thread_safe(tmp_path):
    """AC8: Test thread-safe vessel context resolution."""
    import threading

    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Create multiple vessels
    for i in range(5):
        vessel = Vessel(
            vessel_id=f"v{i}",
            name=f"Vessel {i}",
            description=f"Test vessel {i}",
            community_ids=[f"c{i}"],
            graph_namespace=f"c{i}_graph",
            privacy_level=CommunityPrivacy.PRIVATE,
            constraint_profile_id="default",
        )
        registry.create_vessel(vessel)

    results = []
    errors = []

    def resolve_context(vessel_id):
        try:
            context = VesselContext.from_vessel_id(vessel_id, registry)
            results.append(context)
        except Exception as e:
            errors.append(e)

    # Create threads to resolve contexts concurrently
    threads = []
    for i in range(5):
        t = threading.Thread(target=resolve_context, args=(f"v{i}",))
        threads.append(t)
        t.start()

    # Wait for all threads
    for t in threads:
        t.join()

    # All should succeed
    assert len(errors) == 0
    assert len(results) == 5
    assert all(r is not None for r in results)
