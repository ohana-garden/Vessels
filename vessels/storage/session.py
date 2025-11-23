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

    Stores sessions as graph nodes with full provenance tracking,
    user relationships, and interaction history.
    """

    def __init__(self, falkor_client, ttl_seconds: int = 3600, graph_name: str = "vessels_sessions"):
        """
        Initialize FalkorDB session store.

        Args:
            falkor_client: FalkorDBClient instance
            ttl_seconds: Session TTL in seconds
            graph_name: Graph namespace for sessions
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        self.ttl_seconds = ttl_seconds
        logger.info(f"Using FalkorDBSessionStore with graph '{graph_name}', TTL={ttl_seconds}s")

    def create_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Create session node with optional user relationship.

        Graph structure:
            (user:User) -[HAS_SESSION]-> (session:Session)
        """
        try:
            # Extract user_id if present
            user_id = data.get('user_id')

            # Build session properties
            session_props = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data": json.dumps(data),
                "ttl_seconds": self.ttl_seconds
            }

            if user_id:
                # Create session with user relationship
                query = """
                MERGE (u:User {user_id: $user_id})
                CREATE (s:Session $session_props)
                CREATE (u)-[:HAS_SESSION {created_at: $created_at}]->(s)
                RETURN s
                """
                params = {
                    "user_id": user_id,
                    "session_props": session_props,
                    "created_at": session_props["created_at"]
                }
            else:
                # Create standalone session
                query = """
                CREATE (s:Session $session_props)
                RETURN s
                """
                params = {"session_props": session_props}

            self.graph.query(query, params)
            logger.debug(f"Created session {session_id} in FalkorDB")
            return True

        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session with TTL check.

        Automatically cleans up expired sessions.
        """
        try:
            # Query with TTL validation
            query = """
            MATCH (s:Session {session_id: $session_id})
            RETURN s, s.created_at as created, s.ttl_seconds as ttl, s.data as data
            """

            result = self.graph.query(query, {"session_id": session_id})

            if not result or not result.result_set:
                return None

            row = result.result_set[0]
            created_at_str = row[1]
            ttl_seconds = row[2]
            data_json = row[3]

            # Check TTL manually (FalkorDB datetime functions vary by version)
            created_at = datetime.fromisoformat(created_at_str)
            age_seconds = (datetime.utcnow() - created_at).total_seconds()

            if age_seconds > ttl_seconds:
                # Expired - delete and return None
                self.delete_session(session_id)
                logger.debug(f"Session {session_id} expired (age={age_seconds}s, TTL={ttl_seconds}s)")
                return None

            # Parse and return session data
            return json.loads(data_json)

        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None

    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Update session data and timestamp.

        Preserves user relationships and interaction history.
        """
        try:
            query = """
            MATCH (s:Session {session_id: $session_id})
            SET s.data = $data, s.updated_at = $updated_at
            RETURN s
            """

            params = {
                "session_id": session_id,
                "data": json.dumps(data),
                "updated_at": datetime.utcnow().isoformat()
            }

            result = self.graph.query(query, params)

            if result and result.result_set:
                logger.debug(f"Updated session {session_id}")
                return True

            logger.warning(f"Session {session_id} not found for update")
            return False

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all related interactions.

        Uses DETACH DELETE to remove all relationships.
        """
        try:
            query = """
            MATCH (s:Session {session_id: $session_id})
            DETACH DELETE s
            """

            self.graph.query(query, {"session_id": session_id})
            logger.debug(f"Deleted session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def exists(self, session_id: str) -> bool:
        """Check if session exists."""
        try:
            query = """
            MATCH (s:Session {session_id: $session_id})
            RETURN count(s) as count
            """

            result = self.graph.query(query, {"session_id": session_id})

            if result and result.result_set:
                count = result.result_set[0][0]
                return count > 0

            return False

        except Exception as e:
            logger.error(f"Failed to check session existence {session_id}: {e}")
            return False

    def record_interaction(
        self,
        session_id: str,
        agent_type: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        emotion: Optional[str] = None
    ) -> bool:
        """
        Record an interaction in the session graph.

        Graph structure:
            (session:Session) -[HAS_INTERACTION]-> (interaction:Interaction)
            (interaction) -[WITH_AGENT]-> (agent:Agent {type: agent_type})
        """
        try:
            interaction_props = {
                "timestamp": datetime.utcnow().isoformat(),
                "request": json.dumps(request_data),
                "response": json.dumps(response_data),
                "emotion": emotion or "neutral"
            }

            query = """
            MATCH (s:Session {session_id: $session_id})
            MERGE (a:Agent {type: $agent_type})
            CREATE (i:Interaction $interaction_props)
            CREATE (s)-[:HAS_INTERACTION]->(i)
            CREATE (i)-[:WITH_AGENT]->(a)
            RETURN i
            """

            params = {
                "session_id": session_id,
                "agent_type": agent_type,
                "interaction_props": interaction_props
            }

            result = self.graph.query(query, params)
            return result and result.result_set

        except Exception as e:
            logger.error(f"Failed to record interaction for session {session_id}: {e}")
            return False


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
