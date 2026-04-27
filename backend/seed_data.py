#!/usr/bin/env python3
"""
ForkFinder demo seed data — MongoDB version.
Usage (run from inside the backend container):
  python seed_data.py          # insert seed data (skips if data exists)
  python seed_data.py --wipe   # drop all data first, then re-seed
"""
import argparse
import sys
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, ".")
from app.database import get_db, _next_id
from app.utils.auth import hash_password

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ago(**kwargs) -> datetime:
    return datetime.utcnow() - timedelta(**kwargs)

def _seed_metadata():
    return {"is_seeded": True}

def _normalize_prefs(p: dict) -> dict:
    return {
        "cuisines":        p.get("cuisines", []),
        "price_range":     p.get("price_range", "$$"),
        "dietary":         p.get("dietary", []),
        "ambiance":        p.get("ambiance", []),
        "sort_by":         p.get("sort_by", "rating"),
        "location":        p.get("location", ""),
        "search_radius":   p.get("search_radius", 10),
    }

# ---------------------------------------------------------------------------
# Raw data
# ---------------------------------------------------------------------------
USERS = [
    {"name": "Alice Johnson",  "email": "alice@example.com",   "role": "user"},
    {"name": "Bob Smith",      "email": "bob@example.com",     "role": "user"},
    {"name": "Carol White",    "email": "carol@example.com",   "role": "user"},
    {"name": "David Lee",      "email": "david@example.com",   "role": "user"},
    {"name": "Eva Martinez",   "email": "eva@example.com",     "role": "user"},
    {"name": "Demo User",      "email": "user@demo.com",       "role": "user"},
    {"name": "Demo Owner",     "email": "owner@demo.com",      "role": "owner"},
]

PREFERENCES = {
    "alice@example.com": {
        "cuisines": ["Italian", "Japanese"],
        "price_range": "$$",
        "dietary": ["vegetarian"],
        "ambiance": ["casual", "romantic"],
        "sort_by": "rating",
        "location": "San Jose, CA",
        "search_radius": 10,
    },
    "bob@example.com": {
        "cuisines": ["American", "Mexican"],
        "price_range": "$",
        "dietary": [],
        "ambiance": ["casual", "family-friendly"],
        "sort_by": "distance",
        "location": "San Jose, CA",
        "search_radius": 5,
    },
    "carol@example.com": {
        "cuisines": ["Chinese", "Thai", "Indian"],
        "price_range": "$$",
        "dietary": ["vegan", "gluten-free"],
        "ambiance": ["casual"],
        "sort_by": "rating",
        "location": "San Jose, CA",
        "search_radius": 15,
    },
    "david@example.com": {
        "cuisines": ["French", "Italian"],
        "price_range": "$$$",
        "dietary": [],
        "ambiance": ["fine dining", "romantic"],
        "sort_by": "popularity",
        "location": "San Jose, CA",
        "search_radius": 20,
    },
    "eva@example.com": {
        "cuisines": ["Mexican", "American"],
        "price_range": "$",
        "dietary": ["halal"],
        "ambiance": ["casual", "family-friendly"],
        "sort_by": "price",
        "location": "San Jose, CA",
        "search_radius": 8,
    },
    "user@demo.com": {
        "cuisines": ["Italian", "American", "Japanese"],
        "price_range": "$$",
        "dietary": [],
        "ambiance": ["casual"],
        "sort_by": "rating",
        "location": "San Jose, CA",
        "search_radius": 10,
    },
}

