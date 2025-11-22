import tempfile
from datetime import datetime

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import TierConfig, Vessel
from vessels.knowledge.schema import CommunityPrivacy


def test_vessel_registry_persistence_cycle(tmp_path):
    db_path = tmp_path / "vessels_meta.db"
    registry = VesselRegistry(db_path=str(db_path))

    vessel = Vessel(
        vessel_id="v1",
        name="Test Vessel",
        description="Demo vessel",
        community_ids=["c1"],
        graph_namespace="ns1",
        privacy_level=CommunityPrivacy.PRIVATE,
        constraint_profile_id="default",
        servant_project_ids=["p1"],
        connectors={"nostr": {"enabled": "false"}},
        tier_config=TierConfig(tier0_enabled=True, tier1_enabled=False, tier2_enabled=True),
    )

    registry.create_vessel(vessel)

    loaded = registry.get_vessel("v1")
    assert loaded is not None
    assert loaded.name == "Test Vessel"
    assert loaded.tier_config.tier0_enabled is True
    assert loaded.tier_config.tier1_enabled is False

    registry.attach_project_to_vessel("v1", "p2")
    updated = registry.get_vessel("v1")
    assert "p2" in updated.servant_project_ids

    registry.set_vessel_privacy("v1", CommunityPrivacy.PUBLIC)
    assert registry.get_vessel("v1").privacy_level == CommunityPrivacy.PUBLIC

    registry.delete_vessel("v1")
    assert registry.get_vessel("v1") is None


def test_vessel_load_from_config():
    config = {
        "vessels": [
            {
                "id": "alpha",
                "name": "Alpha",
                "description": "First",
                "community_ids": ["c1", "c2"],
                "graph_namespace": "c1",
                "privacy_level": "shared",
                "constraint_profile_id": "constraints",
                "servant_project_ids": ["proj"],
                "connectors": {"nostr": {"enabled": "true"}},
                "tier_config": {"tier0_enabled": True, "tier1_enabled": True},
            }
        ]
    }

    vessels = VesselRegistry.load_from_config(config)
    assert len(vessels) == 1
    vessel = vessels[0]
    assert vessel.vessel_id == "alpha"
    assert vessel.tier_config.tier0_enabled is True
    assert vessel.privacy_level == CommunityPrivacy.SHARED
