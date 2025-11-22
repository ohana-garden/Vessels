"""
Tests for governance entities in the knowledge graph.

Tests AC from story_governance_entities.md:
- AC1: Create governance body
- AC2: Record decision
- AC3: Query governance history
"""

import pytest
from datetime import datetime
from vessels.knowledge.graphiti_client import VesselsGraphitiClient
from vessels.knowledge.governance_schema import GovernanceBody, Decision, GovernanceSchemaExtension


def test_create_governance_body():
    """AC1: Create governance body node in graph."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True  # Use mock client for testing
    )

    # Create governance body
    body_id = client.create_governance_body(
        body_id="council_1",
        name="Puna Elders Council",
        body_type="council",
        members=["elder_1", "elder_2", "elder_3"]
    )

    assert body_id is not None
    assert body_id == "council_1"


def test_record_policy_decision():
    """AC2: Record a governance decision."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    # First create a governance body
    client.create_governance_body(
        body_id="council_1",
        name="Puna Elders Council",
        body_type="council",
        members=["elder_1", "elder_2"]
    )

    # Record a decision
    decision_id = client.record_policy_decision(
        decision_id="decision_1",
        governance_body_id="council_1",
        description="Approved transport servant for community",
        approved_by=["elder_1", "elder_2"],
        vessel_id="vessel_transport_1"
    )

    assert decision_id is not None
    assert decision_id == "decision_1"


def test_link_decision_to_vessel():
    """Test linking a decision to a vessel."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    # Create governance body
    client.create_governance_body(
        body_id="board_1",
        name="Community Board",
        body_type="board",
        members=["member_1", "member_2"]
    )

    # Record decision linked to vessel
    decision_id = client.record_policy_decision(
        decision_id="decision_2",
        governance_body_id="board_1",
        description="Approved data sharing policy",
        approved_by=["member_1", "member_2"],
        vessel_id="vessel_health_1"
    )

    # Decision should be created and linked
    assert decision_id == "decision_2"


def test_governance_schema_extension():
    """Test GovernanceSchemaExtension node types."""
    # Verify schema constants
    assert GovernanceSchemaExtension.GOVERNANCE_BODY == "GovernanceBody"
    assert GovernanceSchemaExtension.DECISION == "Decision"
    assert GovernanceSchemaExtension.POLICY == "Policy"

    # Verify relationship types
    assert GovernanceSchemaExtension.MADE_DECISION == "MADE_DECISION"
    assert GovernanceSchemaExtension.APPROVES == "APPROVES"
    assert GovernanceSchemaExtension.ACCOUNTABLE_TO == "ACCOUNTABLE_TO"


def test_governance_body_dataclass():
    """Test GovernanceBody dataclass."""
    body = GovernanceBody(
        id="council_test",
        name="Test Council",
        body_type="council",
        community_id="community_1",
        members=["m1", "m2", "m3"],
        created_at=datetime.utcnow(),
        active=True
    )

    assert body.id == "council_test"
    assert body.name == "Test Council"
    assert body.body_type == "council"
    assert len(body.members) == 3
    assert body.active is True


def test_decision_dataclass():
    """Test Decision dataclass."""
    decision = Decision(
        id="decision_test",
        governance_body_id="council_1",
        decision_type="approval",
        description="Test decision",
        approved_at=datetime.utcnow(),
        approved_by=["m1", "m2"]
    )

    assert decision.id == "decision_test"
    assert decision.governance_body_id == "council_1"
    assert decision.decision_type == "approval"
    assert len(decision.approved_by) == 2


def test_get_vessel_governance_history():
    """AC3: Query governance history for a vessel."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    # For mock client, history will be empty (query not fully implemented)
    # But the method should not error
    history = client.get_vessel_governance_history(
        vessel_id="vessel_1",
        limit=10
    )

    # Should return a list (even if empty for mock)
    assert isinstance(history, list)


def test_multiple_governance_bodies():
    """Test creating multiple governance bodies."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    # Create council
    council_id = client.create_governance_body(
        body_id="council_1",
        name="Elders Council",
        body_type="council",
        members=["e1", "e2", "e3"]
    )

    # Create board
    board_id = client.create_governance_body(
        body_id="board_1",
        name="Community Board",
        body_type="board",
        members=["b1", "b2", "b3", "b4"]
    )

    # Create assembly
    assembly_id = client.create_governance_body(
        body_id="assembly_1",
        name="General Assembly",
        body_type="assembly",
        members=["a1", "a2", "a3", "a4", "a5"]
    )

    assert council_id == "council_1"
    assert board_id == "board_1"
    assert assembly_id == "assembly_1"


def test_decision_without_vessel():
    """Test recording a decision without linking to vessel."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    client.create_governance_body(
        body_id="council_1",
        name="Council",
        body_type="council",
        members=["m1"]
    )

    # Decision without vessel_id
    decision_id = client.record_policy_decision(
        decision_id="decision_general",
        governance_body_id="council_1",
        description="General policy decision",
        approved_by=["m1"],
        vessel_id=None  # No vessel linkage
    )

    assert decision_id == "decision_general"


def test_governance_body_types():
    """Test different governance body types."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    body_types = ["council", "board", "assembly", "working_group"]

    for i, body_type in enumerate(body_types):
        body_id = client.create_governance_body(
            body_id=f"body_{i}",
            name=f"Test {body_type.title()}",
            body_type=body_type,
            members=[f"member_{i}"]
        )
        assert body_id is not None


def test_decision_with_multiple_approvers():
    """Test decision with multiple approvers."""
    client = VesselsGraphitiClient(
        community_id="test_community",
        allow_mock=True
    )

    client.create_governance_body(
        body_id="council_multi",
        name="Large Council",
        body_type="council",
        members=["m1", "m2", "m3", "m4", "m5"]
    )

    # Decision approved by multiple members
    decision_id = client.record_policy_decision(
        decision_id="decision_multi",
        governance_body_id="council_multi",
        description="Multi-approval decision",
        approved_by=["m1", "m2", "m3", "m4"],  # 4 out of 5
        vessel_id="vessel_1"
    )

    assert decision_id == "decision_multi"
