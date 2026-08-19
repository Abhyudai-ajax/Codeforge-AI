"""
Pydantic schema package.
"""

from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
)
from app.schemas.health import HealthResponse
from app.schemas.user import (
    MessageResponse,
    PasswordChangeRequest,
    RegisterRequest,
    RegisterResponse,
    UserListResponse,
    UserProfileUpdate,
    UserResponse,
    UserRoleUpdate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    # Registration
    "RegisterRequest",
    "RegisterResponse",
    # User
    "UserResponse",
    "UserProfileUpdate",
    "PasswordChangeRequest",
    "UserRoleUpdate",
    "UserListResponse",
    "MessageResponse",
    # Health
    "HealthResponse",
]
