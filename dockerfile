FROM python:3.11-slim

# Install system dependencies for ML/data processing
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first (for Docker layer caching)
COPY pyproject.toml ./

# Generate uv.lock if it doesn't exist, then sync dependencies
RUN uv lock && uv sync --frozen

# Copy source code
COPY . .

EXPOSE 8000

# Run with opentelemetry instrumentation
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]