"""
Authentication request and response schemas.

Validation rules:
  - name:     2–100 characters
  - email:    valid email format (EmailStr)
  - password: 8–128 characters (enforced by Pydantic; frontend should mirror this)

Logout strategy:
  JWT is stateless — there is no server-side session to invalidate.
  To log out, the client discards the token (clears localStorage / memory).
  The token remains cryptographically valid until it expires, but without it
  the client cannot send authenticated requests.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Jane Doe"])
    email: EmailStr = Field(..., examples=["jane@example.com"])
    password: str = Field(
        ..., min_length=8, max_length=128, examples=["secret123"]
    )


class OwnerSignupRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Mario Rossi"])
    email: EmailStr = Field(..., examples=["mario@ristorantebello.com"])
    password: str = Field(
        ..., min_length=8, max_length=128, examples=["ownerpass1"]
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., examples=["jane@example.com"])
    password: str = Field(..., min_length=1, examples=["secret123"])


class TokenResponse(BaseModel):
    """Returned by every signup and login endpoint."""

    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: str  # "user" | "owner"


class MeResponse(BaseModel):
    """Returned by GET /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    profile_photo_url: Optional[str] = None
    created_at: datetime
