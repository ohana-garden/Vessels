"""
SQLite-based trajectory storage.

Stores:
- States (12D phase space states)
- Transitions (state changes from actions)
- Security events (constraint violations)
- Attractors (discovered behavioral patterns)

REQUIRES AgentZeroCore - all trajectory operations are coordinated through A0.
"""

import sqlite3
import json
import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pathlib import Path

from ..measurement.state import PhaseSpaceState
from ..gating.events import SecurityEvent, StateTransition

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class TrajectoryTracker:
    """
    SQLite-based storage for trajectories and events.

    Schema matches spec section 1.5.
    Supports hybrid mode with Graphiti backend.

    REQUIRES AgentZeroCore - all trajectory operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        db_path: str = "vessels_trajectories.db",
        backend: str = "sqlite",
        graphiti_client=None,
        community_id: Optional[str] = None
    ):
        """
        Initialize tracker with SQLite database and optional Graphiti backend.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            db_path: Path to SQLite database file
            backend: Backend type: "sqlite", "graphiti", or "hybrid"
            graphiti_client: VesselsGraphitiClient instance (for graphiti/hybrid backends)
            community_id: Community ID (for graphiti backend)
        """
        if agent_zero is None:
            raise ValueError("TrajectoryTracker requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.db_path = db_path
        self.backend_type = backend
        self.graphiti_tracker = None

        # Initialize Graphiti backend if requested
        if backend in ["graphiti", "hybrid"]:
            if graphiti_client is None and community_id:
                try:
                    from ..knowledge.graphiti_client import VesselsGraphitiClient
                    graphiti_client = VesselsGraphitiClient(
                        community_id=community_id,
                        allow_mock=True
                    )
                except Exception as e:
                    logger.warning(f"Could not initialize Graphiti client: {e}")
                    if backend == "graphiti":
                        raise
                    self.backend_type = "sqlite"

            if graphiti_client:
                try:
                    from .graphiti_tracker import GraphitiPhaseSpaceTracker
                    self.graphiti_tracker = GraphitiPhaseSpaceTracker(graphiti_client)
                    logger.info(f"Initialized Graphiti trajectory backend (mode: {backend})")
                except Exception as e:
                    logger.warning(f"Could not initialize Graphiti tracker: {e}")
                    if backend == "graphiti":
                        raise
                    self.backend_type = "sqlite"

        # Initialize SQLite for sqlite or hybrid mode
        if self.backend_type in ["sqlite", "hybrid"]:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self._create_schema()
        else:
            self.conn = None

        # Register with A0
        self.agent_zero.trajectory_tracker = self
        logger.info(f"TrajectoryTracker initialized with A0 (backend: {self.backend_type})")

    def _create_schema(self):
        """Create database schema if not exists."""
        cursor = self.conn.cursor()

        # States table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                operational_dims TEXT NOT NULL,
                virtue_dims TEXT NOT NULL,
                confidence TEXT,
                UNIQUE(agent_id, timestamp)
            )
        """)

        # Transitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                from_state TEXT,
                to_state TEXT NOT NULL,
                action_hash TEXT NOT NULL,
                gating_result TEXT NOT NULL,
                action_metadata TEXT
            )
        """)

        # Security events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                violations TEXT NOT NULL,
                original_virtue_state TEXT NOT NULL,
                corrected_virtue_state TEXT,
                residual_violations TEXT,
                blocked INTEGER NOT NULL,
                action_hash TEXT,
                operational_state_snapshot TEXT,
                event_type TEXT NOT NULL,
                metadata TEXT
            )
        """)

        # Attractors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attractors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                center TEXT NOT NULL,
                radius REAL NOT NULL,
                classification TEXT NOT NULL,
                agent_count INTEGER NOT NULL,
                discovered_at TEXT NOT NULL,
                outcomes TEXT,
                metadata TEXT
            )
        """)

        # Backfill metadata column for existing databases
        cursor.execute(
            "PRAGMA table_info(attractors)"
        )
        existing_columns = [row[1] for row in cursor.fetchall()]
        if "metadata" not in existing_columns:
            cursor.execute("ALTER TABLE attractors ADD COLUMN metadata TEXT")

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_states_agent ON states(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_states_timestamp ON states(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transitions_agent ON transitions(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_agent ON security_events(agent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_blocked ON security_events(blocked)")

        self.conn.commit()

    def store_state(self, state: PhaseSpaceState):
        """Store a phase space state."""
        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_tracker:
            try:
                self.graphiti_tracker.store_state(state)
            except Exception as e:
                logger.error(f"Failed to store state in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend
        if self.backend_type in ["sqlite", "hybrid"] and self.conn:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO states
                (agent_id, timestamp, operational_dims, virtue_dims, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                state.agent_id,
                state.timestamp.isoformat(),
                json.dumps(state.operational.to_dict()),
                json.dumps(state.virtue.to_dict()),
                json.dumps(state.confidence) if hasattr(state, 'confidence') else json.dumps({})
            ))

            self.conn.commit()

    def store_transition(self, transition: StateTransition):
        """Store a state transition."""
        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_tracker:
            try:
                self.graphiti_tracker.store_transition(transition)
            except Exception as e:
                logger.error(f"Failed to store transition in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend
        if self.backend_type in ["sqlite", "hybrid"] and self.conn:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO transitions
                (agent_id, timestamp, from_state, to_state, action_hash, gating_result, action_metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                transition.agent_id,
                transition.timestamp.isoformat(),
                json.dumps(transition.from_state) if transition.from_state else None,
                json.dumps(transition.to_state),
                transition.action_hash,
                transition.gating_result,
                json.dumps(transition.action_metadata)
            ))

            self.conn.commit()

    def store_security_event(self, event: SecurityEvent):
        """Store a security event."""
        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_tracker:
            try:
                self.graphiti_tracker.store_security_event(event)
            except Exception as e:
                logger.error(f"Failed to store security event in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend
        if self.backend_type in ["sqlite", "hybrid"] and self.conn:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO security_events
                (agent_id, timestamp, violations, original_virtue_state,
                 corrected_virtue_state, residual_violations, blocked,
                 action_hash, operational_state_snapshot, event_type, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.agent_id,
                event.timestamp.isoformat(),
                json.dumps(event.violations),
                json.dumps(event.original_virtue_state),
                json.dumps(event.corrected_virtue_state) if event.corrected_virtue_state else None,
                json.dumps(event.residual_violations),
                1 if event.blocked else 0,
                event.action_hash,
                json.dumps(event.operational_state_snapshot) if event.operational_state_snapshot else None,
                event.event_type,
                json.dumps(event.metadata)
            ))

            self.conn.commit()

    def store_attractor(
        self,
        center: List[float],
        radius: float,
        classification: str,
        agent_count: int,
        outcomes: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Store a discovered attractor.

        Returns:
            Attractor ID (or 0 if only stored in Graphiti)
        """
        attractor_id = 0

        # Store in Graphiti backend if enabled
        if self.backend_type in ["graphiti", "hybrid"] and self.graphiti_tracker:
            try:
                node_id = self.graphiti_tracker.store_attractor(
                    center, radius, classification, agent_count, outcomes, metadata
                )
                if node_id:
                    # Use hash of node_id as numeric ID for compatibility
                    attractor_id = hash(node_id) % (2**31)
            except Exception as e:
                logger.error(f"Failed to store attractor in Graphiti: {e}")
                if self.backend_type == "graphiti":
                    raise

        # Store in SQLite backend
        if self.backend_type in ["sqlite", "hybrid"] and self.conn:
            cursor = self.conn.cursor()

            cursor.execute("""
                INSERT INTO attractors
                (center, radius, classification, agent_count, discovered_at, outcomes, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                json.dumps(center),
                radius,
                classification,
                agent_count,
                datetime.utcnow().isoformat(),
                json.dumps(outcomes) if outcomes else None,
                json.dumps(metadata) if metadata else None
            ))

            self.conn.commit()
            attractor_id = cursor.lastrowid

        return attractor_id

    def get_trajectory(
        self,
        agent_id: str,
        limit: Optional[int] = None
    ) -> List[PhaseSpaceState]:
        """
        Retrieve trajectory for an agent.

        Args:
            agent_id: Agent ID
            limit: Maximum number of states to retrieve (most recent)

        Returns:
            List of PhaseSpaceState objects
        """
        cursor = self.conn.cursor()

        query = """
            SELECT agent_id, timestamp, operational_dims, virtue_dims, confidence
            FROM states
            WHERE agent_id = ?
            ORDER BY timestamp DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, (agent_id,))

        states = []
        for row in cursor.fetchall():
            state = PhaseSpaceState.from_dict({
                'agent_id': row[0],
                'timestamp': row[1],
                'operational': json.loads(row[2]),
                'virtue': json.loads(row[3]),
                'confidence': json.loads(row[4]) if row[4] else {}
            })
            states.append(state)

        return list(reversed(states))  # Return in chronological order

    def get_all_trajectories(self, window_size: int = 10) -> Dict[str, List[PhaseSpaceState]]:
        """
        Get recent trajectories for all agents.

        Args:
            window_size: Number of recent states per agent

        Returns:
            Dict mapping agent_id to list of states
        """
        cursor = self.conn.cursor()

        # Get all unique agent IDs
        cursor.execute("SELECT DISTINCT agent_id FROM states")
        agent_ids = [row[0] for row in cursor.fetchall()]

        trajectories = {}
        for agent_id in agent_ids:
            trajectories[agent_id] = self.get_trajectory(agent_id, limit=window_size)

        return trajectories

    def get_security_events(
        self,
        agent_id: Optional[str] = None,
        blocked_only: bool = False,
        limit: Optional[int] = None
    ) -> List[SecurityEvent]:
        """Retrieve security events."""
        cursor = self.conn.cursor()

        query = "SELECT * FROM security_events WHERE 1=1"
        params = []

        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        if blocked_only:
            query += " AND blocked = 1"

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)

        events = []
        for row in cursor.fetchall():
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
            events.append(event)

        return events

    def export_to_json(self, output_path: str):
        """Export all data to JSON for backup and analysis."""
        cursor = self.conn.cursor()

        data = {
            'states': [],
            'transitions': [],
            'security_events': [],
            'attractors': [],
            'exported_at': datetime.utcnow().isoformat()
        }

        # Export states
        cursor.execute("SELECT * FROM states")
        for row in cursor.fetchall():
            data['states'].append({
                'id': row[0],
                'agent_id': row[1],
                'timestamp': row[2],
                'operational_dims': json.loads(row[3]),
                'virtue_dims': json.loads(row[4]),
                'confidence': json.loads(row[5]) if row[5] else {}
            })

        # Export transitions
        cursor.execute("SELECT * FROM transitions")
        for row in cursor.fetchall():
            data['transitions'].append({
                'id': row[0],
                'agent_id': row[1],
                'timestamp': row[2],
                'from_state': json.loads(row[3]) if row[3] else None,
                'to_state': json.loads(row[4]),
                'action_hash': row[5],
                'gating_result': row[6],
                'action_metadata': json.loads(row[7]) if row[7] else {}
            })

        # Export security events
        cursor.execute("SELECT * FROM security_events")
        for row in cursor.fetchall():
            data['security_events'].append({
                'id': row[0],
                'agent_id': row[1],
                'timestamp': row[2],
                'violations': json.loads(row[3]),
                'original_virtue_state': json.loads(row[4]),
                'corrected_virtue_state': json.loads(row[5]) if row[5] else None,
                'residual_violations': json.loads(row[6]) if row[6] else [],
                'blocked': bool(row[7]),
                'action_hash': row[8],
                'operational_state_snapshot': json.loads(row[9]) if row[9] else None,
                'event_type': row[10],
                'metadata': json.loads(row[11]) if row[11] else {}
            })

        # Export attractors
        cursor.execute("SELECT * FROM attractors")
        for row in cursor.fetchall():
            data['attractors'].append({
                'id': row[0],
                'center': json.loads(row[1]),
                'radius': row[2],
                'classification': row[3],
                'agent_count': row[4],
                'discovered_at': row[5],
                'outcomes': json.loads(row[6]) if row[6] else None,
                'metadata': json.loads(row[7]) if len(row) > 7 and row[7] else None
            })

        # Write to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_attractors(self) -> List[Dict[str, Any]]:
        """Return all attractors with metadata."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM attractors ORDER BY discovered_at DESC")
        records = []
        for row in cursor.fetchall():
            records.append({
                'id': row[0],
                'center': json.loads(row[1]),
                'radius': row[2],
                'classification': row[3],
                'agent_count': row[4],
                'discovered_at': row[5],
                'outcomes': json.loads(row[6]) if row[6] else None,
                'metadata': json.loads(row[7]) if len(row) > 7 and row[7] else None,
            })
        return records

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
