# FalkorDB Integration - Maximum Off-Device Processing

This document describes the comprehensive FalkorDB integration in Vessels, designed to maximize off-device processing and minimize local storage footprint.

## Overview

FalkorDB is now the **default storage and processing backend** for all Vessels components. This architectural shift moves data and computation from local devices to a graph database, enabling:

- **Persistent storage** - All data survives restarts
- **Semantic relationships** - Graph-native queries for pattern discovery
- **Scalability** - Handles large datasets with efficient graph algorithms
- **Multi-device sync** - Shared graph accessible from multiple devices
- **Rich analytics** - Built-in graph traversal and pattern matching

## Architecture

### Graph Namespaces

The integration uses multiple graph namespaces for different data domains:

| Graph | Purpose | Nodes | Relationships |
|-------|---------|-------|---------------|
| `vessels_sessions` | User session tracking | Session, User, Interaction, Agent | HAS_SESSION, HAS_INTERACTION, WITH_AGENT |
| `vessels_phase_space` | Agent state trajectories | AgentState, Servant, Constraint, SecurityEvent | HAS_STATE, TRANSITIONS_TO, VIOLATED |
| `vessels_memory` | Community memory | MemoryEntry, Servant, Person, Community | REMEMBERS, RELATES_TO, FOR_PERSON |
| `vessels_kala` | Contribution network | Contribution, Person, Community | MADE_CONTRIBUTION, RECEIVED_BY, IN_COMMUNITY |
| `vessels_commercial` | Commercial agent tracking | CommercialAgent, Organization, RevenueRecord | REPRESENTS, GENERATED_REVENUE, INTERACTED_WITH |
| `vessels_grants` | Grant discovery | Grant, Person, Capability, Application | MATCHES, REQUIRES, HAS, FOR |

### Component Modules

#### 1. Session Management (`vessels/storage/session.py`)
**Class**: `FalkorDBSessionStore`

Stores user sessions as graph nodes with relationships:
```cypher
(user:User) -[HAS_SESSION]-> (session:Session)
(session) -[HAS_INTERACTION]-> (interaction:Interaction)
(interaction) -[WITH_AGENT]-> (agent:Agent)
```

**Key Features**:
- Automatic TTL enforcement
- User-session relationship tracking
- Interaction history persistence

**Example Usage**:
```python
from vessels.database.falkordb_client import get_falkordb_client
from vessels.storage.session import FalkorDBSessionStore

client = get_falkordb_client()
store = FalkorDBSessionStore(client, ttl_seconds=3600)

# Create session
store.create_session("session_123", {"user_id": "user_456", "context": []})

# Record interaction
store.record_interaction(
    "session_123",
    agent_type="ElderCareSpecialist",
    request_data={"query": "help with medication"},
    response_data={"recommendation": "..."},
    emotion="positive"
)

# Retrieve session
session = store.get_session("session_123")
```

#### 2. Phase Space Tracking (`vessels/phase_space/falkordb_tracker.py`)
**Class**: `FalkorDBPhaseSpaceTracker`

Tracks agent behavior through 12D phase space:
```cypher
(agent:Servant) -[HAS_STATE]-> (state:AgentState {12D vector})
(state1) -[TRANSITIONS_TO {action_hash}]-> (state2)
(state) -[VIOLATED]-> (constraint:Constraint)
```

**Key Features**:
- Trajectory analysis
- Constraint violation pattern detection
- Attractor discovery and persistence
- Behavioral classification

**Example Queries**:
```python
tracker = FalkorDBPhaseSpaceTracker(client)

# Record state transition
tracker.record_transition(
    agent_id="servant_123",
    from_state=current_state,
    to_state=new_state,
    action_hash="abc123",
    gating_result="allowed"
)

# Find constraint violation patterns
patterns = tracker.find_constraint_violation_patterns(
    lookback_days=30,
    min_co_occurrences=3
)
# Returns: [{"constraint1": "Truthfulness", "constraint2": "Justice", "co_violations": 5}]

# Find frequent violators
violators = tracker.find_frequent_violators(
    constraint_name="Unity",
    min_violations=5
)
```

