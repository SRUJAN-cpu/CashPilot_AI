"""
User Management Routes
Handles registration, login, profile management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from supabase import Client
from typing import Optional
import logging

from config.supabase_config import get_supabase_client, get_supabase_admin_client
from api.middleware.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class UserRegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None


class UserLoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserUpdateRequest(BaseModel):
    """User profile update request"""
    name: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response"""
    access_token: str
    refresh_token: str
    user: dict


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    name: Optional[str]
    created_at: str
    last_login: Optional[str]


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    supabase: Client = Depends(get_supabase_client),
    admin_supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Register a new user account

    - **email**: Valid email address
    - **password**: Minimum 8 characters
    - **name**: Optional display name

    Returns access and refresh tokens
    """
    try:
        # Register user with Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "name": request.name
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )

        # Create user profile in public.users table using admin client (bypasses RLS)
        user_data = {
            "id": auth_response.user.id,
            "email": request.email,
            "name": request.name,
        }

        admin_supabase.table("users").insert(user_data).execute()

        logger.info(f"New user registered: {request.email}")

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": request.name,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Registration error: {e}")

        # Check if it's a duplicate user error (Supabase returns 422 for existing users)
        # Common patterns: "already", "exists", "duplicate", "422", "registered"
        if any(keyword in error_str for keyword in ['already', 'exists', 'duplicate', 'registered', '422', 'user already', 'email already']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered"
            )

        # Other errors - return generic message without exposing internal error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    supabase: Client = Depends(get_supabase_client),
    admin_supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Login with email and password

    Returns access and refresh tokens
    """
    try:
        # Authenticate with Supabase
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user or not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Ensure user exists in public.users table (create if missing)
        try:
            # Check if user exists in public.users using admin client
            user_check = admin_supabase.table("users").select("id").eq("id", auth_response.user.id).execute()

            if not user_check.data:
                # User doesn't exist in public.users, create them using admin client (bypasses RLS)
                user_data = {
                    "id": auth_response.user.id,
                    "email": auth_response.user.email,
                    "name": auth_response.user.user_metadata.get("name"),
                }
                admin_supabase.table("users").insert(user_data).execute()
                logger.info(f"Created missing user profile for: {request.email}")
            else:
                # User exists, update last_login using admin client
                admin_supabase.table("users").update({
                    "last_login": "now()"
                }).eq("id", auth_response.user.id).execute()
        except Exception as e:
            logger.warning(f"Could not update user profile: {e}")

        logger.info(f"User logged in: {request.email}")

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
            "user": {
                "id": auth_response.user.id,
                "email": auth_response.user.email,
                "name": auth_response.user.user_metadata.get("name"),
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        # Check if it's an authentication error from Supabase
        error_str = str(e).lower()
        if 'invalid' in error_str or 'credentials' in error_str or 'password' in error_str or 'email' in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/logout")
async def logout(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Logout current user (invalidates tokens)
    """
    try:
        supabase.auth.sign_out()
        logger.info(f"User logged out: {user['email']}")
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    supabase: Client = Depends(get_supabase_client)
):
    """
    Refresh access token using refresh token
    """
    try:
        auth_response = supabase.auth.refresh_session(refresh_token)

        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        return {
            "access_token": auth_response.session.access_token,
            "refresh_token": auth_response.session.refresh_token,
        }
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


# ============================================================================
# Profile Management
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get current user's profile
    """
    try:
        response = supabase.table("users").select("*").eq("id", user["id"]).single().execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        return response.data
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch profile"
        )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    updates: UserUpdateRequest,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update current user's profile
    """
    try:
        # Update public.users table
        response = supabase.table("users").update(
            updates.dict(exclude_unset=True)
        ).eq("id", user["id"]).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(f"Profile updated: {user['email']}")
        return response.data[0]

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.delete("/me")
async def delete_account(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete current user's account (WARNING: Irreversible!)
    """
    try:
        # Delete from public.users (cascades to conversations, messages, portfolios)
        supabase.table("users").delete().eq("id", user["id"]).execute()

        # Sign out
        supabase.auth.sign_out()

        logger.warning(f"User account deleted: {user['email']}")
        return {"message": "Account successfully deleted"}

    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
