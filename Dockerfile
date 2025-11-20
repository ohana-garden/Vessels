FROM python:3.10-slim

# Install Redis and system dependencies
RUN apt-get update && apt-get install -y \
    redis-server \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install FalkorDB module for Redis
RUN mkdir -p /usr/lib/redis/modules && \
    cd /tmp && \
    curl -L https://github.com/FalkorDB/FalkorDB/releases/download/v4.0.10/falkordb-v4.0.10-ubuntu22.04.so -o falkordb.so && \
    mv falkordb.so /usr/lib/redis/modules/ && \
    chmod 644 /usr/lib/redis/modules/falkordb.so

# Create app directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY shoghi/ ./shoghi/
COPY .bmad/ ./.bmad/
COPY *.py ./
COPY examples/ ./examples/
COPY scripts/ ./scripts/

# Create required directories
RUN mkdir -p \
    /app/work_dir/projects \
    /app/work_dir/shared/vectors \
    /data/falkordb \
    /var/log/shoghi

# Configure Redis for FalkorDB
RUN echo "loadmodule /usr/lib/redis/modules/falkordb.so" > /etc/redis/redis-falkordb.conf && \
    echo "bind 0.0.0.0" >> /etc/redis/redis-falkordb.conf && \
    echo "port 6379" >> /etc/redis/redis-falkordb.conf && \
    echo "dir /data/falkordb" >> /etc/redis/redis-falkordb.conf && \
    echo "dbfilename dump.rdb" >> /etc/redis/redis-falkordb.conf && \
    echo "save 900 1" >> /etc/redis/redis-falkordb.conf && \
    echo "save 300 10" >> /etc/redis/redis-falkordb.conf && \
    echo "save 60 10000" >> /etc/redis/redis-falkordb.conf && \
    echo "appendonly no" >> /etc/redis/redis-falkordb.conf && \
    echo "maxmemory 512mb" >> /etc/redis/redis-falkordb.conf && \
    echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis-falkordb.conf && \
    echo "daemonize no" >> /etc/redis/redis-falkordb.conf

# Copy startup script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create default config
RUN echo '{\
  "falkordb_host": "localhost",\
  "falkordb_port": 6379,\
  "default_community": "lower_puna_elders",\
  "log_level": "INFO"\
}' > /app/config.json

# Expose ports
# 6379 - FalkorDB
# 5000 - Shoghi web interface (if running)
EXPOSE 6379 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD redis-cli -p 6379 ping || exit 1

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    FALKORDB_HOST=localhost \
    FALKORDB_PORT=6379

# Volume for persistence
VOLUME ["/data/falkordb", "/app/work_dir"]

# Run startup script
ENTRYPOINT ["/entrypoint.sh"]
CMD ["demo"]
