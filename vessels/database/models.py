"""
Database Setup and Utilities

Helper functions for database initialization and configuration.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def enable_foreign_keys(conn: sqlite3.Connection):
    """
    Enable foreign key constraints on SQLite connection.

    Args:
        conn: SQLite connection

    Critical fix: Foreign keys are NOT enforced by default in SQLite!
    """
    conn.execute("PRAGMA foreign_keys=ON;")
    logger.debug("Foreign key constraints enabled")


def setup_database(db_path: str, enable_wal: bool = True) -> sqlite3.Connection:
    """
    Set up database with optimal configuration.

    Args:
        db_path: Path to database file
        enable_wal: Enable WAL mode for better concurrency

    Returns:
        Configured SQLite connection
    """
    # Create parent directory if needed
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=30)

    # Enable foreign keys (CRITICAL FIX)
    conn.execute("PRAGMA foreign_keys=ON;")

    if enable_wal:
        # Enable WAL mode for better concurrent access
        conn.execute("PRAGMA journal_mode=WAL;")

    # Set synchronous mode for performance
    conn.execute("PRAGMA synchronous=NORMAL;")

    # Enable dict-like row access
    conn.row_factory = sqlite3.Row

    logger.info(f"Database configured: {db_path} (WAL={enable_wal})")

    return conn


def create_indexes_batch(conn: sqlite3.Connection, indexes: list[str]):
    """
    Create multiple indexes in single transaction.

    Args:
        conn: SQLite connection
        indexes: List of CREATE INDEX statements
    """
    cursor = conn.cursor()

    try:
        cursor.execute("BEGIN TRANSACTION;")

        for index_sql in indexes:
            cursor.execute(index_sql)

        conn.commit()
        logger.info(f"Created {len(indexes)} indexes")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to create indexes: {e}")
        raise


def add_missing_indexes():
    """
    Add all missing indexes identified in the review.

    This fixes critical performance issues with O(n) scans.
    """
    # Memory indexes
    memory_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);",
        "CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);",
        "CREATE INDEX IF NOT EXISTS idx_memories_agent_timestamp ON memories(agent_id, timestamp DESC);",
    ]

    # Trajectory indexes
    trajectory_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_states_agent_timestamp ON states(agent_id, timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_security_events_blocked ON security_events(blocked, timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_transitions_agent ON transitions(agent_id);",
    ]

    # Vessel registry indexes
    vessel_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_vessels_name ON vessels(name);",
        "CREATE INDEX IF NOT EXISTS idx_vessels_privacy ON vessels(privacy_level);",
        "CREATE INDEX IF NOT EXISTS idx_vessels_community ON vessels(community_id);",
    ]

    return {
        'memories': memory_indexes,
        'trajectories': trajectory_indexes,
        'vessels': vessel_indexes
    }
