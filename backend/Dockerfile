FROM python:3.11-slim

WORKDIR /app

# System libraries needed by Pillow (image processing) and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure upload subdirectories exist inside the image
RUN mkdir -p uploads/profiles uploads/restaurants uploads/reviews

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
