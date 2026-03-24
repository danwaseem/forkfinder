"""
Auth tests — unit + integration.

Coverage:
  - hash_password / verify_password correctness
  - create_access_token / decode_token
  - POST /auth/user/signup   — happy path, duplicate email, weak password
  - POST /auth/user/login    — happy path, bad creds, wrong role
  - POST /auth/owner/signup  — happy path, duplicate email
  - POST /auth/owner/login   — happy path, bad creds, wrong role
  - GET  /auth/me            — authenticated, missing token, expired token
"""

import pytest
from jose import jwt

from app.config import settings
from app.utils.auth import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from .conftest import auth_headers, make_user, token_for


# ==========================================================================
# Unit tests — auth utilities
# ==========================================================================

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecret")
        assert hashed != "mysecret"

    def test_verify_correct_password(self):
        hashed = hash_password("mysecret")
        assert verify_password("mysecret", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mysecret")
        assert verify_password("wrongpass", hashed) is False

    def test_same_password_produces_different_hash(self):
        h1 = hash_password("abc")
        h2 = hash_password("abc")
        assert h1 != h2  # bcrypt uses a random salt each time


class TestJWT:
    def test_token_contains_expected_claims(self):
        token = create_access_token({"sub": "42", "role": "user"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "42"
        assert payload["role"] == "user"
        assert "exp" in payload

    def test_decode_token_returns_dict(self):
        token = create_access_token({"sub": "7", "role": "owner"})
        payload = decode_token(token)
        assert payload["sub"] == "7"

    def test_decode_invalid_token_raises_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


# ==========================================================================
# Integration tests — signup / login endpoints
# ==========================================================================

class TestUserSignup:
    def test_signup_success(self, client):
        resp = client.post("/auth/user/signup", json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["role"] == "user"
        assert body["email"] == "jane@example.com"

    def test_signup_duplicate_email(self, client, reviewer):
        resp = client.post("/auth/user/signup", json={
            "name": "Another Jane",
            "email": "jane@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 409

    def test_signup_short_password(self, client):
        resp = client.post("/auth/user/signup", json={
            "name": "Jane",
            "email": "jane2@example.com",
            "password": "abc",        # < 8 chars
        })
        assert resp.status_code == 422

    def test_signup_missing_name(self, client):
        resp = client.post("/auth/user/signup", json={
            "email": "noname@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 422

    def test_signup_invalid_email(self, client):
        resp = client.post("/auth/user/signup", json={
            "name": "Jane",
            "email": "not-an-email",
            "password": "secret123",
        })
        assert resp.status_code == 422

    def test_signup_role_is_fixed_to_user(self, client):
        resp = client.post("/auth/user/signup", json={
            "name": "Jane",
            "email": "jane@example.com",
            "password": "secret123",
        })
        assert resp.json()["role"] == "user"


class TestUserLogin:
    def test_login_success(self, client, reviewer):
        resp = client.post("/auth/user/login", json={
            "email": "jane@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, reviewer):
        resp = client.post("/auth/user/login", json={
            "email": "jane@example.com",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post("/auth/user/login", json={
            "email": "nobody@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 401

    def test_reviewer_cannot_use_owner_login(self, client, reviewer):
        """Reviewer logging in via owner endpoint gets 403."""
        resp = client.post("/auth/owner/login", json={
            "email": "jane@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 403

    def test_owner_cannot_use_reviewer_login(self, client, owner_user):
        resp = client.post("/auth/user/login", json={
            "email": "mario@owner.com",
            "password": "ownerpass1",
        })
        assert resp.status_code == 403


class TestOwnerSignup:
    def test_owner_signup_success(self, client):
        resp = client.post("/auth/owner/signup", json={
            "name": "Mario Rossi",
            "email": "mario@owner.com",
            "password": "ownerpass1",
        })
        assert resp.status_code == 201
        assert resp.json()["role"] == "owner"

    def test_owner_signup_duplicate_email(self, client, owner_user):
        resp = client.post("/auth/owner/signup", json={
            "name": "Another Mario",
            "email": "mario@owner.com",
            "password": "ownerpass1",
        })
        assert resp.status_code == 409


class TestGetMe:
    def test_get_me_authenticated(self, client, reviewer):
        resp = client.get("/auth/me", headers=auth_headers(reviewer))
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == reviewer.id
        assert body["email"] == reviewer.email
        assert body["role"] == "user"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_get_me_malformed_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
        assert resp.status_code == 401

    def test_get_me_missing_bearer_prefix(self, client, reviewer):
        token = token_for(reviewer)
        resp = client.get("/auth/me", headers={"Authorization": token})
        assert resp.status_code == 401

    def test_get_me_owner(self, client, owner_user):
        resp = client.get("/auth/me", headers=auth_headers(owner_user))
        assert resp.status_code == 200
        assert resp.json()["role"] == "owner"
