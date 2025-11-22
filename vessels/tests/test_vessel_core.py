"""
Tests for first-class Vessel abstraction.

Tests cover:
- Vessel creation
- Vessel listing and retrieval
- Project association
- Privacy management
- Persistence and reload
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from vessels.core import Vessel, VesselRegistry, PrivacyLevel


@pytest.fixture
def temp_registry():
    """Create a temporary vessel registry."""
    temp_dir = tempfile.mkdtemp()
    registry = VesselRegistry(registry_dir=temp_dir)
    yield registry
    shutil.rmtree(temp_dir)


def test_create_vessel(temp_registry):
    """Test creating a vessel with minimal config."""
    vessel = temp_registry.create_vessel(
        name="Test Vessel",
        community_id="test_community",
        description="A test vessel"
    )

    assert vessel is not None
    assert vessel.vessel_id is not None
    assert vessel.name == "Test Vessel"
    assert vessel.community_ids == ["test_community"]
    assert vessel.graph_namespace == "test_community_graph"
    assert vessel.config.privacy_level == PrivacyLevel.PRIVATE


def test_create_vessel_with_privacy(temp_registry):
    """Test creating a vessel with custom privacy level."""
    vessel = temp_registry.create_vessel(
        name="Public Vessel",
        community_id="test_community",
        privacy_level=PrivacyLevel.PUBLIC
    )

    assert vessel.config.privacy_level == PrivacyLevel.PUBLIC


def test_list_vessels_empty(temp_registry):
    """Test listing vessels when none exist."""
    vessels = temp_registry.list_vessels()
    assert len(vessels) == 0


def test_list_vessels(temp_registry):
    """Test listing vessels after creating several."""
    temp_registry.create_vessel("Vessel 1", "community1")
    temp_registry.create_vessel("Vessel 2", "community2")
    temp_registry.create_vessel("Vessel 3", "community3")

    vessels = temp_registry.list_vessels()
    assert len(vessels) == 3
    assert all(isinstance(v, Vessel) for v in vessels)


def test_get_vessel(temp_registry):
    """Test retrieving a vessel by ID."""
    vessel = temp_registry.create_vessel("Test Vessel", "test_community")
    vessel_id = vessel.vessel_id

    retrieved = temp_registry.get_vessel(vessel_id)
    assert retrieved is not None
    assert retrieved.vessel_id == vessel_id
    assert retrieved.name == "Test Vessel"


def test_get_vessel_not_found(temp_registry):
    """Test retrieving a non-existent vessel."""
    result = temp_registry.get_vessel("nonexistent_id")
    assert result is None


def test_attach_project(temp_registry):
    """Test attaching a project to a vessel."""
    vessel = temp_registry.create_vessel("Test Vessel", "test_community")
    project_id = "project_123"

    success = temp_registry.attach_project_to_vessel(vessel.vessel_id, project_id)
    assert success is True

    # Verify attachment
    retrieved = temp_registry.get_vessel(vessel.vessel_id)
    assert project_id in retrieved.servant_project_ids


def test_attach_project_idempotent(temp_registry):
    """Test attaching the same project twice (should be idempotent)."""
    vessel = temp_registry.create_vessel("Test Vessel", "test_community")
    project_id = "project_123"

    # Attach twice
    temp_registry.attach_project_to_vessel(vessel.vessel_id, project_id)
    temp_registry.attach_project_to_vessel(vessel.vessel_id, project_id)

    # Should only appear once
    retrieved = temp_registry.get_vessel(vessel.vessel_id)
    assert retrieved.servant_project_ids.count(project_id) == 1


def test_detach_project(temp_registry):
    """Test detaching a project from a vessel."""
    vessel = temp_registry.create_vessel("Test Vessel", "test_community")
    project_id = "project_123"

    temp_registry.attach_project_to_vessel(vessel.vessel_id, project_id)
    temp_registry.detach_project_from_vessel(vessel.vessel_id, project_id)

    retrieved = temp_registry.get_vessel(vessel.vessel_id)
    assert project_id not in retrieved.servant_project_ids


def test_set_privacy(temp_registry):
    """Test changing vessel privacy level."""
    vessel = temp_registry.create_vessel(
        "Test Vessel",
        "test_community",
        privacy_level=PrivacyLevel.PRIVATE
    )

    # Change to shared
    temp_registry.set_vessel_privacy(vessel.vessel_id, PrivacyLevel.SHARED)

    # Verify change
    retrieved = temp_registry.get_vessel(vessel.vessel_id)
    assert retrieved.config.privacy_level == PrivacyLevel.SHARED


def test_persistence(temp_registry):
    """Test that vessels survive registry reload."""
    # Create vessel
    vessel = temp_registry.create_vessel(
        "Persistent Vessel",
        "test_community",
        description="Should persist"
    )
    vessel_id = vessel.vessel_id

    # Create new registry pointing to same directory
    registry_dir = temp_registry.registry_dir
    new_registry = VesselRegistry(registry_dir=str(registry_dir))

    # Verify vessel was loaded
    loaded_vessel = new_registry.get_vessel(vessel_id)
    assert loaded_vessel is not None
    assert loaded_vessel.name == "Persistent Vessel"
    assert loaded_vessel.description == "Should persist"


def test_delete_vessel(temp_registry):
    """Test deleting (archiving) a vessel."""
    vessel = temp_registry.create_vessel("Test Vessel", "test_community")
    vessel_id = vessel.vessel_id

    # Delete vessel
    success = temp_registry.delete_vessel(vessel_id)
    assert success is True

    # Verify not in active vessels
    result = temp_registry.get_vessel(vessel_id)
    assert result is None


def test_get_vessels_by_community(temp_registry):
    """Test retrieving vessels for a specific community."""
    temp_registry.create_vessel("Vessel 1", "community_a")
    temp_registry.create_vessel("Vessel 2", "community_a")
    temp_registry.create_vessel("Vessel 3", "community_b")

    vessels_a = temp_registry.get_vessels_by_community("community_a")
    vessels_b = temp_registry.get_vessels_by_community("community_b")

    assert len(vessels_a) == 2
    assert len(vessels_b) == 1


def test_trusted_communities(temp_registry):
    """Test adding and checking trusted communities."""
    vessel = temp_registry.create_vessel("Test Vessel", "community_a")

    # Not trusted initially
    assert not vessel.is_trusted_community("community_b")

    # Add trust
    vessel.add_trusted_community("community_b")
    assert vessel.is_trusted_community("community_b")

    # Persist and reload
    temp_registry._save_vessel(vessel)
    loaded_vessel = temp_registry.get_vessel(vessel.vessel_id)
    assert loaded_vessel.is_trusted_community("community_b")


def test_vessel_serialization(temp_registry):
    """Test vessel to_dict and from_dict round-trip."""
    vessel = temp_registry.create_vessel(
        "Test Vessel",
        "test_community",
        description="Test description",
        privacy_level=PrivacyLevel.SHARED
    )

    # Serialize
    data = vessel.to_dict()

    # Deserialize
    restored = Vessel.from_dict(data)

    # Verify all fields match
    assert restored.vessel_id == vessel.vessel_id
    assert restored.name == vessel.name
    assert restored.description == vessel.description
    assert restored.community_ids == vessel.community_ids
    assert restored.config.privacy_level == vessel.config.privacy_level


def test_tier_config():
    """Test tier configuration on vessel."""
    vessel = Vessel.create("Test Vessel", "test_community")

    # Check defaults
    assert vessel.config.tier_config.tier0_enabled is True
    assert vessel.config.tier_config.tier0_model == "Llama-3.2-1B"
    assert vessel.config.tier_config.tier1_enabled is True
    assert vessel.config.tier_config.tier2_enabled is False


def test_connector_config():
    """Test connector configuration on vessel."""
    vessel = Vessel.create("Test Vessel", "test_community")

    # Check defaults (all connectors disabled by default for privacy)
    assert vessel.config.connector_config.nostr_enabled is False
    assert vessel.config.connector_config.petals_enabled is False
