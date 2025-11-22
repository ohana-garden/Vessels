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
