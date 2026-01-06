# Stage 1: Build frontend with Node/Vite
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source code
COPY frontend/ ./

# Build frontend (creates /frontend/dist)
RUN npm run build

# Stage 2: Build backend with Python
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.21 /uv /usr/local/bin/

# Copy dependency files
COPY backend/pyproject.toml backend/uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY backend/ ./

# Copy frontend built files into Flask static folder
COPY --from=frontend-builder /frontend/dist ./app/static

# Create photos and thumbnails directories
RUN mkdir -p /app/photos /app/thumbnails

# Expose port
EXPOSE 5001

# Activate venv and run gunicorn directly (1 worker to save memory on fly.io)
# This uses the pre-built venv instead of recreating it with 'uv run'
CMD ["/bin/sh", "-c", ". .venv/bin/activate && exec gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 1 --timeout 120 run:app"]