#### 3. Community Memory (`vessels/memory/falkordb_memory.py`)
**Class**: `FalkorDBCommunityMemory`

Semantic memory graph with typed relationships:
```cypher
(servant:Servant) -[REMEMBERS {confidence}]-> (memory:MemoryEntry)
(memory1) -[RELATES_TO {type: "causation"}]-> (memory2)
(memory) -[FOR_PERSON]-> (person:Person)
```

**Relationship Types**:
- `causation` - A caused B
- `similarity` - A is similar to B
- `temporal` - A happened before B
- `contradiction` - A contradicts B
- `generalization` - B generalizes A
- `solution` - B solves problem A

**Example Usage**:
```python
memory = FalkorDBCommunityMemory(client)

# Store memory
memory.store_memory(
    memory_id="mem_123",
    memory_type=MemoryType.EXPERIENCE,
    content={"event": "delivered groceries", "outcome": "successful"},
    agent_id="servant_123",
    person_id="person_456",
    tags=["delivery", "groceries"]
)

# Link memories
memory.link_memories(
    from_memory_id="mem_123",
    to_memory_id="mem_124",
    relationship_type=RelationshipType.CAUSATION,
    strength=0.9
)

# Find related memories
related = memory.find_related_memories(
    memory_id="mem_123",
    relationship_types=[RelationshipType.CAUSATION, RelationshipType.SOLUTION],
    max_depth=3
)

# Find patterns
patterns = memory.find_patterns(
    community_id="ohana_main",
    min_occurrences=3
)
```

#### 4. Kala Contribution Network (`kala/falkordb_kala.py`)
**Class**: `FalkorDBKalaNetwork`

Value flow tracking and reciprocity analysis:
```cypher
(person1:Person) -[MADE_CONTRIBUTION {value}]-> (contribution:Contribution)
(contribution) -[RECEIVED_BY]-> (person2:Person)
(contribution) -[IN_COMMUNITY]-> (community:Community)
```

**Example Usage**:
```python
kala = FalkorDBKalaNetwork(client)

# Record contribution
kala.record_contribution(
    contribution_id="contrib_123",
    contributor_id="person_456",
    recipient_id="person_789",
    contribution_type=ContributionType.TIME,
    description="Helped with garden",
    kala_value=5.0,
    usd_equivalent=5.00,
    community_id="ohana_main"
)

# Find highly connected contributors
contributors = kala.find_highly_connected_contributors(
    community_id="ohana_main",
    min_connections=5
)

# Analyze reciprocity
reciprocity = kala.analyze_reciprocity("person_456", "person_789")
# Returns: {"person1_to_person2": 10.0, "person2_to_person1": 8.0, "balance": 2.0}

# Get community value flow
flow = kala.get_community_value_flow("ohana_main", lookback_days=30)
# Returns: {"types": [...], "total_kala": 150.0, "total_usd": 150.00}
```

#### 5. Commercial Agent Tracking (`vessels/agents/graph_tracking.py`)
**Class**: `CommercialRelationshipGraph`

Transparent commercial activity tracking:
```cypher
(servant:Servant) -[INTRODUCED]-> (commercial:CommercialAgent)
(commercial) -[INTERACTED_WITH]-> (user:Person)
(user) -[CONSENTED_TO]-> (commercial)
(interaction) -[GENERATED_REVENUE]-> (revenue:RevenueRecord)
```

**Example Usage**:
```python
tracker = CommercialRelationshipGraph(client)

# Register commercial agent
tracker.register_commercial_agent(
    agent_id="commercial_123",
    company="Example Corp",
    compensation_model="per_transaction",
    agent_class="commercial",
    expertise=["insurance", "healthcare"],
    community_id="ohana_main"
)

# Record introduction
tracker.record_commercial_introduction(
    servant_id="servant_123",
    commercial_agent_id="commercial_123",
    user_id="user_456",
    query="need health insurance",
    relevance_score=0.85,
    user_consented=True,
    timestamp=datetime.now(),
    community_id="ohana_main"
)

# Query commercial influence
influence = tracker.query_commercial_influence("user_456", time_window_days=30)
```

