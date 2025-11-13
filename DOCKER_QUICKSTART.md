# 🚀 One-Click Docker Launch - Shoghi Platform

The easiest way to run Shoghi Platform with everything pre-configured.

## ⚡ Super Quick Start (3 Commands)

```bash
git clone https://github.com/ohana-garden/shoghi.git
cd shoghi
./quick-start.sh
```

**That's it!** The platform will be running at http://localhost:5000

## 🎯 Alternative Methods

### Method 1: Quick Start Script (Recommended)
```bash
./quick-start.sh
```
The script will:
- ✅ Check prerequisites
- ✅ Build Docker image
- ✅ Start all services
- ✅ Open browser automatically

### Method 2: Docker Compose
```bash
docker-compose up -d
```
Manual but gives you more control.

### Method 3: Makefile (Power Users)
```bash
make quick
```
Builds, starts, and opens browser in one command.

## 📦 What You Get

The Docker container includes **EVERYTHING**:

### ✅ Pre-Installed Components
- **Python 3.11** with all dependencies
- **Agent Zero** - Meta-coordination engine
- **Shoghi Platform** - Complete codebase
- **Test Suites** - All 168 tests
- **BMAD Agents** - Pre-configured agents
- **Web Server** - Flask with voice UI
- **Database** - SQLite initialized
- **Dependencies** - numpy, pandas, flask, etc.

### ✅ Pre-Configured Features
- Web UI on port 5000
- Voice-first interface
- API endpoints ready
- Health checks enabled
- Auto-restart on failure
- Log rotation
- Data persistence

## 🎮 Easy Management

### With Makefile (Easiest)

```bash
make up        # Start everything
make down      # Stop everything
make logs      # View logs
make test      # Run tests
make shell     # Access container
make help      # See all commands
```

### With Docker Compose

```bash
docker-compose up -d      # Start
docker-compose down       # Stop
docker-compose logs -f    # View logs
docker-compose restart    # Restart
```

### With Scripts

```bash
./quick-start.sh          # Start with wizard
./quick-start.sh --rebuild # Rebuild from scratch
```

## 🔧 Configuration

### Set API Keys

Edit `docker-compose.yml`:
```yaml
environment:
  - GRANTS_GOV_API_KEY=your_key_here
  - FOUNDATION_CENTER_API_KEY=your_key_here
```

### Change Ports

Edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"  # Access on port 8080
```

### Enable Testing on Startup

Edit `docker-compose.yml`:
```yaml
environment:
  - RUN_TESTS=true
```

## 📊 Verify Installation

### Check Status
```bash
docker-compose ps
# Should show "Up" status

make status
# Shows detailed status
```

### Run Tests
```bash
make test
# Runs all 168 tests

docker-compose exec shoghi pytest -v
# Same thing, more verbose
```

### View Logs
```bash
make logs
# Live log stream

docker-compose logs --tail=100
# Last 100 lines
```

## 🛠️ Common Tasks

### Access Container Shell
```bash
make shell
# or
docker-compose exec shoghi bash
```

### Run Python Commands
```bash
docker-compose exec shoghi python3 -c "import shoghi; print('OK')"
```

### Backup Database
```bash
make backup
# Saves to backups/ directory
```

### Update Platform
```bash
make update
# Pulls latest code and restarts
```

## 🐛 Troubleshooting

### Container Won't Start

**Problem**: Container exits immediately
```bash
# Check logs
docker-compose logs shoghi

# Rebuild from scratch
make rebuild
```

**Problem**: Port 5000 already in use
```bash
# Find what's using it
lsof -i :5000

# Or change port in docker-compose.yml
ports:
  - "8080:5000"
```

### Can't Access Web UI

**Check if running**:
```bash
docker-compose ps
```

**Check health**:
```bash
docker inspect --format='{{.State.Health.Status}}' shoghi-platform
```

**Restart**:
```bash
docker-compose restart
```

### Tests Failing

**Run with verbose output**:
```bash
docker-compose exec shoghi pytest -v --tb=long
```

**Check dependencies**:
```bash
docker-compose exec shoghi pip list
```

## 🔒 Security

### Production Deployment

1. **Use environment file for secrets**:
   ```bash
   # Create .env file
   echo "GRANTS_GOV_API_KEY=secret" > .env
   echo ".env" >> .gitignore
   ```

2. **Enable HTTPS** (add reverse proxy):
   - Use nginx or traefik
   - Configure SSL certificates
   - Add to docker-compose.yml

3. **Set resource limits** (already configured):
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 2G
   ```

## 📁 Data Persistence

Data is automatically persisted in Docker volumes:

- **shoghi-data** - Application data
- **shoghi-logs** - Log files
- **./shoghi_grants.db** - Database (bind mount)
- **./.bmad** - Agent configs (bind mount)

### Backup Data
```bash
make backup
```

### Restore Data
```bash
make restore BACKUP=backups/shoghi_grants_20241113.db
```

## 🌐 Network Configuration

### Custom Network
The container uses `shoghi-network` by default.

### Access from Another Container
```bash
docker run --network shoghi_shoghi-network your-image
```

### Expose to Network
Edit `docker-compose.yml`:
```yaml
ports:
  - "0.0.0.0:5000:5000"  # Listen on all interfaces
```

## 🚀 Advanced Usage

### Enable Redis
Uncomment in `docker-compose.yml`:
```yaml
redis:
  image: redis:7-alpine
  ...
```

### Enable PostgreSQL
Uncomment in `docker-compose.yml`:
```yaml
postgres:
  image: postgres:15-alpine
  ...
```

### Scale Services
```bash
make scale INSTANCES=3
# Runs 3 instances with load balancing
```

### Development Mode
```bash
make dev
# Runs with live logs in foreground
```

### Production Mode
```bash
make prod
# Optimized for production
```

## 📚 Documentation

- **Full Docker Guide**: See [DOCKER_README.md](DOCKER_README.md)
- **Platform Docs**: See [README.md](README.md)
- **Architecture**: See [SHOGHI_COMPLETE.md](SHOGHI_COMPLETE.md)

## ✨ Tips & Tricks

### Quick Access Aliases

Add to your `~/.bashrc` or `~/.zshrc`:
```bash
alias shoghi-up='cd ~/shoghi && docker-compose up -d'
alias shoghi-down='cd ~/shoghi && docker-compose down'
alias shoghi-logs='cd ~/shoghi && docker-compose logs -f'
alias shoghi-shell='cd ~/shoghi && docker-compose exec shoghi bash'
alias shoghi-test='cd ~/shoghi && docker-compose exec shoghi pytest -v'
```

### Auto-Start on Boot

Add to systemd or cron:
```bash
@reboot cd /path/to/shoghi && docker-compose up -d
```

### Monitor Resources
```bash
watch -n 2 'docker stats shoghi-platform --no-stream'
```

## 🎉 Success!

If you see this, you're ready:
```
✓ Shoghi Platform installed and running!
Access at: http://localhost:5000
```

## 🆘 Need Help?

1. Check logs: `make logs`
2. Run tests: `make test`
3. View status: `make status`
4. Read docs: [DOCKER_README.md](DOCKER_README.md)
5. Open issue: https://github.com/ohana-garden/shoghi/issues

---

**Remember**: Just run `./quick-start.sh` and you're good to go! 🌺
