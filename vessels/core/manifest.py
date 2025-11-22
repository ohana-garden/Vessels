"""
Vessel manifest loading and validation.

Supports YAML-based vessel definitions for easy configuration.
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any

from .vessel import Vessel, PrivacyLevel, TierConfig, ConnectorConfig, VesselConfig

logger = logging.getLogger(__name__)


def load_manifest(manifest_path: str) -> List[Vessel]:
    """
    Load vessels from a YAML manifest file.

    Args:
        manifest_path: Path to manifest YAML file

    Returns:
        List of Vessel instances

    Example manifest:
        vessels:
          - name: "Lower Puna Elders Care"
            community_id: "lower_puna_elders"
            description: "Elder care coordination"
            privacy_level: "private"
            constraint_profile_id: "servant_default"
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_file, "r") as f:
        data = yaml.safe_load(f)

    if "vessels" not in data:
        raise ValueError("Manifest must contain 'vessels' key")

    vessels = []
    for vessel_data in data["vessels"]:
        vessel = _create_vessel_from_dict(vessel_data)
        vessels.append(vessel)

    logger.info(f"Loaded {len(vessels)} vessels from manifest {manifest_path}")
    return vessels


def validate_manifest(manifest_path: str) -> List[str]:
    """
    Validate a manifest file.

    Args:
        manifest_path: Path to manifest YAML file

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    try:
        manifest_file = Path(manifest_path)
        if not manifest_file.exists():
            errors.append(f"Manifest file not found: {manifest_path}")
            return errors

        with open(manifest_file, "r") as f:
            data = yaml.safe_load(f)

        if "vessels" not in data:
            errors.append("Manifest must contain 'vessels' key")
            return errors

        for i, vessel_data in enumerate(data["vessels"]):
            vessel_errors = _validate_vessel_data(vessel_data, index=i)
            errors.extend(vessel_errors)

    except yaml.YAMLError as e:
        errors.append(f"YAML parsing error: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


def _create_vessel_from_dict(data: Dict[str, Any]) -> Vessel:
    """Create a Vessel from manifest dictionary."""
    # Required fields
    name = data["name"]
    community_id = data["community_id"]

    # Optional fields
    description = data.get("description", "")
    privacy_level = PrivacyLevel(data.get("privacy_level", "private"))
    constraint_profile_id = data.get("constraint_profile_id", "servant_default")

    # Tier config
    tier_data = data.get("tier_config", {})
    tier_config = TierConfig(
        tier0_enabled=tier_data.get("tier0_enabled", True),
        tier0_model=tier_data.get("tier0_model", "Llama-3.2-1B"),
        tier1_enabled=tier_data.get("tier1_enabled", True),
        tier1_host=tier_data.get("tier1_host", "localhost"),
        tier2_enabled=tier_data.get("tier2_enabled", False),
    )

    # Connector config
    connector_data = data.get("connectors", {})
    connector_config = ConnectorConfig(
        nostr_enabled=connector_data.get("nostr_enabled", False),
        petals_enabled=connector_data.get("petals_enabled", False),
    )

    # Trusted communities
    trusted_communities = data.get("trusted_communities", [])

    # Build config
    config = VesselConfig(
        privacy_level=privacy_level,
        constraint_profile_id=constraint_profile_id,
        tier_config=tier_config,
        connector_config=connector_config,
        trusted_communities=trusted_communities,
    )

    # Create vessel
    vessel = Vessel.create(
        name=name,
        community_id=community_id,
        description=description,
        privacy_level=privacy_level,
        constraint_profile_id=constraint_profile_id,
    )

    # Override config
    vessel.config = config

    return vessel


def _validate_vessel_data(data: Dict[str, Any], index: int) -> List[str]:
    """Validate a single vessel entry."""
    errors = []
    prefix = f"Vessel {index}"

    # Required fields
    if "name" not in data:
        errors.append(f"{prefix}: Missing required field 'name'")
    if "community_id" not in data:
        errors.append(f"{prefix}: Missing required field 'community_id'")

    # Validate privacy level
    if "privacy_level" in data:
        try:
            PrivacyLevel(data["privacy_level"])
        except ValueError:
            errors.append(
                f"{prefix}: Invalid privacy_level '{data['privacy_level']}'. "
                f"Must be one of: private, shared, public, federated"
            )

    return errors
