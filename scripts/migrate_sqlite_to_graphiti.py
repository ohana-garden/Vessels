#!/usr/bin/env python3
"""
Migrate SQLite data to Graphiti/FalkorDB

Reads existing SQLite databases and migrates:
- Community memories
- Phase space trajectories
- Security events
- Attractors

Usage:
    python scripts/migrate_sqlite_to_graphiti.py \
        --memory-db community_memory.db \
        --trajectory-db vessels_trajectories.db \
        --community-id lower_puna_elders \
        --dry-run
"""

import argparse
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SQLiteToGraphitiMigrator:
    """Migrates data from SQLite to Graphiti/FalkorDB"""

    def __init__(
        self,
        memory_db_path: str,
        trajectory_db_path: str,
        community_id: str,
        graphiti_host: str = "localhost",
        graphiti_port: int = 6379,
        dry_run: bool = False
    ):
        self.memory_db_path = memory_db_path
        self.trajectory_db_path = trajectory_db_path
        self.community_id = community_id
        self.graphiti_host = graphiti_host
        self.graphiti_port = graphiti_port
        self.dry_run = dry_run

        self.stats = {
            "memories_migrated": 0,
            "states_migrated": 0,
            "transitions_migrated": 0,
            "events_migrated": 0,
            "attractors_migrated": 0,
            "errors": []
        }

    def migrate_all(self):
        """Run complete migration"""
        logger.info("=" * 60)
        logger.info("SQLite to Graphiti Migration")
        logger.info("=" * 60)
        logger.info(f"Community ID: {self.community_id}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("")

        # Initialize Graphiti client
        if not self.dry_run:
            self._init_graphiti()

        # Migrate memories
        if Path(self.memory_db_path).exists():
            logger.info("Migrating memories...")
            self._migrate_memories()
        else:
            logger.warning(f"Memory DB not found: {self.memory_db_path}")

        # Migrate trajectories
        if Path(self.trajectory_db_path).exists():
            logger.info("Migrating trajectories...")
            self._migrate_trajectories()
        else:
            logger.warning(f"Trajectory DB not found: {self.trajectory_db_path}")

        # Print summary
        self._print_summary()

    def _init_graphiti(self):
        """Initialize Graphiti client"""
        try:
            from vessels.knowledge.graphiti_client import VesselsGraphitiClient

            self.graphiti_client = VesselsGraphitiClient(
                community_id=self.community_id,
                host=self.graphiti_host,
                port=self.graphiti_port
            )

            # Test connection
            if not self.graphiti_client.health_check():
                raise RuntimeError("Graphiti health check failed")

            logger.info(f"✓ Connected to Graphiti at {self.graphiti_host}:{self.graphiti_port}")

        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            raise

    def _migrate_memories(self):
        """Migrate community memories"""
        from community_memory import MemoryEntry, MemoryType

        try:
            conn = sqlite3.connect(self.memory_db_path)
            cursor = conn.cursor()

            # Read all memories
            cursor.execute("SELECT * FROM memories")
            rows = cursor.fetchall()

            logger.info(f"Found {len(rows)} memories to migrate")

            for row in rows:
                try:
                    # Parse memory entry
                    memory_entry = MemoryEntry(
                        id=row[0],
                        type=MemoryType(row[1]),
                        content=json.loads(row[2]),
                        agent_id=row[3],
                        timestamp=datetime.fromisoformat(row[4]),
                        tags=json.loads(row[5]) if row[5] else [],
                        relationships=json.loads(row[6]) if row[6] else [],
                        confidence=float(row[7]) if row[7] else 1.0,
                        access_count=int(row[8]) if row[8] else 0
                    )

                    if not self.dry_run:
                        # Store in Graphiti
                        from vessels.knowledge.memory_backend import GraphitiMemoryBackend
                        backend = GraphitiMemoryBackend(self.graphiti_client)
                        backend.store_memory(memory_entry)

                    self.stats["memories_migrated"] += 1

                    if self.stats["memories_migrated"] % 100 == 0:
                        logger.info(f"  Migrated {self.stats['memories_migrated']} memories...")

                except Exception as e:
                    self.stats["errors"].append(f"Memory {row[0]}: {e}")
                    logger.warning(f"Failed to migrate memory {row[0]}: {e}")

            conn.close()
            logger.info(f"✓ Migrated {self.stats['memories_migrated']} memories")

        except Exception as e:
            logger.error(f"Error migrating memories: {e}")
            self.stats["errors"].append(f"Memory migration: {e}")

    def _migrate_trajectories(self):
        """Migrate phase space trajectories"""
        try:
            conn = sqlite3.connect(self.trajectory_db_path)

            # Migrate states
            self._migrate_states(conn)

            # Migrate transitions
            self._migrate_transitions(conn)

            # Migrate security events
            self._migrate_security_events(conn)

            # Migrate attractors
            self._migrate_attractors(conn)

            conn.close()

        except Exception as e:
            logger.error(f"Error migrating trajectories: {e}")
            self.stats["errors"].append(f"Trajectory migration: {e}")

    def _migrate_states(self, conn: sqlite3.Connection):
        """Migrate phase space states"""
        from vessels.measurement.state import PhaseSpaceState

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM states ORDER BY timestamp")
        rows = cursor.fetchall()

        logger.info(f"Found {len(rows)} states to migrate")

        for row in rows:
            try:
                # Parse state
                state_dict = {
                    'agent_id': row[1],
                    'timestamp': row[2],
                    'operational': json.loads(row[3]),
                    'virtue': json.loads(row[4]),
                    'confidence': json.loads(row[5]) if row[5] else {}
                }

                state = PhaseSpaceState.from_dict(state_dict)

                if not self.dry_run:
                    # Store in Graphiti
                    from vessels.phase_space.graphiti_tracker import GraphitiPhaseSpaceTracker
                    tracker = GraphitiPhaseSpaceTracker(self.graphiti_client)
                    tracker.store_state(state)

                self.stats["states_migrated"] += 1

                if self.stats["states_migrated"] % 100 == 0:
                    logger.info(f"  Migrated {self.stats['states_migrated']} states...")

            except Exception as e:
                self.stats["errors"].append(f"State {row[0]}: {e}")
                logger.warning(f"Failed to migrate state {row[0]}: {e}")

        logger.info(f"✓ Migrated {self.stats['states_migrated']} states")

    def _migrate_transitions(self, conn: sqlite3.Connection):
        """Migrate state transitions"""
        from vessels.gating.events import StateTransition

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transitions")
        rows = cursor.fetchall()

        logger.info(f"Found {len(rows)} transitions to migrate")

        for row in rows:
            try:
                transition = StateTransition(
                    agent_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    from_state=json.loads(row[3]) if row[3] else None,
                    to_state=json.loads(row[4]),
                    action_hash=row[5],
                    gating_result=row[6],
                    action_metadata=json.loads(row[7]) if row[7] else {}
                )

                if not self.dry_run:
                    from vessels.phase_space.graphiti_tracker import GraphitiPhaseSpaceTracker
                    tracker = GraphitiPhaseSpaceTracker(self.graphiti_client)
                    tracker.store_transition(transition)

                self.stats["transitions_migrated"] += 1

            except Exception as e:
                self.stats["errors"].append(f"Transition {row[0]}: {e}")
                logger.warning(f"Failed to migrate transition {row[0]}: {e}")

        logger.info(f"✓ Migrated {self.stats['transitions_migrated']} transitions")

    def _migrate_security_events(self, conn: sqlite3.Connection):
        """Migrate security events"""
        from vessels.gating.events import SecurityEvent

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM security_events")
        rows = cursor.fetchall()

        logger.info(f"Found {len(rows)} security events to migrate")

        for row in rows:
            try:
                event = SecurityEvent(
                    agent_id=row[1],
                    timestamp=datetime.fromisoformat(row[2]),
                    violations=json.loads(row[3]),
                    original_virtue_state=json.loads(row[4]),
                    corrected_virtue_state=json.loads(row[5]) if row[5] else None,
                    residual_violations=json.loads(row[6]) if row[6] else [],
                    blocked=bool(row[7]),
                    action_hash=row[8],
                    operational_state_snapshot=json.loads(row[9]) if row[9] else None,
                    event_type=row[10],
                    metadata=json.loads(row[11]) if row[11] else {}
                )

                if not self.dry_run:
                    from vessels.phase_space.graphiti_tracker import GraphitiPhaseSpaceTracker
                    tracker = GraphitiPhaseSpaceTracker(self.graphiti_client)
                    tracker.store_security_event(event)

                self.stats["events_migrated"] += 1

            except Exception as e:
                self.stats["errors"].append(f"Event {row[0]}: {e}")
                logger.warning(f"Failed to migrate event {row[0]}: {e}")

        logger.info(f"✓ Migrated {self.stats['events_migrated']} security events")

    def _migrate_attractors(self, conn: sqlite3.Connection):
        """Migrate discovered attractors"""
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attractors")
        rows = cursor.fetchall()

        logger.info(f"Found {len(rows)} attractors to migrate")

        for row in rows:
            try:
                center = json.loads(row[1])
                radius = float(row[2])
                classification = row[3]
                agent_count = int(row[4])
                outcomes = json.loads(row[6]) if row[6] else None
                metadata = json.loads(row[7]) if len(row) > 7 and row[7] else None

                if not self.dry_run:
                    from vessels.phase_space.graphiti_tracker import GraphitiPhaseSpaceTracker
                    tracker = GraphitiPhaseSpaceTracker(self.graphiti_client)
                    tracker.store_attractor(
                        center, radius, classification, agent_count, outcomes, metadata
                    )

                self.stats["attractors_migrated"] += 1

            except Exception as e:
                self.stats["errors"].append(f"Attractor {row[0]}: {e}")
                logger.warning(f"Failed to migrate attractor {row[0]}: {e}")

        logger.info(f"✓ Migrated {self.stats['attractors_migrated']} attractors")

    def _print_summary(self):
        """Print migration summary"""
        logger.info("")
        logger.info("=" * 60)
        logger.info("Migration Summary")
        logger.info("=" * 60)
        logger.info(f"Memories:        {self.stats['memories_migrated']}")
        logger.info(f"States:          {self.stats['states_migrated']}")
        logger.info(f"Transitions:     {self.stats['transitions_migrated']}")
        logger.info(f"Security Events: {self.stats['events_migrated']}")
        logger.info(f"Attractors:      {self.stats['attractors_migrated']}")
        logger.info(f"Errors:          {len(self.stats['errors'])}")

        if self.stats['errors']:
            logger.warning("")
            logger.warning("Errors encountered:")
            for error in self.stats['errors'][:10]:  # Show first 10
                logger.warning(f"  - {error}")
            if len(self.stats['errors']) > 10:
                logger.warning(f"  ... and {len(self.stats['errors']) - 10} more")

        logger.info("=" * 60)

        if self.dry_run:
            logger.info("DRY RUN - No data was actually migrated")
            logger.info("Remove --dry-run to perform actual migration")


def main():
    parser = argparse.ArgumentParser(
        description="Migrate SQLite data to Graphiti/FalkorDB"
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze data without migrating"
    )

    args = parser.parse_args()

    migrator = SQLiteToGraphitiMigrator(
        memory_db_path=args.memory_db,
        trajectory_db_path=args.trajectory_db,
        community_id=args.community_id,
        graphiti_host=args.host,
        graphiti_port=args.port,
        dry_run=args.dry_run
    )

    try:
        migrator.migrate_all()
    except KeyboardInterrupt:
        logger.info("\nMigration interrupted by user")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()
