# ==============================================================================
# Vessels Unified Container
# Includes: Python + Node.js + TEN Framework + TigerBeetle + Petals + FalkorDB
# ==============================================================================

FROM python:3.10-slim

# ==============================================================================
# SYSTEM DEPENDENCIES
# ==============================================================================

RUN apt-get update && apt-get install -y \
    # Database systems
    redis-server \
    postgresql \
    postgresql-contrib \
    # Node.js for TigerBeetle, TEN Framework, payment services
    curl \
    wget \
    gnupg \
    # Build tools
    build-essential \
    git \
    cmake \
    pkg-config \
    # Audio/Video for TEN Framework
    ffmpeg \
    libopus-dev \
    libopusfile-dev \
    portaudio19-dev \
    # Networking
    netcat-openbsd \
    # Utilities
    supervisor \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Verify installations
RUN node --version && npm --version && python --version

# ==============================================================================
# FALKORDB (Graph Database)
# ==============================================================================

RUN mkdir -p /usr/lib/redis/modules && \
    cd /tmp && \
    curl -L https://github.com/FalkorDB/FalkorDB/releases/download/v4.0.10/falkordb-v4.0.10-ubuntu22.04.so -o falkordb.so && \
    mv falkordb.so /usr/lib/redis/modules/ && \
    chmod 644 /usr/lib/redis/modules/falkordb.so

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

# ==============================================================================
# APPLICATION SETUP
# ==============================================================================

WORKDIR /app

# Python dependencies
COPY requirements.txt requirements-fixed.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-fixed.txt || true

# Payment service dependencies (Node.js/TypeScript)
COPY payment/package*.json payment/tsconfig.json ./payment/
WORKDIR /app/payment
RUN npm ci && npm cache clean --force

# Build payment TypeScript services
COPY payment/ /app/payment/
RUN npm run build

# TEN Framework packages
WORKDIR /app
COPY ten_packages/ /app/ten_packages/
COPY graphs/ /app/graphs/

# Install TEN Framework CLI and dependencies
RUN npm install -g @ten-framework/cli || echo "TEN CLI install optional"

# ==============================================================================
# VESSELS APPLICATION CODE
# ==============================================================================

WORKDIR /app

# Copy all application code
COPY vessels/ ./vessels/
COPY .bmad/ ./.bmad/
COPY config/ ./config/
COPY *.py ./
COPY examples/ ./examples/
COPY scripts/ ./scripts/
COPY *.html ./ 2>/dev/null || true
COPY *.js ./ 2>/dev/null || true
COPY *.yaml ./ 2>/dev/null || true
COPY *.md ./ 2>/dev/null || true

# Create required directories
RUN mkdir -p \
    /app/work_dir/projects \
    /app/work_dir/vessels \
    /app/work_dir/shared/vectors \
    /data/falkordb \
    /data/tigerbeetle \
    /data/postgres \
    /var/log/shoghi \
    /var/log/payment

# ==============================================================================
# SUPERVISORD CONFIGURATION (Run all services in one container)
# ==============================================================================

RUN mkdir -p /etc/supervisor/conf.d

# Configure PostgreSQL
RUN mkdir -p /var/run/postgresql && chown postgres:postgres /var/run/postgresql && \
    mkdir -p /data/postgres && chown postgres:postgres /data/postgres && \
    echo "host all all 0.0.0.0/0 trust" >> /etc/postgresql/*/main/pg_hba.conf && \
    echo "listen_addresses='*'" >> /etc/postgresql/*/main/postgresql.conf

# Download TigerBeetle binary
RUN cd /tmp && \
    wget https://github.com/tigerbeetle/tigerbeetle/releases/download/0.15.3/tigerbeetle-x86_64-linux.zip && \
    unzip tigerbeetle-x86_64-linux.zip && \
    mv tigerbeetle /usr/local/bin/ && \
    chmod +x /usr/local/bin/tigerbeetle && \
    rm tigerbeetle-x86_64-linux.zip

# Initialize TigerBeetle data file
RUN mkdir -p /data/tigerbeetle && \
    tigerbeetle format --cluster=0 --replica=0 --replica-count=1 /data/tigerbeetle/0.tigerbeetle || true

