# Build context: repo root  (docker build -f services/restaurant-service/Dockerfile .)
#
# Logical scope: restaurant CRUD, search, photos, claim flow.
# Routes served: /restaurants/*

FROM python:3.11-slim

LABEL service="restaurant-service" \
      maintainer="ForkFinder"

ENV SERVICE_NAME=restaurant-service

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
