"""
JWT Authentication

Provides token creation, verification, and decorator-based auth.
"""

import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Dict, Any
from flask import request, abort, g
import logging

from .models import User, Role, Permission

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'CHANGE_THIS_IN_PRODUCTION')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '60'))


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token for user.

    Args:
        user: User object to create token for
        expires_delta: Optional custom expiration time

    Returns:
        JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta

    payload = {
        'sub': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role.value,
        'community_id': user.community_id,
        'exp': expire,
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created token for user {user.username} (expires: {expire})")
    return token


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def get_current_user() -> Optional[User]:
    """
    Get current authenticated user from request context.

    Returns:
        User object if authenticated, None otherwise
    """
    return getattr(g, 'current_user', None)


def require_auth(f):
    """
    Decorator to require authentication on endpoint.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_endpoint():
            user = get_current_user()
            return {'user': user.username}
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            logger.warning(f"Missing or invalid Authorization header for {request.path}")
            abort(401, description='Missing or invalid authorization header')

        token = auth_header.replace('Bearer ', '')
        payload = verify_token(token)

        if not payload:
            logger.warning(f"Invalid token for {request.path}")
            abort(401, description='Invalid or expired token')

        # Create User object from payload
        user = User(
            id=payload['sub'],
            username=payload['username'],
            email=payload['email'],
            role=Role(payload['role']),
            community_id=payload.get('community_id')
        )

        # Store in request context
        g.current_user = user

        logger.debug(f"Authenticated user {user.username} for {request.path}")
        return f(*args, **kwargs)

    return decorated


def require_role(*allowed_roles: Role):
    """
    Decorator to require specific role(s).

    Usage:
        @app.route('/api/admin')
        @require_auth
        @require_role(Role.ADMIN)
        def admin_endpoint():
            return {'message': 'Admin only'}
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()

            if not user:
                logger.warning(f"No authenticated user for role-protected {request.path}")
                abort(401, description='Authentication required')

            if user.role not in allowed_roles and user.role != Role.ADMIN:
                logger.warning(f"User {user.username} lacks required role for {request.path}")
                abort(403, description='Insufficient permissions')

            return f(*args, **kwargs)

        return decorated
    return decorator


def require_permission(*required_permissions: Permission):
    """
    Decorator to require specific permission(s).

    Usage:
        @app.route('/api/agents/create')
        @require_auth
        @require_permission(Permission.CREATE_AGENT)
        def create_agent():
            return {'message': 'Agent created'}
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()

            if not user:
                logger.warning(f"No authenticated user for permission-protected {request.path}")
                abort(401, description='Authentication required')

            # Check if user has all required permissions
            for perm in required_permissions:
                if not user.has_permission(perm):
                    logger.warning(
                        f"User {user.username} lacks permission {perm.value} for {request.path}"
                    )
                    abort(403, description=f'Missing required permission: {perm.value}')

            return f(*args, **kwargs)

        return decorated
    return decorator
