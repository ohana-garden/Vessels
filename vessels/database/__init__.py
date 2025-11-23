"""
Database Module

Provides connection pooling, migrations, and optimized database access.
"""

from .connection_pool import ConnectionPool, get_connection
from .migrations import run_migrations, create_migration
from .models import setup_database, enable_foreign_keys

__all__ = [
    'ConnectionPool',
    'get_connection',
    'run_migrations',
    'create_migration',
    'setup_database',
    'enable_foreign_keys'
]
