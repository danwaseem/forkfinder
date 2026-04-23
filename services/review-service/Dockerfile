# Build context: repo root  (docker build -f services/review-service/Dockerfile .)
#
# Logical scope: review CRUD, photo uploads, rating aggregation.
# Routes served: /reviews/*, /restaurants/{id}/reviews

FROM python:3.11-slim

LABEL service="review-service" \
      maintainer="ForkFinder"

ENV SERVICE_NAME=review-service

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
