# Lab 2 Part 3 — MongoDB Migration Guide

## Overview

This guide documents the complete migration of ForkFinder from MySQL (Lab 1) to MongoDB (Lab 2 Part 3).
The Python backend is fully migrated. This guide covers the collection design, mapping from old MySQL
tables, how sessions and bcrypt are handled, and how to run and validate the MongoDB version.

---

## 1. MySQL → MongoDB Collection Mapping

| MySQL Table (Lab 1)      | MongoDB Collection (Lab 2)   | Notes                                                                 |
|--------------------------|------------------------------|-----------------------------------------------------------------------|
| `users`                  | `users`                      | Preferences embedded as subdocument; no separate `user_preferences`  |
| `user_preferences`       | *(embedded in `users`)*      | Stored as `users.preferences: { cuisine_preferences, price_range, … }` |
| `restaurants`            | `restaurants`                | `photos` and `hours` are native arrays/dicts, not JSON strings       |
| `restaurant_claims`      | `restaurant_claims`          | Same fields; ObjectId-free (uses auto-increment int `_id`)           |
| `reviews`                | `reviews`                    | `photos` is a native array                                            |
| `favorites`              | `favorites`                  | Unchanged structure                                                   |
| `conversations`          | `conversations`              | Messages embedded as `messages: [{role, content, created_at}]`       |
| *(not in Lab 1)*         | `sessions`                   | Server-side session audit (new for Lab 2 Part 3)                     |
| *(not in Lab 1)*         | `review_events`              | Kafka audit trail written by Review Worker                           |
| *(not in Lab 1)*         | `restaurant_events`          | Kafka audit trail written by Restaurant Worker                       |
| *(not in Lab 1)*         | `counters`                   | Auto-increment sequences `{ _id: "users", seq: 42 }`                |

---

## 2. MongoDB Collection Schemas

### `users`
```json
{
  "_id": 1,
  "name": "Alice",
  "email": "alice@example.com",
  "password_hash": "$2b$12$...",
  "role": "user",
  "phone": null,
  "about_me": null,
  "city": null,
  "state": null,
  "country": null,
  "languages": null,
  "gender": null,
  "profile_photo_url": null,
  "preferences": {
    "cuisine_preferences": ["italian", "mexican"],
    "price_range": "$$",
    "search_radius": 10,
    "preferred_locations": [],
    "dietary_restrictions": [],
    "ambiance_preferences": ["casual"],
    "sort_preference": "rating",
    "updated_at": "2026-04-15T00:00:00Z"
  },
  "created_at": "2026-04-15T00:00:00Z",
  "updated_at": "2026-04-15T00:00:00Z"
}
```

### `sessions`
```json
{
  "_id": "<ObjectId>",
  "user_id": 1,
  "jti": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-15T10:00:00Z",
  "expires_at": "2026-05-15T10:00:00Z"
}
```
A TTL index on `expires_at` (expireAfterSeconds=0) automatically removes expired session documents.

### `restaurants`
```json
{
  "_id": 1,
  "name": "Trattoria Roma",
  "description": "Authentic Italian",
  "cuisine_type": "Italian",
  "price_range": "$$",
  "address": "123 Main St",
  "city": "San Jose",
  "state": "CA",
  "country": "US",
  "zip_code": "95112",
  "phone": "408-555-0100",
  "website": "https://trattoria.example.com",
  "hours": { "mon": "11am-9pm", "tue": "11am-9pm" },
  "photos": ["/uploads/restaurants/abc.jpg"],
  "avg_rating": 4.5,
  "review_count": 12,
  "is_claimed": false,
  "created_by": 2,
  "claimed_by": null,
  "latitude": 37.3382,
  "longitude": -121.8863,
  "created_at": "2026-04-15T00:00:00Z",
  "updated_at": "2026-04-15T00:00:00Z"
}
```

### `reviews`
```json
{
  "_id": 1,
  "user_id": 1,
  "restaurant_id": 1,
  "rating": 5,
  "comment": "Amazing food and atmosphere!",
  "photos": [],
  "created_at": "2026-04-15T00:00:00Z",
  "updated_at": "2026-04-15T00:00:00Z"
}
```

