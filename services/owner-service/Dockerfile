# Build context: repo root  (docker build -f services/owner-service/Dockerfile .)
#
# Logical scope: restaurant-owner dashboard, profile, analytics, ownership claims.
# Routes served: /auth/owner/*, /owner/*

FROM python:3.11-slim

LABEL service="restaurant-owner-service" \
      maintainer="ForkFinder"

ENV SERVICE_NAME=restaurant-owner-service

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
RUN mkdir -p uploads/profiles uploads/restaurants uploads/reviews

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
