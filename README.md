# ForkFinder — Restaurant Discovery Platform

**Course:** DATA 236 Distributed Systems — Lab 1
**Group:** 7
**Members:** Danish Waseem (19101511), Saketh (019160999)

---

## Overview

ForkFinder is a full-stack Yelp-style restaurant discovery and review platform. It supports two user roles — **reviewers** who discover, rate, and favorite restaurants, and **restaurant owners** who manage listings and view analytics. An embedded AI assistant (powered by Ollama) provides natural-language dining recommendations.

---

## Features

| Area | Highlights |
|---|---|
| Auth | Separate signup/login for reviewers and owners; JWT-based sessions |
| Discovery | Full-text search + filters: cuisine, city, price range, minimum rating, sort |
| Reviews | Create, edit, delete; star rating (1–5), comment, photo upload |
| Favorites | Heart-toggle any restaurant; view saved list |
| Profile | Edit name, bio, photo; set dining preferences |
| Owner dashboard | Aggregate stats, 6-month review trend, sentiment keywords, listing management |
| AI assistant | Natural-language queries, multi-turn conversation, personalized to saved preferences |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Axios, React Router v6 |
| Backend | FastAPI, SQLAlchemy 2.0, Pydantic v2, Uvicorn |
| Database | MySQL 8.0+ |
| Auth | python-jose (JWT), passlib (bcrypt) |
| AI | LangChain + Ollama, Tavily web search |
| File uploads | Pillow (image validation + resize) |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+ (running)
- Ollama (optional — only required for AI assistant)

```bash
# Optional: pull the AI model
ollama pull llama3.2
```

### Database

```sql
CREATE DATABASE restaurant_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Tables are created automatically on first backend start.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in your values
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

`backend/.env`:

| Variable | Example | Notes |
|---|---|---|
| `DATABASE_URL` | `mysql+pymysql://root:pass@localhost:3306/restaurant_platform` | Full SQLAlchemy connection string |
| `SECRET_KEY` | `a-random-string-32-chars-min` | JWT signing secret |
| `ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | 30 days |
| `UPLOAD_DIR` | `uploads` | Relative path for uploaded files |
| `FRONTEND_URL` | `http://localhost:5173` | CORS allowed origin |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Optional — omit to disable AI |
| `OLLAMA_MODEL` | `llama3.2` | Optional |
| `TAVILY_API_KEY` | `tvly-xxxx` | Optional — omit to disable web search |

`frontend/.env`:

| Variable | Example |
|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` |

```bash
cd frontend
cp .env.example .env
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Running Locally

Start these in separate terminals:

```bash
# Terminal 1 — MySQL (if not running as a service)
mysql.server start

# Terminal 2 — Ollama (optional)
ollama serve

# Terminal 3 — Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 4 — Frontend
cd frontend && npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## Seed Data

```bash
cd backend
source venv/bin/activate

python seed_data.py          # safe first-run: inserts only if users table is empty
python seed_data.py --wipe   # full reseed: wipes all data then re-inserts
python seed_data.py --recalc # resync stored avg_rating/review_count without wiping
```

| Entity | Count |
|---|---|
| Users | 8 (5 reviewers + 3 owners) |
| Restaurants | 90 (SF + South Bay focus) |
| Reviews | 75 |
| Favorites | 42 |

---

## API Documentation

Swagger UI is available at **http://localhost:8000/docs** after starting the backend.

To test protected routes in Swagger:
1. Call `POST /auth/user/login` or `POST /auth/owner/login`
2. Copy `access_token` from the response
3. Click **Authorize**, enter `Bearer <token>`, click **Authorize**

A Postman collection (43 requests) is at `backend/docs/postman_collection.json`.

---

## Demo Credentials

All accounts use password: **`password`**

| Role | Email | Notes |
|---|---|---|
| Reviewer | `user@demo.com` | Reviews, favorites, preferences — primary demo account |
| Reviewer | `marcus@demo.com` | Oakland focus |
| Reviewer | `priya@demo.com` | Vegetarian preferences |
| Reviewer | `alex@demo.com` | Fine dining focus |
| Reviewer | `emily@demo.com` | Dim sum / Asian cuisine focus |
| Owner | `owner@demo.com` | Owns Ristorante Bello + Bella Vista Rooftop |
| Owner | `wei@demo.com` | Owns Dragon Garden + Sakura Omakase |
| Owner | `sofia@demo.com` | Owns Taqueria La Paloma + 2 others |

See `backend/docs/DEMO_SCENARIOS.md` for 20 step-by-step graded demo scenarios.

---

## Running Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

120 tests across 5 modules.

| File | Tests |
|---|---|
| `test_auth.py` | 25 |
| `test_restaurants.py` | 32 |
| `test_reviews.py` | 29 |
| `test_favorites.py` | 17 |
| `test_owner.py` | 17 |

---


## Notes

- **`.env` files are git-ignored** — never commit them; use `.env.example` as the template.
- **Ollama is optional** — if not running, the `/ai/chat` endpoint returns a graceful fallback response using rule-based search results.
- **Stale ratings** — if `avg_rating` or `review_count` looks wrong after seeding or testing, run `python seed_data.py --recalc` to resync all stored aggregates from the reviews table without deleting any data.
- **Tables are auto-created** — no migration scripts needed; `Base.metadata.create_all()` runs on startup.
- **Demo walkthrough** — `backend/docs/DEMO_SCENARIOS.md` contains 20 graded scenarios with step-by-step instructions.