### `favorites`
```json
{
  "_id": 1,
  "user_id": 1,
  "restaurant_id": 1,
  "created_at": "2026-04-15T00:00:00Z"
}
```

### `review_events` (Kafka audit — written by Review Worker)
```json
{
  "_id": "<ObjectId>",
  "event_id": "uuid-v4",
  "event_type": "review.created",
  "review_id": 1,
  "restaurant_id": 1,
  "user_id": 1,
  "payload": "{…full Kafka envelope JSON…}",
  "processed_at": "2026-04-15T10:01:00Z"
}
```

### `restaurant_events` (Kafka audit — written by Restaurant Worker)
```json
{
  "_id": "<ObjectId>",
  "event_id": "uuid-v4",
  "event_type": "restaurant.created",
  "restaurant_id": 1,
  "actor_user_id": 2,
  "payload": "{…full Kafka envelope JSON…}",
  "processed_at": "2026-04-15T10:01:00Z"
}
```

---

## 3. Security — bcrypt and Sessions

### Passwords (bcrypt preserved)
- `passlib[bcrypt]` is used via `CryptContext(schemes=["bcrypt"])`.
- `hash_password()` and `verify_password()` in `backend/app/utils/auth.py` are unchanged.
- Passwords are never stored in plaintext. Only `password_hash` (bcrypt digest) is stored in `users`.

### Sessions stored in MongoDB
- On every successful login or signup, `auth.py:_create_session()` inserts a document into the
  `sessions` collection with `user_id`, a UUID `jti`, `created_at`, and `expires_at`.
- A MongoDB TTL index (`expireAfterSeconds=0`) on `expires_at` auto-deletes expired sessions.
- The JWT token remains the live auth mechanism; sessions serve as a server-side audit trail as
  required by Lab 2 Part 3.

---

## 4. Indexes Created at Startup

`database.py:init_indexes()` runs on every startup (idempotent):

| Collection         | Index                                         | Type    |
|--------------------|-----------------------------------------------|---------|
| `users`            | `email`                                       | Unique  |
| `restaurants`      | `name`, `cuisine_type`, `city`, `avg_rating`  | Normal  |
| `reviews`          | `(restaurant_id, user_id)` composite          | Unique  |
| `reviews`          | `restaurant_id`, `user_id`                    | Normal  |
| `favorites`        | `(user_id, restaurant_id)` composite          | Unique  |
| `sessions`         | `user_id`, `jti`, `expires_at`                | TTL     |
| `review_events`    | `event_id`                                    | Normal  |
| `restaurant_events`| `event_id`                                    | Normal  |

---

## 5. Files Changed

| File                                        | Change                                                        |
|---------------------------------------------|---------------------------------------------------------------|
| `backend/app/config.py`                     | `MONGODB_URL` + `MONGODB_DB_NAME` replace `DATABASE_URL`     |
| `backend/app/database.py`                   | Full pymongo layer; `init_indexes()`, `MongoDoc`, `_ns()`    |
| `backend/app/models/*.py`                   | All SQLAlchemy ORM classes replaced with type-hint stubs      |
| `backend/app/utils/auth.py`                 | pymongo user lookup; bcrypt unchanged                         |
| `backend/app/routers/auth.py`               | `_create_session()` writes to MongoDB `sessions` collection  |
| `backend/app/routers/restaurants.py`        | pymongo CRUD                                                  |
| `backend/app/routers/reviews.py`            | pymongo CRUD via review_service                               |
| `backend/app/routers/favorites.py`          | pymongo CRUD via favorites_service                            |
| `backend/app/routers/history.py`            | pymongo queries via history_service                           |
| `backend/app/routers/owner.py`              | pymongo queries via owner_service                             |
| `backend/app/routers/preferences.py`        | pymongo `$set` on embedded subdocument                        |
| `backend/app/services/*.py`                 | All services converted to pymongo                             |
| `backend/workers/review_worker.py`          | SQLAlchemy replaced with pymongo `insert_one`                 |
| `backend/workers/restaurant_worker.py`      | SQLAlchemy replaced with pymongo `insert_one`                 |
| `backend/requirements.txt`                  | `pymongo[srv]` present; SQLAlchemy/PyMySQL removed           |
| `docker-compose.yml`                        | `mysql` service → `mongo:7.0`; `DATABASE_URL` → `MONGODB_URL`|

