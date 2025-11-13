# Shoghi Platform - Complete Docker Image
# Includes Agent Zero, all dependencies, and pre-configured environment

FROM python:3.11-slim

LABEL maintainer="Shoghi Platform"
LABEL description="Voice-First Community Coordination Platform with Agent Zero"
LABEL version="1.0"

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
    wget \
    git \
    lsof \
    procps \
    vim \
    nano \
    postgresql-client \
    redis-tools \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest-asyncio gunicorn

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/data \
    /app/.bmad/agents \
    /app/.bmad/specs \
    /app/.bmad/stories && \
    chmod +x start_shoghi.sh deploy_shoghi.sh deploy_fixed.sh 2>/dev/null || true

# Create entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose ports
# 5000 - Web UI
# 5001 - API endpoint
# 6379 - Redis (if running in container)
EXPOSE 5000 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Set entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Default command
CMD ["python3", "shoghi_web_server.py"]
