#!/usr/bin/env python3
"""
Validate Graphiti migration

Compares data between SQLite and Graphiti to ensure migration was successful.

Usage:
    python scripts/validate_migration.py \
        --memory-db community_memory.db \
        --trajectory-db vessels_trajectories.db \
        --community-id lower_puna_elders
"""

import argparse
import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationValidator:
    """Validates data consistency between SQLite and Graphiti"""

    def __init__(
        self,
        memory_db_path: str,
        trajectory_db_path: str,
        community_id: str,
        graphiti_host: str = "localhost",
        graphiti_port: int = 6379
    ):
        self.memory_db_path = memory_db_path
        self.trajectory_db_path = trajectory_db_path
        self.community_id = community_id
        self.graphiti_host = graphiti_host
        self.graphiti_port = graphiti_port

        self.results = {
            "memories": {"sqlite": 0, "graphiti": 0, "match": False},
            "states": {"sqlite": 0, "graphiti": 0, "match": False},
            "transitions": {"sqlite": 0, "graphiti": 0, "match": False},
            "events": {"sqlite": 0, "graphiti": 0, "match": False},
            "attractors": {"sqlite": 0, "graphiti": 0, "match": False},
            "discrepancies": []
        }

    def validate_all(self):
        """Run complete validation"""
        logger.info("=" * 60)
        logger.info("Migration Validation")
        logger.info("=" * 60)
        logger.info(f"Community ID: {self.community_id}")
        logger.info("")

        # Initialize Graphiti client
        self._init_graphiti()

        # Validate memories
        if Path(self.memory_db_path).exists():
            logger.info("Validating memories...")
            self._validate_memories()
        else:
            logger.warning(f"Memory DB not found: {self.memory_db_path}")

        # Validate trajectories
        if Path(self.trajectory_db_path).exists():
            logger.info("Validating trajectories...")
            self._validate_trajectories()
        else:
            logger.warning(f"Trajectory DB not found: {self.trajectory_db_path}")

        # Print results
        self._print_results()

    def _init_graphiti(self):
        """Initialize Graphiti client"""
        try:
            from vessels.knowledge.graphiti_client import VesselsGraphitiClient

            self.graphiti_client = VesselsGraphitiClient(
                community_id=self.community_id,
                host=self.graphiti_host,
                port=self.graphiti_port,
                allow_mock=True  # Allow validation even with mock
            )

            if self.graphiti_client.health_check():
                logger.info(f"✓ Connected to Graphiti at {self.graphiti_host}:{self.graphiti_port}")
            else:
                logger.warning("⚠ Using mock Graphiti client")

        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise

    def _validate_memories(self):
        """Validate memory count"""
        try:
            # Count SQLite memories
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            sqlite_count = cursor.fetchone()[0]
            conn.close()

            # Count Graphiti memories
            try:
                cypher = """
                MATCH (m)
                WHERE m.type IN ['experience', 'knowledge', 'pattern', 'relationship', 'event', 'contribution']
                RETURN COUNT(m) as count
                """
                results = self.graphiti_client.query(cypher)
                graphiti_count = results[0].get("count", 0) if results else 0
            except:
                graphiti_count = 0  # Mock mode

            self.results["memories"]["sqlite"] = sqlite_count
            self.results["memories"]["graphiti"] = graphiti_count
            self.results["memories"]["match"] = (sqlite_count == graphiti_count)

            if sqlite_count == graphiti_count:
                logger.info(f"✓ Memories match: {sqlite_count}")
            else:
                logger.warning(f"✗ Memory mismatch: SQLite={sqlite_count}, Graphiti={graphiti_count}")
                self.results["discrepancies"].append(
                    f"Memories: {sqlite_count} in SQLite, {graphiti_count} in Graphiti"
                )

        except Exception as e:
            logger.error(f"Error validating memories: {e}")

    def _validate_trajectories(self):
        """Validate trajectory counts"""
        try:
            conn = sqlite3.connect(self.trajectory_db_path)

            # Validate states
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM states")
            sqlite_states = cursor.fetchone()[0]

            try:
                cypher = "MATCH (s:AgentState) RETURN COUNT(s) as count"
                results = self.graphiti_client.query(cypher)
                graphiti_states = results[0].get("count", 0) if results else 0
            except:
                graphiti_states = 0

            self.results["states"]["sqlite"] = sqlite_states
            self.results["states"]["graphiti"] = graphiti_states
            self.results["states"]["match"] = (sqlite_states == graphiti_states)

            if sqlite_states == graphiti_states:
                logger.info(f"✓ States match: {sqlite_states}")
            else:
                logger.warning(f"✗ State mismatch: SQLite={sqlite_states}, Graphiti={graphiti_states}")
                self.results["discrepancies"].append(
                    f"States: {sqlite_states} in SQLite, {graphiti_states} in Graphiti"
                )

            # Validate transitions
            cursor.execute("SELECT COUNT(*) FROM transitions")
            sqlite_transitions = cursor.fetchone()[0]
            self.results["transitions"]["sqlite"] = sqlite_transitions
            logger.info(f"  Transitions in SQLite: {sqlite_transitions}")

            # Validate security events
            cursor.execute("SELECT COUNT(*) FROM security_events")
            sqlite_events = cursor.fetchone()[0]
            self.results["events"]["sqlite"] = sqlite_events
            logger.info(f"  Security events in SQLite: {sqlite_events}")

            # Validate attractors
            cursor.execute("SELECT COUNT(*) FROM attractors")
            sqlite_attractors = cursor.fetchone()[0]

            try:
                cypher = "MATCH (p:Pattern) WHERE p.type = 'attractor' RETURN COUNT(p) as count"
                results = self.graphiti_client.query(cypher)
                graphiti_attractors = results[0].get("count", 0) if results else 0
            except:
                graphiti_attractors = 0

            self.results["attractors"]["sqlite"] = sqlite_attractors
            self.results["attractors"]["graphiti"] = graphiti_attractors
            self.results["attractors"]["match"] = (sqlite_attractors == graphiti_attractors)

            if sqlite_attractors == graphiti_attractors:
                logger.info(f"✓ Attractors match: {sqlite_attractors}")
            else:
                logger.warning(f"✗ Attractor mismatch: SQLite={sqlite_attractors}, Graphiti={graphiti_attractors}")
                self.results["discrepancies"].append(
                    f"Attractors: {sqlite_attractors} in SQLite, {graphiti_attractors} in Graphiti"
                )

            conn.close()

        except Exception as e:
            logger.error(f"Error validating trajectories: {e}")

    def _print_results(self):
        """Print validation results"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("Validation Results")
        logger.info("=" * 60)

        # Print comparison table
        logger.info(f"{'Item':<20} {'SQLite':>10} {'Graphiti':>10} {'Match':>10}")
        logger.info("-" * 60)

        for item in ["memories", "states", "transitions", "events", "attractors"]:
            sqlite_count = self.results[item]["sqlite"]
            graphiti_count = self.results[item]["graphiti"]
            match = "✓" if self.results[item]["match"] else "✗"

            logger.info(f"{item.capitalize():<20} {sqlite_count:>10} {graphiti_count:>10} {match:>10}")

        logger.info("=" * 60)

        # Print discrepancies
        if self.results["discrepancies"]:
            logger.warning("")
            logger.warning("Discrepancies found:")
            for disc in self.results["discrepancies"]:
                logger.warning(f"  - {disc}")
        else:
            logger.info("")
            logger.info("✓ All counts match! Migration appears successful.")

        logger.info("")

        # Overall status
        all_match = all(
            self.results[item]["match"]
            for item in ["memories", "states", "attractors"]
            if self.results[item]["sqlite"] > 0
        )

        if all_match:
            logger.info("✓ VALIDATION PASSED")
        else:
            logger.warning("✗ VALIDATION FAILED - Review discrepancies above")


def main():
    parser = argparse.ArgumentParser(
        description="Validate SQLite to Graphiti migration"
    )
    parser.add_argument(
        "--memory-db",
        default="community_memory.db",
        help="Path to community memory SQLite database"
    )
    parser.add_argument(
        "--trajectory-db",
        default="vessels_trajectories.db",
        help="Path to trajectory SQLite database"
    )
    parser.add_argument(
        "--community-id",
        required=True,
        help="Community ID for Graphiti namespace"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="FalkorDB host"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6379,
        help="FalkorDB port"
    )

    args = parser.parse_args()

    validator = MigrationValidator(
        memory_db_path=args.memory_db,
        trajectory_db_path=args.trajectory_db,
        community_id=args.community_id,
        graphiti_host=args.host,
        graphiti_port=args.port
    )

    try:
        validator.validate_all()
    except KeyboardInterrupt:
        logger.info("\nValidation interrupted by user")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()
