# Shoghi Replicant - Multi-stage Docker Build
# Combines Shoghi moral constraint system + Agent Zero coordination platform

# Stage 1: Base image with Python and system dependencies
FROM python:3.11-slim-bullseye AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base AS dependencies

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 3: Final application image
FROM base AS final

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN useradd -m -u 1000 shoghi && \
    mkdir -p /app/data /app/logs && \
    chown -R shoghi:shoghi /app

# Set working directory
WORKDIR /app

# Copy application files
COPY --chown=shoghi:shoghi . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/.bmad && \
    chown -R shoghi:shoghi /app

# Switch to non-root user
USER shoghi

# Expose port for web server
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["python", "shoghi_web_server.py"]
