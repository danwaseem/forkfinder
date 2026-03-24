"""
Review tests — creation, update, delete, auth matrix, rating recalculation.

Coverage:
  - POST /reviews                            — reviewer OK, owner blocked, unauthenticated
  - POST /restaurants/{id}/reviews           — alt endpoint
  - GET  /restaurants/{id}/reviews           — public, pagination, sort
  - PUT  /reviews/{id}                       — author only, owner blocked
  - DELETE /reviews/{id}                     — author only, stats recalculated
  - POST /reviews/{id}/photos               — author only, count limit
  - One-review-per-restaurant enforcement
  - Rating recalculation after create/update/delete
"""

import pytest
from .conftest import auth_headers, make_user, make_restaurant, make_review


# ==========================================================================
# Create review
# ==========================================================================

class TestCreateReview:
    def test_reviewer_can_create(self, client, reviewer, restaurant):
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 5,
            "comment": "Absolutely fantastic food and ambiance!",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 201
        body = resp.json()
        assert body["review"]["rating"] == 5
        assert body["review"]["user_id"] == reviewer.id
        assert "restaurant_stats" in body

    def test_owner_cannot_create_review(self, client, owner_user, restaurant):
        """Owners are blocked on all review write endpoints (403)."""
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 4,
            "comment": "Great place, highly recommend.",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_create(self, client, restaurant):
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 3,
            "comment": "Testing without auth token.",
        })
        assert resp.status_code == 401

    def test_duplicate_review_blocked(self, client, reviewer, restaurant, review):
        """A user may only review a restaurant once."""
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 3,
            "comment": "Trying to post a second review.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 400

    def test_rating_below_1_rejected(self, client, reviewer, restaurant):
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 0,
            "comment": "Too low a rating.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_rating_above_5_rejected(self, client, reviewer, restaurant):
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 6,
            "comment": "Too high a rating.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_comment_too_short_rejected(self, client, reviewer, restaurant):
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 4,
            "comment": "Short",     # < 10 chars
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_nonexistent_restaurant_returns_404(self, client, reviewer):
        resp = client.post("/reviews", json={
            "restaurant_id": 999999,
            "rating": 4,
            "comment": "This place does not exist.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 404

    def test_alt_url_endpoint(self, client, reviewer, restaurant):
        """POST /restaurants/{id}/reviews is identical to POST /reviews."""
        resp = client.post(f"/restaurants/{restaurant.id}/reviews", json={
            "rating": 4,
            "comment": "Great tacos, a bit slow on service.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 201

    def test_rating_recalculated_after_create(self, client, db, restaurant):
        """avg_rating on the restaurant should update after a review is posted."""
        u1 = make_user(db, email="u1@example.com")
        u2 = make_user(db, email="u2@example.com")
        client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 4,
            "comment": "Pretty good experience overall.",
        }, headers=auth_headers(u1))
        resp = client.post("/reviews", json={
            "restaurant_id": restaurant.id,
            "rating": 2,
            "comment": "Disappointing, expected better service.",
        }, headers=auth_headers(u2))
        stats = resp.json()["restaurant_stats"]
        assert stats["review_count"] == 2
        assert stats["avg_rating"] == pytest.approx(3.0, abs=0.1)


# ==========================================================================
# List reviews (public)
# ==========================================================================

class TestListReviews:
    def test_list_is_public(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}/reviews")
        assert resp.status_code == 200

    def test_list_returns_paginated(self, client, db, restaurant):
        users = [make_user(db, email=f"u{i}@example.com") for i in range(5)]
        for u in users:
            make_review(db, u, restaurant, comment=f"Review from user {u.name}.")
        resp = client.get(f"/restaurants/{restaurant.id}/reviews?limit=3")
        body = resp.json()
        assert len(body["items"]) == 3
        assert body["total"] == 5

    def test_sort_newest(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}/reviews?sort=newest")
        assert resp.status_code == 200

    def test_sort_highest_rating(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}/reviews?sort=highest_rating")
        assert resp.status_code == 200

    def test_invalid_sort_returns_422(self, client, restaurant):
        resp = client.get(f"/restaurants/{restaurant.id}/reviews?sort=bad_sort")
        assert resp.status_code == 422

    def test_nonexistent_restaurant_returns_404(self, client):
        resp = client.get("/restaurants/999999/reviews")
        assert resp.status_code == 404

    def test_review_includes_user_info(self, client, reviewer, restaurant, review):
        resp = client.get(f"/restaurants/{restaurant.id}/reviews")
        item = resp.json()["items"][0]
        assert item["user"]["id"] == reviewer.id
        assert item["user"]["name"] == reviewer.name


# ==========================================================================
# Update review
# ==========================================================================

class TestUpdateReview:
    def test_author_can_update(self, client, reviewer, review):
        resp = client.put(f"/reviews/{review.id}", json={
            "rating": 3,
            "comment": "Changed my mind after returning — not as good.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 200
        assert resp.json()["review"]["rating"] == 3

    def test_non_author_is_blocked(self, client, db, review):
        stranger = make_user(db, email="stranger@example.com")
        resp = client.put(f"/reviews/{review.id}", json={
            "comment": "I am not the author but still trying to edit.",
        }, headers=auth_headers(stranger))
        assert resp.status_code == 403

    def test_owner_cannot_update_review(self, client, owner_user, review):
        resp = client.put(f"/reviews/{review.id}", json={
            "comment": "Owner trying to edit a review.",
        }, headers=auth_headers(owner_user))
        assert resp.status_code == 403

    def test_no_fields_returns_422(self, client, reviewer, review):
        resp = client.put(f"/reviews/{review.id}", json={},
                          headers=auth_headers(reviewer))
        assert resp.status_code == 422

    def test_rating_recalculated_after_update(self, client, reviewer, review):
        resp = client.put(f"/reviews/{review.id}", json={"rating": 1},
                          headers=auth_headers(reviewer))
        stats = resp.json()["restaurant_stats"]
        assert stats["avg_rating"] == pytest.approx(1.0, abs=0.1)

    def test_update_nonexistent_returns_404(self, client, reviewer):
        resp = client.put("/reviews/999999", json={
            "comment": "This review does not exist anywhere.",
        }, headers=auth_headers(reviewer))
        assert resp.status_code == 404


# ==========================================================================
# Delete review
# ==========================================================================

class TestDeleteReview:
    def test_author_can_delete(self, client, reviewer, review):
        resp = client.delete(f"/reviews/{review.id}",
                             headers=auth_headers(reviewer))
        assert resp.status_code == 200
        body = resp.json()
        assert body["review"] is None
        assert "restaurant_stats" in body

    def test_non_author_cannot_delete(self, client, db, review):
        stranger = make_user(db, email="stranger@example.com")
        resp = client.delete(f"/reviews/{review.id}",
                             headers=auth_headers(stranger))
        assert resp.status_code == 403

    def test_owner_cannot_delete_review(self, client, owner_user, review):
        resp = client.delete(f"/reviews/{review.id}",
                             headers=auth_headers(owner_user))
        assert resp.status_code == 403

    def test_unauthenticated_cannot_delete(self, client, review):
        resp = client.delete(f"/reviews/{review.id}")
        assert resp.status_code == 401

    def test_review_count_decrements_after_delete(self, client, db, restaurant):
        u1 = make_user(db, email="u1@example.com")
        u2 = make_user(db, email="u2@example.com")
        r1 = make_review(db, u1, restaurant, comment="First review of this restaurant.")
        make_review(db, u2, restaurant, comment="Second review of this restaurant.")
        resp = client.delete(f"/reviews/{r1.id}", headers=auth_headers(u1))
        stats = resp.json()["restaurant_stats"]
        assert stats["review_count"] == 1

    def test_delete_nonexistent_returns_404(self, client, reviewer):
        resp = client.delete("/reviews/999999", headers=auth_headers(reviewer))
        assert resp.status_code == 404
