# FalkorDB Deployment Guide

**Version:** 1.0
**Date:** 2025-11-22
**Status:** Production Ready

---

## Overview

Vessels now uses **FalkorDB** (a Redis-compatible graph database) as the primary backend for:
- Community memory storage
- Phase space state tracking
- Agent trajectory analysis
- Knowledge graph operations

This guide covers installation, configuration, and deployment.

---

## Prerequisites

- Docker (recommended) or Redis-compatible server
- Python 3.9+
- 2GB+ RAM for FalkorDB
- Network access to port 6379 (default)

---

## Quick Start (Docker)

### 1. Install FalkorDB

```bash
# Pull FalkorDB image
docker pull falkordb/falkordb:latest

# Run FalkorDB
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  -v /data/falkordb:/data \
  --restart unless-stopped \
  falkordb/falkordb:latest
```

### 2. Verify Installation

```bash
# Check container is running
docker ps | grep falkordb

# Test connectivity
redis-cli PING
# Expected output: PONG
```

### 3. Install Python Dependencies

```bash
cd /path/to/Vessels
pip install -r requirements.txt
```

Required packages:
- `graphiti-core==0.3.5`
- `falkordb==4.0.11`
- `redis==5.0.1`
- `sentence-transformers==2.2.2`

### 4. Test Graphiti Connection

```bash
python3 << 'EOF'
from vessels.knowledge.graphiti_client import VesselsGraphitiClient

client = VesselsGraphitiClient(
    community_id="test",
    host="localhost",
    port=6379
)

if client.health_check():
    print("✓ FalkorDB connection successful!")
else:
    print("✗ FalkorDB connection failed")
EOF
```

---

## Production Deployment

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  falkordb:
    image: falkordb/falkordb:latest
    container_name: vessels_falkordb
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
    environment:
      - FALKORDB_MAX_MEMORY=4gb
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  vessels:
    build: .
    depends_on:
      - falkordb
    environment:
      - FALKORDB_HOST=falkordb
      - FALKORDB_PORT=6379
      - COMMUNITY_ID=your_community
    volumes:
      - ./work_dir:/app/work_dir
    restart: unless-stopped

volumes:
  falkordb_data:
```

Deploy:

```bash
docker-compose up -d
```

### Configuration

Set environment variables:

```bash
# FalkorDB connection
export FALKORDB_HOST=localhost
export FALKORDB_PORT=6379

# Community configuration
export COMMUNITY_ID=lower_puna_elders

# Optional: Enable mock mode for testing without FalkorDB
export VESSELS_GRAPHITI_ALLOW_MOCK=1
```

---

## Usage Examples

### Initialize with FalkorDB

```python
from community_memory import CommunityMemory
from vessels.phase_space.tracker import TrajectoryTracker
from vessels.knowledge.graphiti_client import VesselsGraphitiClient

# Option 1: Let CommunityMemory create client automatically
memory = CommunityMemory(
    backend="graphiti",  # Default in Phase 2
    community_id="lower_puna_elders"
)

# Option 2: Provide your own Graphiti client
graphiti = VesselsGraphitiClient(
    community_id="lower_puna_elders",
    host="localhost",
    port=6379
)
memory = CommunityMemory(
    backend="graphiti",
    graphiti_client=graphiti
)

# Phase space tracker
tracker = TrajectoryTracker(
    backend="graphiti",
    community_id="lower_puna_elders"
)
```

### Store and Query Data

```python
# Store experience in graph
memory.store_experience(
    agent_id="transport_servant_1",
    experience={
        "action": "coordinated_pickup",
        "outcome": "success",
        "tags": ["transport", "medical"]
    }
)

# Query using semantic search
results = memory.graphiti_backend.query_memories(
    query="transport coordination",
    limit=5
)

# Store phase space state
from vessels.measurement.state import PhaseSpaceState
from vessels.measurement.dimensions import OperationalDimensions, VirtueDimensions

state = PhaseSpaceState(
    agent_id="servant_1",
    timestamp=datetime.utcnow(),
    operational=OperationalDimensions(
        activity=0.8,
        coordination=0.7,
        effectiveness=0.9,
        resource_consumption=0.3,
        system_health=0.95
    ),
    virtue=VirtueDimensions(
        truthfulness=0.85,
        justice=0.8,
        trustworthiness=0.9,
        unity=0.75,
        service=0.95,
        detachment=0.7,
        understanding=0.8
    )
)

tracker.store_state(state)
```

---

## Performance Tuning

### FalkorDB Configuration

Edit Redis configuration for optimal performance:

```bash
# Create falkordb.conf
cat > falkordb.conf <<EOF
# Memory management
maxmemory 4gb
maxmemory-policy allkeys-lru

# Persistence (RDB snapshots)
save 900 1      # Save after 15 min if 1+ key changed
save 300 10     # Save after 5 min if 10+ keys changed
save 60 10000   # Save after 1 min if 10k+ keys changed

# Database file
dir /data
dbfilename vessels_graph.rdb

# Performance
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Logging
loglevel notice
logfile /var/log/falkordb/falkordb.log
EOF

# Run with custom config
docker run -d \
  --name falkordb \
  -p 6379:6379 \
  -v /data/falkordb:/data \
  -v $(pwd)/falkordb.conf:/etc/falkordb.conf \
  falkordb/falkordb:latest \
  redis-server /etc/falkordb.conf
```

### Query Optimization

```python
# Use indexes for common queries
# FalkorDB automatically indexes graph nodes

