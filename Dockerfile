# Multi-stage Docker build for House Consciousness System
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash consciousness && \
    chown -R consciousness:consciousness /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R consciousness:consciousness /app/data /app/logs /app/config

USER consciousness

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uv", "run", "uvicorn", "consciousness.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Multi-stage build for production
FROM base as production

# Set production environment
ENV ENVIRONMENT=production \
    DEBUG=false

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy only necessary files
COPY --from=base /app /app

# Switch to production user
USER consciousness

CMD ["uv", "run", "uvicorn", "consciousness.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
