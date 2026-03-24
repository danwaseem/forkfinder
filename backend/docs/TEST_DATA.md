# ForkFinder — Example Test Data

Use this data to seed the database for manual testing, demo runs, and grading.

---

## Demo Accounts

| Role | Name | Email | Password | Notes |
|---|---|---|---|---|
| Reviewer | Jane Doe | `user@demo.com` | `password` | Has reviews, favorites, preferences set |
| Reviewer 2 | Bob Smith | `bob@demo.com` | `password` | Has a few reviews |
| Owner | Mario Rossi | `owner@demo.com` | `password` | Owns Ristorante Bello and Bella Vista |
| Owner 2 | Mei Chen | `mei@demo.com` | `password` | Owns Dragon Garden |

---

## Restaurants

### 1. Ristorante Bello (Claimed)

```json
{
  "name": "Ristorante Bello",
  "description": "Authentic Neapolitan pizza and handmade pasta in a warm, candlelit setting. Family recipes passed down for three generations.",
  "cuisine_type": "Italian",
  "price_range": "$$",
  "address": "123 Columbus Ave",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94133",
  "phone": "+1 (415) 555-0101",
  "website": "https://ristorantebello.example.com",
  "latitude": 37.7991,
  "longitude": -122.4076,
  "hours": {
    "monday": "11:30am – 10:00pm",
    "tuesday": "11:30am – 10:00pm",
    "wednesday": "11:30am – 10:00pm",
    "thursday": "11:30am – 10:00pm",
    "friday": "11:30am – 11:00pm",
    "saturday": "10:00am – 11:00pm",
    "sunday": "10:00am – 9:00pm"
  }
}
```

### 2. Dragon Garden (Claimed)

```json
{
  "name": "Dragon Garden",
  "description": "Modern dim sum and traditional Cantonese cuisine. Steamer baskets crafted fresh every morning.",
  "cuisine_type": "Chinese",
  "price_range": "$$",
  "address": "456 Stockton St",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94108",
  "phone": "+1 (415) 555-0202",
  "website": "https://dragongarden.example.com",
  "latitude": 37.7955,
  "longitude": -122.4066,
  "hours": {
    "monday": "Closed",
    "tuesday": "10:00am – 9:00pm",
    "wednesday": "10:00am – 9:00pm",
    "thursday": "10:00am – 9:00pm",
    "friday": "10:00am – 10:00pm",
    "saturday": "9:00am – 10:00pm",
    "sunday": "9:00am – 9:00pm"
  }
}
```

### 3. Spice Route (Unclaimed)

```json
{
  "name": "Spice Route",
  "description": "Northern Indian cuisine with a modern California twist. Known for the lamb rogan josh and the garlic naan.",
  "cuisine_type": "Indian",
  "price_range": "$$$",
  "address": "789 Valencia St",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94110",
  "phone": "+1 (415) 555-0303",
  "hours": {
    "monday": "5:00pm – 10:00pm",
    "tuesday": "5:00pm – 10:00pm",
    "wednesday": "5:00pm – 10:00pm",
    "thursday": "5:00pm – 10:00pm",
    "friday": "5:00pm – 11:00pm",
    "saturday": "12:00pm – 11:00pm",
    "sunday": "12:00pm – 9:00pm"
  }
}
```

### 4. Taqueria La Paloma (Unclaimed)

```json
{
  "name": "Taqueria La Paloma",
  "description": "Family-owned Mexican taqueria serving handmade tortillas, slow-braised carnitas, and fresh salsas since 2001.",
  "cuisine_type": "Mexican",
  "price_range": "$",
  "address": "321 Mission St",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94105",
  "phone": "+1 (415) 555-0404",
  "hours": {
    "monday": "8:00am – 9:00pm",
    "tuesday": "8:00am – 9:00pm",
    "wednesday": "8:00am – 9:00pm",
    "thursday": "8:00am – 9:00pm",
    "friday": "8:00am – 10:00pm",
    "saturday": "8:00am – 10:00pm",
    "sunday": "9:00am – 8:00pm"
  }
}
```

