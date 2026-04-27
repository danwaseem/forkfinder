#!/usr/bin/env python3
"""
Add more restaurants with images for all cuisine types.
Run: python add_restaurants.py
"""
import sys
import subprocess
import os

sys.path.insert(0, ".")
from app.database import get_db, _next_id
from datetime import datetime, timedelta

def _ago(**kwargs):
    return datetime.utcnow() - timedelta(**kwargs)

def _seed_metadata():
    return {"is_seeded": True}

# ---------------------------------------------------------------------------
# Download images
# ---------------------------------------------------------------------------
IMAGES = {
    # Italian
    "pasta2.jpg":       "https://images.unsplash.com/photo-1551183053-bf91798d454b?w=600&q=80&fm=jpg",
    "pizza.jpg":        "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=600&q=80&fm=jpg",
    "risotto.jpg":      "https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=600&q=80&fm=jpg",
    # Japanese
    "ramen.jpg":        "https://images.unsplash.com/photo-1569050467447-ce54b3bbc37d?w=600&q=80&fm=jpg",
    "tempura.jpg":      "https://images.unsplash.com/photo-1618841557871-b4664fbf0cb3?w=600&q=80&fm=jpg",
    "udon.jpg":         "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&q=80&fm=jpg",
    # Mexican
    "burrito.jpg":      "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&q=80&fm=jpg",
    "nachos.jpg":       "https://images.unsplash.com/photo-1513456852971-30c0b8199d4d?w=600&q=80&fm=jpg",
    "enchiladas.jpg":   "https://images.unsplash.com/photo-1534352956036-cd81e27dd615?w=600&q=80&fm=jpg",
    # American
    "bbq.jpg":          "https://images.unsplash.com/photo-1529193591184-b1d58069ecdd?w=600&q=80&fm=jpg",
    "hotdog.jpg":       "https://images.unsplash.com/photo-1619740455993-9d622f3bb3a4?w=600&q=80&fm=jpg",
    "wings.jpg":        "https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=600&q=80&fm=jpg",
    # Chinese
    "noodles.jpg":      "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600&q=80&fm=jpg",
    "dumplings.jpg":    "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600&q=80&fm=jpg",
    "peking.jpg":       "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=600&q=80&fm=jpg",
    # Indian
    "curry.jpg":        "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=600&q=80&fm=jpg",
    "biryani.jpg":      "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=600&q=80&fm=jpg",
    "naan.jpg":         "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&q=80&fm=jpg",
    # Thai
    "padthai.jpg":      "https://images.unsplash.com/photo-1559314809-0d155014e29e?w=600&q=80&fm=jpg",
    "greencurry.jpg":   "https://images.unsplash.com/photo-1455619452474-d2be8b1e70cd?w=600&q=80&fm=jpg",
    "somtam.jpg":       "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&q=80&fm=jpg",
    # French
    "croissant.jpg":    "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600&q=80&fm=jpg",
    "escargot.jpg":     "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=600&q=80&fm=jpg",
    "crepe.jpg":        "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=600&q=80&fm=jpg",
    # Mediterranean
    "hummus.jpg":       "https://images.unsplash.com/photo-1527515637462-cff94eecc1ac?w=600&q=80&fm=jpg",
    "falafel.jpg":      "https://images.unsplash.com/photo-1598511726623-d2e9996892f0?w=600&q=80&fm=jpg",
    "kebab.jpg":        "https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=600&q=80&fm=jpg",
    # Korean
    "bibimbap.jpg":     "https://images.unsplash.com/photo-1590301157890-4810ed352733?w=600&q=80&fm=jpg",
    "kbbq.jpg":         "https://images.unsplash.com/photo-1504544750208-dc0358e9deae?w=600&q=80&fm=jpg",
    "tteokbokki.jpg":   "https://images.unsplash.com/photo-1635363638580-c2809d049eee?w=600&q=80&fm=jpg",
    # Vietnamese
    "pho.jpg":          "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600&q=80&fm=jpg",
    "banh_mi.jpg":      "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80&fm=jpg",
    "spring_roll.jpg":  "https://images.unsplash.com/photo-1515669097368-22e68427d265?w=600&q=80&fm=jpg",
}