RESTAURANTS = [
    {
        "name": "Pasta Paradise",
        "cuisine_type": "Italian",
        "address": "123 Main St",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95101",
        "description": "Authentic Italian pasta dishes made fresh daily.",
        "price_range": "$$",
        "phone": "408-555-0101",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["wifi", "outdoor seating"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Sakura Sushi",
        "cuisine_type": "Japanese",
        "address": "456 Oak Ave",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95112",
        "description": "Fresh sushi and traditional Japanese cuisine.",
        "price_range": "$$$",
        "phone": "408-555-0102",
        "hours": {"everyday": "12pm-11pm"},
        "amenities": ["reservations", "sake bar"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Taco Fiesta",
        "cuisine_type": "Mexican",
        "address": "789 Elm St",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95110",
        "description": "Vibrant Mexican street food and margaritas.",
        "price_range": "$",
        "phone": "408-555-0103",
        "hours": {"everyday": "10am-9pm"},
        "amenities": ["family-friendly", "takeout"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "The Burger Joint",
        "cuisine_type": "American",
        "address": "321 Maple Rd",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95128",
        "description": "Classic American burgers with gourmet toppings.",
        "price_range": "$$",
        "phone": "408-555-0104",
        "hours": {"everyday": "11am-11pm"},
        "amenities": ["wifi", "late night", "takeout"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Golden Dragon",
        "cuisine_type": "Chinese",
        "address": "654 Pine St",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95112",
        "description": "Dim sum and Cantonese specialties.",
        "price_range": "$$",
        "phone": "408-555-0105",
        "hours": {"everyday": "9am-10pm"},
        "amenities": ["family-friendly", "reservations"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Le Petit Bistro",
        "cuisine_type": "French",
        "address": "987 Cedar Blvd",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95125",
        "description": "Elegant French cuisine in a romantic setting.",
        "price_range": "$$$",
        "phone": "408-555-0106",
        "hours": {"tuesday": "5pm-11pm", "wednesday": "5pm-11pm", "thursday": "5pm-11pm", "friday": "5pm-11pm", "saturday": "5pm-11pm", "sunday": "5pm-11pm"},
        "amenities": ["reservations", "wine bar", "romantic"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Spice Garden",
        "cuisine_type": "Indian",
        "address": "147 Walnut Ave",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95134",
        "description": "Rich curries and tandoor specialties from Northern India.",
        "price_range": "$$",
        "phone": "408-555-0107",
        "hours": {"everyday": "11:30am-10pm"},
        "amenities": ["vegetarian options", "takeout", "delivery"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Bangkok Garden",
        "cuisine_type": "Thai",
        "address": "258 Birch Lane",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95116",
        "description": "Authentic Thai dishes with fresh herbs and spices.",
        "price_range": "$",
        "phone": "408-555-0108",
        "hours": {"everyday": "11am-9:30pm"},
        "amenities": ["vegan options", "takeout"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Green Leaf Cafe",
        "cuisine_type": "American",
        "address": "369 Spruce St",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95126",
        "description": "100% plant-based menu with seasonal ingredients.",
        "price_range": "$",
        "phone": "408-555-0109",
        "hours": {"monday": "8am-8pm", "tuesday": "8am-8pm", "wednesday": "8am-8pm", "thursday": "8am-8pm", "friday": "8am-8pm", "saturday": "8am-8pm"},
        "amenities": ["vegan", "gluten-free options", "wifi", "outdoor seating"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
    {
        "name": "Sunset Steakhouse",
        "cuisine_type": "American",
        "address": "741 Redwood Dr",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95120",
        "description": "Prime cuts and classic steakhouse sides.",
        "price_range": "$$$$",
        "phone": "408-555-0110",
        "hours": {"everyday": "5pm-11pm"},
        "amenities": ["reservations", "fine dining", "bar", "private dining"],
        "photos": [],
        "is_claimed": False,
        "claimed_by": None,
    },
]

# Reviews: list of (user_email, restaurant_index, rating, comment)
REVIEWS_DATA = [
    ("alice@example.com",  0, 5, "The carbonara here is absolutely divine. Fresh pasta every time!"),
    ("alice@example.com",  1, 4, "Very fresh fish. The omakase is worth it for a special occasion."),
    ("bob@example.com",    2, 5, "Best tacos in San Jose! The al pastor is incredible."),
    ("bob@example.com",    3, 4, "Solid burgers. The truffle fries are a must-try."),
    ("carol@example.com",  4, 5, "Excellent dim sum on weekends. Always packed for a reason."),
    ("carol@example.com",  6, 5, "Amazing vegetarian options. The paneer tikka masala is perfect."),
    ("carol@example.com",  8, 4, "Great vegan options. The jackfruit tacos are surprisingly good."),
    ("david@example.com",  5, 5, "Finest French food in the South Bay. The duck confit is flawless."),
    ("david@example.com",  0, 4, "Very good pasta, though not quite Paris level. Lovely atmosphere."),
    ("eva@example.com",    2, 4, "Great halal options. Family loved the enchiladas."),
    ("eva@example.com",    7, 5, "Authentic Thai flavors. The pad see ew is the best I've had."),
    ("user@demo.com",      0, 5, "My go-to Italian spot in San Jose. Never disappoints!"),
    ("user@demo.com",      3, 3, "Burgers are okay but nothing special. Fries were cold."),
    ("user@demo.com",      9, 5, "Incredible ribeye. Perfect for a special night out."),
]

FAVORITES_DATA = [
    ("alice@example.com",  0),
    ("alice@example.com",  1),
    ("bob@example.com",    2),
    ("bob@example.com",    3),
    ("carol@example.com",  4),
    ("carol@example.com",  6),
    ("david@example.com",  5),
    ("user@demo.com",      0),
    ("user@demo.com",      9),
]

# ---------------------------------------------------------------------------
# Wipe
# ---------------------------------------------------------------------------
def _wipe(db):
    for col in ["users", "restaurants", "reviews", "favorites", "sessions", "conversations", "counters"]:
        db[col].drop()
    print("  All collections dropped.")

# ---------------------------------------------------------------------------
# Seed
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
    user_map: dict[str, dict] = {}
    for idx, u in enumerate(USERS):
        user_id = _next_id(db, "users")
        prefs_data = _normalize_prefs(PREFERENCES.get(u["email"], {}))
        user_doc = {
            "_id": user_id,
            **u,
            "password_hash": pw,
            "preferences": prefs_data,
            "profile_picture": None,
            "phone": None,
            "about": None,
            "country": "US",
            "city": "San Jose",
            "languages": ["English"],
            "gender": None,
            "created_at": _ago(days=180 - idx * 10),
            "updated_at": _ago(days=180 - idx * 10),
            **_seed_metadata(),
        }
        db.users.insert_one(user_doc)
        user_map[u["email"]] = user_doc
    print(f"  {len(user_map)} users created.")

    # --- Restaurants ---
    print("Creating restaurants...")
    restaurant_map: list[dict] = []
    for idx, r in enumerate(RESTAURANTS):
        rid = _next_id(db, "restaurants")
        rest_doc = {
            "_id": rid,
            **r,
            "avg_rating": 0.0,
            "created_by": 6,
            "country": "United States",
            "website": None,
            "latitude": None,
            "longitude": None,
            "review_count": 0,
            "total_views": 0,
            "created_at": _ago(days=365 - idx * 20),
            "updated_at": _ago(days=365 - idx * 20),
            **_seed_metadata(),
        }
        db.restaurants.insert_one(rest_doc)
        restaurant_map.append(rest_doc)
    print(f"  {len(restaurant_map)} restaurants created.")

    # --- Reviews ---
    print("Creating reviews...")
    review_count = 0
    # Track rating totals per restaurant for aggregate update
    rating_totals: dict[int, list] = {r["_id"]: [] for r in restaurant_map}

    for user_email, rest_idx, rating, comment in REVIEWS_DATA:
        user = user_map.get(user_email)
        restaurant = restaurant_map[rest_idx]
        if not user:
            continue
        rev_id = _next_id(db, "reviews")
        review_doc = {
            "_id": rev_id,
            "user_id": user["_id"],
            "restaurant_id": restaurant["_id"],
            "rating": rating,
            "comment": comment,
            "photos": [],
            "created_at": _ago(days=90 - review_count * 3),
            "updated_at": _ago(days=90 - review_count * 3),
            **_seed_metadata(),
        }
        db.reviews.insert_one(review_doc)
        rating_totals[restaurant["_id"]].append(rating)
        review_count += 1
    print(f"  {review_count} reviews created.")

    # Update restaurant aggregates
    for rid, ratings in rating_totals.items():
        if ratings:
            avg = round(sum(ratings) / len(ratings), 2)
            db.restaurants.update_one(
                {"_id": rid},
                {"$set": {"avg_rating": avg, "review_count": len(ratings)}}
            )

    # --- Favorites ---
    print("Creating favorites...")
    fav_count = 0
    for user_email, rest_idx in FAVORITES_DATA:
        user = user_map.get(user_email)
        restaurant = restaurant_map[rest_idx]
        if not user:
            continue
        fav_id = _next_id(db, "favorites")
        db.favorites.insert_one({
            "_id": fav_id,
            "user_id": user["_id"],
            "restaurant_id": restaurant["_id"],
            "created_at": _ago(days=30),
            **_seed_metadata(),
        })
        fav_count += 1
    print(f"  {fav_count} favorites created.")

    print("\n✅ Seed complete!")
    print("   Demo credentials (all passwords: 'password'):")
    print("   User:  user@demo.com")
    print("   Owner: owner@demo.com")
    print("   Also:  alice@example.com, bob@example.com, carol@example.com")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Seed ForkFinder MongoDB database.")
    parser.add_argument("--wipe", action="store_true", help="Drop all data before seeding")
    args = parser.parse_args()

    db = get_db()
    _seed(db, args.wipe)

if __name__ == "__main__":
    main()