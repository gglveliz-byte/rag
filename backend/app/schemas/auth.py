"""Authentication and API Key request/response models."""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """User registration payload."""

    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT Token response after login or register."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    expires_in_seconds: int


class UserResponse(BaseModel):
    """Public user profile information."""

    user_id: str
    email: str
    created_at: datetime
    active_api_keys_count: int = 0


class APIKeyCreate(BaseModel):
    """Request payload to create a new API Key for external LLMs."""

    name: str = Field(default="Default Key", min_length=1, max_length=50)


class APIKeyResponse(BaseModel):
    """API Key representation."""

    key_id: str
    name: str
    masked_key: str
    raw_key: str | None = Field(default=None, description="Only shown once upon creation")
    created_at: datetime
    is_active: bool = True


class ClaimSessionRequest(BaseModel):
    """Request to transfer a guest session to a registered account."""

    guest_session_id: str = Field(description="UUID of guest session to claim")


class ClaimSessionResponse(BaseModel):
    """Response after claiming guest session."""

    claimed_documents: int
    message: str
