# Build context: repo root  (docker build -f services/user-service/Dockerfile .)
#
# Logical scope: user registration, login, profile, preferences,
#                favorites, activity history.
# Routes served: /auth/user/*, /users/*, /preferences/*, /favorites/*, /history/*
#
# NOTE: The Lab 1 codebase is a single FastAPI monolith. All four service
# Dockerfiles build from the same source and start the same application.
# In Kubernetes each is deployed as an independent, scalable unit under its
# own service DNS name, demonstrating the microservice decomposition pattern.

FROM python:3.11-slim

LABEL service="user-reviewer-service" \
      maintainer="ForkFinder"

ENV SERVICE_NAME=user-reviewer-service

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
