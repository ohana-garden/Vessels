"""
Phase Space Tracker - Tracks agent trajectories through 14D virtue space over time.

This module stores and analyzes how agents move through the moral manifold,
enabling the discovery of attractors and patterns in agent behavior.
"""

import sqlite3
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import numpy as np
from bahai_manifold import BahaiManifold


class PhaseSpaceTracker:
    """
    Tracks agent trajectories through the 14-dimensional virtue space.

    Stores timestamped states in SQLite for efficient querying and analysis.
    Uses standard Euclidean distance (NO weighted metrics) for distance calculations.
    """

    def __init__(self, db_path: str = 'phase_space.db', manifold: Optional[BahaiManifold] = None):
        """
        Initialize the phase space tracker.

        Args:
            db_path: Path to SQLite database file.
            manifold: BahaiManifold instance for virtue names.
        """
        self.db_path = db_path
        self.manifold = manifold or BahaiManifold()
        self.conn = sqlite3.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        """Create database tables for trajectory storage."""
        cursor = self.conn.cursor()

        # Main trajectory table
        trajectory_cols = ['agent_id TEXT', 'timestamp REAL']
        trajectory_cols.extend([f'{virtue} REAL' for virtue in self.manifold.ALL_VIRTUES])

        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS trajectories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {', '.join(trajectory_cols)}
            )
        ''')

        # Index for efficient querying
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_agent_time
            ON trajectories(agent_id, timestamp)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON trajectories(timestamp)
        ''')

        self.conn.commit()

    def record_state(self, agent_id: str, state: Dict[str, float],
                    timestamp: Optional[float] = None) -> int:
        """
        Record an agent's state at a point in time.

        Args:
            agent_id: Unique identifier for the agent.
            state: Dictionary mapping virtue names to values.
            timestamp: Unix timestamp. If None, uses current time.

        Returns:
            Row ID of the inserted record.
        """
        if timestamp is None:
            timestamp = datetime.now().timestamp()

        cursor = self.conn.cursor()

        # Prepare values in correct order
        values = [agent_id, timestamp]
        values.extend([state[virtue] for virtue in self.manifold.ALL_VIRTUES])

        # Prepare placeholders
        placeholders = ', '.join(['?'] * len(values))

        cursor.execute(f'''
            INSERT INTO trajectories
            (agent_id, timestamp, {', '.join(self.manifold.ALL_VIRTUES)})
            VALUES ({placeholders})
        ''', values)

        self.conn.commit()
        return cursor.lastrowid

    def get_trajectory(self, agent_id: str,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None) -> List[Tuple[float, Dict[str, float]]]:
        """
        Get an agent's trajectory over a time period.

        Args:
            agent_id: Agent identifier.
            start_time: Start timestamp (inclusive). If None, from beginning.
            end_time: End timestamp (inclusive). If None, until now.

        Returns:
            List of (timestamp, state) tuples, ordered by timestamp.
        """
        cursor = self.conn.cursor()

        query = f'''
            SELECT timestamp, {', '.join(self.manifold.ALL_VIRTUES)}
            FROM trajectories
            WHERE agent_id = ?
        '''
        params = [agent_id]

        if start_time is not None:
            query += ' AND timestamp >= ?'
            params.append(start_time)

        if end_time is not None:
            query += ' AND timestamp <= ?'
            params.append(end_time)

        query += ' ORDER BY timestamp ASC'

        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of (timestamp, state_dict) tuples
        trajectory = []
        for row in rows:
            timestamp = row[0]
            state = {virtue: row[i+1] for i, virtue in enumerate(self.manifold.ALL_VIRTUES)}
            trajectory.append((timestamp, state))

        return trajectory

    def get_all_trajectories(self,
                           start_time: Optional[float] = None,
                           end_time: Optional[float] = None) -> Dict[str, List[Tuple[float, Dict[str, float]]]]:
        """
        Get all agents' trajectories over a time period.

        Args:
            start_time: Start timestamp (inclusive). If None, from beginning.
            end_time: End timestamp (inclusive). If None, until now.

        Returns:
            Dictionary mapping agent_id to list of (timestamp, state) tuples.
        """
        cursor = self.conn.cursor()

        query = '''
            SELECT DISTINCT agent_id FROM trajectories
        '''
        params = []

        if start_time is not None or end_time is not None:
            query += ' WHERE'
            if start_time is not None:
                query += ' timestamp >= ?'
                params.append(start_time)
            if end_time is not None:
                if start_time is not None:
                    query += ' AND'
                query += ' timestamp <= ?'
                params.append(end_time)

        cursor.execute(query, params)
        agent_ids = [row[0] for row in cursor.fetchall()]

        trajectories = {}
        for agent_id in agent_ids:
            trajectories[agent_id] = self.get_trajectory(agent_id, start_time, end_time)

        return trajectories

    def get_states_matrix(self,
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None) -> Tuple[np.ndarray, List[str], List[float]]:
        """
        Get all states as a matrix for clustering/analysis.

        Args:
            start_time: Start timestamp (inclusive). If None, from beginning.
            end_time: End timestamp (inclusive). If None, until now.

        Returns:
            Tuple of (states_matrix, agent_ids, timestamps):
            - states_matrix: N x 14 numpy array of states
            - agent_ids: List of agent IDs corresponding to each row
            - timestamps: List of timestamps corresponding to each row
        """
        cursor = self.conn.cursor()

        query = f'''
            SELECT agent_id, timestamp, {', '.join(self.manifold.ALL_VIRTUES)}
            FROM trajectories
        '''
        params = []

        if start_time is not None or end_time is not None:
            query += ' WHERE'
            if start_time is not None:
                query += ' timestamp >= ?'
                params.append(start_time)
            if end_time is not None:
                if start_time is not None:
                    query += ' AND'
                query += ' timestamp <= ?'
                params.append(end_time)

        query += ' ORDER BY timestamp ASC'

        cursor.execute(query, params)
        rows = cursor.fetchall()

        if not rows:
            return np.array([]).reshape(0, 14), [], []

        agent_ids = [row[0] for row in rows]
        timestamps = [row[1] for row in rows]
        states = np.array([[row[i+2] for i in range(14)] for row in rows])

        return states, agent_ids, timestamps

    def euclidean_distance(self, state1: Dict[str, float], state2: Dict[str, float]) -> float:
        """
        Calculate standard Euclidean distance between two states.

        NO weighted metrics - uses standard Euclidean distance.

        Args:
            state1: First state.
            state2: Second state.

        Returns:
            Euclidean distance in 14D space.
        """
        sum_sq = 0.0
        for virtue in self.manifold.ALL_VIRTUES:
            diff = state1[virtue] - state2[virtue]
            sum_sq += diff * diff
        return np.sqrt(sum_sq)

    def trajectory_length(self, trajectory: List[Tuple[float, Dict[str, float]]]) -> float:
        """
        Calculate the total path length of a trajectory.

        Args:
            trajectory: List of (timestamp, state) tuples.

        Returns:
            Total Euclidean distance traveled along the trajectory.
        """
        if len(trajectory) < 2:
            return 0.0

        total_length = 0.0
        for i in range(len(trajectory) - 1):
            _, state1 = trajectory[i]
            _, state2 = trajectory[i + 1]
            total_length += self.euclidean_distance(state1, state2)

        return total_length

    def get_final_states(self,
                        start_time: Optional[float] = None,
                        end_time: Optional[float] = None) -> Dict[str, Dict[str, float]]:
        """
        Get the most recent state for each agent in the time period.

        Args:
            start_time: Start timestamp. If None, from beginning.
            end_time: End timestamp. If None, until now.

        Returns:
            Dictionary mapping agent_id to their final state.
        """
        cursor = self.conn.cursor()

        query = f'''
            SELECT agent_id, MAX(timestamp) as max_time
            FROM trajectories
        '''
        params = []

        if start_time is not None or end_time is not None:
            query += ' WHERE'
            if start_time is not None:
                query += ' timestamp >= ?'
                params.append(start_time)
            if end_time is not None:
                if start_time is not None:
                    query += ' AND'
                query += ' timestamp <= ?'
                params.append(end_time)

        query += ' GROUP BY agent_id'

        cursor.execute(query, params)
        agent_times = cursor.fetchall()

        final_states = {}
        for agent_id, max_time in agent_times:
            cursor.execute(f'''
                SELECT {', '.join(self.manifold.ALL_VIRTUES)}
                FROM trajectories
                WHERE agent_id = ? AND timestamp = ?
            ''', (agent_id, max_time))

            row = cursor.fetchone()
            if row:
                state = {virtue: row[i] for i, virtue in enumerate(self.manifold.ALL_VIRTUES)}
                final_states[agent_id] = state

        return final_states

    def clear_agent_data(self, agent_id: str):
        """
        Remove all trajectory data for an agent.

        Args:
            agent_id: Agent to remove.
        """
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM trajectories WHERE agent_id = ?', (agent_id,))
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
