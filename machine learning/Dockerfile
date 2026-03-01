FROM python:3.11-slim

# 1. Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 2. System dependencies for Azure SQL (ODBC Driver 18)
RUN apt-get update && apt-get install -y curl gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Install dependencies using uv
# We copy pyproject/lock from the root of your backend folder
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

# 4. Copy the application code
# This copies the 'app' folder and 'infrastructure' if needed
COPY . .

# 5. Runtime Configuration
# We tell Python where to find your modules
ENV PYTHONPATH=/app

# Launch using OpenTelemetry instrumentation for Phase 8
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]