"""
Authentication request / response schemas.
"""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """
    Request body for the ``POST /auth/login`` endpoint.

    Attributes:
        email: The user's registered email address.
        password: The user's plain-text password (min 8 chars).
    """

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=8, description="Account password (min 8 characters)")


class TokenResponse(BaseModel):
    """
    Response returned after a successful login.

    Attributes:
        access_token:  Short-lived JWT for API requests.
        refresh_token: Long-lived JWT for refreshing the access token.
        token_type:    Always ``"bearer"``.
        expires_in:    Access-token TTL in **seconds**.
    """

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token scheme")
    expires_in: int = Field(..., description="Access token TTL in seconds")
