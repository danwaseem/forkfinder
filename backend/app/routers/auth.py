"""
Authentication router.

Endpoints:
  POST /auth/user/signup   — register a reviewer account
  POST /auth/user/login    — login as a reviewer
  POST /auth/owner/signup  — register a restaurant-owner account
  POST /auth/owner/login   — login as a restaurant owner
  GET  /auth/me            — return profile of the authenticated user

Role enforcement:
  /auth/user/signup  and /auth/user/login  fix role = "user"  (reviewer).
  /auth/owner/signup and /auth/owner/login fix role = "owner" (restaurant owner).
  Logging in via the wrong role endpoint returns 403, so owner tokens and
  reviewer tokens cannot be obtained by calling the wrong endpoint.

Logout strategy:
  JWT is stateless. To log out, the client discards the token (removes it from
  localStorage). No server-side session invalidation is required.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, UserPreferences
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
# Private helpers — not exposed as routes
# ---------------------------------------------------------------------------

def _build_token_response(user: User, token: str) -> TokenResponse:
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
    )


def _signup(db: Session, name: str, email: str, password: str, role: str) -> TokenResponse:
    """Create a user row + empty preferences row, then return a JWT."""
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()  # populate user.id without committing
    db.add(UserPreferences(user_id=user.id))
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return _build_token_response(user, token)


def _login(db: Session, email: str, password: str, required_role: str) -> TokenResponse:
    """Verify credentials, enforce role match, and return a JWT."""
    user = db.query(User).filter(User.email == email).first()

    # Deliberately ambiguous — prevents user-enumeration attacks
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
    return _build_token_response(user, token)


# ---------------------------------------------------------------------------
# OAuth2 token endpoint — used exclusively by Swagger UI "Authorize" button.
# Accepts form-data (username + password) per OAuth2 Password Flow spec.
# username is treated as email; tries reviewer login first, then owner.
# The regular JSON login endpoints below are unchanged.
# ---------------------------------------------------------------------------

@router.post(
    "/token",
    include_in_schema=False,  # hide from Swagger operation list — it's only the auth target
)
def oauth2_token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2-compatible token endpoint for Swagger UI authorization."""
    # Try reviewer role first, then owner — whichever matches.
    user = db.query(User).filter(User.email == form.username).first()
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
    responses={
        201: {
            "description": "Account created, JWT returned",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<jwt>",
                        "token_type": "bearer",
                        "user_id": 1,
                        "name": "Jane Doe",
                        "email": "jane@example.com",
                        "role": "user",
                    }
                }
            },
        },
        409: {"description": "Email already registered"},
        422: {"description": "Validation error (e.g. password too short)"},
    },
)
def user_signup(payload: UserSignupRequest, db: Session = Depends(get_db)):
    """
    Create a new **reviewer** account and return an access token.

    - Role is fixed to `"user"` — the caller cannot override it.
    - Password must be at least 8 characters.
    - On success, store the returned `access_token` and send it as
      `Authorization: Bearer <token>` on subsequent requests.

    **Example request body:**
    ```json
    { "name": "Jane Doe", "email": "jane@example.com", "password": "secret123" }
    ```
    """
    return _signup(db, payload.name, payload.email, payload.password, role="user")


@router.post(
    "/user/login",
    response_model=TokenResponse,
    summary="Login as a reviewer",
    responses={
        200: {"description": "JWT returned"},
        401: {"description": "Wrong email or password"},
        403: {"description": "Account exists but is an owner account, not a reviewer"},
    },
)
def user_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a **reviewer** and return an access token.

    Returns `403` if the credentials are correct but the account was registered
    as a restaurant owner — the caller should use `/auth/owner/login` instead.

    **Example request body:**
    ```json
    { "email": "jane@example.com", "password": "secret123" }
    ```
    """
    return _login(db, payload.email, payload.password, required_role="user")


# ---------------------------------------------------------------------------
# Restaurant owner endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/owner/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a restaurant-owner account",
    responses={
        201: {
            "description": "Owner account created, JWT returned",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "<jwt>",
                        "token_type": "bearer",
                        "user_id": 2,
                        "name": "Mario Rossi",
                        "email": "mario@ristorantebello.com",
                        "role": "owner",
                    }
                }
            },
        },
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
    },
)
def owner_signup(payload: OwnerSignupRequest, db: Session = Depends(get_db)):
    """
    Create a new **restaurant owner** account and return an access token.

    - Role is fixed to `"owner"` — the caller cannot override it.
    - Owner accounts can claim and manage restaurants via `/owner/*` endpoints.

    **Example request body:**
    ```json
    { "name": "Mario Rossi", "email": "mario@ristorantebello.com", "password": "ownerpass1" }
    ```
    """
    return _signup(db, payload.name, payload.email, payload.password, role="owner")


@router.post(
    "/owner/login",
    response_model=TokenResponse,
    summary="Login as a restaurant owner",
    responses={
        200: {"description": "JWT returned"},
        401: {"description": "Wrong email or password"},
        403: {"description": "Account exists but is a reviewer account, not an owner"},
    },
)
def owner_login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a **restaurant owner** and return an access token.

    Returns `403` if the credentials are correct but the account was registered
    as a reviewer — the caller should use `/auth/user/login` instead.

    **Example request body:**
    ```json
    { "email": "mario@ristorantebello.com", "password": "ownerpass1" }
    ```
    """
    return _login(db, payload.email, payload.password, required_role="owner")


# ---------------------------------------------------------------------------
# Shared — works for both roles
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user",
    responses={
        200: {
            "description": "Authenticated user profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Jane Doe",
                        "email": "jane@example.com",
                        "role": "user",
                        "profile_photo_url": None,
                        "created_at": "2026-03-18T10:00:00",
                    }
                }
            },
        },
        401: {"description": "Missing or invalid token"},
    },
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the profile of the currently authenticated user.

    Works for both reviewers (`role: "user"`) and owners (`role: "owner"`).
    Requires `Authorization: Bearer <token>` header.
    """
    return current_user
