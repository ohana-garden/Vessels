# 🌺 Shoghi Platform - Docker Quick Start

Complete Docker setup for the Shoghi Voice-First Community Coordination Platform with Agent Zero integration.

## 🚀 One-Click Launch

### Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/ohana-garden/shoghi.git
cd shoghi

# Launch with Docker Compose (ONE COMMAND!)
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
open http://localhost:5000
```

That's it! Everything is pre-configured and ready to use.

## 📦 What's Included

The Docker image includes:
- ✅ Python 3.11 with all dependencies
- ✅ Agent Zero core system
- ✅ Shoghi platform modules
- ✅ All test suites (168 tests)
- ✅ BMAD agent definitions
- ✅ Web server with voice UI
- ✅ Database initialization
- ✅ Health checks and auto-restart
- ✅ Log rotation and management

## 🛠️ Docker Commands

### Basic Operations

```bash
# Start the platform
docker-compose up -d

# Stop the platform
docker-compose down

# Restart the platform
docker-compose restart

# View logs (live)
docker-compose logs -f shoghi

# View only recent logs
docker-compose logs --tail=100 shoghi

# Check status
docker-compose ps
```

### Development Operations

```bash
# Run tests inside container
docker-compose exec shoghi pytest -v

# Access container shell
docker-compose exec shoghi bash

# Run a specific Python script
docker-compose exec shoghi python3 demo_shoghi.py

# Check application logs
docker-compose exec shoghi tail -f /app/logs/web_server.log
```

### Advanced Operations

```bash
# Build image from scratch
docker-compose build --no-cache

# Pull latest image (if published)
docker-compose pull

# Scale services (if needed)
docker-compose up -d --scale shoghi=3

# View resource usage
docker stats shoghi-platform

# Export logs
docker-compose logs shoghi > shoghi_logs_$(date +%Y%m%d).txt
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  # Enable test suite on startup
  - RUN_TESTS=true

  # Set log level
  - LOG_LEVEL=DEBUG

  # Add API keys
  - GRANTS_GOV_API_KEY=your_key_here
  - FOUNDATION_CENTER_API_KEY=your_key_here
```

### Volumes

Data is persisted in Docker volumes:
- `shoghi-data` - Application data
- `shoghi-logs` - Log files
- `./shoghi_grants.db` - SQLite database (bind mount)
- `./.bmad` - BMAD agent configurations (bind mount)

### Ports

Default ports:
- `5000` - Web UI (Voice-First Interface)
- `5001` - API endpoint (optional)

Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Access on port 8080 instead
```

## 🏥 Health Checks

The container includes automatic health checks:

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' shoghi-platform

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' shoghi-platform
```

## 🗄️ Optional Services

### Enable Redis (for caching)

Uncomment in `docker-compose.yml`:
```yaml
redis:
  image: redis:7-alpine
  # ... (already configured)
```

Then set environment:
```yaml
environment:
  - REDIS_URL=redis://redis:6379/0
```

### Enable PostgreSQL (for production)

Uncomment in `docker-compose.yml`:
```yaml
postgres:
  image: postgres:15-alpine
  # ... (already configured)
```

Then set environment:
```yaml
environment:
  - DATABASE_URL=postgresql://shoghi:shoghi_password@postgres:5432/shoghi
```

## 🧪 Running Tests

```bash
# Run all tests
docker-compose exec shoghi pytest -v

# Run specific test file
docker-compose exec shoghi pytest test_adaptive_tools.py -v

# Run tests with coverage
docker-compose exec shoghi pytest --cov=. --cov-report=html

# Run tests on container startup
docker-compose up -d -e RUN_TESTS=true
```

## 📊 Monitoring

### View Container Stats
```bash
docker stats shoghi-platform
```

### Check Logs
```bash
# Application logs
docker-compose exec shoghi cat /app/logs/web_server.log

# Container logs
docker-compose logs shoghi

# Follow logs in real-time
docker-compose logs -f
```

### Inspect Container
```bash
# View container details
docker inspect shoghi-platform

# View network settings
docker network inspect shoghi_shoghi-network
```

## 🔒 Security Best Practices

1. **Environment Variables**: Never commit API keys to git
   ```bash
   # Create .env file for secrets
   echo "GRANTS_GOV_API_KEY=your_key" > .env
   # Add .env to .gitignore
   ```

2. **Network Isolation**: Use custom networks
   ```bash
   docker network create shoghi-private
   ```

3. **User Permissions**: Run as non-root (add to Dockerfile)
   ```dockerfile
   RUN useradd -m -u 1000 shoghi
   USER shoghi
   ```

4. **Volume Permissions**: Set correct ownership
   ```bash
   docker-compose exec shoghi chown -R 1000:1000 /app/data
   ```

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker-compose logs shoghi

# Verify image built correctly
docker images | grep shoghi

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Memory issues
```bash
# Increase memory limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G  # Increase from 2G
```

### Can't connect to database
```bash
# Check if database file exists
docker-compose exec shoghi ls -la /app/shoghi_grants.db

# Reset database
docker-compose exec shoghi rm /app/shoghi_grants.db
docker-compose restart shoghi
```

## 📝 Custom Builds

### Build with specific tag
```bash
docker build -t shoghi/platform:v1.0 .
```

### Build for different architectures
```bash
# AMD64 (default)
docker build --platform linux/amd64 -t shoghi/platform:amd64 .

# ARM64 (for Apple Silicon)
docker build --platform linux/arm64 -t shoghi/platform:arm64 .

# Multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t shoghi/platform:latest .
```

## 🚢 Deployment

### Production Deployment

1. **Use environment file**:
   ```bash
   docker-compose --env-file .env.production up -d
   ```

2. **Enable all services**:
   - Uncomment Redis and PostgreSQL in docker-compose.yml
   - Set strong passwords
   - Configure backups

3. **Use reverse proxy** (nginx/traefik):
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.shoghi.rule=Host(`shoghi.yourdomain.com`)"
   ```

4. **Enable SSL/TLS**:
   - Use Let's Encrypt with Traefik
   - Or configure nginx with certbot

## 📈 Scaling

```bash
# Run multiple instances
docker-compose up -d --scale shoghi=3

# Use with load balancer
# Add nginx/haproxy configuration
```

## 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Or use watchtower for auto-updates
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  containrrr/watchtower \
  --interval 3600 \
  shoghi-platform
```

## 📞 Support

- Documentation: See README.md
- Issues: https://github.com/ohana-garden/shoghi/issues
- Tests: Run `pytest -v` in container

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `docker-compose up -d` | Start services |
| `docker-compose down` | Stop services |
| `docker-compose logs -f` | View logs |
| `docker-compose exec shoghi bash` | Shell access |
| `docker-compose restart` | Restart services |
| `docker-compose ps` | Service status |
| `docker-compose pull` | Update images |
| `docker-compose build` | Rebuild image |

---

**Ready to launch?** Just run: `docker-compose up -d` 🚀
