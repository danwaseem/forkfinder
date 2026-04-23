# Lab 2 — Kafka Deployment & Validation Guide

End-to-end instructions for running and validating the Kafka producer/consumer
pipeline both locally (Docker) and on AWS EKS.

---

## Part A — Run Locally with Docker Compose

### A1. Start the full stack

```bash
# From the repo root
cp .env.docker.example .env.docker    # only needed once

docker compose --env-file .env.docker up --build
```

This starts 7 containers:
| Container | Role |
|---|---|
| `forkfinder-mongodb` | MongoDB database |
| `forkfinder-zookeeper` | Kafka coordination service |
| `forkfinder-kafka` | Kafka broker |
| `forkfinder-backend` | FastAPI — Review & Restaurant API (producer) |
| `forkfinder-review-worker` | Kafka consumer — review events |
| `forkfinder-restaurant-worker` | Kafka consumer — restaurant events |
| `forkfinder-frontend` | React frontend (Nginx) |

Wait for all containers to show `healthy` or `running`:
```bash
docker compose --env-file .env.docker ps
```

### A2. Seed demo data

```bash
docker compose --env-file .env.docker exec backend python seed_data.py
```

---

## Part B — Validate the Kafka Review Flow

### B1. Get a JWT token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@demo.com","password":"password"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token: ${TOKEN:0:40}..."
```

### B2. Submit a review (triggers Kafka producer)

```bash
curl -s -X POST http://localhost:8000/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_id": 1, "rating": 5, "comment": "Testing Kafka pipeline — excellent food!"}' \
  | python3 -m json.tool
```

Expected: HTTP 201 with `review.id` in the response and the same response as before
Kafka integration — the API response is unchanged.

### B3. Check producer logs

```bash
docker logs forkfinder-backend --tail 20
```

Look for a line like:
```
INFO:app.kafka.producer:Published event to review.created (event_id=<uuid>)
```

### B4. Check consumer logs (review worker)

```bash
docker logs forkfinder-review-worker --tail 20
```

Look for a line like:
```
2026-04-14T... [review-worker] INFO: ✓ Consumed  topic=review.created   review_id=37   restaurant_id=1   event_id=<uuid>
```

### B5. Verify the audit document in the database

```bash
docker compose --env-file .env.docker exec mongodb \
  mongosh restaurant_platform --quiet \
  --eval "db.review_events.find().sort({processed_at: -1}).limit(5).forEach(d => printjson(d))"
```

Expected output:
```json
{
  "_id": ObjectId("..."),
  "event_id": "uuid-here",
  "event_type": "review.created",
  "review_id": 37,
  "restaurant_id": 1,
  "user_id": 1,
  "processed_at": ISODate("2026-04-14T...")
}
```

**Screenshot to capture for the report:** This query output + the worker logs.

### B6. Test update and delete

```bash
REVIEW_ID=37   # replace with the id returned in step B2

# Update the review
curl -s -X PUT http://localhost:8000/reviews/${REVIEW_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "comment": "Updated after second visit — still great!"}' \
  | python3 -m json.tool

# Delete the review
curl -s -X DELETE http://localhost:8000/reviews/${REVIEW_ID} \
  -H "Authorization: Bearer $TOKEN"

# Check all three event types
docker compose --env-file .env.docker exec mongodb \
  mongosh restaurant_platform --quiet \
  --eval "db.review_events.find({},{event_type:1,review_id:1,processed_at:1}).sort({processed_at:-1}).limit(5).forEach(d=>printjson(d))"
```

Expected: rows for `review.created`, `review.updated`, `review.deleted`.

### B7. Test restaurant events

```bash
# Create a restaurant (triggers restaurant.created Kafka event)
curl -s -X POST http://localhost:8000/restaurants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Kafka Test Restaurant","cuisine_type":"Test","city":"San Francisco"}' \
  | python3 -m json.tool

# Verify restaurant_events collection
docker compose --env-file .env.docker exec mongodb \
  mongosh restaurant_platform --quiet \
  --eval "db.restaurant_events.find({},{event_type:1,restaurant_id:1,actor_user_id:1,processed_at:1}).sort({processed_at:-1}).limit(5).forEach(d=>printjson(d))"
```

---

## Part C — Inspect Kafka Topics Directly

### C1. List all topics

```bash
docker exec forkfinder-kafka \
  kafka-topics.sh --bootstrap-server localhost:9092 --list
```

Expected topics:
```
restaurant.claimed
restaurant.created
restaurant.updated
review.created
review.deleted
review.updated
```

### C2. Read messages from a topic (from the beginning)

```bash
# Read all review.created messages
docker exec forkfinder-kafka \
  kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic review.created \
  --from-beginning \
  --max-messages 5