def download_images(upload_dir):
    print("Downloading images...")
    os.makedirs(upload_dir, exist_ok=True)
    for filename, url in IMAGES.items():
        path = os.path.join(upload_dir, filename)
        if os.path.exists(path) and os.path.getsize(path) > 10000:
            print(f"  Skipping {filename} (already exists)")
            continue
        result = subprocess.run(
            ["curl", "-L", "-s", "-o", path, url],
            capture_output=True
        )
        size = os.path.getsize(path) if os.path.exists(path) else 0
        if size > 10000:
            print(f"  Downloaded {filename} ({size//1024}KB)")
        else:
            print(f"  WARNING: {filename} too small ({size} bytes) - URL may be blocked")

# ---------------------------------------------------------------------------
# New restaurants data
# ---------------------------------------------------------------------------
NEW_RESTAURANTS = [
    # ── Italian ──────────────────────────────────────────────────────────────
    {
        "name": "Trattoria Roma",
        "cuisine_type": "Italian",
        "address": "201 Santana Row",
        "city": "San Jose", "state": "CA", "zip_code": "95128",
        "description": "Classic Roman trattoria with handmade pasta and wood-fired dishes.",
        "price_range": "$$$",
        "phone": "408-555-0201",
        "hours": {"monday": "11am-10pm", "tuesday": "11am-10pm", "wednesday": "11am-10pm",
                  "thursday": "11am-10pm", "friday": "11am-11pm", "saturday": "10am-11pm", "sunday": "10am-10pm"},
        "amenities": ["reservations", "wine bar", "romantic"],
        "photos": ["/uploads/pasta2.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Pizzeria Napoli",
        "cuisine_type": "Italian",
        "address": "88 S 1st St",
        "city": "San Jose", "state": "CA", "zip_code": "95113",
        "description": "Authentic Neapolitan pizza baked in a traditional wood-fired oven.",
        "price_range": "$$",
        "phone": "408-555-0202",
        "hours": {"everyday": "11am-11pm"},
        "amenities": ["takeout", "delivery", "family-friendly"],
        "photos": ["/uploads/pizza.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Risotto House",
        "cuisine_type": "Italian",
        "address": "450 N 1st St",
        "city": "San Jose", "state": "CA", "zip_code": "95112",
        "description": "Specialty risotto bar with seasonal ingredients and Italian wines.",
        "price_range": "$$$",
        "phone": "408-555-0203",
        "hours": {"tuesday": "5pm-10pm", "wednesday": "5pm-10pm", "thursday": "5pm-10pm",
                  "friday": "5pm-11pm", "saturday": "5pm-11pm", "sunday": "5pm-9pm"},
        "amenities": ["wine bar", "reservations", "romantic"],
        "photos": ["/uploads/risotto.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Japanese ─────────────────────────────────────────────────────────────
    {
        "name": "Ramen Tanaka",
        "cuisine_type": "Japanese",
        "address": "320 Japantown",
        "city": "San Jose", "state": "CA", "zip_code": "95112",
        "description": "Rich tonkotsu and shoyu ramen bowls with house-made noodles.",
        "price_range": "$$",
        "phone": "408-555-0204",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["casual", "takeout"],
        "photos": ["/uploads/ramen.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Tempura Heaven",
        "cuisine_type": "Japanese",
        "address": "175 W Santa Clara St",
        "city": "San Jose", "state": "CA", "zip_code": "95113",
        "description": "Light, crispy tempura with seasonal vegetables and fresh seafood.",
        "price_range": "$$$",
        "phone": "408-555-0205",
        "hours": {"monday": "11:30am-9pm", "tuesday": "11:30am-9pm", "wednesday": "11:30am-9pm",
                  "thursday": "11:30am-9pm", "friday": "11:30am-10pm", "saturday": "12pm-10pm"},
        "amenities": ["reservations", "sake menu"],
        "photos": ["/uploads/tempura.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Udon & Co",
        "cuisine_type": "Japanese",
        "address": "567 N 6th St",
        "city": "San Jose", "state": "CA", "zip_code": "95112",
        "description": "Hand-pulled udon noodles in rich dashi broth, Tokyo style.",
        "price_range": "$",
        "phone": "408-555-0206",
        "hours": {"everyday": "10:30am-9pm"},
        "amenities": ["casual", "quick bite", "takeout"],
        "photos": ["/uploads/udon.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Mexican ──────────────────────────────────────────────────────────────
    {
        "name": "Burrito Loco",
        "cuisine_type": "Mexican",
        "address": "234 Alum Rock Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95116",
        "description": "Giant Mission-style burritos stuffed with slow-cooked meats.",
        "price_range": "$",
        "phone": "408-555-0207",
        "hours": {"everyday": "9am-10pm"},
        "amenities": ["takeout", "delivery", "family-friendly"],
        "photos": ["/uploads/burrito.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Nacho Mama's",
        "cuisine_type": "Mexican",
        "address": "890 Story Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95122",
        "description": "Loaded nachos, guacamole, and classic Mexican comfort food.",
        "price_range": "$$",
        "phone": "408-555-0208",
        "hours": {"everyday": "11am-11pm"},
        "amenities": ["bar", "sports bar", "family-friendly"],
        "photos": ["/uploads/nachos.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Casa Enchilada",
        "cuisine_type": "Mexican",
        "address": "112 E Santa Clara St",
        "city": "San Jose", "state": "CA", "zip_code": "95113",
        "description": "Homestyle Mexican cooking with grandmother's enchilada recipes.",
        "price_range": "$$",
        "phone": "408-555-0209",
        "hours": {"monday": "11am-9pm", "tuesday": "11am-9pm", "wednesday": "11am-9pm",
                  "thursday": "11am-9pm", "friday": "11am-10pm", "saturday": "10am-10pm", "sunday": "10am-9pm"},
        "amenities": ["family-friendly", "takeout"],
        "photos": ["/uploads/enchiladas.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── American ─────────────────────────────────────────────────────────────
    {
        "name": "Smoke & Barrel BBQ",
        "cuisine_type": "American",
        "address": "345 Meridian Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95126",
        "description": "Slow-smoked Texas BBQ — brisket, ribs, pulled pork and all the fixings.",
        "price_range": "$$",
        "phone": "408-555-0210",
        "hours": {"wednesday": "11am-9pm", "thursday": "11am-9pm", "friday": "11am-10pm",
                  "saturday": "11am-10pm", "sunday": "11am-9pm"},
        "amenities": ["casual", "takeout", "outdoor seating"],
        "photos": ["/uploads/bbq.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "The Wing Stop",
        "cuisine_type": "American",
        "address": "678 Blossom Hill Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95123",
        "description": "Crispy wings in 15 signature sauces with handcut fries.",
        "price_range": "$",
        "phone": "408-555-0211",
        "hours": {"everyday": "11am-12am"},
        "amenities": ["sports bar", "late night", "takeout", "delivery"],
        "photos": ["/uploads/wings.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Chinese ──────────────────────────────────────────────────────────────
    {
        "name": "Noodle King",
        "cuisine_type": "Chinese",
        "address": "199 E Jackson St",
        "city": "San Jose", "state": "CA", "zip_code": "95112",
        "description": "Hand-pulled Lanzhou beef noodles and authentic Chinese street food.",
        "price_range": "$",
        "phone": "408-555-0212",
        "hours": {"everyday": "10am-9pm"},
        "amenities": ["casual", "quick bite"],
        "photos": ["/uploads/noodles.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Dumpling Palace",
        "cuisine_type": "Chinese",
        "address": "888 Story Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95122",
        "description": "Shanghai-style soup dumplings and pan-fried potstickers.",
        "price_range": "$$",
        "phone": "408-555-0213",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["family-friendly", "takeout"],
        "photos": ["/uploads/dumplings.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Peking Duck House",
        "cuisine_type": "Chinese",
        "address": "456 Tully Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95111",
        "description": "Signature Peking duck carved tableside with all traditional accompaniments.",
        "price_range": "$$$",
        "phone": "408-555-0214",
        "hours": {"monday": "11:30am-10pm", "tuesday": "11:30am-10pm", "wednesday": "11:30am-10pm",
                  "thursday": "11:30am-10pm", "friday": "11:30am-11pm", "saturday": "11am-11pm", "sunday": "11am-10pm"},
        "amenities": ["reservations", "private dining", "family-friendly"],
        "photos": ["/uploads/peking.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Indian ───────────────────────────────────────────────────────────────
    {
        "name": "Curry House",
        "cuisine_type": "Indian",
        "address": "2100 Monterey Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95128",
        "description": "South Indian curries, dosas, and idlis made with traditional spices.",
        "price_range": "$$",
        "phone": "408-555-0215",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["vegetarian options", "halal", "takeout"],
        "photos": ["/uploads/curry.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Biryani Bros",
        "cuisine_type": "Indian",
        "address": "3456 Thornton Ave",
        "city": "Fremont", "state": "CA", "zip_code": "94536",
        "description": "Dum biryani slow-cooked in sealed pots for maximum flavor.",
        "price_range": "$$",
        "phone": "510-555-0216",
        "hours": {"everyday": "11:30am-10pm"},
        "amenities": ["halal", "delivery", "takeout"],
        "photos": ["/uploads/biryani.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Naan Stop",
        "cuisine_type": "Indian",
        "address": "789 Capitol Expressway",
        "city": "San Jose", "state": "CA", "zip_code": "95136",
        "description": "Fresh tandoor breads and North Indian classics at budget prices.",
        "price_range": "$",
        "phone": "408-555-0217",
        "hours": {"everyday": "10:30am-9:30pm"},
        "amenities": ["vegetarian options", "quick bite", "takeout"],
        "photos": ["/uploads/naan.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Thai ─────────────────────────────────────────────────────────────────
    {
        "name": "Pad Thai Palace",
        "cuisine_type": "Thai",
        "address": "123 W San Carlos St",
        "city": "San Jose", "state": "CA", "zip_code": "95126",
        "description": "Wok-tossed pad thai and classic Thai noodle dishes.",
        "price_range": "$$",
        "phone": "408-555-0218",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["vegan options", "takeout", "delivery"],
        "photos": ["/uploads/padthai.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Green Curry Co.",
        "cuisine_type": "Thai",
        "address": "567 S Bascom Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95128",
        "description": "Aromatic Thai curries — green, red, and massaman — with jasmine rice.",
        "price_range": "$$",
        "phone": "408-555-0219",
        "hours": {"monday": "11am-9pm", "tuesday": "11am-9pm", "wednesday": "11am-9pm",
                  "thursday": "11am-9pm", "friday": "11am-10pm", "saturday": "11am-10pm"},
        "amenities": ["vegan options", "gluten-free options"],
        "photos": ["/uploads/greencurry.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── French ───────────────────────────────────────────────────────────────
    {
        "name": "Cafe de Paris",
        "cuisine_type": "French",
        "address": "300 Santana Row",
        "city": "San Jose", "state": "CA", "zip_code": "95128",
        "description": "Parisian cafe with fresh croissants, coffee, and light French fare.",
        "price_range": "$$",
        "phone": "408-555-0220",
        "hours": {"everyday": "7am-8pm"},
        "amenities": ["wifi", "outdoor seating", "casual"],
        "photos": ["/uploads/croissant.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "La Creperie",
        "cuisine_type": "French",
        "address": "45 Post St",
        "city": "San Jose", "state": "CA", "zip_code": "95113",
        "description": "Sweet and savory crepes made to order with French cider.",
        "price_range": "$$",
        "phone": "408-555-0221",
        "hours": {"tuesday": "11am-9pm", "wednesday": "11am-9pm", "thursday": "11am-9pm",
                  "friday": "11am-10pm", "saturday": "10am-10pm", "sunday": "10am-8pm"},
        "amenities": ["casual", "romantic", "outdoor seating"],
        "photos": ["/uploads/crepe.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Mediterranean ────────────────────────────────────────────────────────
    {
        "name": "Hummus & Pita Co.",
        "cuisine_type": "Mediterranean",
        "address": "234 Race St",
        "city": "San Jose", "state": "CA", "zip_code": "95126",
        "description": "Israeli-style hummus bowls with fresh pita and Mediterranean sides.",
        "price_range": "$",
        "phone": "408-555-0222",
        "hours": {"everyday": "11am-9pm"},
        "amenities": ["vegan", "vegetarian", "halal", "quick bite"],
        "photos": ["/uploads/hummus.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Falafel House",
        "cuisine_type": "Mediterranean",
        "address": "678 Lincoln Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95126",
        "description": "Crispy falafel wraps, shawarma plates, and fresh tabbouleh.",
        "price_range": "$",
        "phone": "408-555-0223",
        "hours": {"everyday": "10am-10pm"},
        "amenities": ["vegan", "halal", "takeout", "delivery"],
        "photos": ["/uploads/falafel.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Kebab Kingdom",
        "cuisine_type": "Mediterranean",
        "address": "901 E Santa Clara St",
        "city": "San Jose", "state": "CA", "zip_code": "95116",
        "description": "Turkish-style kebabs, grilled meats, and mezze platters.",
        "price_range": "$$",
        "phone": "408-555-0224",
        "hours": {"everyday": "11am-11pm"},
        "amenities": ["halal", "outdoor seating", "casual"],
        "photos": ["/uploads/kebab.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Korean ───────────────────────────────────────────────────────────────
    {
        "name": "Bibimbap Bar",
        "cuisine_type": "Korean",
        "address": "234 N 1st St",
        "city": "San Jose", "state": "CA", "zip_code": "95112",
        "description": "Build-your-own bibimbap bowls with premium Korean ingredients.",
        "price_range": "$$",
        "phone": "408-555-0225",
        "hours": {"everyday": "11am-9:30pm"},
        "amenities": ["vegetarian options", "quick bite"],
        "photos": ["/uploads/bibimbap.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "K-BBQ Grill House",
        "cuisine_type": "Korean",
        "address": "567 Saratoga Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95129",
        "description": "All-you-can-eat Korean BBQ with tabletop grills and banchan.",
        "price_range": "$$$",
        "phone": "408-555-0226",
        "hours": {"everyday": "11:30am-11pm"},
        "amenities": ["family-friendly", "reservations", "bar"],
        "photos": ["/uploads/kbbq.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Tteokbokki Town",
        "cuisine_type": "Korean",
        "address": "890 Hostetter Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95131",
        "description": "Korean street food — tteokbokki, corn dogs, and fried snacks.",
        "price_range": "$",
        "phone": "408-555-0227",
        "hours": {"everyday": "11am-10pm"},
        "amenities": ["casual", "quick bite", "takeout"],
        "photos": ["/uploads/tteokbokki.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    # ── Vietnamese ───────────────────────────────────────────────────────────
    {
        "name": "Pho Saigon",
        "cuisine_type": "Vietnamese",
        "address": "1234 Story Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95122",
        "description": "Rich 24-hour bone broth pho and Vietnamese noodle soups.",
        "price_range": "$",
        "phone": "408-555-0228",
        "hours": {"everyday": "8am-9pm"},
        "amenities": ["casual", "family-friendly", "quick bite"],
        "photos": ["/uploads/pho.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Banh Mi & More",
        "cuisine_type": "Vietnamese",
        "address": "567 McLaughlin Ave",
        "city": "San Jose", "state": "CA", "zip_code": "95116",
        "description": "Crusty French-Vietnamese banh mi sandwiches with house-made pate.",
        "price_range": "$",
        "phone": "408-555-0229",
        "hours": {"monday": "8am-6pm", "tuesday": "8am-6pm", "wednesday": "8am-6pm",
                  "thursday": "8am-6pm", "friday": "8am-7pm", "saturday": "8am-7pm"},
        "amenities": ["quick bite", "takeout"],
        "photos": ["/uploads/banh_mi.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
    {
        "name": "Spring Roll Garden",
        "cuisine_type": "Vietnamese",
        "address": "890 Senter Rd",
        "city": "San Jose", "state": "CA", "zip_code": "95111",
        "description": "Fresh spring rolls, vermicelli bowls, and authentic Vietnamese salads.",
        "price_range": "$",
        "phone": "408-555-0230",
        "hours": {"everyday": "10am-9pm"},
        "amenities": ["vegan options", "gluten-free options", "takeout"],
        "photos": ["/uploads/spring_roll.jpg"],
        "is_claimed": False, "claimed_by": None,
    },
]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    upload_dir = "/app/uploads"
    download_images(upload_dir)

    db = get_db()
    existing = set(r["name"] for r in db.restaurants.find({}, {"name": 1}))

    print(f"\nAdding new restaurants...")
    added = 0
    for idx, r in enumerate(NEW_RESTAURANTS):
        if r["name"] in existing:
            print(f"  Skipping '{r['name']}' (already exists)")
            continue

        rid = _next_id(db, "restaurants")
        rest_doc = {
            "_id": rid,
            **r,
            "avg_rating": 0.0,
            "review_count": 0,
            "total_views": 0,
            "created_by": 6,
            "country": "United States",
            "website": None,
            "latitude": None,
            "longitude": None,
            "created_at": _ago(days=200 - idx * 5),
            "updated_at": _ago(days=200 - idx * 5),
            **_seed_metadata(),
        }
        db.restaurants.insert_one(rest_doc)
        print(f"  Added: {r['name']} ({r['cuisine_type']})")
        added += 1

    total = db.restaurants.count_documents({})
    print(f"\nDone! Added {added} restaurants. Total in DB: {total}")

if __name__ == "__main__":
    main()
