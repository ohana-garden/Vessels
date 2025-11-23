"""
Session Storage Abstraction: Replaces in-memory sessions dict

Provides a clean interface that can use:
- In-memory (development/Tier 0)
- Redis (production/Tier 1+)
- FalkorDB (full graph integration/Tier 2+)
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionStore(ABC):
    """Abstract session store interface."""

    @abstractmethod
    def create_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Create a new session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by ID."""
        pass

    @abstractmethod
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update an existing session."""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        pass

    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        pass


class InMemorySessionStore(SessionStore):
    """
    In-memory session store (Tier 0).

    WARNING: All data lost on restart. Use only for development/testing.
    """

    def __init__(self, ttl_seconds: int = 3600):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        logger.warning(
            "Using InMemorySessionStore - sessions will be lost on restart. "
            "Use RedisSessionStore or FalkorDBSessionStore for production."
        )

    def create_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        self.sessions[session_id] = {
            **data,
            "_created_at": datetime.utcnow().isoformat(),
            "_updated_at": datetime.utcnow().isoformat()
        }
        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if not session:
            return None

        # Check TTL
        created_at = datetime.fromisoformat(session.get("_created_at"))
        if datetime.utcnow() - created_at > timedelta(seconds=self.ttl_seconds):
            self.delete_session(session_id)
            return None

        return session

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        if session_id not in self.sessions:
            return False

        self.sessions[session_id].update(data)
        self.sessions[session_id]["_updated_at"] = datetime.utcnow().isoformat()
        return True

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def exists(self, session_id: str) -> bool:
        return session_id in self.sessions


class RedisSessionStore(SessionStore):
    """
    Redis-backed session store (Tier 1+).

    Provides persistence and distributed access.
    """

    def __init__(self, redis_client, ttl_seconds: int = 3600, key_prefix: str = "vessels:session:"):
        """
        Initialize Redis session store.

        Args:
            redis_client: Redis client instance
            ttl_seconds: Session TTL in seconds
            key_prefix: Prefix for Redis keys
        """
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        logger.info(f"Using RedisSessionStore with TTL={ttl_seconds}s")

    def _make_key(self, session_id: str) -> str:
        return f"{self.key_prefix}{session_id}"

    def create_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        key = self._make_key(session_id)
        session_data = {
            **data,
            "_created_at": datetime.utcnow().isoformat(),
            "_updated_at": datetime.utcnow().isoformat()
        }

        self.redis.setex(
            key,
            self.ttl_seconds,
            json.dumps(session_data)
        )
        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        key = self._make_key(session_id)
        data = self.redis.get(key)

        if not data:
            return None

        return json.loads(data)

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        key = self._make_key(session_id)

        # Get existing session
        existing = self.get_session(session_id)
        if not existing:
            return False

        # Update and save
        existing.update(data)
        existing["_updated_at"] = datetime.utcnow().isoformat()

        self.redis.setex(
            key,
            self.ttl_seconds,
            json.dumps(existing)
        )
        return True

    def delete_session(self, session_id: str) -> bool:
        key = self._make_key(session_id)
        return self.redis.delete(key) > 0

    def exists(self, session_id: str) -> bool:
        key = self._make_key(session_id)
        return self.redis.exists(key) > 0


class FalkorDBSessionStore(SessionStore):
    """
    FalkorDB-backed session store (Tier 2).

    Stores sessions as graph nodes with full provenance tracking.
    """

    def __init__(self, falkor_client, ttl_seconds: int = 3600):
        """
        Initialize FalkorDB session store.

        Args:
            falkor_client: FalkorDB client instance
            ttl_seconds: Session TTL in seconds
        """
        self.falkor = falkor_client
        self.ttl_seconds = ttl_seconds
        logger.info(f"Using FalkorDBSessionStore with graph integration")

    def create_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        # Create session node in graph
        query = """
        CREATE (s:Session {
            session_id: $session_id,
            created_at: $created_at,
            updated_at: $updated_at,
            data: $data,
            ttl_seconds: $ttl
        })
        """

        self.falkor.query(query, {
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "data": json.dumps(data),
            "ttl": self.ttl_seconds
        })
        return True

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (s:Session {session_id: $session_id})
        WHERE datetime(s.created_at) > datetime() - duration({seconds: s.ttl_seconds})
        RETURN s
        """

        result = self.falkor.query(query, {"session_id": session_id})

        if not result or not result.result_set:
            return None

        session_node = result.result_set[0][0]
        data = json.loads(session_node.properties.get("data", "{}"))

        return data

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        query = """
        MATCH (s:Session {session_id: $session_id})
        SET s.data = $data, s.updated_at = $updated_at
        RETURN s
        """

        result = self.falkor.query(query, {
            "session_id": session_id,
            "data": json.dumps(data),
            "updated_at": datetime.utcnow().isoformat()
        })

        return result and len(result.result_set) > 0

    def delete_session(self, session_id: str) -> bool:
        query = """
        MATCH (s:Session {session_id: $session_id})
        DELETE s
        """

        self.falkor.query(query, {"session_id": session_id})
        return True

    def exists(self, session_id: str) -> bool:
        query = """
        MATCH (s:Session {session_id: $session_id})
        RETURN count(s) > 0 as exists
        """

        result = self.falkor.query(query, {"session_id": session_id})
        return result and result.result_set[0][0]


def create_session_store(
    store_type: str = "memory",
    **kwargs
) -> SessionStore:
    """
    Factory function to create appropriate session store.

    Args:
        store_type: Type of store ("memory", "redis", "falkordb")
        **kwargs: Store-specific configuration

    Returns:
        SessionStore instance
    """
    if store_type == "memory":
        return InMemorySessionStore(ttl_seconds=kwargs.get("ttl_seconds", 3600))

    elif store_type == "redis":
        redis_client = kwargs.get("redis_client")
        if not redis_client:
            raise ValueError("redis_client required for RedisSessionStore")
        return RedisSessionStore(
            redis_client=redis_client,
            ttl_seconds=kwargs.get("ttl_seconds", 3600),
            key_prefix=kwargs.get("key_prefix", "vessels:session:")
        )

    elif store_type == "falkordb":
        falkor_client = kwargs.get("falkor_client")
        if not falkor_client:
            raise ValueError("falkor_client required for FalkorDBSessionStore")
        return FalkorDBSessionStore(
            falkor_client=falkor_client,
            ttl_seconds=kwargs.get("ttl_seconds", 3600)
        )

    else:
        raise ValueError(f"Unknown store type: {store_type}")
