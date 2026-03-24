"""
Auth utilities: password hashing, JWT creation/decoding, FastAPI dependencies.

JWT payload shape:
  { "sub": "<user_id>", "role": "<user|owner>", "exp": <unix_ts> }

Dependencies:
  get_current_user     — any authenticated user (user or owner); raises 401 if missing
  get_optional_user    — same, but returns None instead of raising when no token present
  require_owner        — authenticated user whose role == "owner"
  require_user         — authenticated user whose role == "user" (reviewer)
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# tokenUrl points to the OAuth2-compatible form-data endpoint used by Swagger UI.
# The regular login endpoints (/auth/user/login, /auth/owner/login) accept JSON
# and are unchanged; only the Swagger "Authorize" button uses /auth/token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Same scheme but auto_error=False — returns None instead of raising 401
# when no token is present.  Used by public endpoints that enrich responses
# for authenticated callers (e.g. is_favorited on restaurant listings).
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/auth/token", auto_error=False
)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Encode a JWT.

    ``data`` should include at minimum ``{"sub": str(user.id), "role": user.role}``.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Dependency: resolve the Bearer token to a User row.

    Raises 401 if the token is missing, malformed, expired, or the user
    no longer exists in the database.
    """
    from ..models.user import User

    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload.",
        )

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[object]:
    """
    Dependency: resolve the Bearer token to a User if present, else return None.

    Use on public endpoints that can optionally enrich their response for
    authenticated callers — e.g. ``is_favorited`` on restaurant listings.
    Never raises 401.
    """
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None


def require_owner(user=Depends(get_current_user)):
    """
    Dependency: require the authenticated user to be a restaurant owner.

    Raises 403 if the user's role is not ``"owner"``.
    Use on any endpoint under ``/owner/*``.
    """
    if user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required. Please log in with a restaurant-owner account.",
        )
    return user


def require_user(user=Depends(get_current_user)):
    """
    Dependency: require the authenticated user to be a reviewer (role == "user").

    Raises 403 if the user's role is not ``"user"``.
    Use on endpoints that should not be accessible to restaurant owners.
    """
    if user.role != "user":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reviewer access required. This action is not available to restaurant owners.",
        )
    return user
