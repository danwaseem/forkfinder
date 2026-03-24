-- =============================================================================
-- ForkFinder — Demo Seed Data (SQL INSERT statements)
-- =============================================================================
-- PURPOSE: Reference copy of seed data in SQL format for inspection,
--          manual DB imports, or sharing with DB tools.
--
-- RECOMMENDED SEEDING METHOD: Use the Python script, not this file.
--   cd backend && python seed_data.py --wipe
--
-- WHY THE PYTHON SCRIPT IS PREFERRED:
--   bcrypt generates a unique salt on every call, so the password hashes below
--   are static placeholders — they will NOT verify against 'password'.
--   The Python script calls hash_password() at runtime to produce real hashes.
--
-- TO GENERATE A REAL HASH for direct SQL use:
--   python -c "from app.utils.auth import hash_password; print(hash_password('password'))"
--   Then substitute the output into every password_hash column below.
--
-- DATABASE: MySQL (InnoDB). Tables must exist before running this file.
--   Start the FastAPI app once to auto-create tables, then run this file.
--
-- ASSUMPTIONS:
--   - Tables are empty (run seed_data.py --wipe first, or truncate manually).
--   - Auto-increment IDs start at 1 and follow insertion order.
--   - Foreign key checks must be off during import:
--       SET FOREIGN_KEY_CHECKS = 0; -- before running
--       SET FOREIGN_KEY_CHECKS = 1; -- after running
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- =============================================================================
-- USERS (8 rows)
-- IDs: Jane=1, Marcus=2, Priya=3, Alex=4, Emily=5, Mario=6, Wei=7, Sofia=8
-- =============================================================================

INSERT INTO users
  (id, email, name, role, phone, about_me, city, state, country, languages, gender,
   password_hash, profile_photo_url, created_at, updated_at)
