"""
Secure Session Manager

Replaces in-memory dict with TTL-based secure session storage.
"""

from cachetools import TTLCache
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import threading
import uuid

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Thread-safe session manager with automatic expiration.

    Replaces the problematic global `sessions = {}` pattern with:
    - Automatic session expiration (TTL)
    - Thread-safe operations
    - Maximum session limits
    - Secure session ID generation
    """

    def __init__(
        self,
        max_sessions: int = 10000,
        ttl_seconds: int = 3600,
        max_context_items: int = 100
    ):
        """
        Initialize session manager.

        Args:
            max_sessions: Maximum number of concurrent sessions
            ttl_seconds: Session time-to-live in seconds (default 1 hour)
            max_context_items: Maximum context items per session
        """
        self.sessions = TTLCache(maxsize=max_sessions, ttl=ttl_seconds)
        self.lock = threading.RLock()
        self.max_context_items = max_context_items
        self.ttl_seconds = ttl_seconds

        logger.info(
            f"SessionManager initialized: max_sessions={max_sessions}, "
            f"ttl={ttl_seconds}s, max_context={max_context_items}"
        )

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create new session with secure ID.

        Args:
            user_id: Optional user ID to associate with session

        Returns:
            Secure session ID
        """
        session_id = str(uuid.uuid4())

        with self.lock:
            self.sessions[session_id] = {
                'id': session_id,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'context': [],
                'emotion_history': [],
                'current_agents': [],
                'metadata': {}
            }

        logger.info(f"Created session {session_id} for user {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data if exists and not expired, None otherwise
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if session:
                logger.debug(f"Retrieved session {session_id}")
            else:
                logger.debug(f"Session {session_id} not found or expired")

            return session

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data.

        Args:
            session_id: Session identifier
            updates: Dictionary of updates to apply

        Returns:
            True if updated, False if session doesn't exist
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if not session:
                logger.warning(f"Cannot update non-existent session {session_id}")
                return False

            # Apply updates
            for key, value in updates.items():
                if key in session:
                    session[key] = value
                else:
                    session['metadata'][key] = value

            # Re-insert to update TTL
            self.sessions[session_id] = session

            logger.debug(f"Updated session {session_id}")
            return True

    def add_context(self, session_id: str, context_item: str) -> bool:
        """
        Add context item to session with automatic trimming.

        Args:
            session_id: Session identifier
            context_item: Context string to add

        Returns:
            True if added, False if session doesn't exist
        """
        with self.lock:
            session = self.sessions.get(session_id)

            if not session:
                logger.warning(f"Cannot add context to non-existent session {session_id}")
                return False

            # Add to context
            session['context'].append(context_item)

            # Trim if exceeds max
            if len(session['context']) > self.max_context_items:
                session['context'] = session['context'][-self.max_context_items:]
                logger.debug(f"Trimmed context for session {session_id}")

            # Re-insert to update TTL
            self.sessions[session_id] = session

            return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if didn't exist
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session {session_id}")
                return True
            else:
                logger.debug(f"Session {session_id} not found for deletion")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get session manager statistics.

        Returns:
            Dictionary with stats (count, max_size, ttl)
        """
        with self.lock:
            return {
                'active_sessions': len(self.sessions),
                'max_sessions': self.sessions.maxsize,
                'ttl_seconds': self.ttl_seconds,
                'max_context_items': self.max_context_items
            }

    def cleanup_user_sessions(self, user_id: str) -> int:
        """
        Remove all sessions for a specific user.

        Args:
            user_id: User identifier

        Returns:
            Number of sessions removed
        """
        with self.lock:
            to_remove = [
                sid for sid, session in self.sessions.items()
                if session.get('user_id') == user_id
            ]

            for sid in to_remove:
                del self.sessions[sid]

            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} sessions for user {user_id}")

            return len(to_remove)
