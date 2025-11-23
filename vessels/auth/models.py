"""
Authentication Models

Data models for users, roles, and permissions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid


class Role(Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    SERVANT = "servant"
    COMMERCIAL = "commercial"
    VIEWER = "viewer"


class Permission(Enum):
    """Fine-grained permissions"""
    # Agent permissions
    CREATE_AGENT = "create_agent"
    DELETE_AGENT = "delete_agent"
    MANAGE_AGENTS = "manage_agents"
    VIEW_AGENTS = "view_agents"

    # Grant permissions
    SEARCH_GRANTS = "search_grants"
    APPLY_GRANTS = "apply_grants"
    VIEW_GRANTS = "view_grants"

    # Memory permissions
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    DELETE_MEMORY = "delete_memory"

    # Session permissions
    CREATE_SESSION = "create_session"
    VIEW_SESSION = "view_session"
    DELETE_SESSION = "delete_session"

    # Admin permissions
    MANAGE_USERS = "manage_users"
    VIEW_METRICS = "view_metrics"
    MANAGE_CONFIG = "manage_config"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [p for p in Permission],  # All permissions
    Role.USER: [
        Permission.CREATE_AGENT,
        Permission.VIEW_AGENTS,
        Permission.SEARCH_GRANTS,
        Permission.APPLY_GRANTS,
        Permission.VIEW_GRANTS,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
        Permission.CREATE_SESSION,
        Permission.VIEW_SESSION,
    ],
    Role.AGENT: [
        Permission.VIEW_AGENTS,
        Permission.SEARCH_GRANTS,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
        Permission.VIEW_SESSION,
    ],
    Role.SERVANT: [
        Permission.VIEW_AGENTS,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
        Permission.VIEW_SESSION,
    ],
    Role.COMMERCIAL: [
        Permission.VIEW_AGENTS,
        Permission.SEARCH_GRANTS,
        Permission.READ_MEMORY,
        Permission.VIEW_SESSION,
    ],
    Role.VIEWER: [
        Permission.VIEW_AGENTS,
        Permission.VIEW_GRANTS,
        Permission.READ_MEMORY,
        Permission.VIEW_SESSION,
    ]
}


@dataclass
class User:
    """User model with authentication details"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    role: Role = Role.USER
    community_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    metadata: dict = field(default_factory=dict)

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def has_role(self, role: Role) -> bool:
        """Check if user has specific role"""
        return self.role == role or self.role == Role.ADMIN

    def to_dict(self) -> dict:
        """Convert to dictionary (exclude password_hash)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'community_id': self.community_id,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active,
            'metadata': self.metadata
        }
