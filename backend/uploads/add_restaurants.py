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
# Reviews for new restaurants
# (restaurant_name, user_id, rating, comment)
# user_id 1–6 = Alice, Bob, Carol, David, Eva, Demo User (seeded by seed_data.py)
# ---------------------------------------------------------------------------
NEW_REVIEWS = [
    # ── Italian ──────────────────────────────────────────────────────────────
    ("Trattoria Roma",      1, 5, "Handmade pasta that rivals anything I've had in Rome. The cacio e pepe is perfection."),
    ("Trattoria Roma",      4, 4, "Romantic atmosphere and excellent wine list. The wood-fired dishes are outstanding."),
    ("Pizzeria Napoli",     2, 5, "Best Neapolitan pizza in the South Bay. Perfectly charred crust, minimal toppings, maximum flavor."),
    ("Pizzeria Napoli",     6, 4, "Authentic and delicious. The margherita is simple but flawless."),
    ("Risotto House",       4, 5, "The saffron risotto is life-changing. Perfect al dente texture and incredible depth of flavor."),
    ("Risotto House",       1, 4, "Exceptional seasonal menu. The mushroom risotto was earthy and rich."),
    # ── Japanese ─────────────────────────────────────────────────────────────
    ("Ramen Tanaka",        3, 5, "Rich, cloudy tonkotsu broth with perfectly cooked noodles. Worth every minute of the wait."),
    ("Ramen Tanaka",        6, 4, "House-made noodles make all the difference. The spicy miso ramen is incredible."),
    ("Tempura Heaven",      4, 5, "The lightest, crispiest tempura I have ever had. The seasonal vegetable set was extraordinary."),
    ("Tempura Heaven",      1, 4, "An elevated tempura experience. The dipping sauce and grated daikon are perfect complements."),
    ("Udon & Co",           2, 5, "Springy hand-pulled udon in a deeply savory dashi broth. Best quick bite in the area."),
    ("Udon & Co",           5, 4, "Simple, satisfying, and authentic. The cold zaru udon is refreshing and perfect."),
    # ── Mexican ──────────────────────────────────────────────────────────────
    ("Burrito Loco",        2, 5, "Enormous Mission-style burrito stuffed with slow-cooked carnitas. Incredible value."),
    ("Burrito Loco",        6, 4, "The carne asada is tender and well-seasoned. Fresh salsas put this above every chain."),
    ("Nacho Mama's",        2, 4, "Loaded nachos with all the toppings. Great sports bar vibe and solid margaritas."),
    ("Nacho Mama's",        5, 3, "Fun atmosphere but nachos were a bit soggy by the time they arrived. Still tasty."),
    ("Casa Enchilada",      3, 5, "Grandmother's recipes done right. The mole enchiladas are deeply complex and comforting."),
    ("Casa Enchilada",      6, 4, "Homestyle Mexican at its best. The rice and beans alone are worth a visit."),
    # ── American ─────────────────────────────────────────────────────────────
    ("Smoke & Barrel BBQ",  2, 5, "The brisket is perfectly smoked — tender, juicy, and smoky without being overpowering."),
    ("Smoke & Barrel BBQ",  6, 4, "Pulled pork and cornbread combo is outstanding. Worth the mid-week trip."),
    ("The Wing Stop",       2, 4, "Crispy wings in a great variety of sauces. The lemon pepper and mango habanero are standouts."),
    ("The Wing Stop",       5, 4, "Late-night wing spot that delivers. Big portions and the handcut fries are excellent."),
    # ── Chinese ──────────────────────────────────────────────────────────────
    ("Noodle King",         3, 5, "Hand-pulled Lanzhou noodles in a clear, deeply flavored beef broth. Authentic and unbeatable."),
    ("Noodle King",         6, 4, "Quick, cheap, and genuinely delicious. The broad noodles with braised beef are fantastic."),
    ("Dumpling Palace",     3, 5, "The soup dumplings burst with savory broth. One of the best XLB spots outside Shanghai."),
    ("Dumpling Palace",     5, 4, "Pan-fried potstickers are crispy and packed with flavor. Bring a group and order everything."),
    ("Peking Duck House",   4, 5, "Tableside duck carving is theatrical and the skin is impossibly crispy. A special-occasion must."),
    ("Peking Duck House",   3, 4, "The duck is excellent and the pancake presentation is classic. Reserve well in advance."),
    # ── Indian ───────────────────────────────────────────────────────────────
    ("Curry House",         3, 5, "The masala dosa is enormous and perfectly crispy. South Indian done properly with real sambar."),
    ("Curry House",         6, 4, "The lunch thali is an incredible deal. Multiple curries, rice, naan, and dessert included."),
    ("Biryani Bros",        3, 5, "Dum biryani cooked in a sealed pot arrives fragrant and perfectly spiced. Absolutely incredible."),
    ("Biryani Bros",        5, 4, "The chicken biryani is fluffy, aromatic, and hearty. The raita is the perfect complement."),
    ("Naan Stop",           3, 4, "Fresh garlic naan and dal makhani at budget prices. Consistent and satisfying every visit."),
    ("Naan Stop",           6, 4, "Quick service and generous portions. The paneer tikka is a must-order."),
    # ── Thai ─────────────────────────────────────────────────────────────────
    ("Pad Thai Palace",     3, 5, "The pad thai here is perfectly balanced — sweet, sour, and savory. Real wok hei."),
    ("Pad Thai Palace",     6, 4, "Fresh ingredients and bold flavors. The pad see ew is even better than the pad thai."),
    ("Green Curry Co.",     3, 5, "The green curry is deeply aromatic with just the right heat. The massaman is also exceptional."),
    ("Green Curry Co.",     1, 4, "Beautiful, fragrant curries with excellent jasmine rice. Great vegan options available."),
    # ── French ───────────────────────────────────────────────────────────────
    ("Cafe de Paris",       1, 5, "The croissants are perfectly laminated — shatteringly crispy outside, buttery within. Paris-worthy."),
    ("Cafe de Paris",       4, 4, "Lovely Parisian atmosphere and excellent coffee. The quiche lorraine is outstanding."),
    ("La Creperie",         1, 5, "The galette with ham, egg, and Gruyère is a buckwheat masterpiece. Perfect with house cider."),
    ("La Creperie",         4, 4, "Sweet and savory crepes done beautifully. The Nutella banana crepe is indulgent and worth it."),
    # ── Mediterranean ────────────────────────────────────────────────────────
    ("Hummus & Pita Co.",   3, 5, "The hummus is silky smooth and generously topped. The fresh pita is warm and pillowy."),
    ("Hummus & Pita Co.",   6, 4, "Excellent vegan-friendly spot. The falafel bowl with tahini is fresh and filling."),
    ("Falafel House",       3, 4, "Crispy falafel wraps with fresh vegetables and creamy tahini. Best shawarma in the area."),
    ("Falafel House",       5, 5, "The falafel is light and crispy, not heavy and dense. Authentic flavors throughout."),
    ("Kebab Kingdom",       5, 4, "Turkish-style kebabs grilled perfectly. The adana kebab is spicy and smoky."),
    ("Kebab Kingdom",       2, 5, "The mixed mezze platter is a feast. Grilled meats are charred and tender."),
    # ── Korean ───────────────────────────────────────────────────────────────
    ("Bibimbap Bar",        3, 4, "Build-your-own bibimbap concept works really well. Fresh ingredients and good gochujang."),
    ("Bibimbap Bar",        5, 5, "The stone pot bibimbap with crispy rice on the bottom is perfection."),
    ("K-BBQ Grill House",   5, 5, "All-you-can-eat KBBQ with excellent quality meats and unlimited banchan. Outstanding value."),
    ("K-BBQ Grill House",   2, 4, "Fun tabletop grill experience. The chadolbaegi and galbi are the standout cuts."),
    ("Tteokbokki Town",     5, 5, "The rose tteokbokki is creamy, spicy, and addictive. Korean street food done authentically."),
    ("Tteokbokki Town",     6, 4, "Great snacking spot. The corn dog and tteokbokki combo is exactly what you want."),
    # ── Vietnamese ───────────────────────────────────────────────────────────
    ("Pho Saigon",          6, 5, "The 24-hour bone broth pho is everything it should be — clear, rich, and deeply savory."),
    ("Pho Saigon",          2, 4, "Generous portions and authentic flavors. The brisket and tendon combo is outstanding."),
    ("Banh Mi & More",      6, 5, "The crusty baguette with house-made pate is extraordinary. Best banh mi in San Jose."),
    ("Banh Mi & More",      3, 4, "Incredibly fresh and flavorful for the price. The lemongrass chicken banh mi is fantastic."),
    ("Spring Roll Garden",  3, 5, "Fresh spring rolls with vibrant herbs and a bright peanut dipping sauce. Clean and healthy."),
    ("Spring Roll Garden",  6, 4, "The vermicelli bowls are light and flavorful. Great vegan options across the whole menu."),
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

    # Build name→id map for all new restaurants (whether just added or already present)
    name_to_id = {
        r["name"]: r["_id"]
        for r in db.restaurants.find(
            {"name": {"$in": [r["name"] for r in NEW_RESTAURANTS]}},
            {"name": 1}
        )
    }

    print(f"\nSeeding reviews for new restaurants...")
    review_count = 0
    rating_totals: dict = {}
    for rest_name, user_id, rating, comment in NEW_REVIEWS:
        rest_id = name_to_id.get(rest_name)
        if rest_id is None:
            continue
        # Skip if a seeded review by this user for this restaurant already exists
        if db.reviews.find_one({"user_id": user_id, "restaurant_id": rest_id, "is_seeded": True}):
            continue
        rev_id = _next_id(db, "reviews")
        db.reviews.insert_one({
            "_id": rev_id,
            "user_id": user_id,
            "restaurant_id": rest_id,
            "rating": rating,
            "comment": comment,
            "photos": [],
            "created_at": _ago(days=60 - review_count * 1),
            "updated_at": _ago(days=60 - review_count * 1),
            **_seed_metadata(),
        })
        rating_totals.setdefault(rest_id, []).append(rating)
        review_count += 1

    # Recalculate avg_rating and review_count for each affected restaurant
    for rest_id, ratings in rating_totals.items():
        all_ratings = [
            r["rating"] for r in db.reviews.find({"restaurant_id": rest_id}, {"rating": 1})
        ]
        avg = round(sum(all_ratings) / len(all_ratings), 2)
        db.restaurants.update_one(
            {"_id": rest_id},
            {"$set": {"avg_rating": avg, "review_count": len(all_ratings)}}
        )
    print(f"  {review_count} reviews added.")

    total = db.restaurants.count_documents({})
    print(f"\nDone! Added {added} restaurants. Total in DB: {total}")

if __name__ == "__main__":
    main()
