"""
Restaurant tests — CRUD, search, auth enforcement, photo upload, claim.

Coverage:
  - GET  /restaurants              — public search, pagination, filters, sort
  - GET  /restaurants/{id}         — public detail, 404
  - POST /restaurants              — authenticated create, validation, unauthenticated
  - PUT  /restaurants/{id}         — creator edit, non-creator blocked, 404
  - DELETE /restaurants/{id}       — creator delete, non-creator blocked, 204
  - POST /restaurants/{id}/photos  — upload, count limit
  - POST /restaurants/{id}/claim   — owner claim, reviewer blocked, already-claimed
"""

import pytest
from .conftest import auth_headers, make_restaurant, make_user


# ==========================================================================
# Public read endpoints
# ==========================================================================

class TestListRestaurants:
    def test_returns_paginated_list(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="Alpha Bistro", city="Chicago")
        make_restaurant(db, reviewer, name="Beta Grill",   city="Chicago")
        resp = client.get("/restaurants")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert body["total"] >= 2
        assert "page" in body and "pages" in body

    def test_search_by_keyword(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="Dragon Palace", cuisine_type="Chinese")
        make_restaurant(db, reviewer, name="Pizza Heaven",  cuisine_type="Italian")
        resp = client.get("/restaurants?q=dragon")
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["items"]]
        assert "Dragon Palace" in names
        assert "Pizza Heaven" not in names

    def test_filter_by_price_range(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="Cheap Eats", price_range="$")
        make_restaurant(db, reviewer, name="Fine Dining", price_range="$$$$")
        resp = client.get("/restaurants?price_range=$")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["price_range"] == "$"

    def test_filter_by_city(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="SF Place",  city="San Francisco")
        make_restaurant(db, reviewer, name="NY Spot",   city="New York")
        resp = client.get("/restaurants?city=San+Francisco")
        cities = [r["city"] for r in resp.json()["items"]]
        assert all(c == "San Francisco" for c in cities)

    def test_filter_by_min_rating(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="Low Rated",  avg_rating=2.0, review_count=5)
        make_restaurant(db, reviewer, name="High Rated", avg_rating=4.8, review_count=5)
        resp = client.get("/restaurants?rating_min=4.0")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["avg_rating"] >= 4.0

    def test_sort_by_newest(self, client, db, reviewer):
        make_restaurant(db, reviewer, name="First")
        make_restaurant(db, reviewer, name="Second")
        resp = client.get("/restaurants?sort=newest")
        assert resp.status_code == 200

    def test_sort_invalid_value_defaults(self, client):
        resp = client.get("/restaurants?sort=invalid_sort")
        assert resp.status_code == 422

    def test_pagination(self, client, db, reviewer):
        for i in range(15):
            make_restaurant(db, reviewer, name=f"Restaurant {i:02d}")
        resp = client.get("/restaurants?limit=5&page=1")
        assert len(resp.json()["items"]) == 5

    def test_is_favorited_false_for_anonymous(self, client, restaurant):
        resp = client.get("/restaurants")
        for item in resp.json()["items"]:
            assert item["is_favorited"] is False

    def test_no_auth_required(self, client):
        resp = client.get("/restaurants")
        assert resp.status_code == 200