### 5. Sakura Omakase (Claimed)

```json
{
  "name": "Sakura Omakase",
  "description": "Intimate 12-seat omakase experience. Chef's seasonal selection of Edomae sushi, 18 courses.",
  "cuisine_type": "Japanese",
  "price_range": "$$$$",
  "address": "50 Belden Pl",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94104",
  "phone": "+1 (415) 555-0505",
  "website": "https://sakuraomakase.example.com",
  "hours": {
    "monday": "Closed",
    "tuesday": "Closed",
    "wednesday": "6:00pm – 10:00pm",
    "thursday": "6:00pm – 10:00pm",
    "friday": "6:00pm – 11:00pm",
    "saturday": "5:30pm – 11:00pm",
    "sunday": "5:30pm – 9:00pm"
  }
}
```

### 6. Bella Vista Rooftop (Claimed — Out of Hours)

```json
{
  "name": "Bella Vista Rooftop",
  "description": "Rooftop bar and Italian-American kitchen with panoramic bay views. Known for sunset cocktails and wood-fired flatbreads.",
  "cuisine_type": "Italian",
  "price_range": "$$$",
  "address": "200 Powell St",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94102",
  "phone": "+1 (415) 555-0606",
  "website": "https://bellavista.example.com",
  "hours": {
    "monday": "Closed",
    "tuesday": "Closed",
    "wednesday": "4:00pm – 12:00am",
    "thursday": "4:00pm – 12:00am",
    "friday": "3:00pm – 1:00am",
    "saturday": "2:00pm – 1:00am",
    "sunday": "2:00pm – 10:00pm"
  }
}
```

---

## Reviews

### Reviews for Ristorante Bello

```json
[
  {
    "restaurant_id": 1,
    "rating": 5,
    "comment": "Best pasta I've had outside of Naples. The carbonara is silky smooth and the portions are generous. Will definitely come back!",
    "author": "Jane Doe"
  },
  {
    "restaurant_id": 1,
    "rating": 4,
    "comment": "Lovely atmosphere and excellent food. The tiramisu was a highlight. Service was a bit slow on Friday night but understandable given how packed it was.",
    "author": "Bob Smith"
  },
  {
    "restaurant_id": 1,
    "rating": 5,
    "comment": "Authentic Italian experience. The wine list is excellent and reasonably priced. Highly recommend the bruschetta starter.",
    "author": "Sample User 3"
  }
]
```

### Reviews for Dragon Garden

```json
[
  {
    "restaurant_id": 2,
    "rating": 5,
    "comment": "The best dim sum in San Francisco, hands down. Get there early on weekends — the shrimp dumplings and turnip cake sell out fast.",
    "author": "Jane Doe"
  },
  {
    "restaurant_id": 2,
    "rating": 3,
    "comment": "Food is good but the wait times are unreasonable. Two hours on a Saturday morning. The har gow was worth it though.",
    "author": "Sample User 4"
  }
]
```

### Reviews for Spice Route

```json
[
  {
    "restaurant_id": 3,
    "rating": 5,
    "comment": "Exceptional Indian cuisine. The lamb rogan josh is unlike anything I've had — rich, complex, perfectly spiced. The mango lassi is refreshing.",
    "author": "Bob Smith"
  },
  {
    "restaurant_id": 3,
    "rating": 4,
    "comment": "Great vegetarian options! The paneer makhani and dal makhani are both stellar. Definitely not the cheapest option but worth the splurge.",
    "author": "Sample User 5"
  }
]
```

### Reviews for Taqueria La Paloma