# Supervisor config for all services
RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:postgresql]\n\
command=/usr/lib/postgresql/*/bin/postgres -D /var/lib/postgresql/*/main -c config_file=/etc/postgresql/*/main/postgresql.conf\n\
user=postgres\n\
autostart=true\n\
autorestart=true\n\
priority=10\n\
stdout_logfile=/var/log/supervisor/postgres.log\n\
stderr_logfile=/var/log/supervisor/postgres_err.log\n\
\n\
[program:redis-falkordb]\n\
command=redis-server /etc/redis/redis-falkordb.conf\n\
autostart=true\n\
autorestart=true\n\
priority=10\n\
stdout_logfile=/var/log/supervisor/redis.log\n\
stderr_logfile=/var/log/supervisor/redis_err.log\n\
\n\
[program:tigerbeetle]\n\
command=/usr/local/bin/tigerbeetle start --addresses=0.0.0.0:3001 /data/tigerbeetle/0.tigerbeetle\n\
autostart=true\n\
autorestart=true\n\
priority=20\n\
stdout_logfile=/var/log/supervisor/tigerbeetle.log\n\
stderr_logfile=/var/log/supervisor/tigerbeetle_err.log\n\
\n\
[program:payment-service]\n\
command=node /app/payment/dist/index.js\n\
directory=/app/payment\n\
autostart=true\n\
autorestart=true\n\
priority=30\n\
environment=NODE_ENV="production",PORT="3000",TIGERBEETLE_REPLICA_ADDRESSES="localhost:3001",DATABASE_URL="postgresql://vessels:vessels_dev@localhost:5432/vessels_payment"\n\
stdout_logfile=/var/log/supervisor/payment.log\n\
stderr_logfile=/var/log/supervisor/payment_err.log\n\
\n\
[program:vessels-app]\n\
command=python -u main.py\n\
directory=/app\n\
autostart=true\n\
autorestart=true\n\
priority=40\n\
environment=PYTHONUNBUFFERED="1",FALKORDB_HOST="localhost",FALKORDB_PORT="6379",PAYMENT_SERVICE_URL="http://localhost:3000"\n\
stdout_logfile=/var/log/supervisor/vessels.log\n\
stderr_logfile=/var/log/supervisor/vessels_err.log\n\
' > /etc/supervisor/supervisord.conf

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Create default Vessels config
RUN echo '{\n\
  "falkordb_host": "localhost",\n\
  "falkordb_port": 6379,\n\
  "payment_service_url": "http://localhost:3000",\n\
  "default_community": "lower_puna_elders",\n\
  "log_level": "INFO",\n\
  "tier0": {\n\
    "enabled": true,\n\
    "device_models": ["phi3", "llama3.2"]\n\
  },\n\
  "tier1": {\n\
    "enabled": true,\n\
    "edge_url": "http://localhost:11434"\n\
  },\n\
  "tier2": {\n\
    "enabled": false,\n\
    "petals_model": "petals-team/StableBeluga2"\n\
  },\n\
  "ten_framework": {\n\
    "enabled": true,\n\
    "graphs_dir": "/app/graphs"\n\
  }\n\
}' > /app/config.json

# ==============================================================================
# PORTS
# ==============================================================================

EXPOSE 5000 6379 3000 8080

# 5000  - Vessels web interface
# 6379  - FalkorDB
# 3000  - Payment service API
# 8080  - TEN Framework (if running standalone)

# ==============================================================================
# HEALTH CHECK
# ==============================================================================

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD redis-cli -p 6379 ping && \
        curl -f http://localhost:5000/health && \
        curl -f http://localhost:3000/health || exit 1

# ==============================================================================
# ENVIRONMENT VARIABLES
# ==============================================================================

ENV PYTHONUNBUFFERED=1 \
    FALKORDB_HOST=localhost \
    FALKORDB_PORT=6379 \
    PAYMENT_SERVICE_URL=http://localhost:3000 \
    NODE_ENV=production \
    DAEMON=true \
    TEN_FRAMEWORK_ENABLED=true \
    PETALS_ENABLED=false

# ==============================================================================
# VOLUMES
# ==============================================================================

VOLUME ["/data/falkordb", "/data/tigerbeetle", "/data/postgres", "/app/work_dir"]

# ==============================================================================
# STARTUP
# ==============================================================================

# Use supervisord to manage all processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]
