FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY . .

# Create photos and thumbnails directories
RUN mkdir -p /app/photos /app/thumbnails

# Expose port
EXPOSE 5001

# Run with gunicorn via uv
CMD uv run gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --timeout 120 run:app