```json
[
  {
    "restaurant_id": 4,
    "rating": 5,
    "comment": "Best breakfast burrito in the Mission. The carnitas are slow-braised and impossibly tender. Cash only but there's an ATM next door.",
    "author": "Jane Doe"
  },
  {
    "restaurant_id": 4,
    "rating": 4,
    "comment": "Authentic and delicious. The fresh salsas are the real deal — the green tomatillo is my favorite. Lines can be long but move quickly.",
    "author": "Sample User 6"
  },
  {
    "restaurant_id": 4,
    "rating": 5,
    "comment": "I've been coming here for 10 years. Prices are fair, quality never drops. The al pastor tacos are a must-order.",
    "author": "Bob Smith"
  }
]
```

---

## User Preferences (Jane Doe — `user@demo.com`)

```json
{
  "cuisine_preferences": ["Italian", "Japanese", "Indian", "Mexican"],
  "price_range": "$$",
  "search_radius": 15,
  "preferred_locations": ["San Francisco", "Oakland"],
  "dietary_restrictions": [],
  "ambiance_preferences": ["Casual", "Romantic", "Outdoor Seating"],
  "sort_preference": "rating"
}
```

---

## AI Chatbot Test Prompts

Use these to verify the AI assistant during demo:

| # | Prompt | Expected behavior |
|---|---|---|
| 1 | "I want Italian food in San Francisco" | Returns Italian restaurants |
| 2 | "Cheap eats under $15, quick lunch" | Returns $ price restaurants |
| 3 | "Romantic dinner for two, I'll splurge" | Returns $$$ or $$$$ with romantic ambiance |
| 4 | "Vegan options near Mission District" | Returns vegan-friendly, SF results |
| 5 | "Best dim sum for a Sunday family brunch" | Returns Chinese, Family-Friendly |
| 6 | "Something unique, I'm adventurous" | Returns diverse recommendations |
| 7 | "What are the hours for Ristorante Bello?" | May trigger web search or use DB |
| 8 | "What's trending in SF right now?" | Triggers Tavily web search |

---

## Edge Case Inputs for Validation Testing

### Boundary inputs for reviews

| Field | Valid boundary | Invalid boundary |
|---|---|---|
| `rating` | 1 (min), 5 (max) | 0, 6, 1.5, "five" |
| `comment` | 10 chars (min), 5000 chars (max) | 9 chars, 5001 chars |

### Boundary inputs for restaurants

| Field | Valid boundary | Invalid boundary |
|---|---|---|
| `name` | 1 char, 255 chars | 0 chars (empty), 256 chars |
| `price_range` | "$", "$$", "$$$", "$$$$" | "$$$$$", "cheap", "" |
| `website` | "https://foo.com" | "foo.com" (no scheme) |
| `latitude` | -90.0, 90.0 | -91.0, 91.0 |
| `longitude` | -180.0, 180.0 | -181.0, 181.0 |
| `hours` keys | "monday"–"sunday", "weekdays", "weekends", "everyday" | "funday", "mon", "MONDAY" |

### Boundary inputs for auth

| Field | Valid boundary | Invalid boundary |
|---|---|---|
| `password` | 8 chars (min) | 7 chars |
| `name` | 2 chars (min), 100 chars (max) | 1 char, 101 chars |
| `email` | valid RFC 5322 format | "notanemail", "@nodomain.com" |

### File upload edge cases

| Case | File | Expected |
|---|---|---|
| Valid JPEG | `photo.jpg` | 200, URL returned |
| Valid PNG with transparency | `icon.png` | 200, saved as PNG |
| Valid WEBP | `image.webp` | 200 |
| PDF disguised as image | `resume.pdf` renamed to `.jpg` | 400 (Pillow verify fails) |
| Oversized image (2500x2500) | Large JPEG | 200 (downsampled to 1920px) |
| Empty file (0 bytes) | `empty.jpg` | 400 |
| File exactly 5 MB | `5mb.jpg` | 200 |
| File 5 MB + 1 byte | `5mb_plus.jpg` | 400 |
| 11th restaurant photo | Any image | 400 (max 10) |
| 6th review photo | Any image | 400 (max 5) |
