# ForkFinder — AI Chatbot Demo Restaurant Guide

This guide maps each seeded restaurant to the chatbot query patterns it handles best.
Use it when preparing demo scripts, grading AI recommendation quality, or building
test prompts for the AI assistant.

---

## Quick-Reference Table

| # | Restaurant | Cuisine | Price | City | Best AI Trigger Phrases |
|---|---|---|---|---|---|
| 1 | Ristorante Bello | Italian | $$ | SF | "Italian dinner", "romantic pasta", "cozy Italian" |
| 2 | Bella Vista Rooftop | Italian | $$$ | SF | "rooftop", "views", "romantic cocktails", "sunset dinner" |
| 3 | Dragon Garden | Chinese | $$ | SF | "dim sum", "Cantonese", "Sunday brunch", "dumplings" |
| 4 | Sakura Omakase | Japanese | $$$$ | SF | "omakase", "fine dining", "splurge", "best sushi", "Michelin-level" |
| 5 | Ramen House Natori | Japanese | $ | SF | "ramen", "tonkotsu", "cheap lunch", "Japantown", "comfort food" |
| 6 | Taqueria La Paloma | Mexican | $ | SF | "cheap eats", "burrito", "taco", "Mission", "breakfast" |
| 7 | Casa Oaxaca | Mexican | $$$ | SF | "mole", "Oaxacan", "mezcal", "special occasion Mexican" |
| 8 | Spice Route | Indian | $$$ | SF | "Indian food", "lamb", "vegetarian Indian", "curry", "rogan josh" |
| 9 | Bangkok Noodles | Thai | $ | Oakland | "Thai food", "khao soi", "pad see ew", "Oakland", "noodles" |
| 10 | The Smokehouse | American | $$ | Oakland | "BBQ", "brisket", "Texas BBQ", "Oakland", "meat", "ribs" |
| 11 | Blue Plate Diner | American | $ | SF | "diner", "comfort food", "cheap", "grilled cheese", "milkshake" |
| 12 | Olive Branch | Mediterranean | $$ | SF | "Mediterranean", "hummus", "outdoor seating", "mezze", "vegetarian-friendly" |
| 13 | Seoul Kitchen | Korean | $$ | SF | "Korean BBQ", "galbi", "bibimbap", "kimchi", "lunch specials" |
| 14 | Pho Saigon | Vietnamese | $ | SF | "pho", "Vietnamese", "late night", "cheap", "Tenderloin" |
| 15 | Café Madeleine | French | $$$ | SF | "French", "duck confit", "date night", "Bib Gourmand", "prix-fixe" |
| 16 | The Green Bowl | Vegan | $ | Berkeley | "vegan", "plant-based", "vegan options", "gluten-free", "Berkeley" |
| 17 | The Wharf Kitchen | Seafood | $$$ | SF | "seafood", "crab", "oysters", "Fisherman's Wharf", "fresh fish" |
| 18 | Sunday Morning Café | American | $$ | SF | "brunch", "pancakes", "mimosas", "weekend breakfast", "avocado toast" |

---

## Scenario-by-Scenario Chatbot Demos

### 1. "I want Italian food, something cozy and romantic"

**Expect to surface:** Ristorante Bello ($$, romantic candlelit atmosphere), Bella Vista Rooftop ($$$, rooftop with bay views)

**Why it works:** Two Italian restaurants at different price tiers. The AI should mention ambiance keywords ("warm", "candlelit", "rooftop") extracted from the descriptions.

**Follow-up to test multi-turn:** `"What about one with outdoor seating?"` → should narrow to Bella Vista (outdoor heated patio).

---

### 2. "Cheap eats, quick lunch, under $15"

**Expect to surface:** Ramen House Natori ($, Japanese), Taqueria La Paloma ($, Mexican), Bangkok Noodles ($, Thai), Blue Plate Diner ($, American), Pho Saigon ($, Vietnamese)

**Why it works:** Five `$` restaurants with lunch-appropriate hours. The AI should filter by `price_range="$"` and surface quick-service options.

**Good follow-up:** `"I'm in the Mission"` → should weight Taqueria La Paloma, Blue Plate Diner.

---

### 3. "Romantic dinner for two, I'll splurge"

**Expect to surface:** Sakura Omakase ($$$$, intimate 12-seat counter), Café Madeleine ($$$, Bib Gourmand, prix-fixe), Casa Oaxaca ($$$, upscale Oaxacan)

**Why it works:** Highest-price-tier restaurants with romantic or fine-dining ambiance signals. Tests the AI's ability to match `$$$`–`$$$$` with "romantic" and "special occasion" context.

---

### 4. "Vegan options near Mission District / Bay Area"

**Expect to surface:** The Green Bowl (100% vegan, Berkeley), Olive Branch (vegetarian-friendly mezze), Taqueria La Paloma (vegetarian-friendly Mexican), Spice Route (12 vegetarian rotating specials)

**Why it works:** Tests dietary restriction extraction. The AI should detect "vegan" and surface plant-based or highly vegan-accommodating restaurants. The Green Bowl is the cleanest match.

**Pro tip:** This also tests the web search fallback if Tavily is configured — the AI may search for "vegan restaurants San Francisco" to supplement DB results.

---

### 5. "Best dim sum for a Sunday family brunch"

**Expect to surface:** Dragon Garden (Chinese, $$, Chinatown, Sunday hours 9am–9pm)

**Why it works:** Very specific — only Dragon Garden is Chinese with dim sum markers in its description. Tests cuisine + day-of-week + ambiance extraction.

