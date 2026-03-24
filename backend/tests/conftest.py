"""
Shared fixtures for ForkFinder backend tests.

Setup:
  - SQLite in-memory (per-test) to avoid polluting the real MySQL database.
  - FastAPI TestClient with get_db overridden.
  - Helper factories: make_user(), make_restaurant(), make_review().
  - Token / auth-header helpers.

Install test dependencies before running:
  pip install pytest pytest-asyncio httpx

Run:
  cd backend
  pytest -v
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.user import User, UserPreferences
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.models.favorite import Favorite
from app.utils.auth import hash_password, create_access_token

# --------------------------------------------------------------------------
# Test database — SQLite file-per-test-session
# --------------------------------------------------------------------------

SQLITE_URL = "sqlite:///./test_forkfinder.db"
engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------------------------------
# Factory helpers
# --------------------------------------------------------------------------

def make_user(
    db,
    name="Jane Doe",
    email="jane@example.com",
    password="secret123",
    role="user",
):
    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.flush()
    db.add(UserPreferences(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


def make_restaurant(
    db,
    creator,
    name="Ristorante Bello",
    cuisine_type="Italian",
    price_range="$$",
    city="San Francisco",
    state="CA",
    avg_rating=4.5,
    review_count=10,
):
    r = Restaurant(
        name=name,
        cuisine_type=cuisine_type,
        price_range=price_range,
        city=city,
        state=state,
        country="United States",
        avg_rating=avg_rating,
        review_count=review_count,
        created_by=creator.id,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def make_review(db, user, restaurant, rating=4, comment="Really enjoyed this place."):
    from datetime import datetime
    rev = Review(
        user_id=user.id,
        restaurant_id=restaurant.id,
        rating=rating,
        comment=comment,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev


def token_for(user: User) -> str:
    return create_access_token({"sub": str(user.id), "role": user.role})


def auth_headers(user: User) -> dict:
    return {"Authorization": f"Bearer {token_for(user)}"}


# --------------------------------------------------------------------------
# Convenience fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def reviewer(db):
    return make_user(db, name="Jane Doe", email="jane@example.com", role="user")


@pytest.fixture
def reviewer2(db):
    return make_user(db, name="Bob Smith", email="bob@example.com", role="user")


@pytest.fixture
def owner_user(db):
    return make_user(db, name="Mario Rossi", email="mario@owner.com",
                     password="ownerpass1", role="owner")


@pytest.fixture
def restaurant(db, reviewer):
    return make_restaurant(db, creator=reviewer)


@pytest.fixture
def restaurant_owned(db, owner_user):
    r = make_restaurant(db, creator=owner_user, name="Claimed Bistro")
    r.claimed_by = owner_user.id
    r.is_claimed = True
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture
def review(db, reviewer, restaurant):
    return make_review(db, user=reviewer, restaurant=restaurant)
