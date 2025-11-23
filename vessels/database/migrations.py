"""
Database Migration System

Simple migration management for schema versioning.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)


class MigrationManager:
    """
    Manage database schema migrations.

    Provides versioning, rollback capability, and migration tracking.
    """

    def __init__(self, db_path: str, migrations_dir: str = "migrations"):
        """
        Initialize migration manager.

        Args:
            db_path: Path to SQLite database
            migrations_dir: Directory containing migration files
        """
        self.db_path = db_path
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)

        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys=ON;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT
            )
        """)

        conn.commit()
        conn.close()

        logger.debug("Migrations table ensured")

    def get_current_version(self) -> int:
        """
        Get current schema version.

        Returns:
            Current version number (0 if no migrations applied)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        result = cursor.fetchone()[0]

        conn.close()

        return result if result else 0

    def get_applied_migrations(self) -> List[Tuple[int, str, str]]:
        """
        Get list of applied migrations.

        Returns:
            List of (version, name, applied_at) tuples
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT version, name, applied_at
            FROM schema_migrations
            ORDER BY version
        """)

        results = cursor.fetchall()
        conn.close()

        return results

    def apply_migration(self, version: int, name: str, sql: str) -> bool:
        """
        Apply migration.

        Args:
            version: Migration version number
            name: Migration name
            sql: SQL statements to execute

        Returns:
            True if successful
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON;")

            # Start transaction
            cursor.execute("BEGIN TRANSACTION;")

            # Execute migration SQL
            cursor.executescript(sql)

            # Record migration
            cursor.execute("""
                INSERT INTO schema_migrations (version, name, applied_at)
                VALUES (?, ?, ?)
            """, (version, name, datetime.utcnow().isoformat()))

            # Commit
            conn.commit()

            logger.info(f"Applied migration {version}: {name}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to apply migration {version}: {e}")
            raise

        finally:
            conn.close()


def run_migrations(db_path: str, migrations_dir: str = "migrations"):
    """
    Run all pending migrations.

    Args:
        db_path: Path to database
        migrations_dir: Directory containing migrations

    Example migration file (migrations/001_add_indexes.sql):
        -- Migration: Add missing indexes
        -- Version: 1

        CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);
        CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);
    """
    manager = MigrationManager(db_path, migrations_dir)
    current_version = manager.get_current_version()

    logger.info(f"Current schema version: {current_version}")

    # Find and apply pending migrations
    migrations_path = Path(migrations_dir)
    if not migrations_path.exists():
        logger.warning(f"Migrations directory {migrations_dir} not found")
        return

    migration_files = sorted(migrations_path.glob("*.sql"))
    applied_count = 0

    for migration_file in migration_files:
        # Extract version from filename (e.g., 001_add_indexes.sql)
        try:
            version = int(migration_file.stem.split('_')[0])
        except (ValueError, IndexError):
            logger.warning(f"Skipping invalid migration file: {migration_file}")
            continue

        if version <= current_version:
            continue

        # Read migration SQL
        sql = migration_file.read_text()
        name = migration_file.stem

        # Apply migration
        try:
            manager.apply_migration(version, name, sql)
            applied_count += 1
        except Exception as e:
            logger.error(f"Migration {version} failed: {e}")
            break

    if applied_count > 0:
        logger.info(f"Applied {applied_count} migrations")
    else:
        logger.info("No pending migrations")


def create_migration(name: str, migrations_dir: str = "migrations") -> Path:
    """
    Create new migration file.

    Args:
        name: Migration name (e.g., "add_indexes")
        migrations_dir: Directory for migrations

    Returns:
        Path to created migration file
    """
    migrations_path = Path(migrations_dir)
    migrations_path.mkdir(exist_ok=True)

    # Find next version number
    existing = list(migrations_path.glob("*.sql"))
    if existing:
        versions = []
        for f in existing:
            try:
                v = int(f.stem.split('_')[0])
                versions.append(v)
            except:
                continue
        next_version = max(versions) + 1 if versions else 1
    else:
        next_version = 1

    # Create file
    filename = f"{next_version:03d}_{name}.sql"
    filepath = migrations_path / filename

    template = f"""-- Migration: {name}
-- Version: {next_version}
-- Created: {datetime.utcnow().isoformat()}

-- Add your SQL statements below:

"""

    filepath.write_text(template)
    logger.info(f"Created migration: {filepath}")

    return filepath
