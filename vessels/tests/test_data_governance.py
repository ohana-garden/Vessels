"""
Tests for data governance and privacy enforcement.

Tests AC from story_data_governance.md:
- AC1: Cross-vessel query allowed (trusted community)
- AC2: Cross-vessel query denied (untrusted community)
- AC3: Commercial agent write blocked
"""

import pytest
from vessels.core import Vessel, VesselRegistry, PrivacyLevel
from vessels.knowledge.schema import CommunityPrivacy, NodeType, RelationType
from vessels.policy.enforcement import PolicyEnforcer, AccessDecision
from vessels.policy.data_policy import (
    get_allowed_node_types,
    get_allowed_relationship_types,
    is_node_type_allowed,
    is_relationship_type_allowed,
)
from vessels.agents.taxonomy import AgentClass, AgentIdentity


def test_privacy_level_node_policies():
    """Test that each privacy level has the correct node type policies."""
    # PRIVATE: no cross-community access
    private_nodes = get_allowed_node_types(CommunityPrivacy.PRIVATE)
    assert len(private_nodes) == 0

    # SHARED: limited node types
    shared_nodes = get_allowed_node_types(CommunityPrivacy.SHARED)
    assert NodeType.PLACE in shared_nodes
    assert NodeType.ORGANIZATION in shared_nodes
    assert NodeType.PERSON not in shared_nodes  # Sensitive

    # PUBLIC: more node types
    public_nodes = get_allowed_node_types(CommunityPrivacy.PUBLIC)
    assert NodeType.FACT in public_nodes
    assert NodeType.PATTERN in public_nodes

    # FEDERATED: most types
    federated_nodes = get_allowed_node_types(CommunityPrivacy.FEDERATED)
    assert NodeType.SERVANT in federated_nodes
    assert NodeType.AGENT_STATE in federated_nodes


def test_privacy_level_relationship_policies():
    """Test that each privacy level has the correct relationship type policies."""
    # PRIVATE: no cross-community access
    private_rels = get_allowed_relationship_types(CommunityPrivacy.PRIVATE)
    assert len(private_rels) == 0

    # SHARED: limited relationships
    shared_rels = get_allowed_relationship_types(CommunityPrivacy.SHARED)
    assert RelationType.LOCATED_AT in shared_rels
    assert RelationType.HAS_RESOURCE in shared_rels

    # FEDERATED: most relationships
    federated_rels = get_allowed_relationship_types(CommunityPrivacy.FEDERATED)
    assert RelationType.SERVES in federated_rels
    assert RelationType.COORDINATES_WITH in federated_rels


def test_node_type_allowed_check():
    """Test node type allowed checking."""
    # Public level allows FACT
    assert is_node_type_allowed(CommunityPrivacy.PUBLIC, NodeType.FACT) is True

    # Private level allows nothing
    assert is_node_type_allowed(CommunityPrivacy.PRIVATE, NodeType.FACT) is False

    # Shared level doesn't allow PERSON
    assert is_node_type_allowed(CommunityPrivacy.SHARED, NodeType.PERSON) is False


def test_relationship_type_allowed_check():
    """Test relationship type allowed checking."""
    # Federated allows COORDINATES_WITH
    assert is_relationship_type_allowed(
        CommunityPrivacy.FEDERATED,
        RelationType.COORDINATES_WITH
    ) is True

    # Private allows nothing
    assert is_relationship_type_allowed(
        CommunityPrivacy.PRIVATE,
        RelationType.LOCATED_AT
    ) is False


