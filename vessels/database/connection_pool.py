"""
Database Connection Pool

Thread-safe SQLite connection pool replacing check_same_thread=False.
"""

import sqlite3
import threading
from typing import Optional
from contextlib import contextmanager
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Thread-safe SQLite connection pool.

    Replaces unsafe `sqlite3.connect(db_path, check_same_thread=False)` pattern
    with proper connection pooling and thread safety.
    """

    def __init__(
        self,
        database_path: str,
        pool_size: int = 5,
        timeout: int = 30,
        enable_foreign_keys: bool = True,
        journal_mode: str = "WAL",
        synchronous: str = "NORMAL"
    ):
        """
        Initialize connection pool.

        Args:
            database_path: Path to SQLite database file
            pool_size: Number of connections in pool
            timeout: Connection acquisition timeout in seconds
            enable_foreign_keys: Enable foreign key constraints
            journal_mode: SQLite journal mode (WAL recommended)
            synchronous: SQLite synchronous mode
        """
        self.database_path = database_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.enable_foreign_keys = enable_foreign_keys
        self.journal_mode = journal_mode
        self.synchronous = synchronous

        self.pool: Queue = Queue(maxsize=pool_size)
        self.lock = threading.Lock()

        # Initialize connections
        for _ in range(pool_size):
            conn = self._create_connection()
            self.pool.put(conn)

        logger.info(
            f"Connection pool initialized: {database_path}, "
            f"size={pool_size}, WAL={journal_mode=='WAL'}"
        )

    def _create_connection(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection."""
        conn = sqlite3.connect(
            self.database_path,
            timeout=self.timeout,
            check_same_thread=True  # SAFE: Each thread gets its own connection from pool
        )

        # Enable optimizations
        if self.enable_foreign_keys:
            conn.execute("PRAGMA foreign_keys=ON;")

        conn.execute(f"PRAGMA journal_mode={self.journal_mode};")
        conn.execute(f"PRAGMA synchronous={self.synchronous};")

        # Enable row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn

    @contextmanager
    def get_connection(self):
        """
        Get connection from pool (context manager).

        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")

        Yields:
            SQLite connection from pool
        """
        conn = None
        try:
            conn = self.pool.get(timeout=self.timeout)
            yield conn
        except Empty:
            logger.error("Connection pool exhausted, timeout acquiring connection")
            raise RuntimeError("Database connection pool exhausted")
        finally:
            if conn:
                # Return connection to pool
                try:
                    self.pool.put(conn, block=False)
                except Exception as e:
                    logger.error(f"Failed to return connection to pool: {e}")

    def close_all(self):
        """Close all connections in pool."""
        with self.lock:
            while not self.pool.empty():
                try:
                    conn = self.pool.get(block=False)
                    conn.close()
                except Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing connection: {e}")

            logger.info(f"Closed all connections for {self.database_path}")


# Global connection pools
_pools: dict[str, ConnectionPool] = {}
_pool_lock = threading.Lock()


def get_connection_pool(
    database_path: str,
    pool_size: int = 5,
    **kwargs
) -> ConnectionPool:
    """
    Get or create connection pool for database.

    Args:
        database_path: Path to SQLite database
        pool_size: Number of connections in pool
        **kwargs: Additional ConnectionPool arguments

    Returns:
        ConnectionPool instance
    """
    with _pool_lock:
        if database_path not in _pools:
            _pools[database_path] = ConnectionPool(
                database_path,
                pool_size=pool_size,
                **kwargs
            )

        return _pools[database_path]


@contextmanager
def get_connection(database_path: str, **kwargs):
    """
    Convenience function to get database connection.

    Usage:
        from vessels.database import get_connection

        with get_connection("data/vessels.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vessels")

    Args:
        database_path: Path to database file
        **kwargs: Connection pool arguments

    Yields:
        SQLite connection
    """
    pool = get_connection_pool(database_path, **kwargs)
    with pool.get_connection() as conn:
        yield conn


def close_all_pools():
    """Close all connection pools."""
    with _pool_lock:
        for pool in _pools.values():
            pool.close_all()
        _pools.clear()
        logger.info("Closed all connection pools")