```

**Screenshot to capture for the report:** The JSON message envelope showing `event_id`, `topic`, `timestamp`, and `data`.

### C3. Check consumer group lag

```bash
docker exec forkfinder-kafka \
  kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe \
  --group review-worker-group
```

`LAG` column should be 0 (all messages consumed).

---

## Part D — Deploy Kafka on EKS (Kubernetes)

### D1. Prerequisites
- You have already completed `LAB2_AWS_K8S_DEPLOYMENT_GUIDE.md` through Part H
  (namespace, configmap, secrets, MongoDB, and the four backend services are deployed)
- `kubectl get pods -n forkfinder` shows the existing pods Running

### D2. Create the workers ECR repository

```bash
REGION=us-east-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws ecr create-repository \
  --repository-name forkfinder/workers \
  --region ${REGION}
```

### D3. Build and push the workers image

```bash
ECR=${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

docker build -f backend/workers/Dockerfile \
  -t ${ECR}/forkfinder/workers:latest .

docker push ${ECR}/forkfinder/workers:latest
```

### D4. Update the worker manifests with your ECR URI

```bash
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

for f in kubernetes/11-review-worker.yaml kubernetes/12-restaurant-worker.yaml; do
  sed -i '' "s|<YOUR_ECR_REGISTRY>|${ECR_URI}|g" ${f}
done
```

### D5. Deploy Kafka and the workers

```bash
kubectl apply -f kubernetes/10-kafka.yaml
kubectl apply -f kubernetes/11-review-worker.yaml
kubectl apply -f kubernetes/12-restaurant-worker.yaml
```

### D6. Wait for pods to be Running

```bash
kubectl get pods -n forkfinder --watch
```

Expected (new pods):
```
kafka-<hash>                  1/1   Running   0
zookeeper-<hash>              1/1   Running   0
review-worker-<hash>          1/1   Running   0
restaurant-worker-<hash>      1/1   Running   0
```

### D7. Update backend pods to know the Kafka address

The backend Deployments (04–07) need `KAFKA_BOOTSTRAP_SERVERS=kafka:9092`.
The `kafka` K8s Service DNS name is `kafka.forkfinder.svc.cluster.local` (or just `kafka`
within the same namespace).

Patch each backend deployment:
```bash
for dep in user-service owner-service restaurant-service review-service; do
  kubectl set env deployment/${dep} \
    KAFKA_BOOTSTRAP_SERVERS=kafka:9092 \
    -n forkfinder
done
```

### D8. Validate on EKS

```bash
# Check Kafka topics exist
KAFKA_POD=$(kubectl get pod -n forkfinder -l app=kafka \
  -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n forkfinder ${KAFKA_POD} -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# Stream worker logs
kubectl logs -n forkfinder -l app=review-worker --follow
```

**Screenshot to capture:**
1. `kubectl get pods -n forkfinder` showing kafka, zookeeper, review-worker, restaurant-worker all Running
2. Worker log output showing a consumed message
3. Kafka topics list output
4. `review_events` collection documents (via kubectl exec into MongoDB pod)

---

## Part E — Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Workers stuck in `CrashLoopBackOff` | Kafka not ready when worker starts | Workers retry on `NoBrokersAvailable` — check if Kafka pod is Running first |
| Producer logs show "Kafka not available" | `KAFKA_BOOTSTRAP_SERVERS` not set or wrong | Verify env var in docker-compose or K8s deployment |
| `review_events` collection is empty | Worker not running or not consuming | `docker logs forkfinder-review-worker` — check for errors |
| Kafka topic not found | Topics auto-created on first publish | Wait a few seconds; or create manually: `kafka-topics.sh --create --topic review.created --bootstrap-server localhost:9092` |
| Consumer group lag never reaches 0 | Worker crashed after receiving messages | Check `docker logs forkfinder-review-worker` for DB errors |
| `NoBrokersAvailable` on first API request | Kafka still starting | Increase `start_period` in Kafka healthcheck or add retry logic |

---

## Kafka Message Format Reference

Every published message follows this envelope:

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic":    "review.created",
  "timestamp": "2026-04-14T10:23:45.123456+00:00",
  "data": {
    "review_id":     37,
    "user_id":        1,
    "restaurant_id":  1,
    "rating":         5,
    "comment":        "Testing Kafka pipeline — excellent food!",
    "created_at":     "2026-04-14T10:23:44.987654"
  }
}
```
