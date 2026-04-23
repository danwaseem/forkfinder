"""
Authentication router — MongoDB version.

Endpoints:
  POST /auth/user/signup   — register a reviewer account
  POST /auth/user/login    — login as a reviewer
  POST /auth/owner/signup  — register a restaurant-owner account
  POST /auth/owner/login   — login as a restaurant owner
  GET  /auth/me            — return profile of the authenticated user

Sessions:
  On every successful login or signup a session document is written to the
  MongoDB `sessions` collection.  The JWT remains the auth mechanism; sessions
  provide a server-side audit trail as required by Lab 2 Part 3.

bcrypt:
  Passwords are hashed/verified via passlib CryptContext(schemes=["bcrypt"]).
  No change from Lab 1 — only the storage layer (MySQL → MongoDB) changed.
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..config import settings
from ..database import get_db, _next_id, _ns
from ..schemas.auth import (
    LoginRequest,
    MeResponse,
    OwnerSignupRequest,
    TokenResponse,
    UserSignupRequest,
)
from ..utils.auth import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _build_token_response(user, token: str) -> TokenResponse:
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


def _create_session(db, user_id: int) -> None:
    """Write a server-side session record to the sessions collection."""
    db.sessions.insert_one({
        "user_id": user_id,
        "jti": str(uuid.uuid4()),
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    })


def _signup(db, name: str, email: str, password: str, role: str) -> TokenResponse:
    """Create a user document with embedded preferences, then return a JWT."""
    if db.users.find_one({"email": email}):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_id = _next_id(db, "users")
    now = datetime.utcnow()
    doc = {
        "_id": user_id,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "phone": None,
        "about_me": None,
        "city": None,
        "state": None,
        "country": None,
        "languages": None,
        "gender": None,
        "profile_photo_url": None,
        # Preferences embedded — replaces separate user_preferences table
        "preferences": {
            "cuisine_preferences": [],
            "price_range": None,
            "search_radius": 10,
            "preferred_locations": [],
            "dietary_restrictions": [],
            "ambiance_preferences": [],
            "sort_preference": "rating",
            "updated_at": now,
        },
        "created_at": now,
        "updated_at": now,
    }
    db.users.insert_one(doc)
    user = _ns(doc)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    _create_session(db, user.id)
    return _build_token_response(user, token)


def _login(db, email: str, password: str, required_role: str) -> TokenResponse:
    """Verify credentials, enforce role match, and return a JWT."""
    user_doc = db.users.find_one({"email": email})
    user = _ns(user_doc)

    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if user.role != required_role:
        role_label = "reviewer" if required_role == "user" else "restaurant owner"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This account is not registered as a {role_label}. "
                   f"Please use the correct login endpoint.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    _create_session(db, user.id)
    return _build_token_response(user, token)


# ---------------------------------------------------------------------------
# OAuth2 token endpoint — Swagger UI only
# ---------------------------------------------------------------------------

@router.post("/token", include_in_schema=False)
def oauth2_token(form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user_doc = db.users.find_one({"email": form.username})
    user = _ns(user_doc)
    if user:
        try:
            result = _login(db, form.username, form.password, required_role=user.role)
            return {"access_token": result.access_token, "token_type": "bearer"}
        except HTTPException:
            pass
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ---------------------------------------------------------------------------
# Reviewer (user) endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/user/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a reviewer account",
    responses={409: {"description": "Email already registered"}},
)
def user_signup(payload: UserSignupRequest, db=Depends(get_db)):
    return _signup(db, payload.name, payload.email, payload.password, role="user")


@router.post(
    "/user/login",
    response_model=TokenResponse,
    summary="Login as a reviewer",
    responses={401: {"description": "Wrong email or password"}},
)
def user_login(payload: LoginRequest, db=Depends(get_db)):
    return _login(db, payload.email, payload.password, required_role="user")


# ---------------------------------------------------------------------------
# Restaurant owner endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/owner/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a restaurant-owner account",
    responses={409: {"description": "Email already registered"}},
)
def owner_signup(payload: OwnerSignupRequest, db=Depends(get_db)):
    return _signup(db, payload.name, payload.email, payload.password, role="owner")


@router.post(
    "/owner/login",
    response_model=TokenResponse,
    summary="Login as a restaurant owner",
    responses={401: {"description": "Wrong email or password"}},
)
def owner_login(payload: LoginRequest, db=Depends(get_db)):
    return _login(db, payload.email, payload.password, required_role="owner")


# ---------------------------------------------------------------------------
# Shared — both roles
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user",
    responses={401: {"description": "Missing or invalid token"}},
)
def get_me(current_user=Depends(get_current_user)):
    return dict(current_user)
