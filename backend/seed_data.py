#!/usr/bin/env python3
"""
ForkFinder demo seed data script.

Usage (run from the backend/ directory):
  python seed_data.py          # insert seed data (safe – skips if data exists)
  python seed_data.py --wipe   # drop all seed data first, then re-seed
  python seed_data.py --sql    # print SQL INSERT statements to stdout (no DB)

Prerequisites:
  pip install -r requirements.txt
  # Ensure backend/.env has a valid DATABASE_URL pointing to MySQL
  # Tables must exist: start the FastAPI app once to auto-create them
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")  # allow imports from app/

from app.database import SessionLocal
from app.models.conversation import Conversation, ConversationMessage
from app.models.favorite import Favorite
from app.models.restaurant import Restaurant, RestaurantClaim
from app.models.review import Review
from app.models.user import User, UserPreferences
from app.utils.auth import hash_password

# ---------------------------------------------------------------------------
# Timestamps  (spread over the past 6 months for realistic history)
# ---------------------------------------------------------------------------

def _ago(**kwargs):
    return datetime.utcnow() - timedelta(**kwargs)


# ---------------------------------------------------------------------------
# Raw data definitions
# ---------------------------------------------------------------------------

USERS = [
    # Reviewers
    dict(
        email="user@demo.com", name="Jane Doe", role="user",
        phone="+1 (415) 555-0110",
        about_me="Bay Area food blogger and amateur cookbook author. "
                 "I chase after the perfect carbonara and the best Mission burrito.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Italian", gender="female",
    ),
    dict(
        email="marcus@demo.com", name="Marcus Johnson", role="user",
        phone="+1 (510) 555-0221",
        about_me="Oakland native. BBQ purist, sports bar regular, "
                 "and firm believer that the best food is always the cheapest.",
        city="Oakland", state="CA", country="United States",
        languages="English", gender="male",
    ),
    dict(
        email="priya@demo.com", name="Priya Patel", role="user",
        phone="+1 (415) 555-0332",
        about_me="Vegetarian foodie with a weakness for butter chicken (yes, really). "
                 "Mediterranean and Indian cuisine are my spiritual home.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Hindi, Gujarati", gender="female",
    ),
    dict(
        email="alex@demo.com", name="Alex Rivera", role="user",
        phone="+1 (415) 555-0443",
        about_me="Fine dining enthusiast and occasional Michelin chaser. "
                 "If the omakase has more than 12 courses, I'm already there.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Spanish, French", gender="non-binary",
    ),
    dict(
        email="emily@demo.com", name="Emily Chen", role="user",
        phone="+1 (415) 555-0554",
        about_me="Dim sum devotee. I arrive at Dragon Garden before it opens "
                 "and I regret nothing. Ask me about the best soup dumplings in SF.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Mandarin, Cantonese", gender="female",
    ),
    # Owners
    dict(
        email="owner@demo.com", name="Mario Rossi", role="owner",
        phone="+1 (415) 555-0601",
        about_me="Third-generation restaurateur from Naples. I opened "
                 "Ristorante Bello in 2009 and haven't looked back.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Italian", gender="male",
    ),
    dict(
        email="wei@demo.com", name="Wei Zhang", role="owner",
        phone="+1 (415) 555-0702",
        about_me="Grew up in Hong Kong, trained in Tokyo. My restaurants "
                 "bridge Cantonese tradition and Japanese precision.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Mandarin, Cantonese, Japanese", gender="male",
    ),
    dict(
        email="sofia@demo.com", name="Sofia Hernandez", role="owner",
        phone="+1 (415) 555-0803",
        about_me="Oaxacan roots, California soul. My family's recipes are "
                 "the foundation of everything we cook.",
        city="San Francisco", state="CA", country="United States",
        languages="English, Spanish", gender="female",
    ),
]

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

# Restaurant data: (creator_email, claimer_email_or_None, dict)
RESTAURANTS = [
    ("user@demo.com", "owner@demo.com", dict(
        name="Ristorante Bello",
        description="Authentic Neapolitan pizza and handmade pasta in a warm, candlelit "
                    "dining room. Family recipes passed down three generations. Our wood-fired "
                    "oven, imported from Naples in 2009, produces the crispest cornicione in "
                    "the city. Reserve early on weekends.",
        cuisine_type="Italian",
        price_range="$$",
        address="540 Columbus Ave",
        city="San Francisco", state="CA", country="United States", zip_code="94133",
        phone="+1 (415) 555-0101",
        website="https://ristorantebello.example.com",
        latitude=37.7991, longitude=-122.4076,
        hours=json.dumps({
            "monday": "11:30am – 10:00pm", "tuesday": "11:30am – 10:00pm",
            "wednesday": "11:30am – 10:00pm", "thursday": "11:30am – 10:00pm",
            "friday": "11:30am – 11:00pm", "saturday": "10:00am – 11:00pm",
            "sunday": "10:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4+5)/3, 2), review_count=3, is_claimed=True,
    )),
    ("user@demo.com", "owner@demo.com", dict(
        name="Bella Vista Rooftop",
        description="Perched atop a Union Square hotel with sweeping bay views, Bella Vista "
                    "serves Italian-American kitchen classics alongside craft cocktails. "
                    "The wood-fired flatbreads and the hand-rolled gnocchi are must-orders. "
                    "Heated outdoor seating available year-round.",
        cuisine_type="Italian",
        price_range="$$$",
        address="200 Powell St",
        city="San Francisco", state="CA", country="United States", zip_code="94102",
        phone="+1 (415) 555-0606",
        website="https://bellavistasf.example.com",
        latitude=37.7879, longitude=-122.4075,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "4:00pm – 12:00am", "thursday": "4:00pm – 12:00am",
            "friday": "3:00pm – 1:00am", "saturday": "2:00pm – 1:00am",
            "sunday": "2:00pm – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+4)/2, 2), review_count=2, is_claimed=True,
    )),
    ("user@demo.com", "wei@demo.com", dict(
        name="Dragon Garden",
        description="Modern dim sum and traditional Cantonese cuisine in the heart of "
                    "Chinatown. Steamer baskets crafted fresh every morning from market produce. "
                    "The har gow and XO chili crab have won citywide accolades. "
                    "Arrive before 10am on weekends or expect an hour wait.",
        cuisine_type="Chinese",
        price_range="$$",
        address="456 Stockton St",
        city="San Francisco", state="CA", country="United States", zip_code="94108",
        phone="+1 (415) 555-0202",
        website="https://dragongardensf.example.com",
        latitude=37.7955, longitude=-122.4066,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "10:00am – 9:00pm",
            "wednesday": "10:00am – 9:00pm", "thursday": "10:00am – 9:00pm",
            "friday": "10:00am – 10:00pm", "saturday": "9:00am – 10:00pm",
            "sunday": "9:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4)/2, 2), review_count=2, is_claimed=True,
    )),
    ("marcus@demo.com", "wei@demo.com", dict(
        name="Sakura Omakase",
        description="An intimate 12-seat counter experience in the Financial District. "
                    "Chef Kenji's 18-course Edomae omakase changes with the seasons — "
                    "think Hokkaido uni, aged bluefin toro, and house-made tamago. "
                    "Reservations open 60 days in advance; they sell out in minutes.",
        cuisine_type="Japanese",
        price_range="$$$$",
        address="50 Belden Pl",
        city="San Francisco", state="CA", country="United States", zip_code="94104",
        phone="+1 (415) 555-0505",
        website="https://sakuraomakase.example.com",
        latitude=37.7912, longitude=-122.4016,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "6:00pm – 10:30pm", "thursday": "6:00pm – 10:30pm",
            "friday": "6:00pm – 11:00pm", "saturday": "5:30pm – 11:00pm",
            "sunday": "5:30pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+5)/2, 2), review_count=2, is_claimed=True,
    )),
    ("priya@demo.com", None, dict(
        name="Ramen House Natori",
        description="No-frills tonkotsu and shoyu ramen shop in Japantown. "
                    "The 18-hour pork bone broth is the real thing: milky, rich, and deeply savory. "
                    "Noodles made in-house daily. Cash only, no substitutions, no apologies.",
        cuisine_type="Japanese",
        price_range="$",
        address="1737 Post St",
        city="San Francisco", state="CA", country="United States", zip_code="94115",
        phone="+1 (415) 555-0404",
        latitude=37.7851, longitude=-122.4312,
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "12:00pm – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+4)/2, 2), review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", "sofia@demo.com", dict(
        name="Taqueria La Paloma",
        description="Family-owned Mission taqueria with 20 years of slow-braised carnitas "
                    "and hand-ground masa. The al pastor spit turns from 7am; the carne asada "
                    "burrito is the size of a newborn. Fresh salsas made hourly. "
                    "Breakfast burritos until noon, Fri-Sun.",
        cuisine_type="Mexican",
        price_range="$",
        address="3000 Mission St",
        city="San Francisco", state="CA", country="United States", zip_code="94110",
        phone="+1 (415) 555-0404",
        latitude=37.7432, longitude=-122.4194,
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 10:00pm", "saturday": "8:00am – 10:00pm",
            "sunday": "9:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+5+4)/3, 2), review_count=3, is_claimed=True,
    )),
    ("alex@demo.com", "sofia@demo.com", dict(
        name="Casa Oaxaca",
        description="Chef Sofia's homage to her grandmother's kitchen in Oaxaca City. "
                    "The mole negro takes three days to prepare. The tlayudas are "
                    "crispy, enormous, and life-changing. Mezcal list curated by the chef herself. "
                    "Reservations strongly recommended.",
        cuisine_type="Mexican",
        price_range="$$$",
        address="400 Grove St",
        city="San Francisco", state="CA", country="United States", zip_code="94102",
        phone="+1 (415) 555-0707",
        website="https://casaoaxaca.example.com",
        latitude=37.7771, longitude=-122.4225,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:00pm",
            "wednesday": "5:30pm – 10:00pm", "thursday": "5:30pm – 10:00pm",
            "friday": "5:30pm – 11:00pm", "saturday": "5:30pm – 11:00pm",
            "sunday": "5:30pm – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+5)/2, 2), review_count=2, is_claimed=True,
    )),
    ("alex@demo.com", None, dict(
        name="Spice Route",
        description="Northern Indian cuisine with a modern California sensibility. "
                    "The lamb rogan josh braises for six hours. The dal makhani is "
                    "legendary — same pot, low heat, all day. Extensive vegetarian "
                    "menu with 12 rotating daily specials.",
        cuisine_type="Indian",
        price_range="$$$",
        address="789 Valencia St",
        city="San Francisco", state="CA", country="United States", zip_code="94110",
        phone="+1 (415) 555-0303",
        latitude=37.7612, longitude=-122.4212,
        hours=json.dumps({
            "monday": "5:00pm – 10:00pm", "tuesday": "5:00pm – 10:00pm",
            "wednesday": "5:00pm – 10:00pm", "thursday": "5:00pm – 10:00pm",
            "friday": "5:00pm – 11:00pm", "saturday": "12:00pm – 11:00pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4)/2, 2), review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Bangkok Noodles",
        description="A 14-seat hole-in-the-wall in Oakland serving pad see ew and "
                    "drunken noodles so good the wait is always 30 minutes. "
                    "The khao soi — Chiang Mai curry noodle soup — has a cult following. "
                    "Bring cash and patience; it is absolutely worth it.",
        cuisine_type="Thai",
        price_range="$",
        address="388 Grand Ave",
        city="Oakland", state="CA", country="United States", zip_code="94610",
        phone="+1 (510) 555-0809",
        latitude=37.8103, longitude=-122.2574,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:00pm",
            "wednesday": "11:30am – 9:00pm", "thursday": "11:30am – 9:00pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "12:00pm – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+3)/2, 2), review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="The Smokehouse",
        description="Texas-style BBQ in Temescal. Brisket smoked low and slow over "
                    "post oak for 14–18 hours. The ribs are fall-off-the-bone and the "
                    "sides — jalapeño mac, collard greens, smoked beans — are almost as "
                    "good as the meat. Opens at 11am; sells out by 7pm most days.",
        cuisine_type="American",
        price_range="$$",
        address="4031 Broadway",
        city="Oakland", state="CA", country="United States", zip_code="94611",
        phone="+1 (510) 555-0910",
        latitude=37.8318, longitude=-122.2610,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 9:00pm", "saturday": "11:00am – 9:00pm",
            "sunday": "11:00am – 7:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=5.0, review_count=1, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Blue Plate Diner",
        description="An old-school Castro diner serving American comfort food. "
                    "The meatloaf, the grilled cheese, and the chocolate milkshake "
                    "are exactly what you want after a long week. "
                    "Nothing fancy, no reservations, always a wait — and worth every minute.",
        cuisine_type="American",
        price_range="$",
        address="3218 Mission St",
        city="San Francisco", state="CA", country="United States", zip_code="94110",
        phone="+1 (415) 555-1001",
        latitude=37.7463, longitude=-122.4206,
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 10:00pm", "saturday": "8:00am – 10:00pm",
            "sunday": "8:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=3.0, review_count=1, is_claimed=False,
    )),
    ("marcus@demo.com", "sofia@demo.com", dict(
        name="Olive Branch",
        description="A Marina Mediterranean that sources its olive oil directly from a "
                    "small Greek co-op in Crete. The whole roasted fish changes daily. "
                    "The mezze spread — hummus, tabbouleh, lamb kofta — is the way to go "
                    "for groups. Outdoor patio with heat lamps.",
        cuisine_type="Mediterranean",
        price_range="$$",
        address="2020 Chestnut St",
        city="San Francisco", state="CA", country="United States", zip_code="94123",
        phone="+1 (415) 555-1102",
        website="https://olivebranchsf.example.com",
        latitude=37.8001, longitude=-122.4370,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 9:30pm",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:30pm", "saturday": "11:30am – 10:30pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4)/2, 2), review_count=2, is_claimed=True,
    )),
    ("marcus@demo.com", None, dict(
        name="Seoul Kitchen",
        description="Korean BBQ and modern bibimbap in the Tenderloin. "
                    "The galbi (short rib) marinated for 24 hours is the table centerpiece. "
                    "Banchan changes weekly; the house kimchi is house-fermented for 6 weeks. "
                    "Lunch specials until 3pm are an absurd deal.",
        cuisine_type="Korean",
        price_range="$$",
        address="806 Larkin St",
        city="San Francisco", state="CA", country="United States", zip_code="94109",
        phone="+1 (415) 555-1203",
        latitude=37.7829, longitude=-122.4182,
        hours=json.dumps({
            "monday": "11:00am – 10:00pm", "tuesday": "11:00am – 10:00pm",
            "wednesday": "11:00am – 10:00pm", "thursday": "11:00am – 10:00pm",
            "friday": "11:00am – 11:00pm", "saturday": "11:00am – 11:00pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+5)/2, 2), review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Pho Saigon",
        description="A Tenderloin institution for over 30 years. The pho broth simmers "
                    "for 12 hours with star anise, cloves, and beef bones. Order the "
                    "#1 (rare beef + brisket) and load the table with hoisin, sriracha, "
                    "bean sprouts, and Thai basil. Open late, cheap, and glorious.",
        cuisine_type="Vietnamese",
        price_range="$",
        address="709 Larkin St",
        city="San Francisco", state="CA", country="United States", zip_code="94109",
        phone="+1 (415) 555-1304",
        latitude=37.7821, longitude=-122.4181,
        hours=json.dumps({
            "monday": "9:00am – 10:00pm", "tuesday": "9:00am – 10:00pm",
            "wednesday": "9:00am – 10:00pm", "thursday": "9:00am – 10:00pm",
            "friday": "9:00am – 11:00pm", "saturday": "9:00am – 11:00pm",
            "sunday": "9:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((4+4)/2, 2), review_count=2, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Café Madeleine",
        description="A slice of Paris in Hayes Valley. Michelin Bib Gourmand 2023. "
                    "The duck confit is prepared sous-vide for 48 hours and finished "
                    "in brown butter. The cheese cart is a minor religious experience. "
                    "Prix-fixe available Friday and Saturday evenings.",
        cuisine_type="French",
        price_range="$$$",
        address="260 Gough St",
        city="San Francisco", state="CA", country="United States", zip_code="94102",
        phone="+1 (415) 555-1405",
        website="https://cafemadeleine.example.com",
        latitude=37.7756, longitude=-122.4222,
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:30pm", "saturday": "11:30am – 10:30pm",
            "sunday": "11:30am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4)/2, 2), review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="The Green Bowl",
        description="100% plant-based kitchen in Berkeley serving grain bowls, "
                    "jackfruit tacos, and a rotating cast of globally inspired vegan dishes. "
                    "Nothing processed, nothing fake — just whole ingredients treated with care. "
                    "The cashew queso and the miso-glazed eggplant are the stars.",
        cuisine_type="Vegan",
        price_range="$",
        address="2115 Center St",
        city="Berkeley", state="CA", country="United States", zip_code="94704",
        phone="+1 (510) 555-1506",
        website="https://thegreenbowl.example.com",
        latitude=37.8716, longitude=-122.2727,
        hours=json.dumps({
            "monday": "11:00am – 8:00pm", "tuesday": "11:00am – 8:00pm",
            "wednesday": "11:00am – 8:00pm", "thursday": "11:00am – 8:00pm",
            "friday": "11:00am – 9:00pm", "saturday": "10:00am – 9:00pm",
            "sunday": "10:00am – 7:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.0, review_count=1, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="The Wharf Kitchen",
        description="Straight-from-the-boat Dungeness crab, oysters from Tomales Bay, "
                    "and wood-grilled halibut at Fisherman's Wharf. Ask your server what "
                    "came in this morning — the chalkboard changes daily. "
                    "The lobster bisque is the best in the city, period.",
        cuisine_type="Seafood",
        price_range="$$$",
        address="99 Jefferson St",
        city="San Francisco", state="CA", country="United States", zip_code="94133",
        phone="+1 (415) 555-1607",
        website="https://wharfkitchensf.example.com",
        latitude=37.8080, longitude=-122.4160,
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "10:00am – 10:00pm",
            "sunday": "10:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.0, review_count=1, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Sunday Morning Café",
        description="Noe Valley's favorite all-day brunch spot. The ricotta pancakes, "
                    "the smashed avocado toast with everything bagel seasoning, and "
                    "the lemon curd Dutch baby are all worth the weekend crowd. "
                    "Bottomless mimosas until 2pm. Reservations for 6+ only.",
        cuisine_type="American",
        price_range="$$",
        address="4000 24th St",
        city="San Francisco", state="CA", country="United States", zip_code="94114",
        phone="+1 (415) 555-1708",
        latitude=37.7514, longitude=-122.4319,
        hours=json.dumps({
            "monday": "8:00am – 3:00pm", "tuesday": "8:00am – 3:00pm",
            "wednesday": "8:00am – 3:00pm", "thursday": "8:00am – 3:00pm",
            "friday": "8:00am – 4:00pm", "saturday": "7:30am – 4:00pm",
            "sunday": "7:30am – 4:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=round((5+4+5)/3, 2), review_count=3, is_claimed=False,
    )),

    # =========================================================================
    # San Jose & South Bay — expanded dataset
    # =========================================================================

    # --- San Jose · Japanese ---
    ("user@demo.com", "wei@demo.com", dict(
        name="Sushi Kakimoto",
        description="Upscale nigiri and omakase in downtown San Jose. Chef Kakimoto "
                    "trained for 12 years in Osaka before bringing his craft to Silicon Valley. "
                    "The seasonal omakase (15 courses) features fish flown in twice weekly from "
                    "Tsukiji. The sake selection is curated and extensive.",
        cuisine_type="Japanese", price_range="$$$",
        address="87 N San Pedro St", city="San Jose", state="CA",
        country="United States", zip_code="95110",
        phone="+1 (408) 555-2001",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:00pm",
            "wednesday": "5:30pm – 10:00pm", "thursday": "5:30pm – 10:00pm",
            "friday": "5:30pm – 11:00pm", "saturday": "5:00pm – 11:00pm",
            "sunday": "5:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.8, review_count=4, is_claimed=True,
    )),
    ("marcus@demo.com", None, dict(
        name="Hanabi Ramen",
        description="Hakata-style tonkotsu ramen in the heart of San Jose Japantown. "
                    "The broth is simmered 20 hours for a rich, milky consistency. "
                    "Build-your-own bowls with premium toppings: chashu, soft egg, black garlic oil. "
                    "Counter seating only; opens at 11am and often sells out of broth by 8pm.",
        cuisine_type="Japanese", price_range="$",
        address="240 Jackson St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2002",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "12:00pm – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=False,
    )),
    ("priya@demo.com", "wei@demo.com", dict(
        name="Izakaya Maru",
        description="Lively Japanese gastropub in San Jose's SoFA district. "
                    "The menu reads like a greatest hits of izakaya classics: karaage, "
                    "takoyaki, yakitori skewers over binchotan, and an outstanding selection "
                    "of draft Japanese beers and highballs. Late kitchen until midnight on weekends.",
        cuisine_type="Japanese", price_range="$$",
        address="439 S 1st St", city="San Jose", state="CA",
        country="United States", zip_code="95113",
        phone="+1 (408) 555-2003",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 11:00pm",
            "wednesday": "5:00pm – 11:00pm", "thursday": "5:00pm – 11:00pm",
            "friday": "5:00pm – 12:00am", "saturday": "4:00pm – 12:00am",
            "sunday": "4:00pm – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=3, is_claimed=True,
    )),
    ("emily@demo.com", None, dict(
        name="Tenno Sushi",
        description="Neighborhood sushi bar in Willow Glen with a loyal following since 2005. "
                    "The fish is always fresh and the omakase chef's selection changes daily "
                    "based on market availability. Great value for the quality; BYOB friendly.",
        cuisine_type="Japanese", price_range="$$",
        address="1335 Lincoln Ave", city="San Jose", state="CA",
        country="United States", zip_code="95125",
        phone="+1 (408) 555-2004",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:30pm",
            "wednesday": "11:30am – 9:30pm", "thursday": "11:30am – 9:30pm",
            "friday": "11:30am – 10:00pm", "saturday": "12:00pm – 10:00pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Miyuki Japanese Restaurant",
        description="Family-run Japanese restaurant in East San Jose open for over 25 years. "
                    "Teriyaki, tempura, chirashi bowls, and proper miso soup made from dashi scratch. "
                    "Comfort food done faithfully. The bento lunch box is one of the best deals "
                    "in the South Bay.",
        cuisine_type="Japanese", price_range="$$",
        address="1712 Alum Rock Ave", city="San Jose", state="CA",
        country="United States", zip_code="95116",
        phone="+1 (408) 555-2005",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 9:30pm", "saturday": "11:00am – 9:30pm",
            "sunday": "12:00pm – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Yakitori Kohji",
        description="Intimate skewer bar in San Jose Japantown specializing in yakitori "
                    "over imported Japanese charcoal. Every part of the chicken is represented "
                    "— thigh, liver, skin, cartilage, and the prized oyster. "
                    "Pair with cold Sapporo or shochu highballs. Reservations recommended.",
        cuisine_type="Japanese", price_range="$$",
        address="565 N 6th St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2006",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:30pm",
            "wednesday": "5:30pm – 10:30pm", "thursday": "5:30pm – 10:30pm",
            "friday": "5:30pm – 11:30pm", "saturday": "5:00pm – 11:30pm",
            "sunday": "5:00pm – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.7, review_count=3, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Kura Revolving Sushi",
        description="High-tech conveyor belt sushi with fresh nigiri at affordable prices. "
                    "Touch-screen tablets, plates arrive by express train, and the touchless "
                    "plates stay covered until you grab them. Great for families and groups "
                    "who want quality sushi without the ceremony.",
        cuisine_type="Japanese", price_range="$$",
        address="5550 Rossmore Dr", city="San Jose", state="CA",
        country="United States", zip_code="95138",
        phone="+1 (408) 555-2007",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=5, is_claimed=False,
    )),

    # --- San Jose · Chinese ---
    ("emily@demo.com", "wei@demo.com", dict(
        name="Pearl River Dim Sum",
        description="Weekend dim sum institution in the Lion Plaza shopping center. "
                    "Arrive before 10am or wait an hour. The shrimp cheung fun, pineapple buns, "
                    "and char siu baos are the must-orders. Over 60 items roll out on carts "
                    "from 9am–2pm. Cash preferred.",
        cuisine_type="Chinese", price_range="$$",
        address="1828 Tully Rd", city="San Jose", state="CA",
        country="United States", zip_code="95122",
        phone="+1 (408) 555-2101",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "10:00am – 9:00pm",
            "wednesday": "10:00am – 9:00pm", "thursday": "10:00am – 9:00pm",
            "friday": "9:00am – 10:00pm", "saturday": "9:00am – 10:00pm",
            "sunday": "9:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=4, is_claimed=True,
    )),
    ("user@demo.com", None, dict(
        name="Sichuan Garden",
        description="Authentic Chengdu-style Sichuan food in East San Jose — not the "
                    "Americanized version. The mapo tofu is properly numbing, the dan dan noodles "
                    "have real Sichuan peppercorn heat, and the boiled fish in chili broth is "
                    "the signature. Bring your heat tolerance.",
        cuisine_type="Chinese", price_range="$$",
        address="1690 Hostetter Rd", city="San Jose", state="CA",
        country="United States", zip_code="95131",
        phone="+1 (408) 555-2102",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=3, is_claimed=False,
    )),
    ("priya@demo.com", "wei@demo.com", dict(
        name="Golden Phoenix Seafood",
        description="Cantonese banquet-style seafood in San Jose Chinatown. "
                    "Live tanks of Dungeness crab, lobster, and geoduck line the entrance. "
                    "The whole steamed fish with ginger and scallion is impeccable. "
                    "Popular for family gatherings; private rooms available for large parties.",
        cuisine_type="Chinese", price_range="$$$",
        address="125 E San Fernando St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2103",
        hours=json.dumps({
            "monday": "11:00am – 10:00pm", "tuesday": "11:00am – 10:00pm",
            "wednesday": "11:00am – 10:00pm", "thursday": "11:00am – 10:00pm",
            "friday": "11:00am – 10:30pm", "saturday": "10:30am – 10:30pm",
            "sunday": "10:30am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=3, is_claimed=True,
    )),
    ("alex@demo.com", None, dict(
        name="Jade Garden Noodle House",
        description="Hand-pulled noodles and dumplings fresh to order in East San Jose. "
                    "The beef noodle soup with house-pulled flat noodles is the signature. "
                    "Scallion pancakes arrive flaky and blistered from the griddle. "
                    "Cheap, fast, and deeply satisfying.",
        cuisine_type="Chinese", price_range="$",
        address="1355 Blossom Hill Rd", city="San Jose", state="CA",
        country="United States", zip_code="95118",
        phone="+1 (408) 555-2104",
        hours=json.dumps({
            "monday": "11:00am – 8:30pm", "tuesday": "11:00am – 8:30pm",
            "wednesday": "11:00am – 8:30pm", "thursday": "11:00am – 8:30pm",
            "friday": "11:00am – 9:00pm", "saturday": "11:00am – 9:00pm",
            "sunday": "11:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Hot Wok Mongolian BBQ",
        description="Build-your-own stir-fry Mongolian BBQ where you fill your bowl with "
                    "proteins, vegetables, and sauces then watch it cook on a massive iron griddle. "
                    "Great for groups, generous portions, and kids love it. "
                    "Lunch buffet weekdays is an excellent deal.",
        cuisine_type="Chinese", price_range="$$",
        address="3090 Silver Creek Rd", city="San Jose", state="CA",
        country="United States", zip_code="95121",
        phone="+1 (408) 555-2105",
        hours=json.dumps({
            "monday": "11:30am – 9:00pm", "tuesday": "11:30am – 9:00pm",
            "wednesday": "11:30am – 9:00pm", "thursday": "11:30am – 9:00pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=3.9, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Korean ---
    ("emily@demo.com", None, dict(
        name="Gogi Korean BBQ",
        description="The go-to Korean BBQ in San Jose for table grills done right. "
                    "Premium marbled beef, USDA choice galbi, and samgyeopsal (pork belly) "
                    "sizzle over live charcoal. Unlimited banchan spread includes six rotating "
                    "sides. The doenjang jjigae (fermented soybean stew) is homestyle comfort food.",
        cuisine_type="Korean", price_range="$$",
        address="1029 E Capitol Expressway", city="San Jose", state="CA",
        country="United States", zip_code="95121",
        phone="+1 (408) 555-2201",
        hours=json.dumps({
            "monday": "11:00am – 10:00pm", "tuesday": "11:00am – 10:00pm",
            "wednesday": "11:00am – 10:00pm", "thursday": "11:00am – 10:00pm",
            "friday": "11:00am – 11:00pm", "saturday": "11:00am – 11:00pm",
            "sunday": "12:00pm – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=4, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Bibimbap House",
        description="Casual Korean lunch spot in downtown San Jose focused on bibimbap "
                    "and Korean comfort classics. The stone pot bibimbap arrives sizzling "
                    "and properly crispy on the bottom. Affordable lunch sets include "
                    "banchan, soup, and rice. Perfect for a fast, satisfying weekday meal.",
        cuisine_type="Korean", price_range="$",
        address="151 W Santa Clara St", city="San Jose", state="CA",
        country="United States", zip_code="95113",
        phone="+1 (408) 555-2202",
        hours=json.dumps({
            "monday": "10:30am – 8:00pm", "tuesday": "10:30am – 8:00pm",
            "wednesday": "10:30am – 8:00pm", "thursday": "10:30am – 8:00pm",
            "friday": "10:30am – 9:00pm", "saturday": "11:00am – 9:00pm",
            "sunday": "Closed",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Jang Su Jang",
        description="A San Jose institution since 1999. Authentic Korean home cooking "
                    "without compromise — the kind of food that makes you understand why "
                    "Korean grandmothers spend all day in the kitchen. The ox bone soup "
                    "(seolleongtang) simmers overnight. Open late on weekends.",
        cuisine_type="Korean", price_range="$$",
        address="4819 Quimby Ave", city="San Jose", state="CA",
        country="United States", zip_code="95148",
        phone="+1 (408) 555-2203",
        hours=json.dumps({
            "monday": "11:00am – 10:30pm", "tuesday": "11:00am – 10:30pm",
            "wednesday": "11:00am – 10:30pm", "thursday": "11:00am – 10:30pm",
            "friday": "11:00am – 11:30pm", "saturday": "11:00am – 11:30pm",
            "sunday": "11:00am – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Seoul Garden",
        description="Modern Korean restaurant in Willow Glen with a contemporary take "
                    "on traditional recipes. The japchae (glass noodle stir-fry) is silky "
                    "and fragrant. The kimchi fried rice is made with properly aged kimchi. "
                    "Good vegetarian options including soondubu without meat.",
        cuisine_type="Korean", price_range="$$",
        address="1750 W San Carlos St", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 555-2204",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:30pm", "saturday": "11:00am – 10:30pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Indian ---
    ("priya@demo.com", None, dict(
        name="Udupi Palace",
        description="South Indian vegetarian institution in San Jose serving dosas, "
                    "idlis, vadas, and uttapam since 1994. The masala dosa is crispy, "
                    "enormous, and filled with perfectly spiced potato. The sambar is made "
                    "fresh daily. Affordable, authentic, and deeply satisfying. Vegan-friendly.",
        cuisine_type="Indian", price_range="$",
        address="976 E El Camino Real", city="Sunnyvale", state="CA",
        country="United States", zip_code="94087",
        phone="+1 (408) 555-2301",
        hours=json.dumps({
            "monday": "11:30am – 9:30pm", "tuesday": "11:30am – 9:30pm",
            "wednesday": "11:30am – 9:30pm", "thursday": "11:30am – 9:30pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=3, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Curry Corner",
        description="North Indian lunch and dinner spot in San Jose near the airport corridor. "
                    "The butter chicken is rich and deeply spiced, the garlic naan is made to order, "
                    "and the biryani arrives in a sealed pot. Popular with the tech crowd for "
                    "weekday lunch. Generous portions at honest prices.",
        cuisine_type="Indian", price_range="$$",
        address="1655 N First St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2302",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=3, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Tandoor Palace",
        description="Upscale Indian dining in the Santana Row neighborhood of San Jose. "
                    "The clay-oven tandoor works at full capacity all evening: lamb chops, "
                    "paneer tikka, and seekh kebabs emerge charred and juicy. "
                    "The wine list is surprisingly thoughtful for an Indian restaurant.",
        cuisine_type="Indian", price_range="$$$",
        address="3055 Olin Ave", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 555-2303",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 10:00pm",
            "wednesday": "5:00pm – 10:00pm", "thursday": "5:00pm – 10:00pm",
            "friday": "5:00pm – 11:00pm", "saturday": "12:00pm – 11:00pm",
            "sunday": "12:00pm – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Dosa Factory",
        description="Quick-service South Indian dosa bar near San Jose State University. "
                    "Order at the counter: paper dosa, ghee dosa, or the special rava masala. "
                    "The coconut chutney is made fresh twice daily and the filter coffee "
                    "is the real Chennai deal. Student budget-friendly and fast.",
        cuisine_type="Indian", price_range="$",
        address="392 S 1st St", city="San Jose", state="CA",
        country="United States", zip_code="95113",
        phone="+1 (408) 555-2304",
        hours=json.dumps({
            "monday": "10:30am – 8:00pm", "tuesday": "10:30am – 8:00pm",
            "wednesday": "10:30am – 8:00pm", "thursday": "10:30am – 8:00pm",
            "friday": "10:30am – 9:00pm", "saturday": "10:00am – 9:00pm",
            "sunday": "11:00am – 7:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Royal Punjab",
        description="Punjabi home cooking in East San Jose with a loyal neighborhood following. "
                    "The sarson ka saag with makki di roti is a seasonal highlight. "
                    "The lentil dal tadka and aloo paratha are everyday classics done with care. "
                    "Family-run since 2001; the owner's mother still cooks the curries.",
        cuisine_type="Indian", price_range="$$",
        address="2580 Alum Rock Ave", city="San Jose", state="CA",
        country="United States", zip_code="95116",
        phone="+1 (408) 555-2305",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Mexican ---
    ("marcus@demo.com", "sofia@demo.com", dict(
        name="Taqueria Los Compadres",
        description="Standing-room-only taqueria on Story Road that the East San Jose "
                    "community has trusted for 30 years. The carne asada is char-grilled and "
                    "sliced fresh. The horchata is hand-stirred from scratch. "
                    "Two tacos and a drink under $10 — San Jose's best bargain meal.",
        cuisine_type="Mexican", price_range="$",
        address="2051 Story Rd", city="San Jose", state="CA",
        country="United States", zip_code="95122",
        phone="+1 (408) 555-2401",
        hours=json.dumps({
            "monday": "7:00am – 10:00pm", "tuesday": "7:00am – 10:00pm",
            "wednesday": "7:00am – 10:00pm", "thursday": "7:00am – 10:00pm",
            "friday": "7:00am – 11:00pm", "saturday": "7:00am – 11:00pm",
            "sunday": "8:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.7, review_count=4, is_claimed=True,
    )),
    ("user@demo.com", None, dict(
        name="La Fogata Mexican Grill",
        description="Festive interior with colorful murals and a menu anchored by "
                    "regional Mexican specialties. The mole enchiladas use a 34-ingredient "
                    "sauce made from a Puebla family recipe. Margaritas are made with fresh "
                    "lime juice and 100% agave tequila. Great for groups.",
        cuisine_type="Mexican", price_range="$$",
        address="700 Empey Way", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 555-2402",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:30pm", "saturday": "11:00am – 10:30pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=3, is_claimed=False,
    )),
    ("emily@demo.com", "sofia@demo.com", dict(
        name="El Gallo Giro",
        description="Old-school Mexican with an open rotisserie turning all day. "
                    "The pollo asado is marinated in achiote and citrus, juicy and charred. "
                    "Order it with fresh tortillas, guacamole, and the smoky salsa roja "
                    "that comes in a little clay bowl. Cash preferred; always packed.",
        cuisine_type="Mexican", price_range="$",
        address="3950 E Hills Dr", city="San Jose", state="CA",
        country="United States", zip_code="95127",
        phone="+1 (408) 555-2403",
        hours=json.dumps({
            "monday": "9:00am – 9:00pm", "tuesday": "9:00am – 9:00pm",
            "wednesday": "9:00am – 9:00pm", "thursday": "9:00am – 9:00pm",
            "friday": "9:00am – 10:00pm", "saturday": "9:00am – 10:00pm",
            "sunday": "9:00am – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=3, is_claimed=True,
    )),
    ("alex@demo.com", None, dict(
        name="Hacienda Restaurant",
        description="Upscale Mexican with a full mezcal and tequila bar in downtown San Jose. "
                    "The tableside guacamole is a ritual. The cochinita pibil is slow-roasted "
                    "overnight in banana leaves. Live mariachi Friday and Saturday evenings.",
        cuisine_type="Mexican", price_range="$$$",
        address="201 S 1st St", city="San Jose", state="CA",
        country="United States", zip_code="95113",
        phone="+1 (408) 555-2404",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 10:00pm",
            "wednesday": "5:00pm – 10:00pm", "thursday": "5:00pm – 10:00pm",
            "friday": "5:00pm – 11:30pm", "saturday": "12:00pm – 11:30pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),

    # --- San Jose · American ---
    ("user@demo.com", "owner@demo.com", dict(
        name="Original Joe's San Jose",
        description="A Silicon Valley landmark since 1956. The kind of place where "
                    "mayors have lunch and generations of families celebrate birthdays. "
                    "The menu reads like a love letter to old-school American Italian — "
                    "Joe's Special, sand dabs, veal scallopini, and an iceberg wedge. "
                    "The bar is a destination in itself.",
        cuisine_type="American", price_range="$$",
        address="301 S 1st St", city="San Jose", state="CA",
        country="United States", zip_code="95113",
        phone="+1 (408) 292-7030",
        website="https://originaljoes.com",
        hours=json.dumps({
            "monday": "11:00am – 10:00pm", "tuesday": "11:00am – 10:00pm",
            "wednesday": "11:00am – 10:00pm", "thursday": "11:00am – 10:00pm",
            "friday": "11:00am – 11:00pm", "saturday": "11:00am – 11:00pm",
            "sunday": "10:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=5, is_claimed=True,
    )),
    ("marcus@demo.com", None, dict(
        name="Henry's Hi-Life",
        description="Legendary BBQ and steakhouse institution in San Jose open since 1960. "
                    "The ribs are sticky-glazed and the steaks are grilled over live mesquite. "
                    "Nothing trendy, nothing ironic — just honest, generous, American food. "
                    "The garlic bread alone is worth the trip.",
        cuisine_type="American", price_range="$$",
        address="301 W St John St", city="San Jose", state="CA",
        country="United States", zip_code="95110",
        phone="+1 (408) 295-5414",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 9:30pm",
            "wednesday": "5:00pm – 9:30pm", "thursday": "5:00pm – 9:30pm",
            "friday": "5:00pm – 10:00pm", "saturday": "5:00pm – 10:00pm",
            "sunday": "4:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=3, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="The Forager Kitchen",
        description="Farm-to-table American cooking in Willow Glen sourcing from local "
                    "Santa Clara Valley farms. The menu changes weekly based on what's "
                    "at market: roasted vegetables, sustainable proteins, heirloom grains. "
                    "The weekend brunch is a neighborhood institution.",
        cuisine_type="American", price_range="$$",
        address="1584 Meridian Ave", city="San Jose", state="CA",
        country="United States", zip_code="95125",
        phone="+1 (408) 555-2502",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "9:00am – 10:00pm",
            "sunday": "9:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=3, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Oak & Ember Burger",
        description="Craft burger joint in downtown San Jose using dry-aged beef "
                    "ground in-house daily. The OAK burger — double patty, aged cheddar, "
                    "caramelized onion, house sauce — is the definitive version. "
                    "Excellent natural-cut fries and a solid craft beer selection on tap.",
        cuisine_type="American", price_range="$",
        address="88 S 4th St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2503",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:30pm", "saturday": "11:00am – 10:30pm",
            "sunday": "12:00pm – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Italian ---
    ("user@demo.com", "owner@demo.com", dict(
        name="Trattoria Volare",
        description="Intimate Willow Glen trattoria with exposed brick and hand-rolled pasta. "
                    "The pappardelle with wild boar ragù is the dish people drive across "
                    "the South Bay for. Tiramisu is the grandmother's recipe. "
                    "Reservations essential; tables of two always prioritized.",
        cuisine_type="Italian", price_range="$$",
        address="1113 Willow St", city="San Jose", state="CA",
        country="United States", zip_code="95125",
        phone="+1 (408) 555-2601",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 9:30pm",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:30pm", "saturday": "5:00pm – 10:30pm",
            "sunday": "5:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=True,
    )),
    ("alex@demo.com", None, dict(
        name="Pasta Bene",
        description="Neighborhood Italian in the Rose Garden district of San Jose. "
                    "Daily fresh pasta, wood-fired pizza, and a short but well-chosen "
                    "Italian wine list. The gnocchi al gorgonzola is the Friday special "
                    "that regulars plan their week around.",
        cuisine_type="Italian", price_range="$$",
        address="1185 Lincoln Ave", city="San Jose", state="CA",
        country="United States", zip_code="95125",
        phone="+1 (408) 555-2602",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 9:30pm",
            "wednesday": "5:00pm – 9:30pm", "thursday": "5:00pm – 9:30pm",
            "friday": "5:00pm – 10:30pm", "saturday": "5:00pm – 10:30pm",
            "sunday": "4:30pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Piacere Ristorante",
        description="Classic Italian-American in the Almaden Valley. "
                    "The chicken parmigiana is the version that defines the dish: "
                    "thin-pounded, perfectly breaded, San Marzano sauce, fresh mozzarella. "
                    "The veal piccata is a Sunday-dinner staple. Family-friendly and consistent.",
        cuisine_type="Italian", price_range="$$",
        address="5506 Snell Ave", city="San Jose", state="CA",
        country="United States", zip_code="95123",
        phone="+1 (408) 555-2603",
        hours=json.dumps({
            "monday": "11:30am – 9:00pm", "tuesday": "11:30am – 9:00pm",
            "wednesday": "11:30am – 9:00pm", "thursday": "11:30am – 9:00pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "12:00pm – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Thai ---
    ("priya@demo.com", None, dict(
        name="Thai Basil San Jose",
        description="Bright, clean Thai restaurant near Santana Row serving classic "
                    "Central Thai dishes done with care. The pad see ew is properly wok-charred, "
                    "the massaman curry is aromatic and rich, and the green papaya salad "
                    "hits the correct balance of sour, sweet, and heat.",
        cuisine_type="Thai", price_range="$",
        address="3041 Stevens Creek Blvd", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 555-2701",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Krung Thai Restaurant",
        description="A favorite of Thai food enthusiasts in North San Jose. "
                    "The khao soi is the best version in the South Bay — rich coconut curry, "
                    "crispy egg noodles on top, pickled mustard greens on the side. "
                    "The lard nar (gravy noodles) are silky and deeply savory.",
        cuisine_type="Thai", price_range="$",
        address="1742 N First St", city="San Jose", state="CA",
        country="United States", zip_code="95112",
        phone="+1 (408) 555-2702",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:00pm",
            "wednesday": "11:30am – 9:00pm", "thursday": "11:30am – 9:00pm",
            "friday": "11:30am – 9:30pm", "saturday": "12:00pm – 9:30pm",
            "sunday": "12:00pm – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Vietnamese ---
    ("emily@demo.com", None, dict(
        name="Pho Garden San Jose",
        description="Clean, well-lit pho restaurant on Story Road in the heart of "
                    "San Jose's Vietnamese community. The broth is crystal clear, "
                    "slow-cooked with charred ginger and cinnamon. "
                    "Order the special combination with rare beef, brisket, and tendon. "
                    "The banh mi are freshly baked each morning.",
        cuisine_type="Vietnamese", price_range="$",
        address="1723 Story Rd", city="San Jose", state="CA",
        country="United States", zip_code="95122",
        phone="+1 (408) 555-2801",
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 10:00pm", "saturday": "7:30am – 10:00pm",
            "sunday": "7:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=3, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Bun Bo Hue An Nam",
        description="Specializing in the spicy Hue-style beef noodle soup that is bolder "
                    "and more complex than pho. The broth gets its heat from lemongrass "
                    "and shrimp paste. The ox tail, pork knuckle, and cubed beef are the "
                    "correct toppings. This is the real deal — not Americanized.",
        cuisine_type="Vietnamese", price_range="$",
        address="3005 Silver Creek Rd", city="San Jose", state="CA",
        country="United States", zip_code="95121",
        phone="+1 (408) 555-2802",
        hours=json.dumps({
            "monday": "9:00am – 8:00pm", "tuesday": "9:00am – 8:00pm",
            "wednesday": "9:00am – 8:00pm", "thursday": "9:00am – 8:00pm",
            "friday": "9:00am – 9:00pm", "saturday": "8:30am – 9:00pm",
            "sunday": "8:30am – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Saigon Village",
        description="Vietnamese restaurant with a broader menu than most — beyond pho "
                    "and banh mi, look for the crispy imperial rolls, lemongrass chicken, "
                    "and the grilled pork chop with broken rice. "
                    "A solid representation of everyday Saigon home cooking.",
        cuisine_type="Vietnamese", price_range="$$",
        address="1148 W San Carlos St", city="San Jose", state="CA",
        country="United States", zip_code="95126",
        phone="+1 (408) 555-2803",
        hours=json.dumps({
            "monday": "10:00am – 9:30pm", "tuesday": "10:00am – 9:30pm",
            "wednesday": "10:00am – 9:30pm", "thursday": "10:00am – 9:30pm",
            "friday": "10:00am – 10:00pm", "saturday": "9:30am – 10:00pm",
            "sunday": "9:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Mediterranean ---
    ("alex@demo.com", None, dict(
        name="Dish Dash",
        description="Middle Eastern comfort food in downtown San Jose with a devoted following. "
                    "The falafel are crisp outside and herb-flecked inside. The lamb shish taouk "
                    "is perfectly charred on the grill. The pomegranate lemonade is the drink "
                    "of the house. Generous portions and sincere hospitality.",
        cuisine_type="Mediterranean", price_range="$$",
        address="190 W St John St", city="San Jose", state="CA",
        country="United States", zip_code="95110",
        phone="+1 (408) 938-4148",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Falafel's Drive-In",
        description="A San Jose original open since 1966. The hand-formed falafel "
                    "have been made the same way for 50+ years: chickpea, parsley, garlic, "
                    "and cumin, fried golden. The falafel burger — falafel patty in a bun "
                    "with tahini and pickles — is a local cult classic.",
        cuisine_type="Mediterranean", price_range="$",
        address="2301 Stevens Creek Blvd", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 294-7886",
        hours=json.dumps({
            "monday": "9:00am – 6:00pm", "tuesday": "9:00am – 6:00pm",
            "wednesday": "9:00am – 6:00pm", "thursday": "9:00am – 6:00pm",
            "friday": "9:00am – 7:00pm", "saturday": "9:00am – 7:00pm",
            "sunday": "10:00am – 5:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.7, review_count=4, is_claimed=False,
    )),

    # --- San Jose · Vegetarian / Vegan ---
    ("priya@demo.com", None, dict(
        name="The Veggie Table",
        description="All-day vegetarian café in the Willow Glen neighborhood. "
                    "The menu spans Indian-inspired bowls, Mediterranean wraps, and "
                    "hearty grain salads. Everything is made without meat, fish, or poultry. "
                    "The cashew-based mac and cheese has converted dedicated carnivores. "
                    "Great smoothie selection.",
        cuisine_type="Vegetarian", price_range="$",
        address="1224 Lincoln Ave", city="San Jose", state="CA",
        country="United States", zip_code="95125",
        phone="+1 (408) 555-2901",
        hours=json.dumps({
            "monday": "10:00am – 8:00pm", "tuesday": "10:00am – 8:00pm",
            "wednesday": "10:00am – 8:00pm", "thursday": "10:00am – 8:00pm",
            "friday": "10:00am – 9:00pm", "saturday": "9:00am – 9:00pm",
            "sunday": "9:00am – 7:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Loving Hut San Jose",
        description="Vegan restaurant with a broad menu of plant-based comfort food. "
                    "The Vietnamese-inspired pho with mushroom broth and rice noodles "
                    "is warming and satisfying. The lemongrass tofu is crispy and fragrant. "
                    "Affordable, clean, and friendly. Great for groups with mixed dietary preferences.",
        cuisine_type="Vegan", price_range="$",
        address="2090 Alum Rock Ave", city="San Jose", state="CA",
        country="United States", zip_code="95116",
        phone="+1 (408) 555-2902",
        hours=json.dumps({
            "monday": "10:30am – 8:30pm", "tuesday": "10:30am – 8:30pm",
            "wednesday": "10:30am – 8:30pm", "thursday": "10:30am – 8:30pm",
            "friday": "10:30am – 9:00pm", "saturday": "10:30am – 9:00pm",
            "sunday": "11:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # --- San Jose · Fusion ---
    ("alex@demo.com", "owner@demo.com", dict(
        name="Santana Row Kitchen",
        description="Upscale California fusion on the Santana Row promenade. "
                    "The menu pulls from Japanese, Mediterranean, and American traditions "
                    "with seasonal California ingredients. The hamachi crudo with yuzu and "
                    "jalapeño is the opener; the wagyu flat iron with miso butter is the finish. "
                    "Strong cocktail and wine program.",
        cuisine_type="Fusion", price_range="$$$",
        address="334 Santana Row", city="San Jose", state="CA",
        country="United States", zip_code="95128",
        phone="+1 (408) 555-3001",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:00pm",
            "wednesday": "5:30pm – 10:00pm", "thursday": "5:30pm – 10:00pm",
            "friday": "5:00pm – 11:00pm", "saturday": "11:30am – 11:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=3, is_claimed=True,
    )),

    # =========================================================================
    # Santa Clara
    # =========================================================================
    ("priya@demo.com", None, dict(
        name="Kabul Afghan Cuisine",
        description="One of the best Afghan restaurants in the Bay Area. "
                    "The aushak (scallion-stuffed dumplings with yogurt and meat sauce) "
                    "is the signature dish. Mantu dumplings, lamb kebabs over saffron rice, "
                    "and freshly baked naan complement an extensive and welcoming menu.",
        cuisine_type="Mediterranean", price_range="$$",
        address="135 El Camino Real", city="Santa Clara", state="CA",
        country="United States", zip_code="95051",
        phone="+1 (408) 241-6622",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:30pm",
            "wednesday": "11:30am – 9:30pm", "thursday": "11:30am – 9:30pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.7, review_count=3, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Sushi Tomi",
        description="Santa Clara's finest sushi destination with a reputation for "
                    "exceptional fish quality and meticulous preparation. "
                    "The omakase here rivals anything in San Francisco at a fraction of the price. "
                    "Chef Tommy has been behind the counter for 22 years. Reservations essential.",
        cuisine_type="Japanese", price_range="$$$",
        address="3546 El Camino Real", city="Santa Clara", state="CA",
        country="United States", zip_code="95051",
        phone="+1 (408) 246-1444",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:00pm", "saturday": "5:00pm – 10:00pm",
            "sunday": "5:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.9, review_count=3, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Vung Tau Restaurant",
        description="Vietnamese comfort food institution in Santa Clara beloved "
                    "by the large Vietnamese community in the South Bay. "
                    "The broken rice plates (com tam) are the specialty — smoky grilled pork, "
                    "a fried egg, and pickled daikon served over fragrant jasmine rice.",
        cuisine_type="Vietnamese", price_range="$",
        address="535 E Santa Clara St", city="Santa Clara", state="CA",
        country="United States", zip_code="95050",
        phone="+1 (408) 288-8869",
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 10:00pm", "saturday": "8:00am – 10:00pm",
            "sunday": "8:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Mango Pickle",
        description="Modern Indian restaurant in Santa Clara celebrating the diversity "
                    "of regional Indian cuisine. Each quarter the menu rotates to feature "
                    "a different state — Kerala, Rajasthan, Bengal, Tamil Nadu. "
                    "The cocktails incorporate Indian spices in clever ways.",
        cuisine_type="Indian", price_range="$$",
        address="3882 El Camino Real", city="Santa Clara", state="CA",
        country="United States", zip_code="95051",
        phone="+1 (408) 555-3102",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:00pm",
            "wednesday": "5:30pm – 10:00pm", "thursday": "5:30pm – 10:00pm",
            "friday": "5:30pm – 11:00pm", "saturday": "11:30am – 11:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Sundance The Steakhouse",
        description="Santa Clara's premier steakhouse for over four decades. "
                    "USDA Prime beef dry-aged in-house. The porterhouse for two is the "
                    "signature. Classic sides — creamed spinach, lobster mac, truffle fries. "
                    "The private dining room books out for tech company events year-round.",
        cuisine_type="American", price_range="$$$",
        address="1921 El Camino Real", city="Santa Clara", state="CA",
        country="United States", zip_code="95050",
        phone="+1 (650) 321-6798",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:00pm – 10:00pm",
            "wednesday": "5:00pm – 10:00pm", "thursday": "5:00pm – 10:00pm",
            "friday": "5:00pm – 11:00pm", "saturday": "5:00pm – 11:00pm",
            "sunday": "5:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Sunnyvale
    # =========================================================================
    ("user@demo.com", None, dict(
        name="Oren's Hummus Sunnyvale",
        description="Israeli street food and mezze in Sunnyvale. The hummus is made "
                    "fresh every three hours from dried chickpeas — silky, warm, and "
                    "topped with olive oil, paprika, and whole chickpeas. The sabich "
                    "sandwich with fried eggplant and hard-boiled egg is outstanding.",
        cuisine_type="Mediterranean", price_range="$$",
        address="153 S Murphy Ave", city="Sunnyvale", state="CA",
        country="United States", zip_code="94086",
        phone="+1 (408) 736-4746",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Saffron Indian Bistro",
        description="Refined Indian cooking in downtown Sunnyvale with an emphasis "
                    "on North Indian Mughal cuisine. The signature biryani comes sealed "
                    "in dough for table-side opening — the steam carries saffron and "
                    "caramelized onion. The kulfi desserts are house-made daily.",
        cuisine_type="Indian", price_range="$$",
        address="130 S Murphy Ave", city="Sunnyvale", state="CA",
        country="United States", zip_code="94086",
        phone="+1 (408) 738-5800",
        hours=json.dumps({
            "monday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "tuesday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "wednesday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "thursday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "friday": "11:30am – 2:30pm, 5:00pm – 10:00pm",
            "saturday": "11:30am – 10:00pm", "sunday": "11:30am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Ramen Nagi Sunnyvale",
        description="The Bay Area outpost of the famous Tokyo ramen chain. "
                    "Choose your base: Original (tonkotsu), Red (spicy), Black (squid ink), "
                    "or Green (basil pesto tonkotsu). Unlimited thin noodle refills. "
                    "The seasoned soft egg is the required addition.",
        cuisine_type="Japanese", price_range="$$",
        address="157 E El Camino Real", city="Sunnyvale", state="CA",
        country="United States", zip_code="94087",
        phone="+1 (408) 739-9181",
        hours=json.dumps({
            "monday": "11:30am – 9:30pm", "tuesday": "11:30am – 9:30pm",
            "wednesday": "11:30am – 9:30pm", "thursday": "11:30am – 9:30pm",
            "friday": "11:30am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "11:30am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("alex@demo.com", None, dict(
        name="Zinc Bistro Sunnyvale",
        description="Californian bistro in the heart of downtown Sunnyvale. "
                    "The menu changes seasonally with a focus on organic, local ingredients. "
                    "The roasted beet salad with goat cheese and candied walnuts is a "
                    "perennial starter. The duck confit is the Friday evening special.",
        cuisine_type="American", price_range="$$$",
        address="222 S Murphy Ave", city="Sunnyvale", state="CA",
        country="United States", zip_code="94086",
        phone="+1 (408) 736-6711",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 9:30pm",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Taqueria La Bamba Sunnyvale",
        description="Beloved Sunnyvale taqueria known for hand-pressed corn tortillas "
                    "and a rotating birria on weekends. The fish tacos with pickled cabbage "
                    "and crema are a crowd favorite. The agua fresca changes daily — "
                    "the tamarind is the one to get.",
        cuisine_type="Mexican", price_range="$",
        address="625 S Wolfe Rd", city="Sunnyvale", state="CA",
        country="United States", zip_code="94086",
        phone="+1 (408) 555-3303",
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 10:00pm", "saturday": "8:00am – 10:00pm",
            "sunday": "9:00am – 8:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Cupertino
    # =========================================================================
    ("priya@demo.com", None, dict(
        name="Curry Village Cupertino",
        description="South Indian and North Indian crossover restaurant in Cupertino "
                    "serving a tech-industry lunchtime crowd. The thali plate — "
                    "rotating curries, dal, rice, naan, raita, and pickle — is "
                    "the best all-in-one lunch deal in the area. Efficient and flavorful.",
        cuisine_type="Indian", price_range="$$",
        address="10001 N De Anza Blvd", city="Cupertino", state="CA",
        country="United States", zip_code="95014",
        phone="+1 (408) 255-0890",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:30am – 10:00pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Shabusen Cupertino",
        description="Japanese hot pot shabu-shabu restaurant in Cupertino. "
                    "Choose your broth (kombu dashi or spicy miso), then swirl thinly "
                    "sliced wagyu, vegetables, and tofu through the bubbling pot. "
                    "The all-you-can-eat lunch option is popular with the local Japanese community.",
        cuisine_type="Japanese", price_range="$$",
        address="20745 Stevens Creek Blvd", city="Cupertino", state="CA",
        country="United States", zip_code="95014",
        phone="+1 (408) 996-9888",
        hours=json.dumps({
            "monday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "tuesday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "wednesday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "thursday": "11:30am – 2:30pm, 5:00pm – 9:30pm",
            "friday": "11:30am – 2:30pm, 5:00pm – 10:00pm",
            "saturday": "11:30am – 10:00pm", "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Panda Mandarin Cupertino",
        description="Hong Kong–style Cantonese restaurant in Cupertino popular with "
                    "the local Chinese community and neighboring Apple employees. "
                    "The roast duck and char siu pork hang in the window — order them "
                    "over rice for one of the most satisfying quick meals in the area.",
        cuisine_type="Chinese", price_range="$$",
        address="19720 Stevens Creek Blvd", city="Cupertino", state="CA",
        country="United States", zip_code="95014",
        phone="+1 (408) 255-6688",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 9:30pm", "saturday": "11:00am – 9:30pm",
            "sunday": "11:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Mountain View
    # =========================================================================
    ("alex@demo.com", None, dict(
        name="Amber India Mountain View",
        description="Upscale Indian restaurant on El Camino Real consistently ranked "
                    "among the best Indian dining in the Bay Area. The tasting menu "
                    "showcases regional Indian cuisine beyond the usual suspects. "
                    "The rabbit masala and the tandoor-roasted rack of lamb are signatures.",
        cuisine_type="Indian", price_range="$$$",
        address="2290 El Camino Real", city="Mountain View", state="CA",
        country="United States", zip_code="94040",
        phone="+1 (650) 968-7511",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "wednesday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "thursday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "friday": "11:30am – 2:30pm, 5:30pm – 10:30pm",
            "saturday": "11:30am – 10:30pm", "sunday": "11:30am – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=3, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Xanh Restaurant",
        description="Modern Vietnamese cuisine in a sophisticated Mountain View setting. "
                    "The menu elevates traditional Vietnamese flavors with California ingredients. "
                    "The five-spice duck breast and the lemongrass-steamed clams are standout dishes. "
                    "The cocktail program draws on Vietnamese herbs and citrus.",
        cuisine_type="Vietnamese", price_range="$$",
        address="110 Castro St", city="Mountain View", state="CA",
        country="United States", zip_code="94041",
        phone="+1 (650) 964-1888",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 9:30pm",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 10:30pm", "saturday": "11:30am – 10:30pm",
            "sunday": "11:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.5, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Steins Beer Garden Mountain View",
        description="Sprawling German-Californian beer garden in the heart of downtown "
                    "Mountain View. Craft beers from California and Germany on 36 taps. "
                    "The Bavarian pretzels, the currywurst, and the rotating seasonal sausages "
                    "pair perfectly with a cold Märzen. Great outdoor patio.",
        cuisine_type="American", price_range="$$",
        address="895 Villa St", city="Mountain View", state="CA",
        country="United States", zip_code="94041",
        phone="+1 (650) 967-7835",
        hours=json.dumps({
            "monday": "11:30am – 10:00pm", "tuesday": "11:30am – 10:00pm",
            "wednesday": "11:30am – 10:00pm", "thursday": "11:30am – 10:00pm",
            "friday": "11:30am – 11:00pm", "saturday": "11:30am – 11:00pm",
            "sunday": "11:30am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Palo Alto
    # =========================================================================
    ("alex@demo.com", None, dict(
        name="Nobu Palo Alto",
        description="The Bay Area outpost of Nobu Matsuhisa's globally celebrated Japanese-Peruvian "
                    "fusion empire. The black cod with miso is the signature dish the whole restaurant "
                    "is built around. The new-style sashimi with yuzu, jalapeño, and Peruvian chili "
                    "is among the most imitated dishes in the world.",
        cuisine_type="Japanese", price_range="$$$$",
        address="180 Hamilton Ave", city="Palo Alto", state="CA",
        country="United States", zip_code="94301",
        phone="+1 (650) 321-6688",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 10:00pm",
            "wednesday": "5:30pm – 10:00pm", "thursday": "5:30pm – 10:00pm",
            "friday": "5:30pm – 11:00pm", "saturday": "5:30pm – 11:00pm",
            "sunday": "5:30pm – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.7, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Evvia Estiatorio",
        description="Greek Mediterranean with a wood-burning hearth and an Aegean soul "
                    "in downtown Palo Alto. The lamb chops are the best on the Peninsula. "
                    "The grilled whole fish — prepared with olive oil, lemon, and herbs — "
                    "is flawlessly simple. A Stanford and tech industry institution.",
        cuisine_type="Mediterranean", price_range="$$$",
        address="420 Emerson St", city="Palo Alto", state="CA",
        country="United States", zip_code="94301",
        phone="+1 (650) 326-0983",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "wednesday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "thursday": "11:30am – 2:30pm, 5:30pm – 10:00pm",
            "friday": "11:30am – 2:30pm, 5:30pm – 10:30pm",
            "saturday": "5:30pm – 10:30pm", "sunday": "5:30pm – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Campbell
    # =========================================================================
    ("emily@demo.com", None, dict(
        name="Orchard City Kitchen",
        description="Modern American cooking in the heart of downtown Campbell "
                    "with a strong local following. The wood-fired rotisserie chicken "
                    "is the centerpiece of the menu. The cocktail program uses "
                    "house-infused spirits and locally sourced citrus and herbs.",
        cuisine_type="American", price_range="$$",
        address="413 E Campbell Ave", city="Campbell", state="CA",
        country="United States", zip_code="95008",
        phone="+1 (408) 379-6416",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:30pm",
            "wednesday": "11:30am – 9:30pm", "thursday": "11:30am – 9:30pm",
            "friday": "11:30am – 10:30pm", "saturday": "10:00am – 10:30pm",
            "sunday": "10:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Aqui Cal-Mex Campbell",
        description="California-influenced Mexican with a focus on fresh ingredients "
                    "and big flavors. The green chile chicken burrito is the signature. "
                    "Excellent margarita selection including premium agave and "
                    "house-made sour mix. Sunny patio, great for groups.",
        cuisine_type="Mexican", price_range="$",
        address="1875 S Bascom Ave", city="Campbell", state="CA",
        country="United States", zip_code="95008",
        phone="+1 (408) 374-1180",
        hours=json.dumps({
            "monday": "11:00am – 9:00pm", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 10:00pm", "saturday": "10:00am – 10:00pm",
            "sunday": "10:00am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=2, is_claimed=False,
    )),
    ("marcus@demo.com", None, dict(
        name="Campbell Brewing Company",
        description="Craft brewery and pub kitchen in Campbell with 20 house-brewed "
                    "beers on tap. The pub food is serious: double smash burgers, "
                    "beer-battered fish and chips, and house-smoked wings. "
                    "The IPA flights are the best introduction to California hop culture.",
        cuisine_type="American", price_range="$$",
        address="300 Railway Ave", city="Campbell", state="CA",
        country="United States", zip_code="95008",
        phone="+1 (408) 555-3501",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "4:00pm – 10:00pm",
            "wednesday": "4:00pm – 10:00pm", "thursday": "4:00pm – 10:00pm",
            "friday": "12:00pm – 11:00pm", "saturday": "12:00pm – 11:00pm",
            "sunday": "12:00pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Milpitas
    # =========================================================================
    ("emily@demo.com", None, dict(
        name="Tasty Pot Milpitas",
        description="Taiwanese hot pot chain with customizable broths and a vast "
                    "selection of ingredients. The signature milky bone broth is "
                    "deeply savory and mild. AYCE options available on weekday lunch. "
                    "The taro balls and fish cakes are the essential additions.",
        cuisine_type="Chinese", price_range="$$",
        address="175 Ranch Dr", city="Milpitas", state="CA",
        country="United States", zip_code="95035",
        phone="+1 (408) 263-2300",
        hours=json.dumps({
            "monday": "11:00am – 9:30pm", "tuesday": "11:00am – 9:30pm",
            "wednesday": "11:00am – 9:30pm", "thursday": "11:00am – 9:30pm",
            "friday": "11:00am – 10:00pm", "saturday": "11:00am – 10:00pm",
            "sunday": "11:00am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Pho Tau Bay Milpitas",
        description="Pho and Vietnamese noodle soups at the Great Mall area. "
                    "The shop has served the Milpitas Vietnamese community for "
                    "over 20 years. The oxtail pho is the weekend special — "
                    "rich, gelatinous, and deeply satisfying.",
        cuisine_type="Vietnamese", price_range="$",
        address="101 Ranch Dr", city="Milpitas", state="CA",
        country="United States", zip_code="95035",
        phone="+1 (408) 555-3602",
        hours=json.dumps({
            "monday": "8:00am – 9:00pm", "tuesday": "8:00am – 9:00pm",
            "wednesday": "8:00am – 9:00pm", "thursday": "8:00am – 9:00pm",
            "friday": "8:00am – 9:30pm", "saturday": "7:30am – 9:30pm",
            "sunday": "7:30am – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.1, review_count=2, is_claimed=False,
    )),
    ("priya@demo.com", None, dict(
        name="Great India Restaurant Milpitas",
        description="Indian buffet and à la carte restaurant near the Great Mall. "
                    "The lunch buffet is one of the most extensive in the South Bay — "
                    "over 30 items rotating daily including tandoori, curries, biryani, "
                    "chaat, and Indian desserts. Excellent value.",
        cuisine_type="Indian", price_range="$$",
        address="277 Barber Ct", city="Milpitas", state="CA",
        country="United States", zip_code="95035",
        phone="+1 (408) 263-1050",
        hours=json.dumps({
            "monday": "11:00am – 3:00pm, 5:00pm – 9:30pm",
            "tuesday": "11:00am – 3:00pm, 5:00pm – 9:30pm",
            "wednesday": "11:00am – 3:00pm, 5:00pm – 9:30pm",
            "thursday": "11:00am – 3:00pm, 5:00pm – 9:30pm",
            "friday": "11:00am – 3:00pm, 5:00pm – 10:00pm",
            "saturday": "11:00am – 10:00pm", "sunday": "11:00am – 9:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.0, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Los Gatos
    # =========================================================================
    ("alex@demo.com", None, dict(
        name="Manresa",
        description="Three-Michelin-star destination restaurant in Los Gatos helmed "
                    "by Chef David Kinch. The tasting menu is a meditation on the "
                    "Santa Cruz Mountains terroir — produce, fungi, herbs, and proteins "
                    "sourced from the restaurant's own Love Apple Farms. "
                    "One of California's most exceptional dining experiences.",
        cuisine_type="American", price_range="$$$$",
        address="320 Village Ln", city="Los Gatos", state="CA",
        country="United States", zip_code="95030",
        phone="+1 (408) 354-4330",
        website="https://manresarestaurant.com",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "5:30pm – 9:30pm", "saturday": "5:00pm – 9:30pm",
            "sunday": "Closed",
        }),
        photos=json.dumps([]),
        avg_rating=4.9, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Dio Deka",
        description="Greek Mediterranean in the Hotel Los Gatos with a charcoal-fired "
                    "hearth and an extensive Hellenic wine list. The lamb chops with "
                    "tzatziki and the whole fish are the stars. "
                    "The meze spread is ideal for sharing. Warm, elegant setting.",
        cuisine_type="Mediterranean", price_range="$$$",
        address="210 E Main St", city="Los Gatos", state="CA",
        country="United States", zip_code="95030",
        phone="+1 (408) 354-7700",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "5:30pm – 9:30pm",
            "wednesday": "5:30pm – 9:30pm", "thursday": "5:30pm – 9:30pm",
            "friday": "11:30am – 2:00pm, 5:30pm – 10:00pm",
            "saturday": "11:30am – 2:00pm, 5:30pm – 10:00pm",
            "sunday": "11:30am – 2:00pm, 5:30pm – 9:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.6, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Saratoga
    # =========================================================================
    ("alex@demo.com", None, dict(
        name="The Plumed Horse",
        description="One of Silicon Valley's most celebrated fine dining restaurants, "
                    "open since 1952. The Plumed Horse holds a Michelin star and a wine "
                    "cellar of over 1,200 labels. The chef's tasting menu is the "
                    "definitive special-occasion dinner in the South Bay.",
        cuisine_type="American", price_range="$$$$",
        address="14555 Big Basin Way", city="Saratoga", state="CA",
        country="United States", zip_code="95070",
        phone="+1 (408) 867-4711",
        website="https://plumedhorse.com",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "Closed",
            "wednesday": "5:30pm – 9:00pm", "thursday": "5:30pm – 9:00pm",
            "friday": "5:30pm – 9:30pm", "saturday": "5:00pm – 9:30pm",
            "sunday": "Closed",
        }),
        photos=json.dumps([]),
        avg_rating=4.8, review_count=2, is_claimed=False,
    )),

    # =========================================================================
    # Fremont
    # =========================================================================
    ("priya@demo.com", None, dict(
        name="Shalimar Fremont",
        description="Pakistani and North Indian restaurant beloved for its tandoor-baked "
                    "breads and intense curry sauces. The chicken karahi and nihari "
                    "(slow-braised beef shank) are weekend specials that sell out early. "
                    "The paratha is hand-layered and flaky. Halal-certified.",
        cuisine_type="Indian", price_range="$",
        address="37397 Fremont Blvd", city="Fremont", state="CA",
        country="United States", zip_code="94536",
        phone="+1 (510) 555-3801",
        hours=json.dumps({
            "monday": "11:00am – 10:00pm", "tuesday": "11:00am – 10:00pm",
            "wednesday": "11:00am – 10:00pm", "thursday": "11:00am – 10:00pm",
            "friday": "11:00am – 10:30pm", "saturday": "11:00am – 10:30pm",
            "sunday": "11:00am – 10:00pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.4, review_count=2, is_claimed=False,
    )),
    ("user@demo.com", None, dict(
        name="Udupi Bhavan Fremont",
        description="South Indian vegetarian restaurant in Fremont's Little India corridor "
                    "on Fremont Blvd. The idli-vada breakfast combo is the reason to arrive "
                    "before 10am on weekends. Crispy masala dosas and fresh coconut chutney "
                    "made daily. Completely vegetarian and vegan-friendly.",
        cuisine_type="Vegetarian", price_range="$",
        address="39180 Fremont Blvd", city="Fremont", state="CA",
        country="United States", zip_code="94538",
        phone="+1 (510) 555-3802",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:00am – 9:00pm",
            "wednesday": "11:00am – 9:00pm", "thursday": "11:00am – 9:00pm",
            "friday": "11:00am – 9:30pm", "saturday": "9:00am – 9:30pm",
            "sunday": "9:00am – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.3, review_count=2, is_claimed=False,
    )),
    ("emily@demo.com", None, dict(
        name="Papillon Fremont",
        description="Mediterranean bistro in Mission San Jose neighborhood of Fremont. "
                    "The shakshuka, lamb tagine, and oven-roasted whole cauliflower with "
                    "tahini are the dishes regulars return for. "
                    "Warm, unpretentious atmosphere with an excellent lunch value.",
        cuisine_type="Mediterranean", price_range="$$",
        address="43533 Mission Blvd", city="Fremont", state="CA",
        country="United States", zip_code="94539",
        phone="+1 (510) 555-3803",
        hours=json.dumps({
            "monday": "Closed", "tuesday": "11:30am – 9:00pm",
            "wednesday": "11:30am – 9:00pm", "thursday": "11:30am – 9:00pm",
            "friday": "11:30am – 9:30pm", "saturday": "11:30am – 9:30pm",
            "sunday": "12:00pm – 8:30pm",
        }),
        photos=json.dumps([]),
        avg_rating=4.2, review_count=2, is_claimed=False,
    )),
]

# (reviewer_email, restaurant_name, rating, comment, days_ago)
REVIEWS = [
    # Ristorante Bello — 3 reviews
    ("user@demo.com", "Ristorante Bello", 5,
     "Best pasta I've had outside of Naples. The carbonara is silky smooth — no cream, "
     "just egg, guanciale, and pecorino, exactly as it should be. The tiramisu knocked "
     "me sideways. Booked the corner table again for next month.", 45),
    ("marcus@demo.com", "Ristorante Bello", 4,
     "Solid Italian food, great atmosphere. The margherita pizza had a perfect char "
     "on the crust. Only reason it's not a 5 is that we waited 20 minutes for our "
     "check on a busy Saturday night.", 30),
    ("alex@demo.com", "Ristorante Bello", 5,
     "The burrata is from Puglia. The tagliatelle al ragù is textbook. "
     "Mario himself came out to the table and talked pasta shapes for 10 minutes. "
     "This is the real deal.", 15),

    # Bella Vista Rooftop — 2 reviews
    ("emily@demo.com", "Bella Vista Rooftop", 4,
     "The rooftop view alone is worth the price. Bay Bridge lit up at sunset while "
     "we had the flatbreads and a bottle of Montepulciano — honestly magical. "
     "Service a bit slow but the vibe forgives everything.", 20),
    ("alex@demo.com", "Bella Vista Rooftop", 4,
     "Great cocktails, gorgeous view, food is solid if not groundbreaking. "
     "The lobster gnocchi was the highlight. Go for drinks and stay for dinner "
     "if the stars align.", 8),

    # Dragon Garden — 2 reviews
    ("user@demo.com", "Dragon Garden", 5,
     "The best dim sum in San Francisco, full stop. The shrimp dumplings are "
     "translucent-wrapper perfection. The pineapple buns from the cart are "
     "addictive. Go early on Sunday — the line is worth it.", 60),
    ("emily@demo.com", "Dragon Garden", 4,
     "I've been coming here for years and it never disappoints. The XO chili crab "
     "on Fridays is a special event. Only knocked one star because they stopped "
     "serving the egg custard tarts — bring them back!", 35),

    # Sakura Omakase — 2 reviews
    ("user@demo.com", "Sakura Omakase", 5,
     "18 courses of absolute precision. Chef Kenji presented the bluefin toro with "
     "a description of the fishing village in Oma where it was caught. "
     "I understood I was in the presence of something serious. Worth every penny.", 90),
    ("alex@demo.com", "Sakura Omakase", 5,
     "The best meal I've had in San Francisco — and I eat out constantly. "
     "The Hokkaido uni on warm shari was the transcendent moment. "
     "Booked six months out but I'm going back.", 25),

    # Ramen House Natori — 2 reviews
    ("marcus@demo.com", "Ramen House Natori", 4,
     "No-nonsense ramen done brilliantly. The tonkotsu broth is creamy without "
     "being heavy. Soft-boiled egg marinated overnight — perfect. "
     "Cash only, tiny space, worth every inconvenience.", 40),
    ("alex@demo.com", "Ramen House Natori", 4,
     "The tsukemen (dipping noodles) here is one of SF's best-kept secrets. "
     "Thick wavy noodles with a rich, intense dipping broth. No substitutions, "
     "no modifications — the chef knows what they're doing, trust the menu.", 18),

    # Taqueria La Paloma — 3 reviews
    ("user@demo.com", "Taqueria La Paloma", 5,
     "I've been eating here for 10 years. The al pastor is carved off the trompo "
     "right in front of you. The green tomatillo salsa is dangerously addictive. "
     "Best $12 I spend in this city, every single time.", 55),
    ("priya@demo.com", "Taqueria La Paloma", 5,
     "They have incredible bean-and-cheese burritos for vegetarians. "
     "The refried beans are made from scratch daily. Even as a vegetarian, "
     "I make a special trip for the mushroom and potato tacos. Perfect.", 28),
    ("emily@demo.com", "Taqueria La Paloma", 4,
     "Iconic. The breakfast burrito on Saturday morning is life-affirming. "
     "Long line but it moves fast. Get the super burrito, not the regular. "
     "Only four stars because parking in the Mission is impossible.", 12),

    # Casa Oaxaca — 2 reviews
    ("priya@demo.com", "Casa Oaxaca", 4,
     "The mole negro is extraordinary — complex, slightly bitter, perfectly balanced. "
     "I'm vegetarian and they were incredibly accommodating with substitutions. "
     "The mezcal list is curated with real thought. A special-occasion restaurant.", 22),
    ("alex@demo.com", "Casa Oaxaca", 5,
     "Sofia Hernandez is cooking at a Michelin level. The memelas with "
     "epazote and black beans, the tlayuda, the mole — every dish tells a story. "
     "The mezcal flight is an education. Best Mexican fine dining in the Bay.", 10),

    # Spice Route — 2 reviews
    ("priya@demo.com", "Spice Route", 5,
     "As someone who grew up eating real Indian home cooking, this is the "
     "restaurant I recommend to everyone who wants to understand the cuisine. "
     "The dal makhani is slow-cooked for hours — it tastes like my mother's kitchen. "
     "The mango lassi is perfect.", 38),
    ("marcus@demo.com", "Spice Route", 4,
     "Ordered the lamb rogan josh based on a recommendation and it blew me away. "
     "Six-hour braise, deep red, aromatic without being too hot. "
     "The garlic naan was also exceptional. A bit pricey but worth the splurge.", 16),

    # Bangkok Noodles — 2 reviews
    ("alex@demo.com", "Bangkok Noodles", 4,
     "The khao soi here is one of the best things I've eaten in Oakland. "
     "Rich coconut curry broth, crispy egg noodles on top, tender chicken. "
     "Tiny space, often a wait, but the food is absolutely worth it.", 50),
    ("emily@demo.com", "Bangkok Noodles", 3,
     "The pad see ew is solid but I've had better. The khao soi is the reason "
     "to come — everything else is secondary. Service is brusque and the "
     "space is not comfortable. But for that khao soi, I'll return.", 27),

    # The Smokehouse — 1 review
    ("marcus@demo.com", "The Smokehouse", 5,
     "This is the Texas BBQ I moved to California hoping to find and never did — "
     "until now. The 18-hour brisket has the correct smoke ring, the correct bark, "
     "the correct fat render. The burnt ends were a religious experience. "
     "Worth the trip to Oakland a thousand times over.", 32),

    # Blue Plate Diner — 1 review
    ("marcus@demo.com", "Blue Plate Diner", 3,
     "Exactly what it claims to be: a diner. The grilled cheese was fine, "
     "the milkshake was good, the meatloaf was underwhelming. "
     "Comfortable, cheap, reliable. Don't expect anything more.", 65),

    # Olive Branch — 2 reviews
    ("user@demo.com", "Olive Branch", 5,
     "The mezze spread for two is a meal in itself. The hummus with lamb "
     "kafta on top, the baba ganoush, the fattoush salad. "
     "All of it made with genuine care. The outdoor patio is beautiful on a warm evening.", 42),
    ("priya@demo.com", "Olive Branch", 4,
     "Wonderful vegetarian options — the mushroom and halloumi skewers, "
     "the spanakopita, the stuffed peppers. The staff were very knowledgeable "
     "about plant-based choices. Lovely Marina atmosphere.", 19),

    # Seoul Kitchen — 2 reviews
    ("marcus@demo.com", "Seoul Kitchen", 4,
     "The galbi (short rib) is the best in SF. 24-hour marinade shows — "
     "the meat is incredibly tender with that caramelized grill char. "
     "The banchan spread is generous and the kimchi is properly funky. Great value.", 48),
    ("emily@demo.com", "Seoul Kitchen", 5,
     "I grew up eating Korean BBQ and this is the real thing. "
     "The ventilation works properly (no smoke smell on your clothes after). "
     "The sundubu jjigae (soft tofu stew) is outstanding. "
     "The lunch special is one of SF's best-kept secrets.", 14),

    # Pho Saigon — 2 reviews
    ("alex@demo.com", "Pho Saigon", 4,
     "Late-night pho at its finest. The broth is genuinely 12-hour slow-cooked "
     "— you can taste it. The #1 combination (rare beef, brisket, tendon) "
     "is the order. Cheap, authentic, perfect for 1am after a long evening.", 72),
    ("emily@demo.com", "Pho Saigon", 4,
     "My go-to pho in the Tenderloin for 5 years. The broth is clean and aromatic, "
     "not overly salty. The banh mi is underrated — crisp baguette, proper pâté. "
     "Friendly staff, fast service, open late. A neighborhood gem.", 33),

    # Café Madeleine — 2 reviews
    ("user@demo.com", "Café Madeleine", 5,
     "The duck confit arrived with a perfectly crisped skin and melting dark meat "
     "underneath. The cheese cart made a second pass by our table because "
     "the sommelier correctly identified that we would not say no. "
     "Romantic, unhurried, Parisian in the best possible sense.", 53),
    ("alex@demo.com", "Café Madeleine", 4,
     "Michelin Bib Gourmand status is well-earned. The bouillabaisse is impeccable. "
     "The prix-fixe on Friday night is exceptional value at this level of cooking. "
     "Only one star back because the tables are too close together.", 21),

    # The Green Bowl — 1 review
    ("priya@demo.com", "The Green Bowl", 4,
     "A genuinely exciting vegan restaurant — not just sad salads and rice cakes. "
     "The jackfruit tacos taste like the real thing. The miso eggplant is "
     "caramelized and deeply savory. Great for vegetarians and skeptics alike.", 29),

    # The Wharf Kitchen — 1 review
    ("marcus@demo.com", "The Wharf Kitchen", 4,
     "I'm not usually a seafood person but the wood-grilled halibut here "
     "converted me. Fresh, simply cooked, not messed with. "
     "The clam chowder in a sourdough bowl is tourist food but excellent tourist food. "
     "Bring a big appetite and a fat wallet.", 37),

    # Sunday Morning Café — 3 reviews
    ("alex@demo.com", "Sunday Morning Café", 5,
     "The Dutch baby pancake with lemon curd and powdered sugar is "
     "the reason I get up before noon on Sundays. "
     "The bottomless mimosas are dangerously well-priced. "
     "Book a table at 8am to avoid the madness. Worth every minute of the wait.", 68),
    ("emily@demo.com", "Sunday Morning Café", 4,
     "The avocado toast here is how avocado toast was meant to be: "
     "on sourdough, with burrata, finished with chili flakes and microgreens. "
     "The cold brew is exceptional. Long wait on weekends but a beautiful vibe.", 44),
    ("user@demo.com", "Sunday Morning Café", 5,
     "Noe Valley on a Sunday morning, a table by the window, "
     "ricotta pancakes, and a proper cappuccino. "
     "Simple pleasures done perfectly. This is one of my happy places.", 11),

    # =========================================================================
    # South Bay — new restaurants
    # =========================================================================

    # Sushi Kakimoto — 2 reviews
    ("alex@demo.com", "Sushi Kakimoto", 5,
     "This is the omakase San Jose has needed. Chef Kakimoto sources his fish "
     "direct from Tokyo's Toyosu market twice weekly. The otoro was the best "
     "I've had outside Japan — clean, buttery, not unctuous. "
     "Sixteen courses and I could have eaten sixteen more.", 18),
    ("user@demo.com", "Sushi Kakimoto", 5,
     "The kinmedai (golden eye snapper) aged three days had a depth of flavor "
     "I didn't think was possible from a fish. The house-made dashi ice cream "
     "for dessert is quietly brilliant. Book at least three weeks out.", 9),

    # Hanabi Ramen — 2 reviews
    ("marcus@demo.com", "Hanabi Ramen", 5,
     "The tonkotsu broth here is the real deal — they boil the bones for 18 hours "
     "and it shows. Perfectly opaque, rich without being heavy. "
     "The chashu pork melts on contact. Topped off with a soft-boiled egg "
     "that has a jammy yolk. Best ramen in the South Bay, no contest.", 22),
    ("emily@demo.com", "Hanabi Ramen", 4,
     "Love the shoyu ramen here — lighter than the tonkotsu but incredibly "
     "complex with the house tare. The gyoza are pan-fried to crispy perfection. "
     "Only downside: long wait on weekends. Get there when they open.", 14),

    # Gogi Korean BBQ — 2 reviews
    ("marcus@demo.com", "Gogi Korean BBQ", 5,
     "This is the Korean BBQ I've been searching for in the South Bay. "
     "Live charcoal, real ventilation, USDA choice galbi that marinates for "
     "two days minimum. The galbi tang (short rib soup) as a side is underrated. "
     "The unlimited banchan spread hits differently when everything is housemade.", 31),
    ("emily@demo.com", "Gogi Korean BBQ", 4,
     "Samgyeopsal (pork belly) here is outstanding — clean pork flavor, "
     "good fat-to-meat ratio. Wrap it in perilla with a dab of ssamjang "
     "and you're in heaven. The doenjang jjigae is exactly like my halmoni made it.", 17),

    # Jang Su Jang — 2 reviews
    ("emily@demo.com", "Jang Su Jang", 5,
     "Jang Su Jang is a South Bay institution and absolutely deserves its reputation. "
     "The pork belly KBBQ on the gas grill is crowd-pleasing but the real move "
     "is the gamjatang (pork bone soup) — spicy, funky, deeply satisfying. "
     "Lines out the door on weekends for good reason.", 26),
    ("alex@demo.com", "Jang Su Jang", 4,
     "Solid Korean BBQ in a no-frills setting. The galbi is well-marinated "
     "and the service keeps your grill going. I prefer charcoal but gas here "
     "is fine because the meat quality carries it. "
     "The cold naengmyeon noodles to finish are a must.", 11),

    # Udupi Palace — 2 reviews
    ("priya@demo.com", "Udupi Palace", 5,
     "The masala dosa here is the reason I drive across the South Bay. "
     "The crepe is impossibly thin and crisp, the potato filling is fragrant "
     "with mustard seeds and curry leaves, and the chutneys are freshly ground. "
     "Completely vegetarian, completely wonderful. South Indian food at its best.", 35),
    ("user@demo.com", "Udupi Palace", 4,
     "The thali is one of the best deals in San Jose — rice, dal, two sabzis, "
     "sambar, rasam, papad, pickle, and dessert for under $15. "
     "The idli is perfectly steamed and the sambar is layered with flavor. "
     "Go for the buffet on weekends if you can.", 19),

    # Dish Dash — 2 reviews
    ("priya@demo.com", "Dish Dash", 5,
     "Dish Dash is the best Middle Eastern restaurant in the South Bay and "
     "it's not close. The fattoush is electric, the hummus is "
     "satiny-smooth and warm, and the lamb kebabs are masterfully spiced. "
     "The whole roasted lamb shoulder for groups is a special-occasion showstopper.", 28),
    ("alex@demo.com", "Dish Dash", 5,
     "The muhammara (roasted red pepper and walnut spread) alone is worth the trip. "
     "The slow-braised lamb shank with fragrant rice is one of the great South Bay "
     "dishes. Excellent service, deep ingredient knowledge from the staff, "
     "and a wine list that pairs beautifully with the cuisine.", 13),

    # Falafel's Drive-In — 2 reviews
    ("priya@demo.com", "Falafel's Drive-In", 5,
     "A San Jose institution since 1966. The falafel here is what falafel should be: "
     "crispy shell, bright herb-and-chickpea interior, not dense, not greasy. "
     "The tahini sauce is house-made and tangy. The pita is fresh and pillowy. "
     "One of the great casual vegetarian meals anywhere in the Bay Area.", 41),
    ("user@demo.com", "Falafel's Drive-In", 4,
     "They've been making falafel the same way since the 1960s and that's "
     "exactly how it should be. Perfect casual lunch — grab a combo plate "
     "with hummus, tabbouleh, and a couple of falafel balls. "
     "Cheap, fast, and deeply satisfying.", 23),

    # Taqueria Los Compadres — 2 reviews
    ("marcus@demo.com", "Taqueria Los Compadres", 5,
     "The birria tacos here on weekends are extraordinary — consommé so rich "
     "you'd drink it as a broth, quesabirria with that orange-red oil, "
     "mozzarella pull, crispy-edged tortilla. I drove from SF for these tacos "
     "and would drive from anywhere. The best in the South Bay.", 20),
    ("user@demo.com", "Taqueria Los Compadres", 4,
     "Excellent al pastor carved fresh from the trompo on weekends. "
     "The carne asada burrito is huge and well-seasoned. "
     "The agua fresca is made from scratch daily — the Jamaica is outstanding. "
     "Prices are honest, service is fast.", 12),

    # Trattoria Volare — 2 reviews
    ("user@demo.com", "Trattoria Volare", 4,
     "Solid neighborhood Italian in Willow Glen. The handmade pappardelle "
     "with wild boar ragù is the best pasta dish in San Jose. "
     "The tiramisu is classically made and perfectly proportioned. "
     "A dependable romantic dinner option south of SF.", 38),
    ("alex@demo.com", "Trattoria Volare", 4,
     "Not Michelin territory but honest, well-executed Italian cooking. "
     "The ossobuco Milanese is slow-braised and melting. "
     "The wine list has depth beyond the usual by-the-glass suspects. "
     "Best Italian option in the SJ proper.", 16),

    # Original Joe's San Jose — 2 reviews
    ("marcus@demo.com", "Original Joe's San Jose", 4,
     "Classic San Jose Italian-American institution. The counter seats "
     "facing the open kitchen are the best in the house — watch them "
     "hand-toss pasta and work the grill. The Joe's Special (ground beef, "
     "eggs, spinach, mushrooms) is a decades-old signature. Honest, satisfying.", 44),
    ("user@demo.com", "Original Joe's San Jose", 4,
     "Been here since 1956 and they do the classics well. "
     "The minestrone is rich and slow-cooked. The veal piccata is lemon-bright. "
     "Old-school service, old-school portions. A San Jose dining landmark.", 29),

    # Henry's Hi-Life — 1 review
    ("marcus@demo.com", "Henry's Hi-Life", 5,
     "This is where San Jose's BBQ lives. The dry-rubbed ribs have a proper "
     "smoke ring and pull cleanly from the bone. The brisket is sliced to order. "
     "The cowboy beans and the coleslaw are supporting cast worth their own "
     "restaurant. A South Bay institution since 1960.", 33),

    # Manresa — 2 reviews
    ("alex@demo.com", "Manresa", 5,
     "Three Michelin stars that feel genuinely earned. Chef Kinch's connection "
     "to Love Apple Farms runs through every dish — you taste the terroir. "
     "The amuse-bouche sequence alone is more thoughtful than most full meals. "
     "This is California cuisine operating at its absolute ceiling.", 55),
    ("user@demo.com", "Manresa", 5,
     "The 11-course tasting menu is a meditation on the Santa Cruz Mountains. "
     "I don't usually love fungi but the mushroom consommé with forest herbs "
     "made me reconsider everything. Impeccable pacing, warm service. "
     "One of the finest meals I've eaten anywhere.", 30),

    # The Plumed Horse — 1 review
    ("alex@demo.com", "The Plumed Horse", 5,
     "Operating since 1952 and holding a Michelin star — The Plumed Horse "
     "earns every part of its reputation. The wine cellar is extraordinary. "
     "The chef's tasting menu showcases California ingredients with French "
     "technique. A perfect special-occasion restaurant in the South Bay.", 48),

    # Dio Deka — 1 review
    ("user@demo.com", "Dio Deka", 5,
     "The best Greek restaurant I've been to in California. "
     "The lamb chops with tzatziki off the charcoal hearth are extraordinary. "
     "The Hellenic wine list has bottles you won't find anywhere else in the region. "
     "The meze spread for two is the perfect way to start.", 22),

    # Amber India Mountain View — 2 reviews
    ("priya@demo.com", "Amber India Mountain View", 5,
     "Upscale Indian done right. The regional tasting menu takes you through "
     "Goa, Rajasthan, Bengal, and Kerala in one sitting. "
     "The rabbit masala is a revelation — a dish you'd never see at a "
     "typical Indian restaurant. The wine pairings are genuinely thoughtful.", 27),
    ("alex@demo.com", "Amber India Mountain View", 5,
     "Consistently one of the best Indian restaurants in the Bay Area. "
     "The tandoor-roasted rack of lamb is the signature for good reason — "
     "perfectly charred exterior, juicy pink interior. "
     "Service that anticipates your needs. Worth every dollar.", 14),

    # Nobu Palo Alto — 2 reviews
    ("alex@demo.com", "Nobu Palo Alto", 5,
     "The black cod with miso is the canonical Nobu dish and this location "
     "executes it flawlessly — the miso glaze caramelizes perfectly without "
     "crossing into cloying territory. The rock shrimp tempura with creamy "
     "spicy sauce is addictive. Impeccable setting, impeccable service.", 36),
    ("user@demo.com", "Nobu Palo Alto", 4,
     "Nobu is a global brand but the food quality here is genuinely excellent. "
     "The yellowtail jalapeño sashimi is a bright, clean starter. "
     "The wagyu beef tacos are luxurious. Prices reflect the zip code "
     "but the kitchen delivers on its promises.", 18),

    # Kabul Afghan Cuisine — 2 reviews
    ("priya@demo.com", "Kabul Afghan Cuisine", 5,
     "The most underrated restaurant in Santa Clara. The lamb and pumpkin "
     "qorma is spiced with restraint and depth — warming without being hot, "
     "sweet-savory, complex. The bolani (stuffed flatbread) with chutney "
     "is the best bread course in any restaurant in the South Bay.", 32),
    ("alex@demo.com", "Kabul Afghan Cuisine", 4,
     "Afghan cuisine is one of the great undiscovered cuisines in the US "
     "and Kabul Afghan Cuisine is a superb introduction. "
     "The slow-roasted lamb shoulder falls off the bone. "
     "The basmati rice with toppings is fragrant and beautifully presented.", 20),

    # Sushi Tomi — 2 reviews
    ("user@demo.com", "Sushi Tomi", 5,
     "The Edomae omakase at Sushi Tomi is a hidden gem in Santa Clara. "
     "Chef Tomi sources from the Japanese wholesale market and the fish "
     "quality is exceptional. The mackerel cured with kombu had a "
     "clean, ocean flavor I haven't found anywhere else locally.", 25),
    ("emily@demo.com", "Sushi Tomi", 4,
     "Very high quality sushi at fair prices relative to the South Bay. "
     "The albacore tataki with ponzu and crispy onions is the standout appetizer. "
     "The uni hand roll is better than restaurants charging twice as much. "
     "Small space, book ahead.", 11),

    # Oren's Hummus — 1 review
    ("priya@demo.com", "Oren's Hummus Sunnyvale", 5,
     "The hummus here is life-changing. Silky, warm, topped with slow-cooked "
     "whole chickpeas, olive oil, and paprika. Eaten with house-baked pita "
     "fresh from the oven. The sabich (eggplant, hard-boiled egg, tahini) "
     "is one of the best vegetarian dishes I've had anywhere in the Bay Area.", 39),

    # Ramen Nagi — 1 review
    ("marcus@demo.com", "Ramen Nagi Sunnyvale", 4,
     "Ramen Nagi is the real deal from Japan and the Sunnyvale location holds up. "
     "The Original King (pork-based) broth is intensely rich and savory. "
     "You can customize strength, firmness, and richness — I go full power on all three. "
     "The black ramen with squid ink and garlic is the adventurous order.", 21),

    # Pearl River Dim Sum — 2 reviews
    ("emily@demo.com", "Pearl River Dim Sum", 5,
     "The best dim sum in San Jose and it's not even close. "
     "The har gow wrappers are paper-thin and the shrimp filling is snappy-fresh. "
     "The XO turnip cake arrives crispy on the outside and silky inside. "
     "The siu mai has real pork and shrimp — no fillers. Arrive by 10am.", 24),
    ("user@demo.com", "Pearl River Dim Sum", 4,
     "Finally a dim sum house in San Jose that competes with SF Chinatown. "
     "The cart system still works here on weekends. "
     "The egg custard tarts (dan tat) come out hot from the oven at 11am "
     "and they vanish within minutes — station yourself nearby.", 15),

    # Tasty Pot — 1 review
    ("emily@demo.com", "Tasty Pot Milpitas", 4,
     "Hot pot in Milpitas done properly. Individual pots with your choice of "
     "broth — the spicy mala is genuinely numbing in the best way. "
     "The wagyu beef slices are a splurge worth taking. "
     "The sesame dipping sauce is house-made and excellent. "
     "Great for groups, efficient service.", 28),

    # Pho Garden San Jose — 1 review
    ("marcus@demo.com", "Pho Garden San Jose", 4,
     "No-frills pho in East San Jose that punches way above its weight. "
     "The broth is the long-simmered kind — clear, deeply beefy, aromatic "
     "with star anise and clove. The large bowl could feed two. "
     "The fresh basil and bean sprouts are genuinely fresh. "
     "Cash only, worth carrying cash.", 33),

    # Evvia Estiatorio — 1 review
    ("user@demo.com", "Evvia Estiatorio", 5,
     "Evvia is Old Palo Alto Greek dining at its best. "
     "The lamb chops have been on the menu for 25 years for good reason. "
     "The wood-fired octopus is the starter you should never skip. "
     "The Assyrtiko white wine by the glass is the perfect pairing. "
     "A local institution that deserves every compliment it gets.", 40),
]

# (user_email, restaurant_name)
FAVORITES = [
    ("user@demo.com",   "Ristorante Bello"),
    ("user@demo.com",   "Dragon Garden"),
    ("user@demo.com",   "Taqueria La Paloma"),
    ("user@demo.com",   "Café Madeleine"),
    ("marcus@demo.com", "Ristorante Bello"),
    ("marcus@demo.com", "Taqueria La Paloma"),
    ("marcus@demo.com", "The Smokehouse"),
    ("priya@demo.com",  "Casa Oaxaca"),
    ("priya@demo.com",  "Spice Route"),
    ("priya@demo.com",  "The Green Bowl"),
    ("alex@demo.com",   "Sakura Omakase"),
    ("alex@demo.com",   "Casa Oaxaca"),
    ("alex@demo.com",   "Café Madeleine"),
    ("alex@demo.com",   "Sunday Morning Café"),
    ("emily@demo.com",  "Dragon Garden"),
    ("emily@demo.com",  "Taqueria La Paloma"),
    ("emily@demo.com",  "Seoul Kitchen"),
    ("emily@demo.com",  "Sunday Morning Café"),
    # South Bay additions
    ("user@demo.com",   "Sushi Kakimoto"),
    ("user@demo.com",   "Dish Dash"),
    ("user@demo.com",   "Falafel's Drive-In"),
    ("user@demo.com",   "Manresa"),
    ("user@demo.com",   "Evvia Estiatorio"),
    ("marcus@demo.com", "Hanabi Ramen"),
    ("marcus@demo.com", "Gogi Korean BBQ"),
    ("marcus@demo.com", "Taqueria Los Compadres"),
    ("marcus@demo.com", "Henry's Hi-Life"),
    ("priya@demo.com",  "Udupi Palace"),
    ("priya@demo.com",  "Dish Dash"),
    ("priya@demo.com",  "Falafel's Drive-In"),
    ("priya@demo.com",  "Kabul Afghan Cuisine"),
    ("priya@demo.com",  "Oren's Hummus Sunnyvale"),
    ("priya@demo.com",  "Amber India Mountain View"),
    ("alex@demo.com",   "Sushi Kakimoto"),
    ("alex@demo.com",   "Manresa"),
    ("alex@demo.com",   "The Plumed Horse"),
    ("alex@demo.com",   "Nobu Palo Alto"),
    ("alex@demo.com",   "Jang Su Jang"),
    ("emily@demo.com",  "Pearl River Dim Sum"),
    ("emily@demo.com",  "Jang Su Jang"),
    ("emily@demo.com",  "Gogi Korean BBQ"),
    ("emily@demo.com",  "Sushi Tomi"),
]

# AI demo conversations — (user_email, messages: [(role, content), ...])
CONVERSATIONS = [
    ("user@demo.com", [
        ("user",      "I want Italian food tonight, romantic setting, budget around $$"),
        ("assistant", "Based on your preferences, I'd recommend Ristorante Bello in North Beach. "
                      "It's a warm candlelit space with authentic Neapolitan pasta. Rated 4.7/5 with "
                      "consistent reviews praising the carbonara and the intimate atmosphere. "
                      "Would you like to know more, or shall I suggest an alternative?"),
        ("user",      "Sounds perfect. Does it have outdoor seating?"),
        ("assistant", "Ristorante Bello is an indoor dining room — cozy booths and "
                      "candlelight, which actually works beautifully for a romantic evening. "
                      "If outdoor seating is important to you, Bella Vista Rooftop also serves "
                      "Italian cuisine with a heated outdoor terrace and stunning bay views, "
                      "though it's priced at $$$. Shall I compare the two?"),
    ]),
    ("alex@demo.com", [
        ("user",      "I'm looking for the best omakase experience in San Francisco, money is no object"),
        ("assistant", "Sakura Omakase is the standout choice. Chef Kenji's 18-course Edomae "
                      "experience at 50 Belden Pl has a perfect 5.0 rating from reviewers. "
                      "The seasonal menu features Hokkaido uni, aged bluefin toro, and house "
                      "tamago. Reservations open 60 days in advance and sell out quickly — "
                      "I'd recommend booking immediately. Would you like help with anything else?"),
    ]),
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def _wipe(db: "Session"):
    print("Wiping existing seed data…")
    db.query(ConversationMessage).delete()
    db.query(Conversation).delete()
    db.query(Favorite).delete()
    db.query(Review).delete()
    db.query(RestaurantClaim).delete()
    db.query(Restaurant).delete()
    db.query(UserPreferences).delete()
    db.query(User).delete()
    db.commit()
    print("Done.")


def _seed(db: "Session", wipe: bool):
    if wipe:
        _wipe(db)

    if db.query(User).count() > 0:
        print("Database already has users — skipping seed. Use --wipe to reset.")
        return

    pw = hash_password("password")

    # --- Users ---
    print("Creating users…")
    user_map: dict[str, User] = {}
    for idx, u in enumerate(USERS):
        user = User(password_hash=pw, **u)
        user.created_at = _ago(days=180 - idx * 10)
        db.add(user)
        db.flush()
        user_map[u["email"]] = user
        prefs_data = PREFERENCES.get(u["email"], {})
        db.add(UserPreferences(user_id=user.id, **prefs_data))
    db.commit()
    print(f"  {len(user_map)} users created.")

    # --- Restaurants ---
    print("Creating restaurants…")
    rest_map: dict[str, Restaurant] = {}
    for idx, (creator_email, claimer_email, rdata) in enumerate(RESTAURANTS):
        r = Restaurant(
            created_by=user_map[creator_email].id,
            claimed_by=user_map[claimer_email].id if claimer_email else None,
            **rdata,
        )
        r.created_at = _ago(days=150 - idx * 7)
        db.add(r)
        db.flush()
        rest_map[rdata["name"]] = r
    db.commit()
    print(f"  {len(rest_map)} restaurants created.")

    # --- Restaurant claims ---
    print("Creating ownership claims…")
    claim_count = 0
    for creator_email, claimer_email, rdata in RESTAURANTS:
        if claimer_email:
            db.add(RestaurantClaim(
                restaurant_id=rest_map[rdata["name"]].id,
                owner_id=user_map[claimer_email].id,
                status="approved",
            ))
            claim_count += 1
    db.commit()
    print(f"  {claim_count} claims created.")

    # --- Reviews ---
    print("Creating reviews…")
    for reviewer_email, rest_name, rating, comment, days in REVIEWS:
        db.add(Review(
            user_id=user_map[reviewer_email].id,
            restaurant_id=rest_map[rest_name].id,
            rating=rating,
            comment=comment,
            created_at=_ago(days=days),
            updated_at=_ago(days=days),
        ))
    db.commit()
    print(f"  {len(REVIEWS)} reviews created.")

    # --- Sync restaurant aggregates from actual reviews ---
    # The restaurants were created with hardcoded avg_rating / review_count values.
    # Now that the real review rows exist we recalculate from scratch so the
    # stored aggregates exactly match the reviews table (same logic as the
    # runtime review_service.recalc_rating() which is called on every write).
    print("Recalculating restaurant ratings from actual reviews…")
    for r in rest_map.values():
        db.refresh(r)
        reviews = db.query(Review).filter(Review.restaurant_id == r.id).all()
        count = len(reviews)
        r.review_count = count
        r.avg_rating = round(sum(rv.rating for rv in reviews) / count, 2) if count else 0.0
    db.commit()
    print(f"  Ratings synced for {len(rest_map)} restaurants.")

    # --- Favorites ---
    print("Creating favorites…")
    for idx, (user_email, rest_name) in enumerate(FAVORITES):
        db.add(Favorite(
            user_id=user_map[user_email].id,
            restaurant_id=rest_map[rest_name].id,
            created_at=_ago(days=60 - idx * 2),
        ))
    db.commit()
    print(f"  {len(FAVORITES)} favorites created.")

    # --- Demo AI conversations ---
    print("Creating AI conversation history…")
    for user_email, messages in CONVERSATIONS:
        conv = Conversation(
            user_id=user_map[user_email].id,
            created_at=_ago(days=5),
        )
        db.add(conv)
        db.flush()
        for role, content in messages:
            db.add(ConversationMessage(
                conversation_id=conv.id,
                role=role,
                content=content,
            ))
    db.commit()
    print(f"  {len(CONVERSATIONS)} conversations created.")

    print("\n✓ Seed complete!")
    print("  Demo accounts (all passwords: 'password')")
    print("  ├─ Reviewer:  user@demo.com")
    print("  ├─ Reviewer:  marcus@demo.com / priya@demo.com / alex@demo.com / emily@demo.com")
    print("  └─ Owners:    owner@demo.com / wei@demo.com / sofia@demo.com")


# ---------------------------------------------------------------------------
# Optional: dump SQL for reference
# ---------------------------------------------------------------------------

def _print_sql_note():
    print("""
