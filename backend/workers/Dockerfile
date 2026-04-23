# Worker services Dockerfile
# Build context: repo root  (docker build -f backend/workers/Dockerfile .)
#
# A single image for both review_worker and restaurant_worker.
# The CMD is overridden in docker-compose / K8s to select which worker to run.
#
# Default CMD runs the review worker; override in docker-compose or K8s:
#   command: ["python", "-m", "workers.restaurant_worker"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full backend source so workers can share models/utils if needed
COPY backend/ .

CMD ["python", "-m", "workers.review_worker"]
