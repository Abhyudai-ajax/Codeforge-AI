"""
User request / response schemas.

Hashed passwords are **never** included in any response schema —
enforced at the schema layer, not only by the route.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """
    Request body for the ``POST /auth/register`` endpoint.

    Attributes:
        username:  Unique, URL-safe username (3–50 chars, alphanumeric / _ / -).
        email:     Valid email address.
        password:  Plain-text password (8–128 chars).  Hashed before storage.
        full_name: Optional human-readable display name.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Unique username — alphanumeric, underscores, and hyphens only",
        examples=["john_doe"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address (must be unique)",
        examples=["john@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (8–128 characters)",
        examples=["Str0ng!Pass"],
    )
    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Optional display name",
        examples=["John Doe"],
    )


class RegisterResponse(BaseModel):
    """
    Response body for a successful registration.

    Contains only public, non-sensitive user fields.
    """

    id: uuid.UUID = Field(..., description="User UUID")
    username: str
    email: EmailStr
    full_name: str | None
    role: str = Field(..., description="User role (e.g. 'UserRole.USER')")
    is_active: bool
    created_at: datetime

    # Allow constructing from SQLAlchemy ORM instances directly.
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    """
    Full public profile of the authenticated user.

    Returned by ``GET /auth/me`` and profile endpoints.  Never includes ``hashed_password``.
    """

    id: uuid.UUID
    username: str
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    bio: str | None
    role: str = Field(..., description="User role (e.g. 'user', 'admin')")
    is_active: bool
    is_verified: bool
    github_username: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """Request body for ``PATCH /users/me`` to update profile details."""

    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=1024)
    bio: str | None = Field(default=None, max_length=2000)


class PasswordChangeRequest(BaseModel):
    """Request body for ``PUT /users/me/password`` to change account password."""

    current_password: str = Field(
        ..., min_length=8, description="Current password for verification"
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password (8-128 chars)"
    )


class UserRoleUpdate(BaseModel):
    """Request body for admin to update a user's role or status."""

    role: str | None = Field(default=None, description="New role ('user' or 'admin')")
    is_active: bool | None = Field(default=None, description="Set account active status")


class UserListResponse(BaseModel):
    """Paginated list of users for admin directory endpoint."""

    items: list[UserResponse]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    """Generic status message response."""

    message: str
