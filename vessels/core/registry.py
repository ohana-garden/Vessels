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
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from vessels.knowledge.schema import CommunityPrivacy

from .vessel import TierConfig, Vessel


class VesselRegistry:
    """Persist and retrieve Vessel definitions."""

    def __init__(self, db_path: str = "vessels_metadata.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_schema()

    def _create_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS vessels (
                vessel_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                community_ids TEXT NOT NULL,
                graph_namespace TEXT NOT NULL,
                privacy_level TEXT NOT NULL,
                constraint_profile_id TEXT NOT NULL,
                servant_project_ids TEXT,
                connectors TEXT,
                tier_config TEXT
            )
            """
        )
        self.conn.commit()

    def create_vessel(self, vessel: Vessel) -> Vessel:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO vessels
            (vessel_id, name, description, community_ids, graph_namespace, privacy_level,
             constraint_profile_id, servant_project_ids, connectors, tier_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vessel.vessel_id,
                vessel.name,
                vessel.description,
                json.dumps(vessel.community_ids),
                vessel.graph_namespace,
                vessel.privacy_level.value,
                vessel.constraint_profile_id,
                json.dumps(vessel.servant_project_ids),
                json.dumps(vessel.connectors),
                json.dumps(self._tier_to_dict(vessel.tier_config)),
            ),
        )
        self.conn.commit()
        return vessel

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vessels WHERE vessel_id = ?", (vessel_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return self._row_to_vessel(row)

    def list_vessels(self) -> List[Vessel]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vessels ORDER BY vessel_id")
        return [self._row_to_vessel(r) for r in cursor.fetchall()]

    def delete_vessel(self, vessel_id: str) -> None:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM vessels WHERE vessel_id = ?", (vessel_id,))
        self.conn.commit()

    def attach_project_to_vessel(self, vessel_id: str, project_id: str) -> Optional[Vessel]:
        vessel = self.get_vessel(vessel_id)
        if not vessel:
            return None
        vessel.attach_project(project_id)
        return self.create_vessel(vessel)

    def set_vessel_privacy(
        self, vessel_id: str, privacy_level: CommunityPrivacy
    ) -> Optional[Vessel]:
        vessel = self.get_vessel(vessel_id)
        if not vessel:
            return None
        vessel.privacy_level = privacy_level
        return self.create_vessel(vessel)

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def _tier_to_dict(tier: TierConfig) -> Dict[str, Any]:
        return {
            "tier0_enabled": tier.tier0_enabled,
            "tier1_enabled": tier.tier1_enabled,
            "tier2_enabled": tier.tier2_enabled,
            "tier0_endpoints": tier.tier0_endpoints,
            "tier1_endpoints": tier.tier1_endpoints,
            "tier2_endpoints": tier.tier2_endpoints,
        }

    @staticmethod
    def _tier_from_dict(data: Dict[str, Any]) -> TierConfig:
        return TierConfig(
            tier0_enabled=data.get("tier0_enabled", False),
            tier1_enabled=data.get("tier1_enabled", False),
            tier2_enabled=data.get("tier2_enabled", False),
            tier0_endpoints=data.get("tier0_endpoints", {}),
            tier1_endpoints=data.get("tier1_endpoints", {}),
            tier2_endpoints=data.get("tier2_endpoints", {}),
        )

    def _row_to_vessel(self, row: Any) -> Vessel:
        (
            vessel_id,
            name,
            description,
            community_ids,
            graph_namespace,
            privacy_level,
            constraint_profile_id,
            servant_project_ids,
            connectors,
            tier_config,
        ) = row

        return Vessel(
            vessel_id=vessel_id,
            name=name,
            description=description or "",
            community_ids=json.loads(community_ids or "[]"),
            graph_namespace=graph_namespace,
            privacy_level=CommunityPrivacy(privacy_level),
            constraint_profile_id=constraint_profile_id,
            servant_project_ids=json.loads(servant_project_ids or "[]"),
            connectors=json.loads(connectors or "{}"),
            tier_config=self._tier_from_dict(json.loads(tier_config or "{}")),
        )

    @classmethod
    def load_from_config(cls, config: Dict[str, Any]) -> List[Vessel]:
        vessels_config = config.get("vessels", [])
        vessels: List[Vessel] = []
        for entry in vessels_config:
            tier_data = entry.get("tier_config", {})
            tier = cls._tier_from_dict(tier_data)
            vessels.append(
                Vessel(
                    vessel_id=entry["id"],
                    name=entry.get("name", entry["id"]),
                    description=entry.get("description", ""),
                    community_ids=entry.get("community_ids", []),
                    graph_namespace=entry.get("graph_namespace", entry.get("community_ids", [""])[0]),
                    privacy_level=CommunityPrivacy(
                        entry.get("privacy_level", CommunityPrivacy.PRIVATE)
                    ),
                    constraint_profile_id=entry.get("constraint_profile_id", "default"),
                    servant_project_ids=entry.get("servant_project_ids", []),
                    connectors=entry.get("connectors", {}),
                    tier_config=tier,
                )
            )
        return vessels


def load_config_file(path: str) -> Dict[str, Any]:
    import yaml

    resolved = Path(path)
    with resolved.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
