# ForkFinder — Restaurant Discovery Platform

**Course:** DATA 236 Distributed Systems — Lab 1 & Lab 2  
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
| Frontend | React 18, Vite, Tailwind CSS, Axios, React Router v6, Redux Toolkit |
| Backend | FastAPI, PyMongo, Pydantic v2, Uvicorn |
| Database | MongoDB 7.0 |
| Messaging | Apache Kafka 3.3 (Zookeeper mode) |
| Auth | python-jose (JWT), passlib (bcrypt) |
| AI | LangChain + Ollama, Tavily web search |
| File uploads | Pillow (image validation + resize) |
| Containers | Docker, Docker Compose |
| Orchestration | Kubernetes (EKS on AWS) |

---

## Lab 2 — Docker, Kubernetes, Kafka, MongoDB, Redux, JMeter

### Quickstart with Docker Compose (recommended for local dev)

```bash
cp .env.docker.example .env.docker
# Edit .env.docker if needed — defaults work out of the box

docker compose --env-file .env.docker up --build
```

Services started:

| Service | URL |
|---|---|
| Frontend | http://localhost:80 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| MongoDB | localhost:27017 |
| Kafka | localhost:9093 (external), kafka:9092 (internal) |

To run without Kafka (lighter):

```bash
docker compose --env-file .env.docker up mongodb backend frontend
```

---

### Kubernetes Deployment (AWS EKS)

See **`LAB2_AWS_K8S_DEPLOYMENT_GUIDE.md`** for the full step-by-step guide.

Quick reference — after building and pushing ECR images:

```bash
# Apply all manifests in order
kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/01-configmap.yaml
kubectl apply -f kubernetes/02-secrets.yaml      # copy from 02-secrets.yaml.example first
kubectl apply -f kubernetes/03-mongodb.yaml
kubectl apply -f kubernetes/04-user-service.yaml
kubectl apply -f kubernetes/05-owner-service.yaml
kubectl apply -f kubernetes/06-restaurant-service.yaml
kubectl apply -f kubernetes/07-review-service.yaml
kubectl apply -f kubernetes/08-frontend.yaml
kubectl apply -f kubernetes/09-ingress.yaml
kubectl apply -f kubernetes/10-kafka.yaml
kubectl apply -f kubernetes/11-review-worker.yaml
kubectl apply -f kubernetes/12-restaurant-worker.yaml

# Verify all pods are Running
kubectl get pods -n forkfinder
```

---

### Kafka Integration

The backend publishes events to Kafka on every review/restaurant write. Two worker services consume those events and write audit logs to MongoDB.

| Topic | Producer | Consumer |
|---|---|---|
| `review.created` | Review API | Review Worker |
| `review.updated` | Review API | Review Worker |
| `review.deleted` | Review API | Review Worker |
| `restaurant.created` | Restaurant API | Restaurant Worker |
| `restaurant.updated` | Restaurant API | Restaurant Worker |
| `restaurant.claimed` | Restaurant API | Restaurant Worker |

See **`LAB2_KAFKA_DEPLOYMENT_GUIDE.md`** for the deployment guide and message flow diagram.  
See **`LAB2_ARCHITECTURE_DIAGRAM.md`** for the producer → Kafka → consumer architecture diagram.

---

### MongoDB

All data (users, sessions, restaurants, reviews, favorites, conversations, event logs) is stored in MongoDB 7.0. Sessions use a TTL index for automatic expiry. Passwords are bcrypt-hashed.

See **`LAB2_MONGODB_MIGRATION_GUIDE.md`** for collection schemas, index table, and validation checklist.

---

### Redux State Management

The React frontend uses Redux Toolkit with four slices:

| Slice | State managed |
|---|---|
| `auth` | JWT token, user object, `isAuthenticated` |
| `restaurants` | search results, featured list, pagination |
| `reviews` | review list per restaurant |
| `favorites` | favorited restaurants, fast ID lookup set |

See **`LAB2_REDUX_INTEGRATION_NOTES.md`** for store structure, dispatch locations, DevTools demo guide, and selectors reference.

---

### JMeter Performance Testing

The test plan is at `jmeter/forkfinder_load_test.jmx`. It covers three endpoints at 100 / 200 / 300 / 400 / 500 concurrent users:

- `POST /auth/user/login`
- `GET /restaurants?q=pizza&limit=12`
- `POST /restaurants/{id}/reviews`

