# Quick Start Guide - Using the Fixes

This guide shows you how to immediately start using all the applied fixes.

---

## 1. ONE-COMMAND SETUP

```bash
# Install dependencies
pip install -r requirements-fixed.txt

# Set up environment
cp .env.example .env
# Edit .env and change JWT_SECRET_KEY to a secure random string

# Run migrations
python -c "from vessels.database.migrations import run_migrations; run_migrations('data/vessels.db')"

# Start fixed web server
python vessels_web_server_fixed.py
```

---

## 2. DOCKER QUICK START

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.fixed.yml up --build

# Access:
# - API: http://localhost:5000
# - Health: http://localhost:8080/health
# - Metrics: http://localhost:9090/metrics
```

---

## 3. TEST AUTHENTICATION

```bash
# Login (get JWT token)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "pass"}'

# Response:
{
  "success": true,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}

# Use token for authenticated requests
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## 4. CHECK HEALTH

```bash
# Kubernetes liveness probe
curl http://localhost:8080/health

# Response:
{
  "status": "healthy",
  "timestamp": "2025-01-23T12:00:00Z",
  "duration_ms": 15.2,
  "checks": [
    {"name": "database", "status": "healthy", ...},
    {"name": "redis", "status": "healthy", ...},
    {"name": "sessions", "status": "healthy", ...}
  ]
}
```

---

## 5. VIEW METRICS

```bash
# Prometheus-formatted metrics
curl http://localhost:9090/metrics

# Response:
# HELP requests_total Total HTTP requests
# TYPE requests_total counter
requests_total 1542.0

# HELP request_duration_seconds HTTP request duration
# TYPE request_duration_seconds histogram
request_duration_seconds_sum 125.3
request_duration_seconds_count 1542
```

---

## 6. USE SECURE SESSIONS

```python
from vessels.auth.session_manager import SessionManager

# Create session manager
sessions = SessionManager(
    max_sessions=10000,
    ttl_seconds=3600  # 1 hour expiration
)

# Create session
session_id = sessions.create_session(user_id="user-123")

# Add context
sessions.add_context(session_id, "User asked about grants")

# Get session
session = sessions.get_session(session_id)
print(session['context'])  # ['User asked about grants']

# Sessions automatically expire after 1 hour
```

---

## 7. USE DATABASE CONNECTION POOL

```python
from vessels.database import get_connection

# Thread-safe connection access
with get_connection("data/vessels.db") as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vessels WHERE name = ?", (name,))
    results = cursor.fetchall()

# Connection automatically returned to pool
```

---

## 8. USE METRICS DECORATORS

```python
from vessels.monitoring import track_time, track_count

@track_time('memory_search_duration_seconds')
@track_count('memory_searches_total')
def search_memories(query):
    # Function implementation
    return results

# Automatically tracks execution time and call count
```

---

## 9. REGISTER HEALTH CHECKS

```python
from vessels.monitoring import register_health_check

@register_health_check('my_service')
def check_my_service():
    try:
        # Test service connectivity
        service.ping()
        return True, "Service OK"
    except Exception as e:
        return False, f"Service error: {e}"

# Automatically included in /health endpoint
```

---

## 10. ENABLE PRE-COMMIT HOOKS

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Now every commit will automatically:
# - Format code with black
# - Sort imports with isort
# - Run linters
# - Check for secrets
# - Validate YAML files
```

---

## 11. RUN TESTS WITH CI/CD

GitHub Actions will automatically run on every push:

```bash
git add .
git commit -m "Apply comprehensive fixes"
git push origin claude/vessels-codebase-review-011jyoPnyXAjAimgvhSBQK8f

# GitHub Actions will:
# ✓ Run linting
# ✓ Run type checking
# ✓ Run security scans
# ✓ Run test suite
# ✓ Build Docker image
# ✓ Deploy to staging (if on develop branch)
```

---

## 12. KEY CONFIGURATION OPTIONS

Edit `.env` to configure:

```bash
# Security
JWT_SECRET_KEY=your-secure-random-string-here
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Database
VESSELS_DB_PATH=data/vessels.db
REDIS_HOST=localhost
REDIS_PORT=6379

# Performance
MAX_WORKERS=50
ENABLE_CACHING=true
CACHE_TTL_SECONDS=300

# Observability
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=false  # true for production
ENABLE_METRICS=true
```

---

## 13. MIGRATION FROM OLD CODE

If you have existing code using the old patterns:

### Before (UNSAFE):
```python
# Old pattern
sessions = {}  # Global dict
session_id = request.json.get('session_id', 'default')
sessions[session_id] = {...}
```

### After (SAFE):
```python
# New pattern
from vessels.auth.session_manager import SessionManager

session_manager = SessionManager()
session_id = session_manager.create_session(user_id)
session = session_manager.get_session(session_id)
```

### Before (SLOW):
```python
# Old pattern - event loop per request
loop = asyncio.new_event_loop()
result = loop.run_until_complete(async_function())
```

### After (FAST):
```python
# New pattern - use sync or proper async framework
result = sync_function()  # Or migrate to FastAPI for native async
```

---

## 14. VERIFY FIXES APPLIED

```bash
# Check database has indexes
python -c "
from vessels.database import get_connection
with get_connection('data/vessels.db') as conn:
    cursor = conn.cursor()
    cursor.execute('PRAGMA index_list(memories)')
    print('Indexes:', cursor.fetchall())
"

# Check foreign keys enabled
python -c "
from vessels.database import get_connection
with get_connection('data/vessels.db') as conn:
    cursor = conn.cursor()
    cursor.execute('PRAGMA foreign_keys')
    result = cursor.fetchone()[0]
    print('Foreign keys:', 'ENABLED' if result == 1 else 'DISABLED')
"

# Check dependencies updated
python -c "import torch; print('PyTorch:', torch.__version__)"
python -c "import transformers; print('Transformers:', transformers.__version__)"
```

---

## 15. COMMON ISSUES & SOLUTIONS

### Issue: `ModuleNotFoundError: No module named 'vessels.auth'`
**Solution**: Install updated dependencies:
```bash
pip install -r requirements-fixed.txt
```

### Issue: `ValueError: JWT_SECRET_KEY must be changed in production`
**Solution**: Set environment variable:
```bash
export JWT_SECRET_KEY="your-secure-random-string-at-least-32-chars"
```

### Issue: Database locked
**Solution**: Connection pool fixes this. If using old code, migrate to:
```python
from vessels.database import get_connection
```

### Issue: 401 Unauthorized on all endpoints
**Solution**: All endpoints now require authentication. Get token first:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "password"}'
```

---

## 16. WHAT TO DO NEXT

1. **Test the fixed web server**:
   ```bash
   python vessels_web_server_fixed.py
   ```

2. **Set up monitoring**:
   - Open http://localhost:9090/metrics
   - View Prometheus metrics
   - Set up Grafana dashboards (optional)

3. **Run security scans**:
   ```bash
   pip install bandit safety
   bandit -r vessels/
   safety check
   ```

4. **Enable CI/CD**:
   - Push to GitHub
   - Check Actions tab for pipeline runs
   - Fix any test failures

5. **Deploy to staging**:
   ```bash
   docker-compose -f docker-compose.fixed.yml up -d
   ```

---

## SUCCESS INDICATORS

✅ Web server starts without errors
✅ `/health` returns `{"status": "healthy"}`
✅ `/metrics` shows Prometheus metrics
✅ Authentication works (get JWT token)
✅ Database queries use indexes (check with EXPLAIN)
✅ Pre-commit hooks run on commit
✅ CI/CD pipeline passes all checks

**You're ready to go!** 🚀
