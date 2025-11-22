"""
Vessel Registry: Manages vessel lifecycle.

Provides CRUD operations for vessels and persistence.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .vessel import Vessel, PrivacyLevel

logger = logging.getLogger(__name__)


class VesselRegistry:
    """
    Registry for managing vessel instances.

    Handles:
    - Vessel creation
    - Listing and retrieval
    - Persistence to disk
    - Project association
    """

    def __init__(self, registry_dir: str = "work_dir/vessels"):
        """
        Initialize vessel registry.

        Args:
            registry_dir: Directory for storing vessel metadata
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.vessels: Dict[str, Vessel] = {}
        self._load_vessels()

    def _load_vessels(self):
        """Load all vessels from disk."""
        for vessel_file in self.registry_dir.glob("*.json"):
            try:
                with open(vessel_file, "r") as f:
                    data = json.load(f)
                vessel = Vessel.from_dict(data)
                self.vessels[vessel.vessel_id] = vessel
                logger.debug(f"Loaded vessel: {vessel.name} ({vessel.vessel_id})")
            except Exception as e:
                logger.error(f"Error loading vessel from {vessel_file}: {e}")

        logger.info(f"Loaded {len(self.vessels)} vessels from {self.registry_dir}")

    def _save_vessel(self, vessel: Vessel):
        """Persist vessel to disk."""
        vessel_file = self.registry_dir / f"{vessel.vessel_id}.json"
        with open(vessel_file, "w") as f:
            json.dump(vessel.to_dict(), f, indent=2)
        logger.debug(f"Saved vessel: {vessel.name} to {vessel_file}")

    def create_vessel(
        self,
        name: str,
        community_id: str,
        description: str = "",
        privacy_level: PrivacyLevel = PrivacyLevel.PRIVATE,
        constraint_profile_id: str = "servant_default",
    ) -> Vessel:
        """
        Create a new vessel.

        Args:
            name: Human-readable vessel name
            community_id: Primary community ID
            description: Vessel description
            privacy_level: Privacy level for vessel data
            constraint_profile_id: ID of constraint profile to use

        Returns:
            Created Vessel instance
        """
        vessel = Vessel.create(
            name=name,
            community_id=community_id,
            description=description,
            privacy_level=privacy_level,
            constraint_profile_id=constraint_profile_id,
        )

        self.vessels[vessel.vessel_id] = vessel
        self._save_vessel(vessel)

        logger.info(f"Created vessel: {name} ({vessel.vessel_id})")
        return vessel

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        """
        Retrieve a vessel by ID.

        Args:
            vessel_id: Vessel ID

        Returns:
            Vessel instance or None if not found
        """
        return self.vessels.get(vessel_id)

    def list_vessels(self) -> List[Vessel]:
        """
        List all vessels.

        Returns:
            List of all vessel instances
        """
        return list(self.vessels.values())

    def attach_project_to_vessel(self, vessel_id: str, project_id: str) -> bool:
        """
        Attach a project to a vessel.

        Args:
            vessel_id: Vessel ID
            project_id: Project ID

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if vessel is None:
            logger.warning(f"Vessel {vessel_id} not found")
            return False

        vessel.attach_project(project_id)
        self._save_vessel(vessel)

        logger.info(f"Attached project {project_id} to vessel {vessel_id}")
        return True

    def detach_project_from_vessel(self, vessel_id: str, project_id: str) -> bool:
        """
        Detach a project from a vessel.

        Args:
            vessel_id: Vessel ID
            project_id: Project ID

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if vessel is None:
            logger.warning(f"Vessel {vessel_id} not found")
            return False

        vessel.detach_project(project_id)
        self._save_vessel(vessel)

        logger.info(f"Detached project {project_id} from vessel {vessel_id}")
        return True

    def set_vessel_privacy(self, vessel_id: str, privacy_level: PrivacyLevel) -> bool:
        """
        Set vessel privacy level.

        Args:
            vessel_id: Vessel ID
            privacy_level: New privacy level

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if vessel is None:
            logger.warning(f"Vessel {vessel_id} not found")
            return False

        vessel.set_privacy_level(privacy_level)
        self._save_vessel(vessel)

        logger.info(f"Set vessel {vessel_id} privacy to {privacy_level.value}")
        return True

    def delete_vessel(self, vessel_id: str) -> bool:
        """
        Delete (archive) a vessel.

        Args:
            vessel_id: Vessel ID

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if vessel is None:
            logger.warning(f"Vessel {vessel_id} not found")
            return False

        # Archive instead of hard delete
        vessel.status = "archived"
        self._save_vessel(vessel)

        # Remove from active vessels
        del self.vessels[vessel_id]

        logger.info(f"Archived vessel {vessel_id}")
        return True

    def get_vessels_by_community(self, community_id: str) -> List[Vessel]:
        """
        Get all vessels for a specific community.

        Args:
            community_id: Community ID

        Returns:
            List of vessels associated with the community
        """
        return [
            v for v in self.vessels.values()
            if community_id in v.community_ids
        ]


# Global registry instance
vessel_registry = VesselRegistry()