def test_cross_vessel_read_access_allowed(tmp_path):
    """AC1: Cross-vessel query allowed for trusted community."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Create vessel A with SHARED privacy
    vessel_a = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Shared vessel",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.SHARED,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel_a)

    # Mark community_b as trusted
    vessel_a.add_trusted_community("community_b")
    registry.create_vessel(vessel_a)  # Update

    # Agent from community_b (trusted)
    agent_from_b = AgentIdentity(
        agent_id="agent_b",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_b",
        vessel_id="vessel_b"
    )

    enforcer = PolicyEnforcer(registry)

    # Should allow read access
    decision = enforcer.check_read_access(
        vessel_id="vessel_a",
        agent_identity=agent_from_b,
        resource="community_graph"
    )

    assert decision.allowed is True
    assert "trusted" in decision.reason.lower()


def test_cross_vessel_read_access_denied(tmp_path):
    """AC2: Cross-vessel query denied for untrusted community."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    # Create vessel A with SHARED privacy
    vessel_a = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Shared vessel",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.SHARED,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel_a)

    # Agent from community_c (NOT trusted)
    agent_from_c = AgentIdentity(
        agent_id="agent_c",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_c",
        vessel_id="vessel_c"
    )

    enforcer = PolicyEnforcer(registry)

    # Should deny read access
    decision = enforcer.check_read_access(
        vessel_id="vessel_a",
        agent_identity=agent_from_c,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "not trusted" in decision.reason.lower()


def test_commercial_agent_read_denied(tmp_path):
    """Commercial agents cannot access community servant knowledge."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Test vessel",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PUBLIC,  # Even public!
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Commercial agent
    commercial_agent = AgentIdentity(
        agent_id="commercial_1",
        agent_class=AgentClass.COMMERCIAL_AGENT,
        community_id=None,
        vessel_id=None
    )

    enforcer = PolicyEnforcer(registry)

    # Should deny access to community_graph
    decision = enforcer.check_read_access(
        vessel_id="vessel_a",
        agent_identity=commercial_agent,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "commercial" in decision.reason.lower()


def test_commercial_agent_write_blocked(tmp_path):
    """AC3: Commercial agent write blocked to community resources."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Test vessel",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PUBLIC,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Commercial agent
    commercial_agent = AgentIdentity(
        agent_id="commercial_1",
        agent_class=AgentClass.COMMERCIAL_AGENT,
        community_id=None,
        vessel_id=None
    )

    enforcer = PolicyEnforcer(registry)

    # Should block write access
    decision = enforcer.check_write_access(
        vessel_id="vessel_a",
        agent_identity=commercial_agent,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "commercial" in decision.reason.lower()
    assert "cannot write" in decision.reason.lower()


def test_servant_agent_write_allowed(tmp_path):
    """Community servants can write to their own vessel."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Test vessel",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Servant agent from same community
    servant_agent = AgentIdentity(
        agent_id="servant_1",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_a",
        vessel_id="vessel_a"
    )

    enforcer = PolicyEnforcer(registry)

    # Should allow write access
    decision = enforcer.check_write_access(
        vessel_id="vessel_a",
        agent_identity=servant_agent,
        resource="community_graph"
    )

    assert decision.allowed is True
    assert "servant" in decision.reason.lower()


def test_servant_agent_write_denied_different_vessel(tmp_path):
    """Community servants cannot write to different vessel."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel_a = Vessel(
        vessel_id="vessel_a",
        name="Vessel A",
        description="Test vessel A",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel_a)

    # Servant agent from different community
    servant_agent_b = AgentIdentity(
        agent_id="servant_b",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_b",
        vessel_id="vessel_b"
    )

    enforcer = PolicyEnforcer(registry)

    # Should deny write access
    decision = enforcer.check_write_access(
        vessel_id="vessel_a",
        agent_identity=servant_agent_b,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "different vessel" in decision.reason.lower()


def test_public_vessel_read_access(tmp_path):
    """Public vessels allow read access to anyone."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_public",
        name="Public Vessel",
        description="Public knowledge",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PUBLIC,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Any agent
    any_agent = AgentIdentity(
        agent_id="agent_x",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_x",
        vessel_id="vessel_x"
    )

    enforcer = PolicyEnforcer(registry)

    # Should allow read access
    decision = enforcer.check_read_access(
        vessel_id="vessel_public",
        agent_identity=any_agent,
        resource="community_graph"
    )

    assert decision.allowed is True
    assert "public" in decision.reason.lower()


def test_private_vessel_same_community(tmp_path):
    """Private vessels allow access only to same community."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_private",
        name="Private Vessel",
        description="Private knowledge",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Agent from same community
    same_community_agent = AgentIdentity(
        agent_id="agent_a",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_a",
        vessel_id="vessel_private"
    )

    enforcer = PolicyEnforcer(registry)

    # Should allow access
    decision = enforcer.check_read_access(
        vessel_id="vessel_private",
        agent_identity=same_community_agent,
        resource="community_graph"
    )

    assert decision.allowed is True
    assert "same community" in decision.reason.lower()


def test_private_vessel_different_community(tmp_path):
    """Private vessels deny access to different community."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    vessel = Vessel(
        vessel_id="vessel_private",
        name="Private Vessel",
        description="Private knowledge",
        community_ids=["community_a"],
        graph_namespace="community_a_graph",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
    )
    registry.create_vessel(vessel)

    # Agent from different community
    different_community_agent = AgentIdentity(
        agent_id="agent_b",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_b",
        vessel_id="vessel_b"
    )

    enforcer = PolicyEnforcer(registry)

    # Should deny access
    decision = enforcer.check_read_access(
        vessel_id="vessel_private",
        agent_identity=different_community_agent,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "private" in decision.reason.lower() or "denied" in decision.reason.lower()


def test_vessel_not_found(tmp_path):
    """Gracefully handle vessel not found."""
    registry = VesselRegistry(db_path=str(tmp_path / "test.db"))

    agent = AgentIdentity(
        agent_id="agent_1",
        agent_class=AgentClass.COMMUNITY_SERVANT,
        community_id="community_a",
        vessel_id="vessel_a"
    )

    enforcer = PolicyEnforcer(registry)

    # Try to access non-existent vessel
    decision = enforcer.check_read_access(
        vessel_id="nonexistent",
        agent_identity=agent,
        resource="community_graph"
    )

    assert decision.allowed is False
    assert "not found" in decision.reason.lower()
