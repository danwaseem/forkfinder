#!/usr/bin/env python3
"""
ForkFinder demo seed data script for MongoDB.

Usage (run from the backend/ directory):
  python seed_data.py          # insert seed data (safe – skips if data exists)
  python seed_data.py --wipe   # drop all seed data first, then re-seed
  python seed_data.py --sql    # print note only (no DB writes)
  python seed_data.py --recalc # recompute restaurant aggregates from reviews

Prerequisites:
  pip install -r requirements.txt
  # Ensure backend/.env has valid MongoDB settings:
  #   MONGODB_URL=...
  #   MONGODB_DB_NAME=...
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, ".")  # allow imports from app/

from app.database import get_db, _next_id
from app.utils.auth import hash_password


# ---------------------------------------------------------------------------
# Timestamps  (spread over the past 6 months for realistic history)
# ---------------------------------------------------------------------------

def _ago(**kwargs) -> datetime:
    return datetime.utcnow() - timedelta(**kwargs)


# ---------------------------------------------------------------------------
# Raw data definitions
# ---------------------------------------------------------------------------
# Keep your existing USERS / PREFERENCES / RESTAURANTS / REVIEWS / FAVORITES /
# CONVERSATIONS constants exactly as they are in your current file.
# ---------------------------------------------------------------------------

USERS = [...]  # keep existing value
PREFERENCES = {
    "user@demo.com": dict(
        cuisine_preferences=json.dumps(["Italian", "Japanese", "French"]),
        price_range="$$",
        search_radius=15,
        preferred_locations=json.dumps(["San Francisco", "Oakland"]),
        dietary_restrictions=json.dumps([]),
        ambiance_preferences=json.dumps(["Romantic", "Casual", "Fine Dining"]),
        sort_preference="rating",
    ),
    "marcus@demo.com": dict(
        cuisine_preferences=json.dumps(["American", "BBQ", "Mexican"]),
        price_range="$",
        search_radius=20,
        preferred_locations=json.dumps(["Oakland", "San Francisco"]),
        dietary_restrictions=json.dumps([]),
        ambiance_preferences=json.dumps(["Sports Bar", "Casual", "Quick Bite"]),
        sort_preference="most_reviewed",
    ),
    "priya@demo.com": dict(
        cuisine_preferences=json.dumps(["Indian", "Mediterranean", "Vegan", "Thai"]),
        price_range="$$",
        search_radius=10,
        preferred_locations=json.dumps(["San Francisco"]),
        dietary_restrictions=json.dumps(["Vegetarian"]),
        ambiance_preferences=json.dumps(["Casual", "Outdoor Seating", "Family-Friendly"]),
        sort_preference="rating",
    ),
    "alex@demo.com": dict(
        cuisine_preferences=json.dumps(["French", "Japanese", "Korean", "Seafood"]),
        price_range="$$$",
        search_radius=25,
        preferred_locations=json.dumps(["San Francisco"]),
        dietary_restrictions=json.dumps([]),
        ambiance_preferences=json.dumps(["Fine Dining", "Romantic", "Rooftop"]),
        sort_preference="rating",
    ),
    "emily@demo.com": dict(
        cuisine_preferences=json.dumps(["Chinese", "Japanese", "Vietnamese", "Korean"]),
        price_range="$$",
        search_radius=12,
        preferred_locations=json.dumps(["San Francisco", "Oakland"]),
        dietary_restrictions=json.dumps([]),
        ambiance_preferences=json.dumps(["Casual", "Outdoor Seating", "Brunch Spot"]),
        sort_preference="newest",
    ),
}
RESTAURANTS = [...]  # keep existing value
REVIEWS = [...]  # keep existing value
FAVORITES = [...]  # keep existing value
CONVERSATIONS = [...]  # keep existing value


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _maybe_json_load(value: Any) -> Any:
    """Convert JSON-encoded strings used by legacy seed data into native Python types."""
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not stripped:
        return value
    if stripped[0] not in "[{":
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _normalize_prefs(prefs: dict[str, Any]) -> dict[str, Any]:
    return {k: _maybe_json_load(v) for k, v in prefs.items()}


def _normalize_restaurant_data(rdata: dict[str, Any]) -> dict[str, Any]:
    doc = dict(rdata)
    if "hours" in doc:
        doc["hours"] = _maybe_json_load(doc["hours"])
    if "photos" in doc:
        doc["photos"] = _maybe_json_load(doc["photos"])
    return doc


def _seed_metadata() -> dict[str, Any]:
    return {
        "seed_source": "seed_data.py",
        "seeded_at": datetime.utcnow(),
    }


# ---------------------------------------------------------------------------
# Destructive wipe
# ---------------------------------------------------------------------------

def _wipe(db):
    print("Wiping existing seed data...")

    db.conversations.delete_many({})
    db.favorites.delete_many({})
    db.reviews.delete_many({})
    db.restaurant_claims.delete_many({})
    db.restaurants.delete_many({})
    db.users.delete_many({})

    db.counters.delete_many(
        {
            "_id": {
                "$in": [
                    "users",
                    "restaurants",
                    "restaurant_claims",
                    "reviews",
                    "favorites",
                    "conversations",
                ]
            }
        }
    )

    print("Done.")


# ---------------------------------------------------------------------------
# Aggregate recalculation
# ---------------------------------------------------------------------------

def _recalc_restaurant_rating(db, restaurant_id: int) -> tuple[int, float]:
    reviews = list(db.reviews.find({"restaurant_id": restaurant_id}, {"rating": 1}))
    count = len(reviews)
    avg = round(sum(r["rating"] for r in reviews) / count, 2) if count else 0.0
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"review_count": count, "avg_rating": avg, "updated_at": datetime.utcnow()}},
    )
    return count, avg


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def _seed(db, wipe: bool):
    if wipe:
        _wipe(db)

    if db.users.count_documents({}) > 0:
        print("Database already has users — skipping seed. Use --wipe to reset.")
        return

    pw = hash_password("password")

    # --- Users ---
    print("Creating users...")
    user_map: dict[str, dict[str, Any]] = {}
    for idx, u in enumerate(USERS):
        user_id = _next_id(db, "users")
        prefs_data = _normalize_prefs(PREFERENCES.get(u["email"], {}))
        user_doc = {
            "_id": user_id,
            **u,
            "password_hash": pw,
            "preferences": prefs_data,
            "created_at": _ago(days=180 - idx * 10),
            "updated_at": _ago(days=180 - idx * 10),
            **_seed_metadata(),
        }
        db.users.insert_one(user_doc)
        user_map[u["email"]] = user_doc
    print(f"  {len(user_map)} users created.")

    # --- Restaurants ---
    print("Creating restaurants...")
    rest_map: dict[str, dict[str, Any]] = {}
    for idx, (creator_email, claimer_email, rdata) in enumerate(RESTAURANTS):
        rest_id = _next_id(db, "restaurants")
        normalized = _normalize_restaurant_data(rdata)
        created_at = _ago(days=max(1, 150 - idx * 2))
        restaurant_doc = {
            "_id": rest_id,
            **normalized,
            "created_by": user_map[creator_email]["_id"],
            "claimed_by": user_map[claimer_email]["_id"] if claimer_email else None,
            "created_at": created_at,
            "updated_at": created_at,
            **_seed_metadata(),
        }
        db.restaurants.insert_one(restaurant_doc)
        rest_map[rdata["name"]] = restaurant_doc
    print(f"  {len(rest_map)} restaurants created.")

    # --- Restaurant claims ---
    print("Creating ownership claims...")
    claim_count = 0
    for _, claimer_email, rdata in RESTAURANTS:
        if not claimer_email:
            continue
        db.restaurant_claims.insert_one(
            {
                "_id": _next_id(db, "restaurant_claims"),
                "restaurant_id": rest_map[rdata["name"]]["_id"],
                "owner_id": user_map[claimer_email]["_id"],
                "status": "approved",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                **_seed_metadata(),
            }
        )
        claim_count += 1
    print(f"  {claim_count} claims created.")

    # --- Reviews ---
    print("Creating reviews...")
    for reviewer_email, rest_name, rating, comment, days in REVIEWS:
        created_at = _ago(days=days)
        db.reviews.insert_one(
            {
                "_id": _next_id(db, "reviews"),
                "user_id": user_map[reviewer_email]["_id"],
                "restaurant_id": rest_map[rest_name]["_id"],
                "rating": rating,
                "comment": comment,
                "photos": [],
                "created_at": created_at,
                "updated_at": created_at,
                **_seed_metadata(),
            }
        )
    print(f"  {len(REVIEWS)} reviews created.")

    # --- Sync restaurant aggregates from actual reviews ---
    print("Recalculating restaurant ratings from actual reviews...")
    for r in rest_map.values():
        _recalc_restaurant_rating(db, r["_id"])
    print(f"  Ratings synced for {len(rest_map)} restaurants.")

    # --- Favorites ---
    print("Creating favorites...")
    for idx, (user_email, rest_name) in enumerate(FAVORITES):
        db.favorites.insert_one(
            {
                "_id": _next_id(db, "favorites"),
                "user_id": user_map[user_email]["_id"],
                "restaurant_id": rest_map[rest_name]["_id"],
                "created_at": _ago(days=max(1, 60 - idx * 2)),
                "updated_at": datetime.utcnow(),
                **_seed_metadata(),
            }
        )
    print(f"  {len(FAVORITES)} favorites created.")

    # --- Demo AI conversations ---
    print("Creating AI conversation history...")
    for idx, (user_email, messages) in enumerate(CONVERSATIONS):
        conv_created_at = _ago(days=5 + idx)
        message_docs = []
        for msg_idx, (role, content) in enumerate(messages):
            message_docs.append(
                {
                    "role": role,
                    "content": content,
                    "created_at": conv_created_at + timedelta(minutes=msg_idx),
                }
            )
        db.conversations.insert_one(
            {
                "_id": _next_id(db, "conversations"),
                "user_id": user_map[user_email]["_id"],
                "messages": message_docs,
                "created_at": conv_created_at,
                "updated_at": datetime.utcnow(),
                **_seed_metadata(),
            }
        )
    print(f"  {len(CONVERSATIONS)} conversations created.")

    print("\n✓ Seed complete!")
    print("  Demo accounts (all passwords: 'password')")
    print("  ├─ Reviewer:  user@demo.com")
    print("  ├─ Reviewer:  marcus@demo.com / priya@demo.com / alex@demo.com / emily@demo.com")
    print("  └─ Owners:    owner@demo.com / wei@demo.com / sofia@demo.com")


# ---------------------------------------------------------------------------
# Optional: note only
# ---------------------------------------------------------------------------

def _print_sql_note():
    print(
        """
