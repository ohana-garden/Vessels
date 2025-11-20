# Shoghi - Single Container Deployment

**100% pre-configured. Zero setup. Just run.**

---

## Quick Start

### 1. Build

```bash
./docker-build.sh
```

### 2. Run

```bash
# Run demo
./docker-run.sh demo

# Run with persistent data
./docker-run.sh demo-persist

# Start web server (daemon)
./docker-run.sh web

# Interactive shell
./docker-run.sh shell
```

---

## What's Inside

Single container includes:
- ✅ **FalkorDB** (Redis + graph module) - Port 6379
- ✅ **Shoghi Platform** - Projects + Graphiti architecture
- ✅ **All dependencies** - Pre-installed
- ✅ **Default config** - Ready to use
- ✅ **Demo scripts** - Working examples

---

## Manual Commands

### Build

```bash
docker build -t shoghi:latest .
```

### Run Demo (ephemeral)

```bash
docker run --rm shoghi:latest
```

### Run Demo (persistent)

```bash
docker run --rm \
  -v shoghi-data:/data/falkordb \
  -v shoghi-work:/app/work_dir \
  shoghi:latest demo
```

### Run Web Server (daemon)

```bash
docker run -d \
  --name shoghi-web \
  -p 5000:5000 \
  -p 6379:6379 \
  -v shoghi-data:/data/falkordb \
  -v shoghi-work:/app/work_dir \
  -e DAEMON=true \
  shoghi:latest web
```

### Interactive Shell

```bash
docker run -it --rm shoghi:latest shell
```

### Custom Command

```bash
docker run --rm shoghi:latest python /app/my_script.py
```

---

## Container Structure

```
/app/                          # Application root
├── shoghi/                    # Shoghi packages
│   ├── knowledge/            # Graph & vector stores
│   └── projects/             # Servant isolation
├── work_dir/                  # Persistent workspace
│   ├── projects/             # Servant projects
│   └── shared/               # Shared knowledge
├── examples/
│   └── projects_demo.py      # Demo script
└── config.json               # Default configuration

/data/falkordb/               # FalkorDB persistence
└── dump.rdb                  # Graph database

/etc/redis/
└── redis-falkordb.conf       # Pre-configured Redis
```

---

## Ports

- **6379** - FalkorDB (Redis protocol)
- **5000** - Shoghi web interface (if running web mode)

---

## Volumes

- **/data/falkordb** - Graph database persistence
- **/app/work_dir** - Project workspaces and knowledge stores

---

## Environment Variables

All have sensible defaults, but you can override:

```bash
docker run -e FALKORDB_HOST=localhost \
           -e FALKORDB_PORT=6379 \
           -e LOG_LEVEL=DEBUG \
           shoghi:latest
```

---

## Examples

### Run demo and see output

```bash
docker run --rm shoghi:latest demo
```

### Run demo with data that persists across runs

```bash
# First run
docker run --rm -v shoghi-data:/data/falkordb shoghi:latest demo

# Second run - data still there
docker run --rm -v shoghi-data:/data/falkordb shoghi:latest demo
```

### Start web server in background

```bash
./docker-run.sh web

# Check logs
docker logs -f shoghi-web

# Stop
./docker-run.sh stop
```

### Connect to running FalkorDB

```bash
# Start container in background
./docker-run.sh web

# Connect with redis-cli
redis-cli -h localhost -p 6379

# Or from another container
docker run -it --rm --network host redis:latest redis-cli -h localhost -p 6379
```

### Explore inside the container

```bash
# Start shell
./docker-run.sh shell

# Inside container
root@container:/app# python examples/projects_demo.py
root@container:/app# redis-cli ping
root@container:/app# ls work_dir/projects/
```

---

## Container Commands

The entrypoint script supports these commands:

- **demo** (default) - Run projects demo
- **web** - Start web server
- **shell** - Interactive bash shell
- **<any command>** - Run custom command

---

## Health Check

Container includes a health check that pings FalkorDB:

```bash
docker ps  # Look for "healthy" status
```

---

## Pre-configured Defaults

Everything is pre-configured:

✅ FalkorDB with optimized settings:
   - RDB persistence (900s/300s/60s intervals)
   - 512MB max memory (LRU eviction)
   - Graph module loaded

✅ Shoghi with sensible defaults:
   - Community: "lower_puna_elders"
   - Log level: INFO
   - FalkorDB: localhost:6379

✅ Directories created:
   - /app/work_dir/projects
   - /app/work_dir/shared/vectors
   - /data/falkordb

---

## Troubleshooting

### Container won't start

```bash
# Check Docker is running
docker info

# View logs
docker logs shoghi-web
```

### FalkorDB not ready

```bash
# Check if Redis is responding
docker exec shoghi-web redis-cli ping
# Should return: PONG
```

### Demo fails

```bash
# Run with verbose logging
docker run --rm -e LOG_LEVEL=DEBUG shoghi:latest demo
```

### Clean slate

```bash
# Remove all Shoghi data
./docker-run.sh clean

# Rebuild from scratch
./docker-build.sh
./docker-run.sh demo
```

---

## Production Deployment

For production, use persistent volumes and proper networking:

```bash
docker run -d \
  --name shoghi-prod \
  --restart unless-stopped \
  -p 5000:5000 \
  -v /opt/shoghi/data:/data/falkordb \
  -v /opt/shoghi/work:/app/work_dir \
  -e DAEMON=true \
  -e LOG_LEVEL=INFO \
  shoghi:latest web
```

---

## Size

- **Base image**: ~150MB (python:3.10-slim)
- **Dependencies**: ~300MB (Redis, Python packages)
- **Final image**: ~450MB

---

## What's Running

When you start the container:

1. **Redis/FalkorDB** starts on port 6379
2. **Health check** waits for FalkorDB to be ready
3. **Shoghi app** starts (demo/web/shell depending on command)
4. **Graceful shutdown** on SIGTERM/SIGINT

---

## Next Steps

1. Build: `./docker-build.sh`
2. Run demo: `./docker-run.sh demo`
3. Read output - see Projects + Graphiti in action!
4. Try web mode: `./docker-run.sh web`
5. Explore: `./docker-run.sh shell`

**That's it!** Zero configuration needed. Everything just works.

---

🌺 Built with Aloha for the Ohana Garden community 🌺