#### 6. Grants Discovery (`grants/falkordb_grants.py`)
**Class**: `FalkorDBGrantsDiscovery`

Intelligent grant matching:
```cypher
(grant:Grant) -[MATCHES {score}]-> (person:Person)
(grant) -[REQUIRES {mandatory}]-> (capability:Capability)
(person) -[HAS {level}]-> (capability)
```

**Example Usage**:
```python
grants = FalkorDBGrantsDiscovery(client)

# Register grant
grants.register_grant(
    grant_id="grant_123",
    title="Community Garden Funding",
    description="...",
    funder="Green Foundation",
    amount=50000.0,
    deadline=datetime(2025, 12, 31),
    required_capabilities=[
        {"name": "gardening", "level": "intermediate"},
        {"name": "project_management", "level": "advanced"}
    ]
)

# Register person capabilities
grants.register_person_capability("person_456", "gardening", "expert")
grants.register_person_capability("person_456", "project_management", "advanced")

# Find matching grants
matches = grants.find_matching_grants("person_456", min_match_score=0.7)
# Returns: [{"grant_id": "grant_123", "match_score": 0.95, ...}]

# Get application pipeline
pipeline = grants.get_application_pipeline("person_456")
# Returns: {"draft": [...], "submitted": [...], "approved": [...]}
```

## Configuration

### Environment Variables

Add to `.env`:
```bash
# FalkorDB Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# For FalkorDB Cloud
# REDIS_HOST=your-instance.falkordb.cloud
# REDIS_PORT=6379
# REDIS_PASSWORD=your-password
```

### Docker Setup

FalkorDB is already configured in `docker-compose.yml`:

```yaml
falkordb:
  image: falkordb/falkordb:latest
  ports:
    - "6379:6379"
  volumes:
    - falkordb-data:/data
```

Start with:
```bash
docker-compose up -d falkordb
```

### System Initialization

```python
from vessels.system import VesselsSystem

# FalkorDB-first mode (default)
system = VesselsSystem(
    use_falkordb=True,              # Enable FalkorDB (default)
    session_store_type="falkordb",  # Use FalkorDB sessions (default)
    enable_gating=True              # Enable moral constraints
)

# Access components
system.phase_space_tracker     # FalkorDBPhaseSpaceTracker
system.community_memory        # FalkorDBCommunityMemory
system.kala_network           # FalkorDBKalaNetwork
system.commercial_tracker     # CommercialRelationshipGraph
system.grants_discovery       # FalkorDBGrantsDiscovery

# Fallback to in-memory mode
system = VesselsSystem(use_falkordb=False)
```

## Performance Optimizations

### Indexes

Indexes are automatically created on initialization:

```cypher
// Session lookups
CREATE INDEX FOR (s:Session) ON (s.session_id)
CREATE INDEX FOR (u:User) ON (u.user_id)

// Phase space queries
CREATE INDEX FOR (a:AgentState) ON (a.agent_id)
CREATE INDEX FOR (a:AgentState) ON (a.timestamp)
CREATE INDEX FOR (c:Constraint) ON (c.name)

// Memory queries
CREATE INDEX FOR (m:MemoryEntry) ON (m.memory_id)
CREATE INDEX FOR (p:Person) ON (p.person_id)

// Kala queries
CREATE INDEX FOR (c:Contribution) ON (c.timestamp)

// Grant queries
CREATE INDEX FOR (g:Grant) ON (g.deadline)
```

### Query Patterns

#### Efficient Pattern: Use Indexes
```cypher
// ✅ GOOD - Uses index
MATCH (person:Person {person_id: $person_id})
MATCH (person)-[:HAS]->(cap:Capability)
RETURN cap
```

#### Inefficient Pattern: Table Scans
```cypher
// ❌ BAD - Full table scan
MATCH (person:Person)
WHERE person.name = $name
RETURN person
```

## Migration from In-Memory

### 1. Session Data