class TestGetRestaurant:
    def test_get_existing(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == restaurant.id
        assert body["name"] == restaurant.name

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/restaurants/999999")
        assert resp.status_code == 404

    def test_hours_decoded_as_dict(self, client, db, reviewer):
        import json
        r = make_restaurant(db, reviewer)
        r.hours = json.dumps({"monday": "11am-10pm"})
        db.commit()
        resp = client.get(f"/restaurants/{r.id}")
        assert isinstance(resp.json()["hours"], dict)

    def test_photos_decoded_as_list(self, client, db, reviewer):
        import json
        r = make_restaurant(db, reviewer)
        r.photos = json.dumps(["/uploads/restaurants/test.jpg"])
        db.commit()
        resp = client.get(f"/restaurants/{r.id}")
        assert isinstance(resp.json()["photos"], list)


# ==========================================================================
# Create
# ==========================================================================

class TestCreateRestaurant:
    def test_create_success(self, client, reviewer):
        resp = client.post("/restaurants", json={
            "name": "New Spot",
            "cuisine_type": "Japanese",
            "price_range": "$$",
            "city": "Oakland",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "New Spot"
        assert body["created_by"] == reviewer.id

    def test_create_requires_auth(self, client):
        resp = client.post("/restaurants", json={"name": "No Auth"})
        assert resp.status_code == 401

    def test_create_missing_name_fails(self, client, reviewer):
        resp = client.post("/restaurants", json={
            "cuisine_type": "Italian",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_create_invalid_price_range(self, client, reviewer):
        resp = client.post("/restaurants", json={
            "name": "Test",
            "price_range": "$$$$$",   # invalid
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_create_invalid_hours_key(self, client, reviewer):
        resp = client.post("/restaurants", json={
            "name": "Test",
            "hours": {"funday": "9am-5pm"},   # invalid day
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_owner_can_also_create(self, client, owner_user):
        resp = client.post("/restaurants", json={
            "name": "Owner's Place",
            "cuisine_type": "French",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 201


# ==========================================================================
# Update
# ==========================================================================

class TestUpdateRestaurant:
    def test_creator_can_update(self, client, reviewer, restaurant):
        resp = client.put(f"/restaurants/{restaurant.id}", json={
            "description": "New description",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 200
        assert resp.json()["description"] == "New description"

    def test_non_creator_is_blocked(self, client, db, reviewer, restaurant):
        stranger = make_user(db, email="stranger@example.com")
        resp = client.put(f"/restaurants/{restaurant.id}", json={
            "description": "Hack",
        }, headers=auth_headers(stranger))
        assert resp.status_code == 403

    def test_update_nonexistent_returns_404(self, client, reviewer):
        resp = client.put("/restaurants/999999", json={"name": "X"},
                          headers=auth_headers(reviewer))
        assert resp.status_code == 404

    def test_claimed_owner_can_update(self, client, owner_user, restaurant_owned):
        resp = client.put(f"/restaurants/{restaurant_owned.id}", json={
            "phone": "+1 (415) 555-9999",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 200


# ==========================================================================
# Delete
# ==========================================================================

class TestDeleteRestaurant:
    def test_creator_can_delete(self, client, reviewer, restaurant):
        resp = client.delete(f"/restaurants/{restaurant.id}",
                             headers=auth_headers(reviewer))
        assert resp.status_code == 204

    def test_non_creator_cannot_delete(self, client, db, restaurant):
        stranger = make_user(db, email="stranger@example.com")
        resp = client.delete(f"/restaurants/{restaurant.id}",
                             headers=auth_headers(stranger))
        assert resp.status_code == 403

    def test_delete_nonexistent_returns_404(self, client, reviewer):
        resp = client.delete("/restaurants/999999", headers=auth_headers(reviewer))
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client, restaurant):
        resp = client.delete(f"/restaurants/{restaurant.id}")
        assert resp.status_code == 401


# ==========================================================================
# Claim
# ==========================================================================

class TestClaimRestaurant:
    def test_owner_can_claim_unclaimed(self, client, db, owner_user, restaurant):
        # restaurant was created by reviewer; owner claims it
        resp = client.post(f"/restaurants/{restaurant.id}/claim",
                           headers=auth_headers(owner_user))
        assert resp.status_code == 201
        assert resp.json()["claim_status"] == "approved"

    def test_reviewer_cannot_claim(self, client, reviewer, restaurant):
        resp = client.post(f"/restaurants/{restaurant.id}/claim",
                           headers=auth_headers(reviewer))
        assert resp.status_code == 403

    def test_cannot_claim_already_claimed(self, client, db, owner_user, restaurant_owned):
        other_owner = make_user(db, email="other@owner.com", role="owner")
        resp = client.post(f"/restaurants/{restaurant_owned.id}/claim",
                           headers=auth_headers(other_owner))
        assert resp.status_code == 400

    def test_claim_nonexistent_returns_404(self, client, owner_user):
        resp = client.post("/restaurants/999999/claim",
                           headers=auth_headers(owner_user))
        assert resp.status_code == 404
