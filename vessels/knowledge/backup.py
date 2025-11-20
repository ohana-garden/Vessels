"""
Vessels Graph Backup and Restore

Provides dual persistence strategy:
1. Redis RDB (automatic, fast recovery)
2. JSON exports (human-readable, portable, disaster recovery)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class GraphBackupMetadata:
    """Metadata for a graph backup"""
    community_id: str
    export_timestamp: str
    node_count: int
    edge_count: int
    backup_version: str = "1.0"


class GraphBackupManager:
    """
    Manages backup and restore of community knowledge graphs

    Exports graphs to JSON format for:
    - Human readability
    - Version control
    - Migration to other graph databases
    - Disaster recovery
    """

    def __init__(self, backup_dir: Path = Path("backups/graphs")):
        """
        Initialize backup manager

        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def export_community_graph(
        self,
        graphiti_client,
        community_id: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Export a community graph to JSON

        Args:
            graphiti_client: ShorghiGraphitiClient instance
            community_id: Community ID to export
            output_dir: Optional output directory (defaults to backup_dir/YYYY-MM-DD/)

        Returns:
            Path to exported JSON file
        """
        # Create timestamped backup directory
        if output_dir is None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d")
            output_dir = self.backup_dir / timestamp

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Export nodes
            nodes_query = "MATCH (n) RETURN n"
            nodes_results = graphiti_client.query(nodes_query)
            nodes_data = [self._node_to_dict(node) for node in nodes_results]

            # Export relationships
            rels_query = "MATCH ()-[r]->() RETURN r"
            rels_results = graphiti_client.query(rels_query)
            rels_data = [self._rel_to_dict(rel) for rel in rels_results]

            # Create metadata
            metadata = GraphBackupMetadata(
                community_id=community_id,
                export_timestamp=datetime.utcnow().isoformat(),
                node_count=len(nodes_data),
                edge_count=len(rels_data)
            )

            # Create backup data structure
            backup_data = {
                "metadata": asdict(metadata),
                "nodes": nodes_data,
                "relationships": rels_data
            }

            # Write JSON file
            json_file = output_dir / f"{community_id}_graph.json"
            with open(json_file, "w") as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"Exported {metadata.node_count} nodes and {metadata.edge_count} relationships to {json_file}")

            # Also generate Cypher restore script
            self._generate_cypher_script(backup_data, output_dir / f"{community_id}_restore.cypher")

            return json_file

        except Exception as e:
            logger.error(f"Error exporting graph: {e}")
            raise

    def export_all_graphs(self, communities: List[str]) -> Path:
        """
        Export all community graphs

        Args:
            communities: List of community IDs to export

        Returns:
            Path to backup directory
        """
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = self.backup_dir / timestamp

        for community_id in communities:
            try:
                # Import here to avoid circular dependency
                from .graphiti_client import VesselsGraphitiClient

                client = VesselsGraphitiClient(community_id)
                self.export_community_graph(client, community_id, output_dir)

            except Exception as e:
                logger.error(f"Error exporting {community_id}: {e}")

        logger.info(f"Exported {len(communities)} community graphs to {output_dir}")
        return output_dir

    def restore_from_backup(self, backup_file: Path, graphiti_client) -> bool:
        """
        Restore a graph from JSON backup

        Args:
            backup_file: Path to JSON backup file
            graphiti_client: ShorghiGraphitiClient instance

        Returns:
            True if successful
        """
        try:
            with open(backup_file, "r") as f:
                backup_data = json.load(f)

            metadata = backup_data["metadata"]
            nodes = backup_data["nodes"]
            relationships = backup_data["relationships"]

            logger.info(f"Restoring graph: {metadata['community_id']}")
            logger.info(f"  Nodes: {metadata['node_count']}")
            logger.info(f"  Relationships: {metadata['edge_count']}")

            # Restore nodes
            for node_data in nodes:
                try:
                    graphiti_client.create_node(
                        node_type=node_data["type"],
                        node_id=node_data["id"],
                        properties=node_data["properties"]
                    )
                except Exception as e:
                    logger.error(f"Error restoring node {node_data.get('id')}: {e}")

            # Restore relationships
            for rel_data in relationships:
                try:
                    graphiti_client.create_relationship(
                        source_id=rel_data["source"],
                        rel_type=rel_data["type"],
                        target_id=rel_data["target"],
                        properties=rel_data.get("properties", {})
                    )
                except Exception as e:
                    logger.error(f"Error restoring relationship: {e}")

            logger.info(f"Successfully restored graph from {backup_file}")
            return True

        except Exception as e:
            logger.error(f"Error restoring graph: {e}")
            return False

    def _node_to_dict(self, node) -> Dict[str, Any]:
        """Convert node to dictionary"""
        # This will need to be adapted based on actual Graphiti node structure
        if isinstance(node, dict):
            return node

        # For now, assume node has id, type, and properties
        try:
            return {
                "id": getattr(node, "id", None) or node.get("id"),
                "type": getattr(node, "type", None) or node.get("type"),
                "properties": getattr(node, "properties", None) or node.get("properties", {})
            }
        except Exception as e:
            logger.error(f"Error converting node to dict: {e}")
            return {}

    def _rel_to_dict(self, rel) -> Dict[str, Any]:
        """Convert relationship to dictionary"""
        if isinstance(rel, dict):
            return rel

        try:
            return {
                "source": getattr(rel, "source", None) or rel.get("source"),
                "type": getattr(rel, "type", None) or rel.get("type"),
                "target": getattr(rel, "target", None) or rel.get("target"),
                "properties": getattr(rel, "properties", None) or rel.get("properties", {})
            }
        except Exception as e:
            logger.error(f"Error converting relationship to dict: {e}")
            return {}

    def _generate_cypher_script(self, backup_data: Dict, output_file: Path):
        """Generate Cypher script for manual restore"""
        try:
            with open(output_file, "w") as f:
                f.write("// Vessels Graph Restore Script\n")
                f.write(f"// Generated: {datetime.utcnow().isoformat()}\n")
                f.write(f"// Community: {backup_data['metadata']['community_id']}\n\n")

                # Create nodes
                f.write("// Create Nodes\n")
                for node in backup_data["nodes"]:
                    props_str = self._properties_to_cypher(node["properties"])
                    f.write(f"CREATE (n:{node['type']} {{id: '{node['id']}', {props_str}}})\n")

                f.write("\n// Create Relationships\n")
                for rel in backup_data["relationships"]:
                    props_str = self._properties_to_cypher(rel.get("properties", {}))
                    props_clause = f" {{{props_str}}}" if props_str else ""
                    f.write(
                        f"MATCH (a {{id: '{rel['source']}'}}), (b {{id: '{rel['target']}'}})\n"
                        f"CREATE (a)-[:{rel['type']}{props_clause}]->(b)\n"
                    )

            logger.info(f"Generated Cypher script: {output_file}")

        except Exception as e:
            logger.error(f"Error generating Cypher script: {e}")

    def _properties_to_cypher(self, properties: Dict[str, Any]) -> str:
        """Convert properties dict to Cypher format"""
        if not properties:
            return ""

        prop_strings = []
        for key, value in properties.items():
            if isinstance(value, str):
                # Escape single quotes
                value_escaped = value.replace("'", "\\'")
                prop_strings.append(f"{key}: '{value_escaped}'")
            elif isinstance(value, (int, float, bool)):
                prop_strings.append(f"{key}: {value}")
            else:
                # Convert to JSON string
                value_json = json.dumps(value).replace("'", "\\'")
                prop_strings.append(f"{key}: '{value_json}'")

        return ", ".join(prop_strings)

    def list_backups(self, community_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups

        Args:
            community_id: Optional filter by community

        Returns:
            List of backup metadata
        """
        backups = []

        # Scan backup directory
        for date_dir in sorted(self.backup_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            for backup_file in date_dir.glob("*_graph.json"):
                try:
                    with open(backup_file, "r") as f:
                        data = json.load(f)
                        metadata = data["metadata"]

                        if community_id is None or metadata["community_id"] == community_id:
                            backups.append({
                                "file": str(backup_file),
                                "community_id": metadata["community_id"],
                                "timestamp": metadata["export_timestamp"],
                                "node_count": metadata["node_count"],
                                "edge_count": metadata["edge_count"]
                            })

                except Exception as e:
                    logger.error(f"Error reading backup {backup_file}: {e}")

        return backups

    def prune_old_backups(self, keep_days: int = 30):
        """
        Delete backups older than specified days

        Args:
            keep_days: Number of days to keep backups
        """
        cutoff = datetime.utcnow().timestamp() - (keep_days * 86400)
        deleted_count = 0

        for date_dir in self.backup_dir.iterdir():
            if not date_dir.is_dir():
                continue

            # Check directory timestamp
            if date_dir.stat().st_mtime < cutoff:
                try:
                    # Delete all files in directory
                    for file in date_dir.iterdir():
                        file.unlink()
                    date_dir.rmdir()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {date_dir}")

                except Exception as e:
                    logger.error(f"Error deleting backup {date_dir}: {e}")

        logger.info(f"Pruned {deleted_count} old backup directories (kept last {keep_days} days)")
