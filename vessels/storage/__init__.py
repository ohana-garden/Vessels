"""
Storage abstractions for Vessels.

Provides clean interfaces for session management, state persistence,
and other storage needs across deployment tiers.
"""

from .session import (
    SessionStore,
    InMemorySessionStore,
    RedisSessionStore,
    FalkorDBSessionStore,
    create_session_store
)

__all__ = [
    "SessionStore",
    "InMemorySessionStore",
    "RedisSessionStore",
    "FalkorDBSessionStore",
    "create_session_store"
]
