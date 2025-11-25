"""
Vessel Registry: Manages vessel lifecycle using SQLite persistence.
"""
import json
import sqlite3
import logging
import threading
from typing import Any, Dict, List, Optional, Union, overload
from datetime import datetime
from pathlib import Path

# Ensure these imports match your project structure
from .vessel import TierConfig, Vessel, PrivacyLevel
from vessels.knowledge.schema import CommunityPrivacy

logger = logging.getLogger(__name__)


class VesselRegistry:
    """Persist and retrieve Vessel definitions using SQLite."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        registry_dir: Optional[str] = None
    ):
        """
        Initialize VesselRegistry.

        Args:
            db_path: Path to SQLite database file
            registry_dir: Directory for storing vessel data (db_path will be created in this dir)
        """
        if registry_dir:
            self.registry_dir = Path(registry_dir)
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(self.registry_dir / "vessels_metadata.db")
        else:
            self.db_path = db_path or "vessels_metadata.db"
            self.registry_dir = Path(self.db_path).parent

        self._lock = threading.RLock()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_schema()

    def _create_schema(self) -> None:
        """Create the database schema if it doesn't exist."""
        with self._lock:
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
                    tier_config TEXT,
                    created_at TEXT,
                    last_active TEXT,
                    status TEXT
                )
                """
            )
            self.conn.commit()

    def create_vessel(
        self,
        vessel_or_name: Union[Vessel, str],
        community_id: Optional[str] = None,
        description: str = "",
        privacy_level: Optional[Union[PrivacyLevel, CommunityPrivacy]] = None,
        constraint_profile_id: str = "servant_default",
    ) -> Vessel:
        """
        Create and persist a vessel.

        Can be called two ways:
        1. create_vessel(vessel: Vessel) - Save an existing Vessel object
        2. create_vessel(name, community_id, ...) - Create new Vessel from parameters

        Args:
            vessel_or_name: Either a Vessel object or a vessel name string
            community_id: Community ID (required if vessel_or_name is a string)
            description: Vessel description
            privacy_level: Privacy level (defaults to PRIVATE)
            constraint_profile_id: Constraint profile ID

        Returns:
            The created/saved Vessel
        """
        if isinstance(vessel_or_name, Vessel):
            # Called with Vessel object - save it directly
            vessel = vessel_or_name
        else:
            # Called with name and community_id - create new Vessel
            if community_id is None:
                raise ValueError("community_id is required when creating vessel by name")

            # Handle privacy level
            if privacy_level is None:
                cp_privacy = CommunityPrivacy.PRIVATE
            elif isinstance(privacy_level, PrivacyLevel):
                cp_privacy = CommunityPrivacy(privacy_level.value)
            else:
                cp_privacy = privacy_level

            vessel = Vessel.create(
                name=vessel_or_name,
                community_id=community_id,
                description=description,
                privacy_level=PrivacyLevel(cp_privacy.value),
                constraint_profile_id=constraint_profile_id,
            )

        return self._save_vessel(vessel)

    def _save_vessel(self, vessel: Vessel) -> Vessel:
        """
        Persist a vessel to the database.

        Args:
            vessel: Vessel to save

        Returns:
            The saved Vessel
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO vessels
                (vessel_id, name, description, community_ids, graph_namespace, privacy_level,
                 constraint_profile_id, servant_project_ids, connectors, tier_config,
                 created_at, last_active, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    vessel.created_at.isoformat(),
                    vessel.last_active.isoformat(),
                    vessel.status
                ),
            )
            self.conn.commit()
        return vessel

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        """
        Retrieve a vessel by ID.

        Args:
            vessel_id: The vessel ID to look up

        Returns:
            Vessel if found, None otherwise
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vessels WHERE vessel_id = ?", (vessel_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_vessel(row)

    def list_vessels(self) -> List[Vessel]:
        """
        List all active vessels.

        Returns:
            List of all Vessel objects
        """
        with self._lock:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM vessels WHERE status != 'archived' ORDER BY vessel_id")
            return [self._row_to_vessel(r) for r in cursor.fetchall()]

    def get_vessels_by_community(self, community_id: str) -> List[Vessel]:
        """
        Get all vessels associated with a community.

        Args:
            community_id: The community ID to filter by

        Returns:
            List of Vessels belonging to the community
        """
        with self._lock:
            cursor = self.conn.cursor()
            # Use LIKE to search in JSON array - not ideal but works for SQLite
            cursor.execute(
                "SELECT * FROM vessels WHERE community_ids LIKE ? AND status != 'archived'",
                (f'%"{community_id}"%',)
            )
            return [self._row_to_vessel(r) for r in cursor.fetchall()]

    def delete_vessel(self, vessel_id: str) -> bool:
        """
        Delete (archive) a vessel.

        Args:
            vessel_id: The vessel ID to delete

        Returns:
            True if vessel was deleted, False if not found
        """
        with self._lock:
            vessel = self.get_vessel(vessel_id)
            if not vessel:
                return False

            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM vessels WHERE vessel_id = ?", (vessel_id,))
            self.conn.commit()
            return True

    def attach_project_to_vessel(self, vessel_id: str, project_id: str) -> bool:
        """
        Attach a servant project to a vessel.

        Args:
            vessel_id: The vessel ID
            project_id: The project ID to attach

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if not vessel:
            return False
        vessel.attach_project(project_id)
        self._save_vessel(vessel)
        return True

    def detach_project_from_vessel(self, vessel_id: str, project_id: str) -> bool:
        """
        Detach a servant project from a vessel.

        Args:
            vessel_id: The vessel ID
            project_id: The project ID to detach

        Returns:
            True if successful, False if vessel not found
        """
        vessel = self.get_vessel(vessel_id)
        if not vessel:
            return False
        vessel.detach_project(project_id)
        self._save_vessel(vessel)
        return True

    def set_vessel_privacy(
        self,
        vessel_id: str,
        privacy_level: Union[PrivacyLevel, CommunityPrivacy]
    ) -> Optional[Vessel]:
        """
        Update a vessel's privacy level.

        Args:
            vessel_id: The vessel ID
            privacy_level: New privacy level

        Returns:
            Updated Vessel if successful, None if not found
        """
        vessel = self.get_vessel(vessel_id)
        if not vessel:
            return None

        if isinstance(privacy_level, PrivacyLevel):
            vessel.privacy_level = CommunityPrivacy(privacy_level.value)
        else:
            vessel.privacy_level = privacy_level

        return self._save_vessel(vessel)

    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self.conn.close()

    @staticmethod
    def _tier_to_dict(tier: TierConfig) -> Dict[str, Any]:
        """Convert TierConfig to dictionary for storage."""
        return {
            "tier0_enabled": tier.tier0_enabled,
            "tier0_model": getattr(tier, 'tier0_model', 'Llama-3.2-1B'),
            "tier0_device": getattr(tier, 'tier0_device', 'cpu'),
            "tier1_enabled": tier.tier1_enabled,
            "tier1_host": getattr(tier, 'tier1_host', 'localhost'),
            "tier1_port": getattr(tier, 'tier1_port', 8080),
            "tier1_model": getattr(tier, 'tier1_model', 'Llama-3.1-70B'),
            "tier2_enabled": tier.tier2_enabled,
            "tier2_allowed_models": getattr(tier, 'tier2_allowed_models', []),
            "tier2_sanitize_data": getattr(tier, 'tier2_sanitize_data', True),
            "tier0_endpoints": getattr(tier, 'tier0_endpoints', {}),
            "tier1_endpoints": getattr(tier, 'tier1_endpoints', {}),
            "tier2_endpoints": getattr(tier, 'tier2_endpoints', {}),
        }

    @staticmethod
    def _tier_from_dict(data: Dict[str, Any]) -> TierConfig:
        """Create TierConfig from dictionary."""
        return TierConfig(
            tier0_enabled=data.get("tier0_enabled", True),
            tier0_model=data.get("tier0_model", "Llama-3.2-1B"),
            tier0_device=data.get("tier0_device", "cpu"),
            tier0_endpoints=data.get("tier0_endpoints", {}),
            tier1_enabled=data.get("tier1_enabled", True),
            tier1_host=data.get("tier1_host", "localhost"),
            tier1_port=data.get("tier1_port", 8080),
            tier1_model=data.get("tier1_model", "Llama-3.1-70B"),
            tier1_endpoints=data.get("tier1_endpoints", {}),
            tier2_enabled=data.get("tier2_enabled", False),
            tier2_allowed_models=data.get("tier2_allowed_models", []),
            tier2_sanitize_data=data.get("tier2_sanitize_data", True),
            tier2_endpoints=data.get("tier2_endpoints", {}),
        )

    @classmethod
    def load_from_config(cls, config: Dict[str, Any]) -> List[Vessel]:
        """
        Load Vessel definitions from a configuration dictionary.

        Args:
            config: Configuration dictionary with 'vessels' key containing list of vessel configs

        Returns:
            List of Vessel objects created from config
        """
        vessels = []
        vessel_configs = config.get("vessels", [])

        for vc in vessel_configs:
            # Parse privacy level
            privacy_str = vc.get("privacy_level", "private")
            try:
                privacy_level = CommunityPrivacy(privacy_str)
            except ValueError:
                privacy_level = CommunityPrivacy.PRIVATE

            # Parse tier config
            tier_data = vc.get("tier_config", {})
            tier_config = cls._tier_from_dict(tier_data)

            vessel = Vessel(
                vessel_id=vc.get("id", vc.get("vessel_id")),
                name=vc.get("name", ""),
                description=vc.get("description", ""),
                community_ids=vc.get("community_ids", []),
                graph_namespace=vc.get("graph_namespace", ""),
                privacy_level=privacy_level,
                constraint_profile_id=vc.get("constraint_profile_id", "default"),
                servant_project_ids=vc.get("servant_project_ids", []),
                connectors=vc.get("connectors", {}),
                tier_config=tier_config,
            )
            vessels.append(vessel)

        return vessels

    def _row_to_vessel(self, row: Any) -> Vessel:
        """Convert database row to Vessel object."""
        (
            vessel_id, name, description, community_ids, graph_namespace,
            privacy_level_str, constraint_profile_id, servant_project_ids,
            connectors, tier_config, created_at, last_active, status
        ) = row

        try:
            privacy_level = CommunityPrivacy(privacy_level_str)
        except ValueError:
            privacy_level = CommunityPrivacy.PRIVATE

        return Vessel(
            vessel_id=vessel_id,
            name=name,
            description=description or "",
            community_ids=json.loads(community_ids or "[]"),
            graph_namespace=graph_namespace,
            privacy_level=privacy_level,
            constraint_profile_id=constraint_profile_id,
            servant_project_ids=json.loads(servant_project_ids or "[]"),
            connectors=json.loads(connectors or "{}"),
            tier_config=self._tier_from_dict(json.loads(tier_config or "{}")),
            created_at=datetime.fromisoformat(created_at) if created_at else datetime.utcnow(),
            last_active=datetime.fromisoformat(last_active) if last_active else datetime.utcnow(),
            status=status or "active"
        )