VALUES
  (1, 'user@demo.com',  'Jane Doe',       'user',  '+1 (415) 555-0110',
   'Bay Area food blogger and amateur cookbook author. I chase after the perfect carbonara and the best Mission burrito.',
   'San Francisco', 'CA', 'United States', 'English, Italian',       'female',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-09-22 09:00:00', '2025-09-22 09:00:00'),

  (2, 'marcus@demo.com','Marcus Johnson', 'user',  '+1 (510) 555-0221',
   'Oakland native. BBQ purist, sports bar regular, and firm believer that the best food is always the cheapest.',
   'Oakland',       'CA', 'United States', 'English',                'male',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-10-02 09:00:00', '2025-10-02 09:00:00'),

  (3, 'priya@demo.com', 'Priya Patel',   'user',  '+1 (415) 555-0332',
   'Vegetarian foodie with a weakness for butter chicken (yes, really). Mediterranean and Indian cuisine are my spiritual home.',
   'San Francisco', 'CA', 'United States', 'English, Hindi, Gujarati','female',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-10-12 09:00:00', '2025-10-12 09:00:00'),

  (4, 'alex@demo.com',  'Alex Rivera',   'user',  '+1 (415) 555-0443',
   'Fine dining enthusiast and occasional Michelin chaser. If the omakase has more than 12 courses, I''m already there.',
   'San Francisco', 'CA', 'United States', 'English, Spanish, French','non-binary',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-10-22 09:00:00', '2025-10-22 09:00:00'),

  (5, 'emily@demo.com', 'Emily Chen',    'user',  '+1 (415) 555-0554',
   'Dim sum devotee. I arrive at Dragon Garden before it opens and I regret nothing. Ask me about the best soup dumplings in SF.',
   'San Francisco', 'CA', 'United States', 'English, Mandarin, Cantonese','female',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-11-01 09:00:00', '2025-11-01 09:00:00'),

  (6, 'owner@demo.com', 'Mario Rossi',   'owner', '+1 (415) 555-0601',
   'Third-generation restaurateur from Naples. I opened Ristorante Bello in 2009 and haven''t looked back.',
   'San Francisco', 'CA', 'United States', 'English, Italian',       'male',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-11-11 09:00:00', '2025-11-11 09:00:00'),

  (7, 'wei@demo.com',   'Wei Zhang',     'owner', '+1 (415) 555-0702',
   'Grew up in Hong Kong, trained in Tokyo. My restaurants bridge Cantonese tradition and Japanese precision.',
   'San Francisco', 'CA', 'United States', 'English, Mandarin, Cantonese, Japanese','male',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-11-21 09:00:00', '2025-11-21 09:00:00'),

  (8, 'sofia@demo.com', 'Sofia Hernandez','owner','+1 (415) 555-0803',
   'Oaxacan roots, California soul. My family''s recipes are the foundation of everything we cook.',
   'San Francisco', 'CA', 'United States', 'English, Spanish',       'female',
   '$2b$12$REPLACE_WITH_HASH_GENERATED_BY_PYTHON_SCRIPT',
   NULL, '2025-12-01 09:00:00', '2025-12-01 09:00:00');


-- =============================================================================
-- USER PREFERENCES (5 rows — reviewers only)
-- =============================================================================

INSERT INTO user_preferences
  (user_id, cuisine_preferences, price_range, search_radius,
   preferred_locations, dietary_restrictions, ambiance_preferences, sort_preference)
VALUES
  (1, '["Italian", "Japanese", "French"]', '$$', 15,
   '["San Francisco", "Oakland"]', '[]',
   '["Romantic", "Casual", "Fine Dining"]', 'rating'),

  (2, '["American", "BBQ", "Mexican"]', '$', 20,
   '["Oakland", "San Francisco"]', '[]',
   '["Sports Bar", "Casual", "Quick Bite"]', 'most_reviewed'),

  (3, '["Indian", "Mediterranean", "Vegan", "Thai"]', '$$', 10,
   '["San Francisco"]', '["Vegetarian"]',
   '["Casual", "Outdoor Seating", "Family-Friendly"]', 'rating'),

  (4, '["French", "Japanese", "Korean", "Seafood"]', '$$$', 25,
   '["San Francisco"]', '[]',
   '["Fine Dining", "Romantic", "Rooftop"]', 'rating'),

  (5, '["Chinese", "Japanese", "Vietnamese", "Korean"]', '$$', 12,
   '["San Francisco", "Oakland"]', '[]',
   '["Casual", "Outdoor Seating", "Brunch Spot"]', 'newest');


-- =============================================================================
-- RESTAURANTS (18 rows)
-- IDs 1–18 correspond to insertion order below.
-- created_by / claimed_by reference users.id.
-- =============================================================================

INSERT INTO restaurants
  (id, name, description, cuisine_type, price_range, address, city, state,
   country, zip_code, phone, website, latitude, longitude,
   hours, photos, avg_rating, review_count, is_claimed,
   created_by, claimed_by, created_at, updated_at)
VALUES

-- 1. Ristorante Bello (created by Jane=1, claimed by Mario=6)
(1, 'Ristorante Bello',
 'Authentic Neapolitan pizza and handmade pasta in a warm, candlelit dining room. Family recipes passed down three generations. Our wood-fired oven, imported from Naples in 2009, produces the crispest cornicione in the city. Reserve early on weekends.',
 'Italian', '$$', '540 Columbus Ave', 'San Francisco', 'CA', 'United States', '94133',
 '+1 (415) 555-0101', 'https://ristorantebello.example.com', 37.7991, -122.4076,
 '{"monday":"11:30am \u2013 10:00pm","tuesday":"11:30am \u2013 10:00pm","wednesday":"11:30am \u2013 10:00pm","thursday":"11:30am \u2013 10:00pm","friday":"11:30am \u2013 11:00pm","saturday":"10:00am \u2013 11:00pm","sunday":"10:00am \u2013 9:00pm"}',
 '[]', 4.67, 3, TRUE, 1, 6, '2025-10-22 10:00:00', '2025-10-22 10:00:00'),

-- 2. Bella Vista Rooftop (created by Jane=1, claimed by Mario=6)
(2, 'Bella Vista Rooftop',
 'Perched atop a Union Square hotel with sweeping bay views, Bella Vista serves Italian-American kitchen classics alongside craft cocktails. The wood-fired flatbreads and the hand-rolled gnocchi are must-orders. Heated outdoor seating available year-round.',
 'Italian', '$$$', '200 Powell St', 'San Francisco', 'CA', 'United States', '94102',
 '+1 (415) 555-0606', 'https://bellavistasf.example.com', 37.7879, -122.4075,
 '{"monday":"Closed","tuesday":"Closed","wednesday":"4:00pm \u2013 12:00am","thursday":"4:00pm \u2013 12:00am","friday":"3:00pm \u2013 1:00am","saturday":"2:00pm \u2013 1:00am","sunday":"2:00pm \u2013 10:00pm"}',
 '[]', 4.00, 2, TRUE, 1, 6, '2025-10-29 10:00:00', '2025-10-29 10:00:00'),

-- 3. Dragon Garden (created by Jane=1, claimed by Wei=7)
(3, 'Dragon Garden',
 'Modern dim sum and traditional Cantonese cuisine in the heart of Chinatown. Steamer baskets crafted fresh every morning from market produce. The har gow and XO chili crab have won citywide accolades. Arrive before 10am on weekends or expect an hour wait.',
 'Chinese', '$$', '456 Stockton St', 'San Francisco', 'CA', 'United States', '94108',
 '+1 (415) 555-0202', 'https://dragongardensf.example.com', 37.7955, -122.4066,
 '{"monday":"Closed","tuesday":"10:00am \u2013 9:00pm","wednesday":"10:00am \u2013 9:00pm","thursday":"10:00am \u2013 9:00pm","friday":"10:00am \u2013 10:00pm","saturday":"9:00am \u2013 10:00pm","sunday":"9:00am \u2013 9:00pm"}',
 '[]', 4.50, 2, TRUE, 1, 7, '2025-11-05 10:00:00', '2025-11-05 10:00:00'),

-- 4. Sakura Omakase (created by Marcus=2, claimed by Wei=7)
(4, 'Sakura Omakase',
 'An intimate 12-seat counter experience in the Financial District. Chef Kenji''s 18-course Edomae omakase changes with the seasons — think Hokkaido uni, aged bluefin toro, and house-made tamago. Reservations open 60 days in advance; they sell out in minutes.',
 'Japanese', '$$$$', '50 Belden Pl', 'San Francisco', 'CA', 'United States', '94104',
 '+1 (415) 555-0505', 'https://sakuraomakase.example.com', 37.7912, -122.4016,
 '{"monday":"Closed","tuesday":"Closed","wednesday":"6:00pm \u2013 10:30pm","thursday":"6:00pm \u2013 10:30pm","friday":"6:00pm \u2013 11:00pm","saturday":"5:30pm \u2013 11:00pm","sunday":"5:30pm \u2013 9:00pm"}',
 '[]', 5.00, 2, TRUE, 2, 7, '2025-11-12 10:00:00', '2025-11-12 10:00:00'),

-- 5. Ramen House Natori (created by Priya=3, unclaimed)
(5, 'Ramen House Natori',
 'No-frills tonkotsu and shoyu ramen shop in Japantown. The 18-hour pork bone broth is the real thing: milky, rich, and deeply savory. Noodles made in-house daily. Cash only, no substitutions, no apologies.',
 'Japanese', '$', '1737 Post St', 'San Francisco', 'CA', 'United States', '94115',
 '+1 (415) 555-0404', NULL, 37.7851, -122.4312,
 '{"monday":"11:00am \u2013 9:00pm","tuesday":"11:00am \u2013 9:00pm","wednesday":"11:00am \u2013 9:00pm","thursday":"11:00am \u2013 9:00pm","friday":"11:00am \u2013 10:00pm","saturday":"11:00am \u2013 10:00pm","sunday":"12:00pm \u2013 8:00pm"}',
 '[]', 4.00, 2, FALSE, 3, NULL, '2025-11-19 10:00:00', '2025-11-19 10:00:00'),

-- 6. Taqueria La Paloma (created by Priya=3, claimed by Sofia=8)
(6, 'Taqueria La Paloma',
 'Family-owned Mission taqueria with 20 years of slow-braised carnitas and hand-ground masa. The al pastor spit turns from 7am; the carne asada burrito is the size of a newborn. Fresh salsas made hourly. Breakfast burritos until noon, Fri-Sun.',
 'Mexican', '$', '3000 Mission St', 'San Francisco', 'CA', 'United States', '94110',
 '+1 (415) 555-0404', NULL, 37.7432, -122.4194,
 '{"monday":"8:00am \u2013 9:00pm","tuesday":"8:00am \u2013 9:00pm","wednesday":"8:00am \u2013 9:00pm","thursday":"8:00am \u2013 9:00pm","friday":"8:00am \u2013 10:00pm","saturday":"8:00am \u2013 10:00pm","sunday":"9:00am \u2013 8:00pm"}',
 '[]', 4.67, 3, TRUE, 3, 8, '2025-11-26 10:00:00', '2025-11-26 10:00:00'),

-- 7. Casa Oaxaca (created by Alex=4, claimed by Sofia=8)
(7, 'Casa Oaxaca',
 'Chef Sofia''s homage to her grandmother''s kitchen in Oaxaca City. The mole negro takes three days to prepare. The tlayudas are crispy, enormous, and life-changing. Mezcal list curated by the chef herself. Reservations strongly recommended.',
 'Mexican', '$$$', '400 Grove St', 'San Francisco', 'CA', 'United States', '94102',
 '+1 (415) 555-0707', 'https://casaoaxaca.example.com', 37.7771, -122.4225,
 '{"monday":"Closed","tuesday":"5:30pm \u2013 10:00pm","wednesday":"5:30pm \u2013 10:00pm","thursday":"5:30pm \u2013 10:00pm","friday":"5:30pm \u2013 11:00pm","saturday":"5:30pm \u2013 11:00pm","sunday":"5:30pm \u2013 9:30pm"}',
 '[]', 4.50, 2, TRUE, 4, 8, '2025-12-03 10:00:00', '2025-12-03 10:00:00'),

-- 8. Spice Route (created by Alex=4, unclaimed)
(8, 'Spice Route',
 'Northern Indian cuisine with a modern California sensibility. The lamb rogan josh braises for six hours. The dal makhani is legendary — same pot, low heat, all day. Extensive vegetarian menu with 12 rotating daily specials.',
 'Indian', '$$$', '789 Valencia St', 'San Francisco', 'CA', 'United States', '94110',
 '+1 (415) 555-0303', NULL, 37.7612, -122.4212,
 '{"monday":"5:00pm \u2013 10:00pm","tuesday":"5:00pm \u2013 10:00pm","wednesday":"5:00pm \u2013 10:00pm","thursday":"5:00pm \u2013 10:00pm","friday":"5:00pm \u2013 11:00pm","saturday":"12:00pm \u2013 11:00pm","sunday":"12:00pm \u2013 9:00pm"}',
 '[]', 4.50, 2, FALSE, 4, NULL, '2025-12-10 10:00:00', '2025-12-10 10:00:00'),

-- 9. Bangkok Noodles (created by Emily=5, unclaimed)
(9, 'Bangkok Noodles',
 'A 14-seat hole-in-the-wall in Oakland serving pad see ew and drunken noodles so good the wait is always 30 minutes. The khao soi — Chiang Mai curry noodle soup — has a cult following. Bring cash and patience; it is absolutely worth it.',
 'Thai', '$', '388 Grand Ave', 'Oakland', 'CA', 'United States', '94610',
 '+1 (510) 555-0809', NULL, 37.8103, -122.2574,
 '{"monday":"Closed","tuesday":"11:30am \u2013 9:00pm","wednesday":"11:30am \u2013 9:00pm","thursday":"11:30am \u2013 9:00pm","friday":"11:30am \u2013 10:00pm","saturday":"11:30am \u2013 10:00pm","sunday":"12:00pm \u2013 8:00pm"}',
 '[]', 3.50, 2, FALSE, 5, NULL, '2025-12-17 10:00:00', '2025-12-17 10:00:00'),

-- 10. The Smokehouse (created by Emily=5, unclaimed)
(10, 'The Smokehouse',
 'Texas-style BBQ in Temescal. Brisket smoked low and slow over post oak for 14-18 hours. The ribs are fall-off-the-bone and the sides — jalapeño mac, collard greens, smoked beans — are almost as good as the meat. Opens at 11am; sells out by 7pm most days.',
 'American', '$$', '4031 Broadway', 'Oakland', 'CA', 'United States', '94611',
 '+1 (510) 555-0910', NULL, 37.8318, -122.2610,
 '{"monday":"Closed","tuesday":"Closed","wednesday":"11:00am \u2013 9:00pm","thursday":"11:00am \u2013 9:00pm","friday":"11:00am \u2013 9:00pm","saturday":"11:00am \u2013 9:00pm","sunday":"11:00am \u2013 7:00pm"}',
 '[]', 5.00, 1, FALSE, 5, NULL, '2025-12-24 10:00:00', '2025-12-24 10:00:00'),

-- 11. Blue Plate Diner (created by Jane=1, unclaimed)
(11, 'Blue Plate Diner',
 'An old-school Castro diner serving American comfort food. The meatloaf, the grilled cheese, and the chocolate milkshake are exactly what you want after a long week. Nothing fancy, no reservations, always a wait — and worth every minute.',
 'American', '$', '3218 Mission St', 'San Francisco', 'CA', 'United States', '94110',
 '+1 (415) 555-1001', NULL, 37.7463, -122.4206,
 '{"monday":"8:00am \u2013 9:00pm","tuesday":"8:00am \u2013 9:00pm","wednesday":"8:00am \u2013 9:00pm","thursday":"8:00am \u2013 9:00pm","friday":"8:00am \u2013 10:00pm","saturday":"8:00am \u2013 10:00pm","sunday":"8:00am \u2013 8:00pm"}',
 '[]', 3.00, 1, FALSE, 1, NULL, '2025-12-31 10:00:00', '2025-12-31 10:00:00'),

-- 12. Olive Branch (created by Marcus=2, claimed by Sofia=8)
(12, 'Olive Branch',
 'A Marina Mediterranean that sources its olive oil directly from a small Greek co-op in Crete. The whole roasted fish changes daily. The mezze spread — hummus, tabbouleh, lamb kofta — is the way to go for groups. Outdoor patio with heat lamps.',
 'Mediterranean', '$$', '2020 Chestnut St', 'San Francisco', 'CA', 'United States', '94123',
 '+1 (415) 555-1102', 'https://olivebranchsf.example.com', 37.8001, -122.4370,
 '{"monday":"Closed","tuesday":"5:30pm \u2013 9:30pm","wednesday":"5:30pm \u2013 9:30pm","thursday":"5:30pm \u2013 9:30pm","friday":"5:30pm \u2013 10:30pm","saturday":"11:30am \u2013 10:30pm","sunday":"11:30am \u2013 9:00pm"}',
 '[]', 4.50, 2, TRUE, 2, 8, '2026-01-07 10:00:00', '2026-01-07 10:00:00'),

-- 13. Seoul Kitchen (created by Marcus=2, unclaimed)
(13, 'Seoul Kitchen',
 'Korean BBQ and modern bibimbap in the Tenderloin. The galbi (short rib) marinated for 24 hours is the table centerpiece. Banchan changes weekly; the house kimchi is house-fermented for 6 weeks. Lunch specials until 3pm are an absurd deal.',
 'Korean', '$$', '806 Larkin St', 'San Francisco', 'CA', 'United States', '94109',
 '+1 (415) 555-1203', NULL, 37.7829, -122.4182,
 '{"monday":"11:00am \u2013 10:00pm","tuesday":"11:00am \u2013 10:00pm","wednesday":"11:00am \u2013 10:00pm","thursday":"11:00am \u2013 10:00pm","friday":"11:00am \u2013 11:00pm","saturday":"11:00am \u2013 11:00pm","sunday":"12:00pm \u2013 9:00pm"}',
 '[]', 4.50, 2, FALSE, 2, NULL, '2026-01-14 10:00:00', '2026-01-14 10:00:00'),

-- 14. Pho Saigon (created by Priya=3, unclaimed)
(14, 'Pho Saigon',
 'A Tenderloin institution for over 30 years. The pho broth simmers for 12 hours with star anise, cloves, and beef bones. Order the #1 (rare beef + brisket) and load the table with hoisin, sriracha, bean sprouts, and Thai basil. Open late, cheap, and glorious.',
 'Vietnamese', '$', '709 Larkin St', 'San Francisco', 'CA', 'United States', '94109',
 '+1 (415) 555-1304', NULL, 37.7821, -122.4181,
 '{"monday":"9:00am \u2013 10:00pm","tuesday":"9:00am \u2013 10:00pm","wednesday":"9:00am \u2013 10:00pm","thursday":"9:00am \u2013 10:00pm","friday":"9:00am \u2013 11:00pm","saturday":"9:00am \u2013 11:00pm","sunday":"9:00am \u2013 9:00pm"}',
 '[]', 4.00, 2, FALSE, 3, NULL, '2026-01-21 10:00:00', '2026-01-21 10:00:00'),

-- 15. Café Madeleine (created by Alex=4, unclaimed)
(15, 'Café Madeleine',
 'A slice of Paris in Hayes Valley. Michelin Bib Gourmand 2023. The duck confit is prepared sous-vide for 48 hours and finished in brown butter. The cheese cart is a minor religious experience. Prix-fixe available Friday and Saturday evenings.',
 'French', '$$$', '260 Gough St', 'San Francisco', 'CA', 'United States', '94102',
 '+1 (415) 555-1405', 'https://cafemadeleine.example.com', 37.7756, -122.4222,
 '{"monday":"Closed","tuesday":"Closed","wednesday":"5:30pm \u2013 9:30pm","thursday":"5:30pm \u2013 9:30pm","friday":"5:30pm \u2013 10:30pm","saturday":"11:30am \u2013 10:30pm","sunday":"11:30am \u2013 8:00pm"}',
 '[]', 4.50, 2, FALSE, 4, NULL, '2026-01-28 10:00:00', '2026-01-28 10:00:00'),

-- 16. The Green Bowl (created by Emily=5, unclaimed)
(16, 'The Green Bowl',
 '100% plant-based kitchen in Berkeley serving grain bowls, jackfruit tacos, and a rotating cast of globally inspired vegan dishes. Nothing processed, nothing fake — just whole ingredients treated with care. The cashew queso and the miso-glazed eggplant are the stars.',
 'Vegan', '$', '2115 Center St', 'Berkeley', 'CA', 'United States', '94704',
 '+1 (510) 555-1506', 'https://thegreenbowl.example.com', 37.8716, -122.2727,
 '{"monday":"11:00am \u2013 8:00pm","tuesday":"11:00am \u2013 8:00pm","wednesday":"11:00am \u2013 8:00pm","thursday":"11:00am \u2013 8:00pm","friday":"11:00am \u2013 9:00pm","saturday":"10:00am \u2013 9:00pm","sunday":"10:00am \u2013 7:00pm"}',
 '[]', 4.00, 1, FALSE, 5, NULL, '2026-02-04 10:00:00', '2026-02-04 10:00:00'),

-- 17. The Wharf Kitchen (created by Alex=4, unclaimed)
(17, 'The Wharf Kitchen',
 'Straight-from-the-boat Dungeness crab, oysters from Tomales Bay, and wood-grilled halibut at Fisherman''s Wharf. Ask your server what came in this morning — the chalkboard changes daily. The lobster bisque is the best in the city, period.',
 'Seafood', '$$$', '99 Jefferson St', 'San Francisco', 'CA', 'United States', '94133',
 '+1 (415) 555-1607', 'https://wharfkitchensf.example.com', 37.8080, -122.4160,
 '{"monday":"11:00am \u2013 9:00pm","tuesday":"11:00am \u2013 9:00pm","wednesday":"11:00am \u2013 9:00pm","thursday":"11:00am \u2013 9:00pm","friday":"11:00am \u2013 10:00pm","saturday":"10:00am \u2013 10:00pm","sunday":"10:00am \u2013 9:00pm"}',
 '[]', 4.00, 1, FALSE, 4, NULL, '2026-02-11 10:00:00', '2026-02-11 10:00:00'),

-- 18. Sunday Morning Café (created by Emily=5, unclaimed)
(18, 'Sunday Morning Café',
 'Noe Valley''s favorite all-day brunch spot. The ricotta pancakes, the smashed avocado toast with everything bagel seasoning, and the lemon curd Dutch baby are all worth the weekend crowd. Bottomless mimosas until 2pm. Reservations for 6+ only.',
 'American', '$$', '4000 24th St', 'San Francisco', 'CA', 'United States', '94114',
 '+1 (415) 555-1708', NULL, 37.7514, -122.4319,
 '{"monday":"8:00am \u2013 3:00pm","tuesday":"8:00am \u2013 3:00pm","wednesday":"8:00am \u2013 3:00pm","thursday":"8:00am \u2013 3:00pm","friday":"8:00am \u2013 4:00pm","saturday":"7:30am \u2013 4:00pm","sunday":"7:30am \u2013 4:00pm"}',
 '[]', 4.67, 3, FALSE, 5, NULL, '2026-02-18 10:00:00', '2026-02-18 10:00:00');


-- =============================================================================
-- RESTAURANT CLAIMS (9 rows — one per claimed restaurant)
-- owner_id references users.id (only owner-role users may claim)
-- =============================================================================

INSERT INTO restaurant_claims
  (restaurant_id, owner_id, status, created_at)
VALUES
  (1,  6, 'approved', '2025-10-23 12:00:00'),   -- Ristorante Bello → Mario
  (2,  6, 'approved', '2025-10-30 12:00:00'),   -- Bella Vista Rooftop → Mario
  (3,  7, 'approved', '2025-11-06 12:00:00'),   -- Dragon Garden → Wei
  (4,  7, 'approved', '2025-11-13 12:00:00'),   -- Sakura Omakase → Wei
  (6,  8, 'approved', '2025-11-27 12:00:00'),   -- Taqueria La Paloma → Sofia
  (7,  8, 'approved', '2025-12-04 12:00:00'),   -- Casa Oaxaca → Sofia
  (12, 8, 'approved', '2026-01-08 12:00:00');   -- Olive Branch → Sofia


-- =============================================================================
-- REVIEWS (35 rows)
-- user_id and restaurant_id reference the IDs assigned above.
-- photos stored as JSON array (empty for all seed reviews).
-- =============================================================================

INSERT INTO reviews
  (user_id, restaurant_id, rating, comment, photos, created_at, updated_at)
VALUES

-- Ristorante Bello (id=1) — 3 reviews → avg 4.67
(1, 1, 5,
 'Best pasta I''ve had outside of Naples. The carbonara is silky smooth — no cream, just egg, guanciale, and pecorino, exactly as it should be. The tiramisu knocked me sideways. Booked the corner table again for next month.',
 '[]', '2026-02-04 19:30:00', '2026-02-04 19:30:00'),

(2, 1, 4,
 'Solid Italian food, great atmosphere. The margherita pizza had a perfect char on the crust. Only reason it''s not a 5 is that we waited 20 minutes for our check on a busy Saturday night.',
 '[]', '2026-02-19 20:00:00', '2026-02-19 20:00:00'),

(4, 1, 5,
 'The burrata is from Puglia. The tagliatelle al ragù is textbook. Mario himself came out to the table and talked pasta shapes for 10 minutes. This is the real deal.',
 '[]', '2026-03-06 20:30:00', '2026-03-06 20:30:00'),

-- Bella Vista Rooftop (id=2) — 2 reviews → avg 4.00
(5, 2, 4,
 'The rooftop view alone is worth the price. Bay Bridge lit up at sunset while we had the flatbreads and a bottle of Montepulciano — honestly magical. Service a bit slow but the vibe forgives everything.',
 '[]', '2026-03-01 19:00:00', '2026-03-01 19:00:00'),

(4, 2, 4,
 'Great cocktails, gorgeous view, food is solid if not groundbreaking. The lobster gnocchi was the highlight. Go for drinks and stay for dinner if the stars align.',
 '[]', '2026-03-13 21:00:00', '2026-03-13 21:00:00'),

-- Dragon Garden (id=3) — 2 reviews → avg 4.50
(1, 3, 5,
 'The best dim sum in San Francisco, full stop. The shrimp dumplings are translucent-wrapper perfection. The pineapple buns from the cart are addictive. Go early on Sunday — the line is worth it.',
 '[]', '2026-01-20 11:00:00', '2026-01-20 11:00:00'),

(5, 3, 4,
 'I''ve been coming here for years and it never disappoints. The XO chili crab on Fridays is a special event. Only knocked one star because they stopped serving the egg custard tarts — bring them back!',
 '[]', '2026-02-14 12:30:00', '2026-02-14 12:30:00'),

-- Sakura Omakase (id=4) — 2 reviews → avg 5.00
(1, 4, 5,
 '18 courses of absolute precision. Chef Kenji presented the bluefin toro with a description of the fishing village in Oma where it was caught. I understood I was in the presence of something serious. Worth every penny.',
 '[]', '2025-12-21 21:00:00', '2025-12-21 21:00:00'),

(4, 4, 5,
 'The best meal I''ve had in San Francisco — and I eat out constantly. The Hokkaido uni on warm shari was the transcendent moment. Booked six months out but I''m going back.',
 '[]', '2026-02-24 21:30:00', '2026-02-24 21:30:00'),

-- Ramen House Natori (id=5) — 2 reviews → avg 4.00
(2, 5, 4,
 'No-nonsense ramen done brilliantly. The tonkotsu broth is creamy without being heavy. Soft-boiled egg marinated overnight — perfect. Cash only, tiny space, worth every inconvenience.',
 '[]', '2026-02-09 13:00:00', '2026-02-09 13:00:00'),

(4, 5, 4,
 'The tsukemen (dipping noodles) here is one of SF''s best-kept secrets. Thick wavy noodles with a rich, intense dipping broth. No substitutions, no modifications — the chef knows what they''re doing, trust the menu.',
 '[]', '2026-03-03 13:30:00', '2026-03-03 13:30:00'),

-- Taqueria La Paloma (id=6) — 3 reviews → avg 4.67
(1, 6, 5,
 'I''ve been eating here for 10 years. The al pastor is carved off the trompo right in front of you. The green tomatillo salsa is dangerously addictive. Best $12 I spend in this city, every single time.',
 '[]', '2026-01-25 12:30:00', '2026-01-25 12:30:00'),

(3, 6, 5,
 'They have incredible bean-and-cheese burritos for vegetarians. The refried beans are made from scratch daily. Even as a vegetarian, I make a special trip for the mushroom and potato tacos. Perfect.',
 '[]', '2026-02-21 12:00:00', '2026-02-21 12:00:00'),

(5, 6, 4,
 'Iconic. The breakfast burrito on Saturday morning is life-affirming. Long line but it moves fast. Get the super burrito, not the regular. Only four stars because parking in the Mission is impossible.',
 '[]', '2026-03-09 10:30:00', '2026-03-09 10:30:00'),

-- Casa Oaxaca (id=7) — 2 reviews → avg 4.50
(3, 7, 4,
 'The mole negro is extraordinary — complex, slightly bitter, perfectly balanced. I''m vegetarian and they were incredibly accommodating with substitutions. The mezcal list is curated with real thought. A special-occasion restaurant.',
 '[]', '2026-02-27 19:30:00', '2026-02-27 19:30:00'),

(4, 7, 5,
 'Sofia Hernandez is cooking at a Michelin level. The memelas with epazote and black beans, the tlayuda, the mole — every dish tells a story. The mezcal flight is an education. Best Mexican fine dining in the Bay.',
 '[]', '2026-03-11 20:00:00', '2026-03-11 20:00:00'),

-- Spice Route (id=8) — 2 reviews → avg 4.50
(3, 8, 5,
 'As someone who grew up eating real Indian home cooking, this is the restaurant I recommend to everyone who wants to understand the cuisine. The dal makhani is slow-cooked for hours — it tastes like my mother''s kitchen. The mango lassi is perfect.',
 '[]', '2026-02-11 20:00:00', '2026-02-11 20:00:00'),

(2, 8, 4,
 'Ordered the lamb rogan josh based on a recommendation and it blew me away. Six-hour braise, deep red, aromatic without being too hot. The garlic naan was also exceptional. A bit pricey but worth the splurge.',
 '[]', '2026-03-05 20:30:00', '2026-03-05 20:30:00'),

-- Bangkok Noodles (id=9) — 2 reviews → avg 3.50
(4, 9, 4,
 'The khao soi here is one of the best things I''ve eaten in Oakland. Rich coconut curry broth, crispy egg noodles on top, tender chicken. Tiny space, often a wait, but the food is absolutely worth it.',
 '[]', '2026-01-30 13:00:00', '2026-01-30 13:00:00'),

(5, 9, 3,
 'The pad see ew is solid but I''ve had better. The khao soi is the reason to come — everything else is secondary. Service is brusque and the space is not comfortable. But for that khao soi, I''ll return.',
 '[]', '2026-02-22 13:30:00', '2026-02-22 13:30:00'),

-- The Smokehouse (id=10) — 1 review → avg 5.00
(2, 10, 5,
 'This is the Texas BBQ I moved to California hoping to find and never did — until now. The 18-hour brisket has the correct smoke ring, the correct bark, the correct fat render. The burnt ends were a religious experience. Worth the trip to Oakland a thousand times over.',
 '[]', '2026-02-17 14:00:00', '2026-02-17 14:00:00'),

-- Blue Plate Diner (id=11) — 1 review → avg 3.00
(2, 11, 3,
 'Exactly what it claims to be: a diner. The grilled cheese was fine, the milkshake was good, the meatloaf was underwhelming. Comfortable, cheap, reliable. Don''t expect anything more.',
 '[]', '2026-01-15 13:00:00', '2026-01-15 13:00:00'),

-- Olive Branch (id=12) — 2 reviews → avg 4.50
(1, 12, 5,
 'The mezze spread for two is a meal in itself. The hummus with lamb kafta on top, the baba ganoush, the fattoush salad. All of it made with genuine care. The outdoor patio is beautiful on a warm evening.',
 '[]', '2026-02-07 19:30:00', '2026-02-07 19:30:00'),

(3, 12, 4,
 'Wonderful vegetarian options — the mushroom and halloumi skewers, the spanakopita, the stuffed peppers. The staff were very knowledgeable about plant-based choices. Lovely Marina atmosphere.',
 '[]', '2026-03-02 19:00:00', '2026-03-02 19:00:00'),

-- Seoul Kitchen (id=13) — 2 reviews → avg 4.50
(2, 13, 4,
 'The galbi (short rib) is the best in SF. 24-hour marinade shows — the meat is incredibly tender with that caramelized grill char. The banchan spread is generous and the kimchi is properly funky. Great value.',
 '[]', '2026-02-01 19:00:00', '2026-02-01 19:00:00'),

(5, 13, 5,
 'I grew up eating Korean BBQ and this is the real thing. The ventilation works properly (no smoke smell on your clothes after). The sundubu jjigae (soft tofu stew) is outstanding. The lunch special is one of SF''s best-kept secrets.',
 '[]', '2026-03-07 13:00:00', '2026-03-07 13:00:00'),

-- Pho Saigon (id=14) — 2 reviews → avg 4.00
(4, 14, 4,
 'Late-night pho at its finest. The broth is genuinely 12-hour slow-cooked — you can taste it. The #1 combination (rare beef, brisket, tendon) is the order. Cheap, authentic, perfect for 1am after a long evening.',
 '[]', '2026-01-08 23:00:00', '2026-01-08 23:00:00'),

(5, 14, 4,
 'My go-to pho in the Tenderloin for 5 years. The broth is clean and aromatic, not overly salty. The banh mi is underrated — crisp baguette, proper pâté. Friendly staff, fast service, open late. A neighborhood gem.',
 '[]', '2026-02-16 21:00:00', '2026-02-16 21:00:00'),

-- Café Madeleine (id=15) — 2 reviews → avg 4.50
(1, 15, 5,
 'The duck confit arrived with a perfectly crisped skin and melting dark meat underneath. The cheese cart made a second pass by our table because the sommelier correctly identified that we would not say no. Romantic, unhurried, Parisian in the best possible sense.',
 '[]', '2026-01-27 20:30:00', '2026-01-27 20:30:00'),

(4, 15, 4,
 'Michelin Bib Gourmand status is well-earned. The bouillabaisse is impeccable. The prix-fixe on Friday night is exceptional value at this level of cooking. Only one star back because the tables are too close together.',
 '[]', '2026-02-28 21:00:00', '2026-02-28 21:00:00'),

-- The Green Bowl (id=16) — 1 review → avg 4.00
(3, 16, 4,
 'A genuinely exciting vegan restaurant — not just sad salads and rice cakes. The jackfruit tacos taste like the real thing. The miso eggplant is caramelized and deeply savory. Great for vegetarians and skeptics alike.',
 '[]', '2026-02-20 13:00:00', '2026-02-20 13:00:00'),

-- The Wharf Kitchen (id=17) — 1 review → avg 4.00
(2, 17, 4,
 'I''m not usually a seafood person but the wood-grilled halibut here converted me. Fresh, simply cooked, not messed with. The clam chowder in a sourdough bowl is tourist food but excellent tourist food. Bring a big appetite and a fat wallet.',
 '[]', '2026-02-12 19:30:00', '2026-02-12 19:30:00'),

-- Sunday Morning Café (id=18) — 3 reviews → avg 4.67
(4, 18, 5,
 'The Dutch baby pancake with lemon curd and powdered sugar is the reason I get up before noon on Sundays. The bottomless mimosas are dangerously well-priced. Book a table at 8am to avoid the madness. Worth every minute of the wait.',
 '[]', '2026-01-12 09:30:00', '2026-01-12 09:30:00'),

(5, 18, 4,
 'The avocado toast here is how avocado toast was meant to be: on sourdough, with burrata, finished with chili flakes and microgreens. The cold brew is exceptional. Long wait on weekends but a beautiful vibe.',
 '[]', '2026-02-05 10:00:00', '2026-02-05 10:00:00'),

(1, 18, 5,
 'Noe Valley on a Sunday morning, a table by the window, ricotta pancakes, and a proper cappuccino. Simple pleasures done perfectly. This is one of my happy places.',
 '[]', '2026-03-10 09:00:00', '2026-03-10 09:00:00');


-- =============================================================================
-- FAVORITES (18 rows)
-- =============================================================================

INSERT INTO favorites
  (user_id, restaurant_id, created_at)
VALUES
  (1,  1,  '2026-01-20 10:00:00'),   -- Jane → Ristorante Bello
  (1,  3,  '2026-01-22 10:00:00'),   -- Jane → Dragon Garden
  (1,  6,  '2026-01-24 10:00:00'),   -- Jane → Taqueria La Paloma
  (1,  15, '2026-01-26 10:00:00'),   -- Jane → Café Madeleine
  (2,  1,  '2026-01-28 10:00:00'),   -- Marcus → Ristorante Bello
  (2,  6,  '2026-01-30 10:00:00'),   -- Marcus → Taqueria La Paloma
  (2,  10, '2026-02-01 10:00:00'),   -- Marcus → The Smokehouse
  (3,  7,  '2026-02-03 10:00:00'),   -- Priya → Casa Oaxaca
  (3,  8,  '2026-02-05 10:00:00'),   -- Priya → Spice Route
  (3,  16, '2026-02-07 10:00:00'),   -- Priya → The Green Bowl
  (4,  4,  '2026-02-09 10:00:00'),   -- Alex → Sakura Omakase
  (4,  7,  '2026-02-11 10:00:00'),   -- Alex → Casa Oaxaca
  (4,  15, '2026-02-13 10:00:00'),   -- Alex → Café Madeleine
  (4,  18, '2026-02-15 10:00:00'),   -- Alex → Sunday Morning Café
  (5,  3,  '2026-02-17 10:00:00'),   -- Emily → Dragon Garden
  (5,  6,  '2026-02-19 10:00:00'),   -- Emily → Taqueria La Paloma
  (5,  13, '2026-02-21 10:00:00'),   -- Emily → Seoul Kitchen
  (5,  18, '2026-02-23 10:00:00');   -- Emily → Sunday Morning Café


-- =============================================================================
-- AI CONVERSATIONS (2 demo sessions)
-- Requires conversations and conversation_messages tables.
-- =============================================================================

INSERT INTO conversations (id, user_id, created_at)
VALUES
  (1, 1, '2026-03-16 19:00:00'),   -- Jane's Italian dinner conversation
  (2, 4, '2026-03-16 20:00:00');   -- Alex's omakase conversation

INSERT INTO conversation_messages (conversation_id, role, content, created_at)
VALUES
  (1, 'user',
   'I want Italian food tonight, romantic setting, budget around $$',
   '2026-03-16 19:00:05'),
  (1, 'assistant',
   'Based on your preferences, I''d recommend Ristorante Bello in North Beach. It''s a warm candlelit space with authentic Neapolitan pasta. Rated 4.7/5 with consistent reviews praising the carbonara and the intimate atmosphere. Would you like to know more, or shall I suggest an alternative?',
   '2026-03-16 19:00:07'),
  (1, 'user',
   'Sounds perfect. Does it have outdoor seating?',
   '2026-03-16 19:01:20'),
  (1, 'assistant',
   'Ristorante Bello is an indoor dining room — cozy booths and candlelight, which actually works beautifully for a romantic evening. If outdoor seating is important to you, Bella Vista Rooftop also serves Italian cuisine with a heated outdoor terrace and stunning bay views, though it''s priced at $$$. Shall I compare the two?',
   '2026-03-16 19:01:22'),

  (2, 'user',
   'I''m looking for the best omakase experience in San Francisco, money is no object',
   '2026-03-16 20:00:05'),
  (2, 'assistant',
   'Sakura Omakase is the standout choice. Chef Kenji''s 18-course Edomae experience at 50 Belden Pl has a perfect 5.0 rating from reviewers. The seasonal menu features Hokkaido uni, aged bluefin toro, and house tamago. Reservations open 60 days in advance and sell out quickly — I''d recommend booking immediately. Would you like help with anything else?',
   '2026-03-16 20:00:08');


-- =============================================================================
-- Re-enable foreign key checks
-- =============================================================================

SET FOREIGN_KEY_CHECKS = 1;

-- End of seed_data.sql
-- Total rows inserted:
--   users:                  8
--   user_preferences:       5
--   restaurants:           18
--   restaurant_claims:      7
--   reviews:               35
--   favorites:             18
--   conversations:          2
--   conversation_messages:  6
