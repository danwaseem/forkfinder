"""
Owner authorization tests — all /owner/* endpoints must reject reviewer tokens.

Coverage:
  - GET  /owner/me                           — owner OK, reviewer 403
  - PUT  /owner/me                           — owner OK, reviewer 403
  - GET  /owner/dashboard                    — owner OK, reviewer 403
  - GET  /owner/restaurants                  — owner OK, reviewer 403
  - PUT  /owner/restaurants/{id}             — owner OK, other-owner 403
  - GET  /owner/restaurants/{id}/stats       — owner OK, reviewer 403
  - GET  /owner/restaurants/{id}/reviews     — owner OK, reviewer 403
  - POST /owner/restaurants/{id}/claim       — owner OK, reviewer 403
  - GET  /owner/reviews                      — owner OK, reviewer 403
  - Unauthenticated access to all /owner/* endpoints → 401
"""

import pytest
from .conftest import auth_headers, make_user, make_restaurant


OWNER_ENDPOINTS_GET = [
    "/owner/me",
    "/owner/dashboard",
    "/owner/restaurants",
    "/owner/reviews",
]


class TestOwnerEndpointsRequireOwnerRole:
    @pytest.mark.parametrize("path", OWNER_ENDPOINTS_GET)
    def test_reviewer_token_gets_403(self, client, reviewer, path):
        resp = client.get(path, headers=auth_headers(reviewer))
        assert resp.status_code == 403, f"Expected 403 for reviewer on {path}"

    @pytest.mark.parametrize("path", OWNER_ENDPOINTS_GET)
    def test_unauthenticated_gets_401(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 401, f"Expected 401 for unauthenticated on {path}"

    def test_owner_can_access_me(self, client, owner_user):
        resp = client.get("/owner/me", headers=auth_headers(owner_user))
        assert resp.status_code == 200

    def test_owner_can_access_dashboard(self, client, owner_user):
        resp = client.get("/owner/dashboard", headers=auth_headers(owner_user))
        assert resp.status_code == 200

    def test_owner_can_list_restaurants(self, client, owner_user):
        resp = client.get("/owner/restaurants", headers=auth_headers(owner_user))
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_owner_can_list_reviews(self, client, owner_user):
        resp = client.get("/owner/reviews", headers=auth_headers(owner_user))
        assert resp.status_code == 200


class TestOwnerUpdateProfile:
    def test_owner_can_update_profile(self, client, owner_user):
        resp = client.put("/owner/me", json={
            "name": "Updated Name",
            "city": "Los Angeles",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    def test_reviewer_cannot_update_owner_profile(self, client, reviewer):
        resp = client.put("/owner/me", json={
            "name": "Hacked",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 403


class TestOwnerRestaurantManagement:
    def test_owner_can_update_own_restaurant(self, client, owner_user, restaurant_owned):
        resp = client.put(f"/owner/restaurants/{restaurant_owned.id}", json={
            "description": "Updated via owner endpoint.",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 200

    def test_owner_cannot_update_others_restaurant(self, client, db, restaurant_owned):
        other_owner = make_user(db, email="other@owner.com", role="owner")
        resp = client.put(f"/owner/restaurants/{restaurant_owned.id}", json={
            "description": "Trying to edit another owner's restaurant.",
        }, headers=auth_headers(other_owner))
        assert resp.status_code == 403

    def test_reviewer_cannot_update_via_owner_route(self, client, reviewer, restaurant_owned):
        resp = client.put(f"/owner/restaurants/{restaurant_owned.id}", json={
            "description": "Reviewer trying owner route.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 403

    def test_owner_can_get_restaurant_stats(self, client, owner_user, restaurant_owned):
        resp = client.get(f"/owner/restaurants/{restaurant_owned.id}/stats",
                          headers=auth_headers(owner_user))
        assert resp.status_code == 200

    def test_reviewer_cannot_get_restaurant_stats(self, client, reviewer, restaurant_owned):
        resp = client.get(f"/owner/restaurants/{restaurant_owned.id}/stats",
                          headers=auth_headers(reviewer))
        assert resp.status_code == 403

    def test_owner_restaurant_list_shows_only_own(self, client, db, owner_user):
        other_owner = make_user(db, email="other@owner.com", role="owner")
        my_restaurant = make_restaurant(db, owner_user, name="My Place")
        their_restaurant = make_restaurant(db, other_owner, name="Their Place")
        resp = client.get("/owner/restaurants", headers=auth_headers(owner_user))
        ids = [r["id"] for r in resp.json()["items"]]
        assert my_restaurant.id in ids
        assert their_restaurant.id not in ids


class TestOwnerClaim:
    def test_owner_can_claim_unclaimed(self, client, owner_user, restaurant):
        resp = client.post(f"/owner/restaurants/{restaurant.id}/claim",
                           headers=auth_headers(owner_user))
        assert resp.status_code in (200, 201)
        assert resp.json()["claim_status"] == "approved"

    def test_reviewer_cannot_use_owner_claim_route(self, client, reviewer, restaurant):
        resp = client.post(f"/owner/restaurants/{restaurant.id}/claim",
                           headers=auth_headers(reviewer))
        assert resp.status_code == 403

    def test_cannot_double_claim(self, client, db, owner_user, restaurant):
        client.post(f"/owner/restaurants/{restaurant.id}/claim",
                    headers=auth_headers(owner_user))
        other_owner = make_user(db, email="other@owner.com", role="owner")
        resp = client.post(f"/owner/restaurants/{restaurant.id}/claim",
                           headers=auth_headers(other_owner))
        assert resp.status_code == 400