---

## 6. Step-by-Step: Run the MongoDB Version

### Prerequisites
- Docker and Docker Compose installed
- Ports 27017, 8000, 9092, 9093, 80 free

### Step 1 — Copy env file
```bash
cp .env.docker.example .env.docker
# No changes needed — defaults point to MongoDB at mongodb:27017
```

### Step 2 — Build and start all services
```bash
docker compose --env-file .env.docker up --build
```

This starts: `mongodb`, `zookeeper`, `kafka`, `backend`, `review-worker`, `restaurant-worker`, `frontend`.

### Step 3 — Verify MongoDB is running
```bash
docker exec -it forkfinder-mongodb mongosh --eval "db.adminCommand('ping')"
# Expected: { ok: 1 }
```

### Step 4 — Verify backend is healthy
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

### Step 5 — Register a user (creates session in MongoDB)
```bash
curl -X POST http://localhost:8000/auth/user/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'
```

### Step 6 — Inspect sessions collection
```bash
docker exec -it forkfinder-mongodb mongosh restaurant_platform \
  --eval "db.sessions.find().pretty()"
# Should show one session document with user_id, jti, created_at, expires_at
```

### Step 7 — Inspect users (confirm bcrypt hash)
```bash
docker exec -it forkfinder-mongodb mongosh restaurant_platform \
  --eval "db.users.findOne({},{password_hash:1,email:1})"
# password_hash should start with $2b$12$ (bcrypt)
```

### Step 8 — Create a restaurant and check review_events
```bash
# Login first to get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}' | jq -r .access_token)

# Create restaurant
curl -X POST http://localhost:8000/restaurants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Place","cuisine_type":"Italian","address":"1 Main St","city":"San Jose","state":"CA","country":"US"}'

# Verify Kafka event was consumed and written to MongoDB
docker exec -it forkfinder-mongodb mongosh restaurant_platform \
  --eval "db.restaurant_events.find().pretty()"
```

### Step 9 — (Optional) Run without Kafka
```bash
docker compose --env-file .env.docker up mongodb backend frontend
```
The backend works fully without Kafka — event publishing is skipped silently.

---

## 7. Screenshots to Capture for Report

1. `docker compose up` terminal output showing all services healthy
2. `db.adminCommand('ping')` output in mongosh
3. `db.users.findOne()` showing `password_hash` starting with `$2b$` (bcrypt)
4. `db.sessions.find().pretty()` showing at least one session with `expires_at`
5. `db.restaurants.find().pretty()` and `db.reviews.find().pretty()` after test data
6. `db.review_events.find().pretty()` showing Kafka consumer wrote audit records
7. `db.restaurant_events.find().pretty()` showing restaurant Kafka audit records
8. Swagger UI at `http://localhost:8000/docs` with a successful authenticated request

---

## 8. Validation Checklist

- [ ] `db.users` contains documents with `password_hash` starting with `$2b$` (bcrypt)
- [ ] `db.sessions` contains a document for every login/signup with `expires_at` set
- [ ] TTL index exists: `db.sessions.getIndexes()` shows `expires_at` with `expireAfterSeconds: 0`
- [ ] `db.restaurants`, `db.reviews`, `db.favorites` contain expected data
- [ ] `db.review_events` grows after review create/update/delete actions
- [ ] `db.restaurant_events` grows after restaurant create/update/claim actions
- [ ] `db.users.preferences` subdocument exists and is updated via `PUT /preferences/me`
- [ ] No `mysql` or `DATABASE_URL` references remain in any running service

---

## 9. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ServerSelectionTimeoutError` | MongoDB container not ready yet; wait for healthcheck to pass |
| `duplicate key error` on `email` | Email already registered; use a different one |
| Workers not writing to `review_events` | Ensure Kafka is healthy: `docker compose logs kafka` |
| Sessions not expiring | TTL index runs every 60 s; check `db.sessions.getIndexes()` |
