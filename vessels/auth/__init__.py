"""
Authentication and Authorization Module

Provides JWT-based authentication, role-based access control,
and session management for the Vessels platform.
"""

from .jwt_auth import (
    create_access_token,
    verify_token,
    require_auth,
    require_role,
    get_current_user
)
from .session_manager import SessionManager
from .models import User, Role, Permission

__all__ = [
    'create_access_token',
    'verify_token',
    'require_auth',
    'require_role',
    'get_current_user',
    'SessionManager',
    'User',
    'Role',
    'Permission'
]