```bash
# Single run — 100 users
jmeter -n -t jmeter/forkfinder_load_test.jmx \
  -Jthreads=100 -Jrampup=30 \
  -JBASE_HOST=localhost -JBASE_PORT=8000 -JRESTAURANT_ID=1 \
  -l jmeter/results/raw_100.jtl -e -o jmeter/results/html_100
```

See **`LAB2_JMETER_RUNBOOK.md`** for all five runs, result extraction, graph generation, and analysis guidance.

---

## Local Dev (without Docker)

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB 7.0 (running locally on port 27017)
- Ollama (optional — for AI assistant)

```bash
# Optional: pull the AI model
ollama pull llama3.2
```

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
| `MONGODB_URL` | `mongodb://localhost:27017` | PyMongo connection string |
| `MONGODB_DB_NAME` | `restaurant_platform` | Database name |
| `SECRET_KEY` | `a-random-string-32-chars-min` | JWT signing secret |
| `ALGORITHM` | `HS256` | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | 30 days |
| `UPLOAD_DIR` | `uploads` | Relative path for uploaded files |
| `FRONTEND_URL` | `http://localhost:5173` | CORS allowed origin |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Optional — omit to disable Kafka |
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

```bash
# Terminal 1 — MongoDB (if not running as a service)
mongod --dbpath ~/data/db

# Terminal 2 — Ollama (optional)
ollama serve

# Terminal 3 — Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 4 — Frontend
cd frontend && npm run dev

# Terminal 5 — Review Worker (optional — requires Kafka)
cd backend
python -m workers.review_worker

# Terminal 6 — Restaurant Worker (optional — requires Kafka)
cd backend
python -m workers.restaurant_worker
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

python seed_data.py          # safe first-run: inserts only if users collection is empty
python seed_data.py --wipe   # full reseed: wipes all data then re-inserts
python seed_data.py --recalc # resync stored avg_rating/review_count
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

## Repository Checklist (Lab 2 Submission)

| Item | Location | Status |
|---|---|---|
| Dockerfiles — backend, frontend | `backend/Dockerfile`, `frontend/Dockerfile` | Done |
| Dockerfiles — 4 logical services | `services/*/Dockerfile` | Done |
| docker-compose.yml (full stack) | `docker-compose.yml` | Done |
| Kubernetes manifests — all services | `kubernetes/` | Done |
| Kubernetes — MongoDB | `kubernetes/03-mongodb.yaml` | Done |
| Kubernetes — Kafka + Zookeeper | `kubernetes/10-kafka.yaml` | Done |
| Kubernetes — Workers | `kubernetes/11-12-*-worker.yaml` | Done |
| Kafka producer + topics | `backend/app/kafka/` | Done |
| Kafka workers (consumers) | `backend/workers/` | Done |
| MongoDB migration | `backend/app/` (all Python) | Done |
| Redux store + slices | `frontend/src/store/` | Done |
| JMeter test plan (.jmx) | `jmeter/forkfinder_load_test.jmx` | Done |
| JMeter user CSV | `jmeter/users.csv` | Done |
| AWS/K8s deployment guide | `LAB2_AWS_K8S_DEPLOYMENT_GUIDE.md` | Done |
| Kafka deployment guide | `LAB2_KAFKA_DEPLOYMENT_GUIDE.md` | Done |
| MongoDB migration guide | `LAB2_MONGODB_MIGRATION_GUIDE.md` | Done |
| Redux integration notes | `LAB2_REDUX_INTEGRATION_NOTES.md` | Done |
| JMeter runbook | `LAB2_JMETER_RUNBOOK.md` | Done |
| Architecture diagram | `LAB2_ARCHITECTURE_DIAGRAM.md` | Done |
| AWS screenshots | **Manual** — run on EKS, take screenshots | Pending |
| Redux DevTools screenshots | **Manual** — run app locally, screenshot DevTools | Pending |
| JMeter results graph | **Manual** — run jmeter tests, fill in table | Pending |

---

## Notes

- **`.env` files are git-ignored** — never commit them; use `.env.example` as the template.
- **Ollama is optional** — if not running, the AI assistant returns a graceful fallback response.
- **Kafka is optional** — if `KAFKA_BOOTSTRAP_SERVERS` is not set, the backend degrades gracefully; all API endpoints still work without the broker.
- **MongoDB** — collections and indexes are created automatically on first backend start.
- **Private repo access** — ensure `Devdatta1999` and `Saurabh2504` have access.
