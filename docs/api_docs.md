# ForkFinder API Documentation

Base URL: `http://localhost:8000`
Interactive Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

All protected endpoints require:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Authentication

### POST /auth/register
Register a new user or owner.

**Request body:**
```json
{
  "name": "Alice Chen",
  "email": "alice@example.com",
  "password": "password123",
  "role": "user"   // "user" | "owner"
}
```

**Response 201:**
```json
{
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user_id": 1,
  "name": "Alice Chen",
  "email": "alice@example.com",
  "role": "user"
}
```

---

### POST /auth/login
Authenticate and receive JWT.

**Request body:**
```json
{ "email": "alice@example.com", "password": "password123" }
```

**Response 200:** Same structure as register.

---

### GET /auth/me
Validate current token.
**Protected** ✓

---

## Users

### GET /users/me
Get authenticated user's full profile.
**Protected** ✓

**Response 200:**
```json
{
  "id": 1, "name": "Alice Chen", "email": "alice@example.com",
  "role": "user", "phone": "+1-415-555-0101",
  "about_me": "...", "city": "San Francisco", "state": "CA",
  "country": "United States", "languages": "English, Mandarin",
  "gender": "female", "profile_photo_url": "/uploads/profiles/abc123.jpg",
  "created_at": "2024-01-15T10:00:00"
}
```

---

### PUT /users/me
Update profile fields (partial update supported).
**Protected** ✓

**Request body (all optional):**
```json
{
  "name": "Alice Chen", "email": "new@example.com",
  "phone": "+1-415-555-0101", "about_me": "Food explorer",
  "city": "San Francisco", "state": "CA", "country": "United States",
  "languages": "English, Mandarin", "gender": "female"
}
```

---

### POST /users/me/photo
Upload profile photo. `multipart/form-data`.
**Protected** ✓
**Form field:** `file` (JPEG/PNG/GIF/WEBP, max 5MB)

**Response 200:**
```json
{ "profile_photo_url": "/uploads/profiles/abc123.jpg" }
```

---

### GET /users/me/preferences
Get user dining preferences.
**Protected** ✓

**Response 200:**
```json
{
  "cuisine_preferences": ["Italian", "Japanese"],
  "price_range": "$$",
  "search_radius": 15,
  "dietary_restrictions": ["Gluten-Free"],
  "ambiance_preferences": ["Casual", "Romantic"],
  "sort_preference": "rating"
}
```

---

### PUT /users/me/preferences
Update dining preferences.
**Protected** ✓
**Request body:** Same structure as GET response.

---

### GET /users/me/favorites
Get list of favorited restaurants.
**Protected** ✓

---

### GET /users/me/history
Get user's review history and restaurants they added.
**Protected** ✓

**Response 200:**
```json
{
  "reviews": [
    {
      "id": 1, "restaurant_id": 3, "restaurant_name": "Sakura Sushi",
      "rating": 5, "comment": "...", "created_at": "..."
    }
  ],
  "restaurants_added": [...]
}
```

---

## Restaurants

### GET /restaurants
Search and filter restaurants.
**Public** (no auth required)

**Query parameters:**

| Parameter   | Type   | Description                        |
|-------------|--------|------------------------------------|
| q           | string | Search name, cuisine, description  |
| cuisine     | string | Filter by cuisine type             |
| city        | string | Filter by city                     |
| price_range | string | "$" \| "$$" \| "$$$" \| "$$$$"   |
| rating_min  | float  | Minimum average rating (0–5)       |
| page        | int    | Page number (default: 1)           |
| limit       | int    | Results per page (default: 12)     |

**Response 200:**
```json
{
  "items": [ { ...restaurant } ],
  "total": 42,
  "page": 1,
  "limit": 12,
  "pages": 4
}
```

---

### GET /restaurants/{id}
Get restaurant details.
**Public**

---

### POST /restaurants
Create a new restaurant listing.
**Protected** ✓

**Request body:**
```json
{
  "name": "Pizza Palace",
  "description": "Authentic Neapolitan pizza...",
  "cuisine_type": "Italian",
  "price_range": "$$",
  "address": "1234 Market St",
  "city": "San Francisco",
  "state": "CA",
  "country": "United States",
  "zip_code": "94103",
  "phone": "+1-415-555-1001",
  "website": "https://pizzapalace.com",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "hours": {
    "monday": "11am-10pm",
    "friday": "11am-11pm"
  }
}
```

---

