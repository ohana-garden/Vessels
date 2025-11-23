# Vessels Platform - Windows Docker Desktop Quick Start

Run the complete Vessels platform in a single Docker container on your Windows laptop.

## Prerequisites

1. **Docker Desktop for Windows** - [Download here](https://www.docker.com/products/docker-desktop/)
   - Install and start Docker Desktop
   - Ensure it's running (check the system tray icon)
   - WSL 2 backend is recommended for better performance

2. **System Requirements**
   - Windows 10/11 (64-bit)
   - At least 4GB RAM available for Docker
   - 5GB free disk space

## Quick Start

### Option 1: Using PowerShell (Recommended)

```powershell
# 1. Build the Docker image (first time only, ~5-10 minutes)
.\docker-windows.ps1 build

# 2. Run Vessels Platform
.\docker-windows.ps1 run

# The web interface will be available at: http://localhost:5000
```

### Option 2: Using Command Prompt

```cmd
REM 1. Build the Docker image (first time only)
docker-windows.bat build

REM 2. Run Vessels Platform
docker-windows.bat run

REM The web interface will be available at: http://localhost:5000
```

### Option 3: Manual Docker Commands

```bash
# Build
docker build -t vessels:latest .

# Run
docker run -d \
  --name vessels-platform \
  -p 5000:5000 \
  -p 6379:6379 \
  -v vessels-data:/data/falkordb \
  -v vessels-workdir:/app/work_dir \
  --restart unless-stopped \
  vessels:latest

# Access at: http://localhost:5000
```

## What's Included

The single container includes:

✅ **FalkorDB** - Graph database (Redis + FalkorDB module)
✅ **Vessels Core** - Agent coordination system
✅ **Web Interface** - Voice-enabled UI on port 5000
✅ **All Dependencies** - Python packages, AI models, etc.
✅ **Persistent Storage** - Data survives container restarts

## Usage

### Accessing the Platform

1. **Web Interface**: http://localhost:5000
   - Voice-enabled UI
   - Multi-agent coordination
   - Real-time agent interaction

2. **FalkorDB**: localhost:6379
   - Direct database access if needed
   - Use any Redis client

### Management Commands

#### PowerShell:
```powershell
.\docker-windows.ps1 run      # Start the platform
.\docker-windows.ps1 stop     # Stop the platform
.\docker-windows.ps1 logs     # View logs
.\docker-windows.ps1 shell    # Open shell in container
.\docker-windows.ps1 clean    # Remove container and image
```

#### Command Prompt:
```cmd
docker-windows.bat run        # Start the platform
docker-windows.bat stop       # Stop the platform
docker-windows.bat logs       # View logs
docker-windows.bat shell      # Open shell in container
docker-windows.bat clean      # Remove container and image
```

#### Direct Docker:
```bash
docker logs -f vessels-platform      # View logs
docker exec -it vessels-platform bash  # Shell access
docker stop vessels-platform         # Stop
docker start vessels-platform        # Start
docker restart vessels-platform      # Restart
```

## Data Persistence

Your data is stored in Docker volumes and persists across container restarts:

- **vessels-data**: FalkorDB graph database
- **vessels-workdir**: Project files and agent workspaces

### View Volumes:
```bash
docker volume ls | findstr vessels
```

### Backup Data:
```bash
# Backup FalkorDB
docker run --rm -v vessels-data:/data -v %cd%:/backup alpine tar czf /backup/vessels-data-backup.tar.gz /data

# Backup work directory
docker run --rm -v vessels-workdir:/data -v %cd%:/backup alpine tar czf /backup/vessels-workdir-backup.tar.gz /data
```

### Restore Data:
```bash
# Restore FalkorDB
docker run --rm -v vessels-data:/data -v %cd%:/backup alpine tar xzf /backup/vessels-data-backup.tar.gz -C /

# Restore work directory
docker run --rm -v vessels-workdir:/data -v %cd%:/backup alpine tar xzf /backup/vessels-workdir-backup.tar.gz -C /
```

## Troubleshooting

### Container Won't Start

1. Check Docker is running:
   ```bash
   docker info
   ```

2. Check if ports are in use:
   ```bash
   netstat -ano | findstr :5000
   netstat -ano | findstr :6379
   ```

3. View container logs:
   ```bash
   docker logs vessels-platform
   ```

### Build Fails

1. Ensure stable internet connection (downloads ~500MB of dependencies)

2. Clear Docker cache and rebuild:
   ```bash
   docker builder prune -a
   docker-windows.ps1 build
   ```

### Web Interface Not Accessible

1. Verify container is running:
   ```bash
   docker ps
   ```

2. Check container health:
   ```bash
   docker inspect vessels-platform | findstr Health
   ```

3. View application logs:
   ```bash
   docker logs vessels-platform | findstr -i error
   ```

### Performance Issues

1. Allocate more resources to Docker Desktop:
   - Right-click Docker Desktop icon → Settings
   - Resources → Advanced
   - Increase CPU and Memory

2. Use WSL 2 backend (if not already):
   - Settings → General → Use WSL 2 based engine

### FalkorDB Connection Issues

1. Check FalkorDB is responding:
   ```bash
   docker exec vessels-platform redis-cli ping
   ```

2. Restart the container:
   ```bash
   docker restart vessels-platform
   ```

## Advanced Configuration

### Running Different Modes

The container supports different startup modes:

```bash
# Web server mode (default)
docker run ... vessels:latest web

# Demo mode (CLI demonstration)
docker run ... vessels:latest demo

# Interactive shell
docker run -it ... vessels:latest shell
```

### Environment Variables

Customize behavior with environment variables:

```bash
docker run -d \
  --name vessels-platform \
  -e FALKORDB_HOST=localhost \
  -e FALKORDB_PORT=6379 \
  -e DAEMON=true \
  -p 5000:5000 \
  -p 6379:6379 \
  vessels:latest
```

### Mount Local Directories

For development, mount local code:

```bash
docker run -d \
  --name vessels-platform \
  -v %cd%/vessels:/app/vessels \
  -v %cd%/work_dir:/app/work_dir \
  -p 5000:5000 \
  -p 6379:6379 \
  vessels:latest
```

## Updating

To update to the latest version:

```powershell
# Pull latest code
git pull

# Rebuild image
.\docker-windows.ps1 clean
.\docker-windows.ps1 build

# Start with new version
.\docker-windows.ps1 run
```

## Uninstalling

Complete removal:

```bash
# Stop and remove container
docker stop vessels-platform
docker rm vessels-platform

# Remove image
docker rmi vessels:latest

# Remove volumes (⚠️ deletes all data)
docker volume rm vessels-data vessels-workdir
```

## Getting Help

1. **View container logs**:
   ```bash
   docker logs -f vessels-platform
   ```

2. **Access container shell**:
   ```bash
   docker exec -it vessels-platform bash
   ```

3. **Check FalkorDB**:
   ```bash
   docker exec -it vessels-platform redis-cli
   ```

4. **Test connectivity**:
   ```bash
   curl http://localhost:5000/api/status
   ```

## Architecture

```
┌─────────────────────────────────────────┐
│    Vessels Platform Container           │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Web Interface (Port 5000)       │  │
│  │  - Voice UI                       │  │
│  │  - Agent Coordination            │  │
│  └──────────────────────────────────┘  │
│                ↓                        │
│  ┌──────────────────────────────────┐  │
│  │  Vessels Core System              │  │
│  │  - AgentZeroCore                 │  │
│  │  - Dynamic Agent Factory          │  │
│  │  - Community Memory               │  │
│  └──────────────────────────────────┘  │
│                ↓                        │
│  ┌──────────────────────────────────┐  │
│  │  FalkorDB (Port 6379)            │  │
│  │  - Graph Database                 │  │
│  │  - Redis + FalkorDB Module       │  │
│  └──────────────────────────────────┘  │
│                                         │
│  Persistent Volumes:                    │
│  - /data/falkordb → vessels-data       │
│  - /app/work_dir → vessels-workdir     │
└─────────────────────────────────────────┘
```

## Next Steps

1. **Access the web interface**: http://localhost:5000
2. **Try voice commands** or text input
3. **Explore the agent system** - see multi-agent coordination in action
4. **Check the logs** to understand what's happening
5. **Read the main README** for more about Vessels architecture

## Security Notes

**For Development/Testing Only** - This configuration is optimized for local testing:

- FalkorDB is exposed on port 6379 (only accessible from localhost)
- No authentication configured
- Web interface has no login
- Not hardened for production use

For production deployment, see the main `docker-compose.yml` which includes:
- API Gateway (nginx)
- Proper network isolation
- Health checks
- Restart policies
- Future: payment service integration

---

**Enjoy exploring Vessels! 🚢**