**Before** (in-memory):
```python
sessions = {}  # Lost on restart
```

**After** (FalkorDB):
```python
session_store = FalkorDBSessionStore(client)
# Persists across restarts, accessible from multiple devices
```

### 2. Phase Space Tracking

**Before** (SQLite flat tables):
```python
# Linear scans, no relationships
conn.execute("SELECT * FROM states WHERE agent_id = ?", (agent_id,))
```

**After** (FalkorDB graph):
```python
# Graph traversal, finds patterns
tracker.find_constraint_violation_patterns()
```

### 3. Community Memory

**Before** (dict of lists):
```python
relationships = defaultdict(list)  # No semantic types
```

**After** (FalkorDB semantic graph):
```python
memory.link_memories(mem1, mem2, RelationshipType.CAUSATION)
memory.find_related_memories(mem1, relationship_types=[...])
```

## Cloud Deployment

### FalkorDB Cloud

1. Create account at https://cloud.falkordb.com
2. Create database instance
3. Get connection credentials
4. Update `.env`:
```bash
REDIS_HOST=your-instance.falkordb.cloud
REDIS_PORT=6379
REDIS_PASSWORD=your-password
```

### Self-Hosted

Use `docker-compose.yml` for local/self-hosted deployment:

```bash
# Start FalkorDB
docker-compose up -d falkordb

# Verify
docker-compose logs falkordb

# Check health
docker exec vessels-falkordb redis-cli ping
# Should return: PONG
```

## Monitoring

### Health Check

```python
from vessels.database.falkordb_client import get_falkordb_client

client = get_falkordb_client()
if client.health_check():
    print("✅ FalkorDB connected")
else:
    print("❌ FalkorDB connection failed")
```

### Graph Statistics

```python
# Get graph info
graph = client.get_graph("vessels_sessions")
result = graph.query("CALL db.labels()")  # List all node types
result = graph.query("CALL db.relationshipTypes()")  # List all relationship types
result = graph.query("MATCH (n) RETURN count(n)")  # Total nodes
```

## Benefits Summary

| Aspect | Before (In-Memory/SQLite) | After (FalkorDB) |
|--------|---------------------------|------------------|
| **Data Persistence** | Lost on restart | ✅ Survives restarts |
| **Multi-Device** | Single device only | ✅ Shared across devices |
| **Relationships** | Manual joins, no semantics | ✅ Native graph relationships |
| **Pattern Discovery** | Requires custom code | ✅ Built-in graph queries |
| **Scalability** | Limited by RAM | ✅ Scales to billions of nodes |
| **Query Performance** | O(n) table scans | ✅ O(log n) with indexes |
| **Analytics** | Complex SQL | ✅ Simple Cypher patterns |
| **Auditability** | Limited provenance | ✅ Full graph provenance |

## Troubleshooting

### Connection Errors

**Problem**: `Failed to connect to FalkorDB`

**Solution**:
1. Check FalkorDB is running: `docker-compose ps`
2. Verify port 6379 is accessible: `telnet localhost 6379`
3. Check environment variables in `.env`

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'falkordb'`

**Solution**:
```bash
pip install falkordb==4.0.11
```

### Performance Issues

**Problem**: Slow queries

**Solution**:
1. Verify indexes are created: `client.create_indexes()`
2. Use `EXPLAIN` to analyze query plans:
   ```cypher
   EXPLAIN MATCH (p:Person {person_id: $id}) RETURN p
   ```
3. Limit result sizes with `LIMIT` clause
4. Use node property indexes for common filters

## Next Steps

1. **Start FalkorDB**: `docker-compose up -d falkordb`
2. **Initialize System**: Use `VesselsSystem(use_falkordb=True)`
3. **Migrate Data**: Export from SQLite, import to FalkorDB
4. **Monitor**: Check logs and health checks
5. **Optimize**: Add custom indexes for your query patterns

For questions and support, see:
- FalkorDB Docs: https://docs.falkordb.com
- Vessels Architecture: `ARCHITECTURE_REFACTOR.md`
- Graph Schema: `vessels/knowledge/schema.py`
