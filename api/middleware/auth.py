"""
Authentication Middleware for CashPilot AI
Uses Supabase Auth for JWT validation
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from typing import Optional, Dict, Any
import logging

from config.supabase_config import get_supabase_client

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase_client)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["id"]}

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials

    try:
        # Verify JWT token with Supabase
        response = supabase.auth.get_user(token)

        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = response.user

        # Return user data
        return {
            "id": user.id,
            "email": user.email,
            "user_metadata": user.user_metadata,
            "created_at": user.created_at,
        }

    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    supabase: Client = Depends(get_supabase_client)
) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Use for endpoints that work with or without authentication.

    Usage:
        @app.get("/public-or-private")
        async def mixed_route(user: Optional[dict] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to require admin role.

    Usage:
        @app.post("/admin/action")
        async def admin_action(user: dict = Depends(require_admin)):
            ...
    """
    user_metadata = user.get("user_metadata", {})
    is_admin = user_metadata.get("role") == "admin"

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return user