-- ============================================================
-- ForkFinder seed data — MongoDB version
-- ============================================================
-- This project now seeds MongoDB collections directly.
-- Run this script directly instead:
--   python seed_data.py
-- Or recalculate aggregates with:
--   python seed_data.py --recalc
-- ============================================================
"""
    )


# ---------------------------------------------------------------------------
# Non-destructive aggregate recalculation
# ---------------------------------------------------------------------------

def _recalc_all(db):
    print("Recalculating all restaurant ratings from reviews collection...")
    restaurants = list(db.restaurants.find({}, {"_id": 1, "review_count": 1, "avg_rating": 1}))
    updated = 0
    for r in restaurants:
        reviews = list(db.reviews.find({"restaurant_id": r["_id"]}, {"rating": 1}))
        count = len(reviews)
        avg = round(sum(rv["rating"] for rv in reviews) / count, 2) if count else 0.0
        if r.get("review_count") != count or round(float(r.get("avg_rating", 0.0)), 2) != avg:
            db.restaurants.update_one(
                {"_id": r["_id"]},
                {"$set": {"review_count": count, "avg_rating": avg, "updated_at": datetime.utcnow()}},
            )
            updated += 1
    print(f"  {updated} / {len(restaurants)} restaurants updated.")
    print("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ForkFinder demo seed script")
    parser.add_argument("--wipe", action="store_true", help="Wipe all data before seeding")
    parser.add_argument("--sql", action="store_true", help="Print note instead of seeding")
    parser.add_argument("--recalc", action="store_true", help="Recalculate all restaurant ratings without wiping data")
    args = parser.parse_args()

    if args.sql:
        _print_sql_note()
        return

    db = get_db()
    try:
        if args.recalc:
            _recalc_all(db)
            return
        _seed(db, args.wipe)
    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