### PUT /restaurants/{id}
Update restaurant. Only creator or claimed owner.
**Protected** ✓
**Request body:** All fields optional (same as POST).

---

### DELETE /restaurants/{id}
Delete restaurant. Only creator or claimed owner.
**Protected** ✓
**Response 204 No Content**

---

### POST /restaurants/{id}/photos
Upload a restaurant photo. `multipart/form-data`.
**Protected** ✓
**Form field:** `file`

---

### POST /restaurants/{id}/claim
Claim a restaurant listing (owners only).
**Protected** ✓ **Owner role required**

---

## Reviews

### GET /restaurants/{id}/reviews
Get all reviews for a restaurant.
**Public**

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "restaurant_id": 3,
      "rating": 5,
      "comment": "Best sushi in SF!",
      "photos": ["/uploads/reviews/photo.jpg"],
      "created_at": "2024-01-15T10:00:00",
      "updated_at": "2024-01-15T10:00:00",
      "user": {
        "id": 1,
        "name": "Alice Chen",
        "profile_photo_url": null
      }
    }
  ],
  "total": 12
}
```

---

### POST /restaurants/{id}/reviews
Create a review (one per user per restaurant).
**Protected** ✓

**Request body:**
```json
{ "rating": 5, "comment": "Absolutely amazing food!" }
```

---

### PUT /reviews/{id}
Edit own review.
**Protected** ✓

**Request body (all optional):**
```json
{ "rating": 4, "comment": "Updated my review..." }
```

---

### DELETE /reviews/{id}
Delete own review.
**Protected** ✓
**Response 204 No Content**

---

### POST /reviews/{id}/photos
Upload photo to a review. `multipart/form-data`.
**Protected** ✓

---

## Favorites

### POST /favorites/{restaurant_id}
Add restaurant to favorites.
**Protected** ✓
**Response 201:**
```json
{ "message": "Added to favorites" }
```

---

### DELETE /favorites/{restaurant_id}
Remove from favorites.
**Protected** ✓
**Response 204 No Content**

---

## Owner Dashboard

### GET /owner/restaurants
List all restaurants owned or created by the current user.
**Protected** ✓ **Owner role required**

---

### GET /owner/restaurants/{id}/stats
Get analytics for a specific restaurant.
**Protected** ✓ **Owner role required**

**Response 200:**
```json
{
  "restaurant": { "id": 1, "name": "Pizza Palace", "avg_rating": 4.8, "review_count": 47 },
  "rating_distribution": { "1": 0, "2": 1, "3": 3, "4": 12, "5": 31 },
  "monthly_trend": [
    { "month": "Sep 2024", "count": 8 },
    { "month": "Oct 2024", "count": 11 }
  ],
  "recent_reviews": [ { "id": 1, "rating": 5, "comment": "...", "user_name": "Alice Chen", "created_at": "..." } ]
}
```

---

### GET /owner/reviews
Get all reviews across all owned restaurants.
**Protected** ✓ **Owner role required**

---

## AI Assistant

### POST /ai-assistant/chat
Chat with the AI dining guide.
**Protected** ✓

**Request body:**
```json
{
  "message": "Find me a romantic Italian restaurant in San Francisco under $50",
  "conversation_history": [
    { "role": "user", "content": "Previous message..." },
    { "role": "assistant", "content": "Previous response..." }
  ]
}
```

**Response 200:**
```json
{
  "response": "Here are some romantic Italian options in San Francisco that fit your budget...",
  "restaurants": [
    {
      "id": 1,
      "name": "Pizza Palace",
      "cuisine": "Italian",
      "price_range": "$$",
      "city": "San Francisco",
      "avg_rating": 4.8,
      "review_count": 47,
      "description": "Authentic Neapolitan pizza..."
    }
  ],
  "web_results": "Optional Tavily search results for current info..."
}
```

**AI features:**
- Loads user's dining preferences on first query
- Extracts filters: cuisine, price, city, dietary restrictions, occasion, ambiance
- Searches restaurant database with extracted filters
- Ranks results using query + user preferences
- Supports follow-up questions and conversation history
- Uses Tavily web search for current hours, events, trending spots
- Graceful fallback when OpenAI/Tavily keys not configured

---

## Error Responses

All errors follow this format:
```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning                        |
|--------|--------------------------------|
| 400    | Bad request / validation error |
| 401    | Unauthorized (no/invalid token)|
| 403    | Forbidden (wrong role/owner)   |
| 404    | Resource not found             |
| 422    | Unprocessable entity (Pydantic)|
| 500    | Internal server error          |