-- ============================================================
-- ForkFinder seed data — SQL reference
-- ============================================================
-- IMPORTANT: password_hash values below are bcrypt hashes of
-- the string "password" with cost factor 12.
-- They were generated by running:
--   python seed_data.py  (which uses hash_password() from app)
-- Each bcrypt call produces a unique hash; the values below
-- were pre-computed from a single run of seed_data.py.
-- Use the Python script for fresh, verified inserts.
-- ============================================================
""")


# ---------------------------------------------------------------------------
# Non-destructive aggregate recalculation
# ---------------------------------------------------------------------------

def _recalc_all(db: "Session"):
    """
    Recalculate avg_rating and review_count for every restaurant from the
    actual reviews table without wiping any data.

    Safe to run against a live database at any time.
    Use this to fix stale stored aggregates without a full reseed.

    Usage (from the backend/ directory):
        python seed_data.py --recalc
    """
    print("Recalculating all restaurant ratings from reviews table…")
    restaurants = db.query(Restaurant).all()
    updated = 0
    for r in restaurants:
        reviews = db.query(Review).filter(Review.restaurant_id == r.id).all()
        count = len(reviews)
        avg   = round(sum(rv.rating for rv in reviews) / count, 2) if count else 0.0
        if r.review_count != count or round(r.avg_rating or 0.0, 2) != avg:
            r.review_count = count
            r.avg_rating   = avg
            updated += 1
    db.commit()
    print(f"  {updated} / {len(restaurants)} restaurants updated.")
    print("Done.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ForkFinder demo seed script")
    parser.add_argument("--wipe",   action="store_true", help="Wipe all data before seeding")
    parser.add_argument("--sql",    action="store_true", help="Print SQL instructions instead of seeding")
    parser.add_argument("--recalc", action="store_true", help="Recalculate all restaurant ratings without wiping data")
    args = parser.parse_args()

    if args.sql:
        _print_sql_note()
        print("-- Run this script directly instead: python seed_data.py")
        print("-- The seed_data.sql file in docs/ contains the full static SQL.")
        return

    db = SessionLocal()
    try:
        if args.recalc:
            _recalc_all(db)
            return
        _seed(db, args.wipe)
    except Exception as exc:
        db.rollback()
        print(f"\nERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