# Limit query depth for performance
neighbors = graphiti.get_neighbors(
    node_id="agent_123",
    max_depth=2  # Don't traverse too deep
)

# Use lookback windows for temporal queries
trajectory = tracker.graphiti_tracker.get_trajectory(
    agent_id="servant_1",
    lookback_days=7  # Only last week
)
```

---

## Backup and Recovery

### Automatic RDB Backups

FalkorDB creates RDB snapshots automatically based on configuration.

```bash
# Manual backup
docker exec falkordb redis-cli SAVE

# Copy backup
docker cp falkordb:/data/vessels_graph.rdb ./backups/
```

### JSON Export (Recommended)

```python
from vessels.knowledge.backup import GraphBackupManager

# Export entire graph to JSON
backup_mgr = GraphBackupManager()
backup_mgr.export_community_graph(
    community_id="lower_puna_elders",
    output_dir="./backups/2025-11-22/"
)
```

### Restore from Backup

```bash
# Stop FalkorDB
docker stop falkordb

# Replace RDB file
docker cp ./backups/vessels_graph.rdb falkordb:/data/

# Restart
docker start falkordb
```

Or restore from JSON:

```python
backup_mgr.restore_from_backup("./backups/2025-11-22/lower_puna_elders_graph.json")
```

---

## Monitoring

### Health Checks

```python
from vessels.knowledge.graphiti_client import VesselsGraphitiClient

client = VesselsGraphitiClient(community_id="test")

# Check connection
if client.health_check():
    print("✓ FalkorDB is healthy")
else:
    print("✗ FalkorDB is down")
```

### Metrics

```bash
# FalkorDB info
redis-cli INFO

# Graph statistics
redis-cli GRAPH.QUERY "lower_puna_elders_graph" "MATCH (n) RETURN count(n)"

# Memory usage
redis-cli INFO memory
```

### Logs

```bash
# Docker logs
docker logs falkordb -f

# Log file (if configured)
tail -f /var/log/falkordb/falkordb.log
```

---

## Troubleshooting

### Issue: "Module not found: graphiti-core"

```bash
pip install graphiti-core==0.3.5
```

### Issue: "Connection refused on port 6379"

```bash
# Check if FalkorDB is running
docker ps | grep falkordb

# Check port binding
netstat -tuln | grep 6379

# Restart FalkorDB
docker restart falkordb
```

### Issue: "Mock client being used"

This happens when FalkorDB is unavailable. Check:

```python
import os
os.environ.get("VESSELS_GRAPHITI_ALLOW_MOCK")  # Should be None or 0
```

Ensure FalkorDB is running:

```bash
docker start falkordb
redis-cli PING  # Should return PONG
```

### Issue: High memory usage

```bash
# Check memory
redis-cli INFO memory

# Set max memory
redis-cli CONFIG SET maxmemory 4gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Or restart with config file
```

---

## Migration from SQLite (If Needed)

If you have existing SQLite data to migrate:

```python
# Enable hybrid mode temporarily
memory = CommunityMemory(
    backend="hybrid",  # Writes to both
    community_id="your_community"
)

# New data will be written to both backends
# Old SQLite data can be queried via:
memory.backend_type = "sqlite"
old_data = memory.search_memories("query")

# Then switch to Graphiti only:
memory = CommunityMemory(
    backend="graphiti",
    community_id="your_community"
)
```

---

## Security

### Network Security

```bash
# Bind to localhost only (development)
redis-cli CONFIG SET bind "127.0.0.1"

# Use authentication (production)
redis-cli CONFIG SET requirepass "your_strong_password"
```

Update client:

```python
client = VesselsGraphitiClient(
    community_id="your_community",
    host="localhost",
    port=6379,
    password="your_strong_password"  # Add to VesselsGraphitiClient if needed
)
```

### Firewall Rules

```bash
# Only allow localhost (development)
sudo ufw allow from 127.0.0.1 to any port 6379

# Allow specific IPs (production)
sudo ufw allow from 192.168.1.0/24 to any port 6379
```

---

## Off-Grid Deployment

For solar-powered or resource-constrained environments:

### Low-Power Configuration

```bash
# Reduce memory footprint
maxmemory 512mb
maxmemory-policy allkeys-lru

# Less aggressive persistence
save 3600 1     # Save every hour
appendonly no   # Disable AOF for lower I/O
```

### Battery-Aware Operation

```python
# Batch writes when solar power available
if battery_level > 0.5:
    memory.backend_type = "graphiti"  # Write to graph
else:
    memory.backend_type = "sqlite"  # Low-power fallback
```

---

## Next Steps

1. **Deploy FalkorDB**: `docker-compose up -d`
2. **Verify Connection**: Run health check
3. **Initialize Community**: Set `COMMUNITY_ID`
4. **Start Vessels**: All memory operations now use FalkorDB
5. **Monitor**: Check logs and metrics

---

## Resources

- **FalkorDB Docs**: https://docs.falkordb.com/
- **Graphiti Docs**: https://github.com/getzep/graphiti
- **Vessels Implementation Plan**: `IMPLEMENTATION_PLAN.md`
- **Phase 2 Completion**: `PHASE_2_COMPLETE.md`

---

**Deployment Checklist:**
- [ ] FalkorDB installed and running
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Health check passes
- [ ] Community ID configured
- [ ] Backup strategy in place
- [ ] Monitoring enabled
- [ ] Security configured (firewall, auth)

---

**Prepared By:** Claude Code
**Date:** 2025-11-22
**Status:** Production Ready