**Good follow-up:** `"How long is the wait usually?"` → should note from reviews: "arrive before 10am, line is worth it."

---

### 6. "Something unique, I'm adventurous — surprise me"

**Expect to surface:** Sakura Omakase (18-course omakase), Casa Oaxaca (mole negro, tlayuda, mezcal), The Smokehouse (Texas BBQ in California), Bangkok Noodles (cult khao soi), Spice Route (modern Indian)

**Why it works:** No hard filter — the AI should use diverse high-rated options. Tests the AI's ability to handle open-ended "serendipitous discovery" queries. Good for demonstrating that the system returns varied recommendations, not just the top-rated Italian every time.

---

### 7. "Business lunch, professional setting, not too expensive"

**Expect to surface:** Café Madeleine (French, $$$ but set lunch possible), Olive Branch (Mediterranean, $$, patio), Seoul Kitchen (Korean, $$, lunch specials), Ramen House Natori ($, quick and serious)

**Why it works:** Tests ambiance inference ("professional", "business lunch") and price sensitivity ("not too expensive" = $–$$). Café Madeleine is the correct high-end pick; Seoul Kitchen for a relaxed but quality lunch.

---

### 8. "Korean BBQ for a group of 6"

**Expect to surface:** Seoul Kitchen (Korean BBQ, $$ SF, ventilation works, banchan spread)

**Why it works:** Only Korean BBQ in the dataset. Should trigger group-seating and social-dining signals from the description.

---

### 9. "Late-night food, I'm hungry after midnight"

**Expect to surface:** Bella Vista Rooftop (open until 1am Fri-Sat), Taqueria La Paloma (open until 10pm Fri-Sat), Pho Saigon (open until 11pm Fri-Sat)

**Why it works:** Tests time-of-day reasoning. The AI should scan hours data and surface restaurants open late. Pho Saigon is the classic late-night choice; Bella Vista for the upscale option.

---

### 10. "I want seafood by the water"

**Expect to surface:** The Wharf Kitchen (Seafood, $$$, Fisherman's Wharf, Jefferson St)

**Why it works:** Only dedicated seafood restaurant in the dataset. Location (Fisherman's Wharf) + cuisine match. Should also trigger web search if Tavily is enabled.

---

### 11. "What's trending in San Francisco right now?" (Tavily test)

**Expect:** AI triggers a Tavily web search for current SF dining trends, then blends with DB results.

**Why it works:** This query has no good static DB answer. It's specifically designed to test the web search tool call. If the AI assistant has `TavilySearchResults` configured, it should call the tool and blend live results with the seeded restaurant list.

---

### 12. "What are the hours for Ristorante Bello?"

**Expect:** AI reads the `hours` JSON field from the DB and returns a formatted schedule.

Why it works: Simple factual lookup. No web search needed. Tests that the AI grounds its answer in the DB record rather than hallucinating.

---

## Multi-Turn Conversation Templates

### Template A — Narrowing by Price and Ambiance

| Turn | User Input | Expected AI Behavior |
|---|---|---|
| 1 | "Find me a great dinner in San Francisco" | Returns 5–6 diverse options |
| 2 | "Something more romantic" | Narrows to Ristorante Bello, Bella Vista, Café Madeleine, Sakura Omakase |
| 3 | "Under $50 per person" | Removes Sakura Omakase ($$$$); surfaces Ristorante Bello, Bella Vista, Café Madeleine |
| 4 | "What about one with a view?" | Highlights Bella Vista Rooftop specifically |

### Template B — Vegetarian Focus + Group Dining

| Turn | User Input | Expected AI Behavior |
|---|---|---|
| 1 | "I need somewhere for a group of 4 with a vegetarian in the group" | Returns restaurants with good vegetarian options |
| 2 | "Mediterranean or Middle Eastern if possible" | Narrows to Olive Branch |
| 3 | "Outdoor seating?" | Confirms Olive Branch has patio with heat lamps |

### Template C — Budget Escalation

| Turn | User Input | Expected AI Behavior |
|---|---|---|
| 1 | "Cheap dinner tonight, just me" | Returns $-tier options |
| 2 | "Actually I want to celebrate — money is no object" | Re-surfaces Sakura Omakase, Casa Oaxaca, Café Madeleine |
| 3 | "Japanese cuisine specifically" | Narrows to Sakura Omakase |

---

## Notes for Graders

- **Cuisine variety**: The 18 restaurants cover 12 distinct cuisine types. The AI should never return only one cuisine type unless the user explicitly asked for it.
- **Price tier distribution**: 6 × `$`, 7 × `$$`, 4 × `$$$`, 1 × `$$$$`. A "cheap" query should reliably surface `$` options; a "splurge" query should surface `$$$`+.
- **Geographic variety**: 15 SF restaurants, 2 Oakland, 1 Berkeley. A "near me" query without location should default to SF; a location-specific query should filter correctly.
- **Hours edge case**: Sakura Omakase is Closed Mon–Tue; Bella Vista is Closed Mon–Tue; Dragon Garden is Closed Monday. Queries mentioning "Monday night" or "Tuesday lunch" should avoid these restaurants or note limited availability.
- **Claimed vs. Unclaimed**: 9 restaurants are claimed (owner linked). Scenarios testing the owner dashboard should use claimed restaurants (Ristorante Bello, Bella Vista, Dragon Garden, Sakura Omakase, Taqueria La Paloma, Casa Oaxaca, Olive Branch).
