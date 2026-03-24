"""
Favorites tests — add, remove, list, duplicate enforcement.

Coverage:
  - POST /favorites/{id}   — add, already-added 400, nonexistent 404
  - DELETE /favorites/{id} — remove, not-favorited 400, nonexistent 404
  - GET  /favorites/me     — list, ordered, unauthenticated
  - is_favorited flag on restaurant list and detail endpoints
"""

import pytest
from .conftest import auth_headers, make_user, make_restaurant


class TestAddFavorite:
    def test_add_success(self, client, reviewer, restaurant):
        resp = client.post(f"/favorites/{restaurant.id}",
                           headers=auth_headers(reviewer))
        assert resp.status_code == 201
        body = resp.json()
        assert body["is_favorited"] is True
        assert body["restaurant_id"] == restaurant.id

    def test_add_duplicate_returns_400(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        assert resp.status_code == 400

    def test_add_nonexistent_restaurant_returns_404(self, client, reviewer):
        resp = client.post("/favorites/999999", headers=auth_headers(reviewer))
        assert resp.status_code == 404

    def test_add_requires_auth(self, client, restaurant):
        resp = client.post(f"/favorites/{restaurant.id}")
        assert resp.status_code == 401

    def test_owner_can_also_favorite(self, client, owner_user, restaurant):
        resp = client.post(f"/favorites/{restaurant.id}",
                           headers=auth_headers(owner_user))
        assert resp.status_code == 201


class TestRemoveFavorite:
    def test_remove_success(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.delete(f"/favorites/{restaurant.id}",
                             headers=auth_headers(reviewer))
        assert resp.status_code == 200
        assert resp.json()["is_favorited"] is False

    def test_remove_not_favorited_returns_400(self, client, reviewer, restaurant):
        resp = client.delete(f"/favorites/{restaurant.id}",
                             headers=auth_headers(reviewer))
        assert resp.status_code == 400

    def test_remove_nonexistent_restaurant_returns_404(self, client, reviewer):
        resp = client.delete("/favorites/999999", headers=auth_headers(reviewer))
        assert resp.status_code == 404

    def test_remove_requires_auth(self, client, restaurant):
        resp = client.delete(f"/favorites/{restaurant.id}")
        assert resp.status_code == 401


class TestListFavorites:
    def test_list_returns_favorited_restaurants(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.get("/favorites/me", headers=auth_headers(reviewer))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["restaurant"]["id"] == restaurant.id

    def test_empty_list_for_new_user(self, client, db):
        fresh = make_user(db, email="fresh@example.com")
        resp = client.get("/favorites/me", headers=auth_headers(fresh))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_requires_auth(self, client):
        resp = client.get("/favorites/me")
        assert resp.status_code == 401

    def test_favorites_isolated_per_user(self, client, db, restaurant):
        u1 = make_user(db, email="u1@example.com")
        u2 = make_user(db, email="u2@example.com")
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(u1))
        resp = client.get("/favorites/me", headers=auth_headers(u2))
        assert resp.json()["total"] == 0

    def test_includes_favorited_at_timestamp(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.get("/favorites/me", headers=auth_headers(reviewer))
        assert "favorited_at" in resp.json()["items"][0]


class TestIsFavoritedFlag:
    def test_is_favorited_true_for_authenticated_user(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.get(f"/restaurants/{restaurant.id}",
                          headers=auth_headers(reviewer))
        assert resp.json()["is_favorited"] is True

    def test_is_favorited_false_after_removal(self, client, reviewer, restaurant):
        client.post(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        client.delete(f"/favorites/{restaurant.id}", headers=auth_headers(reviewer))
        resp = client.get(f"/restaurants/{restaurant.id}",
                          headers=auth_headers(reviewer))
        assert resp.json()["is_favorited"] is False

    def test_is_favorited_false_for_anonymous(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}")
        assert resp.json()["is_favorited"] is False
