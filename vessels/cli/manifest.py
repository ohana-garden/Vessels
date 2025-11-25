"""
Vessel Manifest - Load and validate vessel definitions from YAML/JSON files.

Manifest format:
```yaml
vessels:
  - id: lower_puna_elders
    name: Lower Puna Elders Care
    description: Elder care vessel for Lower Puna community
    community_ids:
      - lower_puna
    graph_namespace: lower_puna_graph
    privacy_level: shared
    constraint_profile_id: servant_default
    tier_config:
      tier0_enabled: true
      tier0_model: Llama-3.2-1B
      tier1_enabled: true
      tier1_host: edge.lowerpuna.local
      tier1_port: 8080
      tier2_enabled: false
    connectors:
      nostr:
        enabled: false
```
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

import yaml

from vessels.core.vessel import (
    Vessel,
    PrivacyLevel,
    TierConfig,
    ConnectorConfig,
)
from vessels.knowledge.schema import CommunityPrivacy

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Manifest validation error."""
    path: str
    message: str
    severity: str = "error"  # error, warning


@dataclass
class ManifestValidationResult:
    """Result of manifest validation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    def add_error(self, path: str, message: str):
        self.errors.append(ValidationError(path, message, "error"))
        self.valid = False

    def add_warning(self, path: str, message: str):
        self.warnings.append(ValidationError(path, message, "warning"))


class ManifestLoader:
    """
    Loads and validates vessel manifest files.

    Supports YAML and JSON formats.
    """

    REQUIRED_VESSEL_FIELDS = ["name", "community_ids"]
    VALID_PRIVACY_LEVELS = ["private", "shared", "public", "federated"]

    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize manifest loader.

        Args:
            base_dir: Base directory for resolving relative paths
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def load(self, manifest_path: Union[str, Path]) -> List[Vessel]:
        """
        Load vessels from manifest file.

        Args:
            manifest_path: Path to manifest file (YAML or JSON)

        Returns:
            List of Vessel objects

        Raises:
            FileNotFoundError: If manifest file doesn't exist
            ValueError: If manifest is invalid
        """
        manifest_path = Path(manifest_path)

        if not manifest_path.is_absolute():
            manifest_path = self.base_dir / manifest_path

        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

        # Load manifest content
        content = self._load_file(manifest_path)

        # Validate manifest
        validation = self.validate(content)
        if not validation.valid:
            error_msgs = [f"{e.path}: {e.message}" for e in validation.errors]
            raise ValueError(f"Invalid manifest:\n" + "\n".join(error_msgs))

        # Log warnings
        for warning in validation.warnings:
            logger.warning(f"Manifest warning at {warning.path}: {warning.message}")

        # Parse vessels
        return self._parse_vessels(content)

    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load YAML or JSON file."""
        with open(path, "r") as f:
            if path.suffix in [".yaml", ".yml"]:
                return yaml.safe_load(f)
            elif path.suffix == ".json":
                return json.load(f)
            else:
                # Try YAML first, then JSON
                content = f.read()
                try:
                    return yaml.safe_load(content)
                except yaml.YAMLError:
                    return json.loads(content)

    def validate(self, content: Dict[str, Any]) -> ManifestValidationResult:
        """
        Validate manifest content.

        Args:
            content: Parsed manifest content

        Returns:
            ManifestValidationResult with errors and warnings
        """
        result = ManifestValidationResult(valid=True)

        # Check for vessels key
        if "vessels" not in content:
            result.add_error("root", "Missing 'vessels' key")
            return result

        vessels = content.get("vessels", [])
        if not isinstance(vessels, list):
            result.add_error("vessels", "Must be a list")
            return result

        if len(vessels) == 0:
            result.add_warning("vessels", "No vessels defined")

        # Validate each vessel
        for i, vessel_config in enumerate(vessels):
            self._validate_vessel(vessel_config, f"vessels[{i}]", result)

        return result

    def _validate_vessel(
        self,
        config: Dict[str, Any],
        path: str,
        result: ManifestValidationResult
    ):
        """Validate a single vessel configuration."""
        if not isinstance(config, dict):
            result.add_error(path, "Must be a dictionary")
            return

        # Check required fields
        for field in self.REQUIRED_VESSEL_FIELDS:
            if field not in config:
                result.add_error(f"{path}.{field}", f"Required field '{field}' is missing")

        # Validate name
        name = config.get("name")
        if name and not isinstance(name, str):
            result.add_error(f"{path}.name", "Must be a string")

        # Validate community_ids
        community_ids = config.get("community_ids")
        if community_ids:
            if not isinstance(community_ids, list):
                result.add_error(f"{path}.community_ids", "Must be a list")
            elif len(community_ids) == 0:
                result.add_warning(f"{path}.community_ids", "Empty community list")

        # Validate privacy_level
        privacy_level = config.get("privacy_level")
        if privacy_level and privacy_level not in self.VALID_PRIVACY_LEVELS:
            result.add_error(
                f"{path}.privacy_level",
                f"Invalid privacy level. Must be one of: {self.VALID_PRIVACY_LEVELS}"
            )

        # Validate tier_config
        tier_config = config.get("tier_config")
        if tier_config:
            self._validate_tier_config(tier_config, f"{path}.tier_config", result)

    def _validate_tier_config(
        self,
        config: Dict[str, Any],
        path: str,
        result: ManifestValidationResult
    ):
        """Validate tier configuration."""
        if not isinstance(config, dict):
            result.add_error(path, "Must be a dictionary")
            return

        # Validate tier0
        if "tier0_enabled" in config:
            if not isinstance(config["tier0_enabled"], bool):
                result.add_error(f"{path}.tier0_enabled", "Must be a boolean")

        # Validate tier1
        if "tier1_enabled" in config:
            if not isinstance(config["tier1_enabled"], bool):
                result.add_error(f"{path}.tier1_enabled", "Must be a boolean")

        if "tier1_port" in config:
            port = config["tier1_port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                result.add_error(f"{path}.tier1_port", "Must be a valid port number (1-65535)")

        # Validate tier2
        if "tier2_enabled" in config:
            if not isinstance(config["tier2_enabled"], bool):
                result.add_error(f"{path}.tier2_enabled", "Must be a boolean")

    def _parse_vessels(self, content: Dict[str, Any]) -> List[Vessel]:
        """Parse vessel configurations into Vessel objects."""
        vessels = []

        for vessel_config in content.get("vessels", []):
            vessel = self._parse_vessel(vessel_config)
            vessels.append(vessel)

        return vessels

    def _parse_vessel(self, config: Dict[str, Any]) -> Vessel:
        """Parse a single vessel configuration."""
        # Parse privacy level
        privacy_str = config.get("privacy_level", "private")
        try:
            privacy_level = CommunityPrivacy(privacy_str)
        except ValueError:
            privacy_level = CommunityPrivacy.PRIVATE

        # Parse tier config
        tier_config = self._parse_tier_config(config.get("tier_config", {}))

        # Generate ID if not provided
        vessel_id = config.get("id") or config.get("vessel_id")
        if not vessel_id:
            import uuid
            vessel_id = str(uuid.uuid4())

        # Generate graph namespace
        community_ids = config.get("community_ids", [])
        graph_namespace = config.get("graph_namespace")
        if not graph_namespace and community_ids:
            graph_namespace = f"{community_ids[0]}_graph"

        return Vessel(
            vessel_id=vessel_id,
            name=config.get("name", ""),
            description=config.get("description", ""),
            community_ids=community_ids,
            graph_namespace=graph_namespace or "default_graph",
            privacy_level=privacy_level,
            constraint_profile_id=config.get("constraint_profile_id", "servant_default"),
            servant_project_ids=config.get("servant_project_ids", []),
            connectors=config.get("connectors", {}),
            tier_config=tier_config,
        )

    def _parse_tier_config(self, config: Dict[str, Any]) -> TierConfig:
        """Parse tier configuration."""
        return TierConfig(
            tier0_enabled=config.get("tier0_enabled", True),
            tier0_model=config.get("tier0_model", "Llama-3.2-1B"),
            tier0_device=config.get("tier0_device", "cpu"),
            tier0_endpoints=config.get("tier0_endpoints", {}),
            tier1_enabled=config.get("tier1_enabled", True),
            tier1_host=config.get("tier1_host", "localhost"),
            tier1_port=config.get("tier1_port", 8080),
            tier1_model=config.get("tier1_model", "Llama-3.1-70B"),
            tier1_endpoints=config.get("tier1_endpoints", {}),
            tier2_enabled=config.get("tier2_enabled", False),
            tier2_allowed_models=config.get("tier2_allowed_models", []),
            tier2_sanitize_data=config.get("tier2_sanitize_data", True),
            tier2_endpoints=config.get("tier2_endpoints", {}),
        )


def load_manifest(manifest_path: Union[str, Path]) -> List[Vessel]:
    """
    Load vessels from a manifest file.

    Convenience function for quick manifest loading.

    Args:
        manifest_path: Path to manifest file

    Returns:
        List of Vessel objects
    """
    loader = ManifestLoader()
    return loader.load(manifest_path)


def validate_manifest(manifest_path: Union[str, Path]) -> ManifestValidationResult:
    """
    Validate a manifest file without loading vessels.

    Args:
        manifest_path: Path to manifest file

    Returns:
        ManifestValidationResult
    """
    loader = ManifestLoader()
    path = Path(manifest_path)

    if not path.exists():
        result = ManifestValidationResult(valid=False)
        result.add_error("file", f"File not found: {manifest_path}")
        return result

    content = loader._load_file(path)
    return loader.validate(content)
