"""
FalkorDB Vessel Registry: Manages vessel lifecycle using FalkorDB graph storage.

Replaces SQLite-based registry with graph-native storage that enables:
- Relationship queries between vessels and communities
- Efficient traversal of vessel hierarchies
- Native integration with the knowledge graph

REQUIRES AgentZeroCore - all vessel operations are coordinated through A0.
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from datetime import datetime

from .vessel import TierConfig, Vessel, PrivacyLevel
from vessels.knowledge.schema import CommunityPrivacy

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class FalkorDBVesselRegistry:
    """
    Persist and retrieve Vessel definitions using FalkorDB graph database.

    REQUIRES AgentZeroCore - all vessel operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        falkor_client=None,
        graph_name: str = "vessels_registry"
    ):
        """
        Initialize FalkorDB VesselRegistry.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            falkor_client: FalkorDBClient instance (will create if None)
            graph_name: Name of the graph for vessel storage
        """
        if agent_zero is None:
            raise ValueError("FalkorDBVesselRegistry requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.graph_name = graph_name

        if falkor_client is None:
            from vessels.database.falkordb_client import get_falkordb_client
            self.falkor_client = get_falkordb_client()
        else:
            self.falkor_client = falkor_client

        self.graph = self.falkor_client.get_graph(graph_name)
        self._ensure_indexes()

        # Register with A0
        self.agent_zero.falkordb_registry = self
        logger.info(f"FalkorDB VesselRegistry initialized with A0 (graph: '{graph_name}')")

    def _ensure_indexes(self):
        """Create indexes for efficient vessel queries."""
        indexes = [
            "CREATE INDEX FOR (v:Vessel) ON (v.vessel_id)",
            "CREATE INDEX FOR (v:Vessel) ON (v.name)",
            "CREATE INDEX FOR (c:Community) ON (c.community_id)",
            "CREATE INDEX FOR (p:Project) ON (p.project_id)"
        ]

        for query in indexes:
            try:
                self.graph.query(query)
            except Exception:
                # Index may already exist
                pass

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
            vessel = vessel_or_name
        else:
            if community_id is None:
                raise ValueError("community_id is required when creating vessel by name")

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
        Persist a vessel to FalkorDB.

        Args:
            vessel: Vessel to save

        Returns:
            The saved Vessel
        """
        vessel_props = {
            "vessel_id": vessel.vessel_id,
            "name": vessel.name,
            "description": vessel.description,
            "graph_namespace": vessel.graph_namespace,
            "privacy_level": vessel.privacy_level.value,
            "constraint_profile_id": vessel.constraint_profile_id,
            "servant_project_ids": json.dumps(vessel.servant_project_ids),
            "connectors": json.dumps(vessel.connectors),
            "tier_config": json.dumps(self._tier_to_dict(vessel.tier_config)),
            "created_at": vessel.created_at.isoformat(),
            "last_active": vessel.last_active.isoformat(),
            "status": vessel.status
        }

        try:
            # Upsert vessel node
            query = """
            MERGE (v:Vessel {vessel_id: $vessel_id})
            SET v.name = $name,
                v.description = $description,
                v.graph_namespace = $graph_namespace,
                v.privacy_level = $privacy_level,
                v.constraint_profile_id = $constraint_profile_id,
                v.servant_project_ids = $servant_project_ids,
                v.connectors = $connectors,
                v.tier_config = $tier_config,
                v.created_at = $created_at,
                v.last_active = $last_active,
                v.status = $status
            RETURN v
            """
            self.graph.query(query, vessel_props)

            # Create community relationships
            for community_id in vessel.community_ids:
                community_query = """
                MATCH (v:Vessel {vessel_id: $vessel_id})
                MERGE (c:Community {community_id: $community_id})
                MERGE (v)-[:BELONGS_TO]->(c)
                """
                self.graph.query(community_query, {
                    "vessel_id": vessel.vessel_id,
                    "community_id": community_id
                })

            logger.debug(f"Saved vessel {vessel.vessel_id} to FalkorDB")
            return vessel

        except Exception as e:
            logger.error(f"Failed to save vessel {vessel.vessel_id}: {e}")
            raise

    def get_vessel(self, vessel_id: str) -> Optional[Vessel]:
        """
        Retrieve a vessel by ID.

        Args:
            vessel_id: The vessel ID to look up

        Returns:
            Vessel if found, None otherwise
        """
        try:
            query = """
            MATCH (v:Vessel {vessel_id: $vessel_id})
            OPTIONAL MATCH (v)-[:BELONGS_TO]->(c:Community)
            WITH v, collect(c.community_id) as community_ids
            RETURN v, community_ids
            """
            result = self.graph.query(query, {"vessel_id": vessel_id})

            if not result or not result.result_set:
                return None

            row = result.result_set[0]
            return self._row_to_vessel(row[0], row[1])

        except Exception as e:
            logger.error(f"Failed to get vessel {vessel_id}: {e}")
            return None

    def list_vessels(self) -> List[Vessel]:
        """
        List all active vessels.

        Returns:
            List of all Vessel objects
        """
        try:
            query = """
            MATCH (v:Vessel)
            WHERE v.status <> 'archived'
            OPTIONAL MATCH (v)-[:BELONGS_TO]->(c:Community)
            WITH v, collect(c.community_id) as community_ids
            RETURN v, community_ids
            ORDER BY v.vessel_id
            """
            result = self.graph.query(query)

            if not result or not result.result_set:
                return []

            return [self._row_to_vessel(row[0], row[1]) for row in result.result_set]

        except Exception as e:
            logger.error(f"Failed to list vessels: {e}")
            return []

    def get_vessels_by_community(self, community_id: str) -> List[Vessel]:
        """
        Get all vessels associated with a community.

        Args:
            community_id: The community ID to filter by

        Returns:
            List of Vessels belonging to the community
        """
        try:
            query = """
            MATCH (v:Vessel)-[:BELONGS_TO]->(c:Community {community_id: $community_id})
            WHERE v.status <> 'archived'
            OPTIONAL MATCH (v)-[:BELONGS_TO]->(c2:Community)
            WITH v, collect(c2.community_id) as community_ids
            RETURN v, community_ids
            """
            result = self.graph.query(query, {"community_id": community_id})

            if not result or not result.result_set:
                return []

            return [self._row_to_vessel(row[0], row[1]) for row in result.result_set]

        except Exception as e:
            logger.error(f"Failed to get vessels for community {community_id}: {e}")
            return []

    def delete_vessel(self, vessel_id: str) -> bool:
        """
        Delete (archive) a vessel.

        Args:
            vessel_id: The vessel ID to delete

        Returns:
            True if vessel was deleted, False if not found
        """
        try:
            # First check if vessel exists
            vessel = self.get_vessel(vessel_id)
            if not vessel:
                return False

            # Delete vessel and its relationships
            query = """
            MATCH (v:Vessel {vessel_id: $vessel_id})
            DETACH DELETE v
            """
            self.graph.query(query, {"vessel_id": vessel_id})
            logger.info(f"Deleted vessel {vessel_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete vessel {vessel_id}: {e}")
            return False

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

        # Also create explicit relationship for graph queries
        try:
            query = """
            MATCH (v:Vessel {vessel_id: $vessel_id})
            MERGE (p:Project {project_id: $project_id})
            MERGE (v)-[:HAS_PROJECT]->(p)
            """
            self.graph.query(query, {
                "vessel_id": vessel_id,
                "project_id": project_id
            })
        except Exception as e:
            logger.warning(f"Failed to create project relationship: {e}")

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

        # Also remove explicit relationship
        try:
            query = """
            MATCH (v:Vessel {vessel_id: $vessel_id})-[r:HAS_PROJECT]->(p:Project {project_id: $project_id})
            DELETE r
            """
            self.graph.query(query, {
                "vessel_id": vessel_id,
                "project_id": project_id
            })
        except Exception as e:
            logger.warning(f"Failed to remove project relationship: {e}")

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
            privacy_str = vc.get("privacy_level", "private")
            try:
                privacy_level = CommunityPrivacy(privacy_str)
            except ValueError:
                privacy_level = CommunityPrivacy.PRIVATE

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

    def _row_to_vessel(self, node_props: Any, community_ids: List[str]) -> Vessel:
        """Convert FalkorDB node to Vessel object."""
        # Handle both dict-like and object-like access
        if hasattr(node_props, 'properties'):
            props = node_props.properties
        else:
            props = node_props

        try:
            privacy_level = CommunityPrivacy(props.get("privacy_level", "private"))
        except ValueError:
            privacy_level = CommunityPrivacy.PRIVATE

        tier_config_data = props.get("tier_config", "{}")
        if isinstance(tier_config_data, str):
            tier_config_data = json.loads(tier_config_data)

        servant_project_ids = props.get("servant_project_ids", "[]")
        if isinstance(servant_project_ids, str):
            servant_project_ids = json.loads(servant_project_ids)

        connectors = props.get("connectors", "{}")
        if isinstance(connectors, str):
            connectors = json.loads(connectors)

        created_at = props.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not created_at:
            created_at = datetime.utcnow()

        last_active = props.get("last_active")
        if isinstance(last_active, str):
            last_active = datetime.fromisoformat(last_active)
        elif not last_active:
            last_active = datetime.utcnow()

        return Vessel(
            vessel_id=props.get("vessel_id"),
            name=props.get("name", ""),
            description=props.get("description", ""),
            community_ids=community_ids or [],
            graph_namespace=props.get("graph_namespace", ""),
            privacy_level=privacy_level,
            constraint_profile_id=props.get("constraint_profile_id", "servant_default"),
            servant_project_ids=servant_project_ids,
            connectors=connectors,
            tier_config=self._tier_from_dict(tier_config_data),
            created_at=created_at,
            last_active=last_active,
            status=props.get("status", "active")
        )

    def close(self) -> None:
        """Close the FalkorDB connection (no-op, client manages connection)."""
        pass
