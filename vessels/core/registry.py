"""
Vessel Registry: Manages vessel lifecycle using SQLite persistence.
"""
import json
import sqlite3
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Ensure these imports match your project structure
from .vessel import TierConfig, Vessel
from vessels.knowledge.schema import CommunityPrivacy

logger = logging.getLogger(__name__)

class VesselRegistry:
    """Persist and retrieve Vessel definitions using SQLite."""

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
                tier_config TEXT,
                created_at TEXT,
                last_active TEXT,
                status TEXT
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

    def set_vessel_privacy(self, vessel_id: str, privacy_level: CommunityPrivacy) -> Optional[Vessel]:
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
