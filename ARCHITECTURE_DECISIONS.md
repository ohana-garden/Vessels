# Shoghi Architecture Decisions: Projects + Graphiti/FalkorDB

**Date**: 2025-11-20
**Status**: PROPOSED
**Decision Authority**: Ohana Garden Development Team

## Context

Refactoring Shoghi to implement servant isolation via Agent Zero Projects while adding Graphiti/FalkorDB as a shared knowledge graph. This document addresses the five key design decisions from the specification.

---

## Decision 1: Graph Database Architecture

### Question
One FalkorDB instance with namespaces, or one DB per community?

### Decision: **Single FalkorDB Instance with Namespace Partitioning**

### Rationale

**Chosen Approach:**
```
FalkorDB Instance (port 6379)
├── Graph: lower_puna_elders
│   ├── Servant: malama_transport (can read/write)
│   ├── Servant: meal_coordination (can read/write)
│   └── Servant: medical_scheduling (can read/write)
├── Graph: pahoa_food_sovereignty
│   ├── Servant: garden_logistics (can read/write)
│   └── Servant: distribution_planning (can read/write)
└── Graph: shared_infrastructure
    ├── Servant: voice_interface (read-only to communities)
    └── Servant: grant_writer (read-only to communities)
```

**Advantages:**
- ✅ **Resource efficiency**: Off-grid deployment constraints favor single Redis process
- ✅ **Cross-community coordination**: Servants can discover opportunities across communities via read-only access
- ✅ **Simpler deployment**: One container, one backup process, one monitoring target
- ✅ **FalkorDB design**: Redis-based architecture naturally supports multiple graphs
- ✅ **Atomic operations**: Cross-graph transactions possible when needed
- ✅ **Hawaiian values**: Reflects interconnected communities (not isolated silos)

**Security Model:**
```python
# Per-servant Graphiti client with namespace enforcement
graphiti = Graphiti(
    graph_driver=FalkorDriver(host="localhost", port=6379),
    community_graph=f"{community_id}_graph",  # Primary write graph
    read_only_graphs=[other_community_graphs]  # Cross-community read
)
```

**Rejected Alternative:** One DB per community
- ❌ Resource intensive (multiple Redis processes)
- ❌ Harder to coordinate across communities
- ❌ More complex deployment/backup
- ❌ Over-isolation contradicts Hawaiian values of interconnection

### Implementation Notes
- FalkorDB runs as single Redis instance on port 6379
- Each community = separate graph within FalkorDB
- Servants declare primary graph (read/write) + optional read-only graphs
- Graph naming: `{community_id}_graph` (e.g., `lower_puna_elders_graph`)

---

## Decision 2: Vector Store Sharing Strategy

### Question
Shared embeddings layer, or strictly per-project?

### Decision: **Hybrid Architecture - Per-Project Primary + Shared Secondary**

### Rationale

**Architecture:**
```
Servant Project: malama_transport/
├── vector_store/              # PRIMARY (hot path)
│   ├── transport_routes.npz   # Local knowledge
│   ├── driver_schedules.npz
│   └── medical_facilities.npz
└── graphiti_client
    └── queries shared_community_embeddings  # SECONDARY (fallback)

Shared Knowledge Store:
├── community_protocols/       # Cultural knowledge
├── universal_contacts/        # Shared contact database
└── cross_cutting_procedures/  # General procedures
```

**Query Strategy (Latency Budget: <100ms):**
```python
async def assemble_context(query: str, project_id: str):
    # Step 1: Project vector store (FAST - in-process)
    project_results = await project_vector_store.query(query, top_k=5)  # ~10ms

    # Step 2: Graphiti graph traversal (MEDIUM - local Redis)
    graph_context = await graphiti.get_related_entities(project_results)  # ~20ms

    # Step 3: Shared vectors (SLOW - if needed)
    if len(project_results) < 3:
        shared_results = await shared_vector_store.query(query, top_k=3)  # ~30ms

    # Step 4: Combine and rank (FAST - in-process)
    return rank_by_relevance(project_results + graph_context + shared_results)  # ~10ms

    # Total: ~70ms (within <100ms target)
```

**Advantages:**
- ✅ **Performance**: Project-specific = fast retrieval (no namespace filtering overhead)
- ✅ **Relevance**: Task-specific embeddings optimized for servant role
- ✅ **Deduplication**: Shared store prevents redundant encoding of universal knowledge
- ✅ **Graceful degradation**: Shared store as fallback when project store insufficient
- ✅ **Memory efficiency**: Cultural protocols encoded once, not per-servant

**Rejected Alternatives:**

1. **Strictly per-project**: ❌ Massive duplication of cultural knowledge across servants
2. **Fully shared**: ❌ Slower queries (namespace filtering), lower relevance
3. **Graphiti-only (no separate vectors)**: ❌ Graph DBs not optimized for dense vector search

### Implementation Notes

**Vector Store Technology:**
- **Project stores**: Simple NumPy `.npz` files (lightweight, no daemon required)
- **Shared store**: Redis Vector Search (shared with FalkorDB process)
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 80MB model, fast)

**Storage Layout:**
```
work_dir/projects/
├── lower_puna_elders/
│   ├── malama_transport/
│   │   └── vectors/
│   │       ├── embeddings.npz      # Vectors
│   │       └── metadata.json       # Document IDs
│   └── meal_coordination/
│       └── vectors/
└── shared/
    └── vectors/
        ├── community_protocols.npz  # Shared across all
        └── universal_contacts.npz
```

---

## Decision 3: Servant Spawning Strategy

### Question
Reactive (on explicit request) or proactive (graph pattern detection)?

### Decision: **Phased Approach - Reactive First, Proactive Later**

### Rationale

**Phase 1 (Months 1-3): Reactive Spawning**
```python
# Explicit user request via natural language
user: "I need help coordinating transport for kupuna"
→ shoghi_interface.py parses intent
→ dynamic_agent_factory.py spawns transport servant
→ Project created in work_dir/projects/lower_puna_elders/malama_transport/
```

**Phase 2 (Months 4-6): Supervised Proactive**
```python
# Graph pattern detection with human approval
graph_query: MATCH (e:Elder)-[:NEEDS]->(s:Service {type: 'transport'})
             WHERE NOT EXISTS((e)-[:SERVED_BY]->(:Servant))
             RETURN e.name, e.location

→ Shoghi detects unmet need pattern
→ Proposes: "I notice 3 kupuna in Pahoa need transport. Spawn coordinator?"
→ User approves: "yes"
→ Servant spawned with context from graph
```

**Phase 3 (Months 7+): Autonomous Proactive**
```python
# Fully autonomous with moral constraint gating
pattern = detect_unmet_need_in_graph()
spawn_decision = moral_constraint_validator.validate(
    action="spawn_servant",
    context=pattern,
    virtues=current_12d_state
)
if spawn_decision.allowed:
    spawn_servant(pattern)
    notify_user(f"Spawned {servant_name} to address {pattern}")
```

**Advantages:**
- ✅ **Safety**: Build trust before autonomy
- ✅ **Data quality**: Need sufficient graph data for pattern detection
- ✅ **User comfort**: Hawaiian communities value consultation before action
- ✅ **Debugging**: Easier to tune spawning logic with reactive baseline
- ✅ **Moral constraints**: Proactive spawning must pass virtue thresholds (Service > 0.7, Understanding > 0.6)

**Rejected Alternatives:**
1. **Immediate proactive**: ❌ Insufficient graph data initially, trust not established
2. **Strictly reactive forever**: ❌ Misses Shoghi's core value prop (proactive service)

### Implementation Notes

**Reactive Spawning (Phase 1):**
```python
# In dynamic_agent_factory.py
def spawn_servant_from_intent(intent: str, community_id: str) -> AgentInstance:
    project_dir = f"work_dir/projects/{community_id}/{sanitize(intent)}/"

    # Create Project
    project = Project(
        id=generate_id(),
        directory=project_dir,
        graphiti_namespace=f"{community_id}_graph",
        system_prompt=generate_servant_prompt(intent, community_id)
    )

    # Create Graphiti client
    graphiti = Graphiti(
        graph_driver=FalkorDriver("localhost", 6379),
        community_graph=f"{community_id}_graph"
    )

    # Initialize vector store
    vector_store = ProjectVectorStore(project_dir)

    return AgentInstance(project, graphiti, vector_store)
```

**Proactive Spawning (Phase 2):**
```python
# In community.py (NEW FILE)
class ProactiveSpawnDetector:
    def scan_for_opportunities(self, community_id: str) -> List[SpawnOpportunity]:
        patterns = [
            UnmetNeedPattern(),
            ResourceMismatchPattern(),
            CoordinationGapPattern()
        ]

        opportunities = []
        for pattern in patterns:
            matches = pattern.detect_in_graph(self.graphiti, community_id)
            for match in matches:
                if self.should_propose_spawn(match):
                    opportunities.append(SpawnOpportunity(match))

        return opportunities

    def should_propose_spawn(self, match: PatternMatch) -> bool:
        # Check 12D moral constraints
        proposed_state = self.simulate_servant_spawn(match)
        return self.constraint_validator.validate(proposed_state).is_valid
```

---

## Decision 4: Cross-Community Visibility

### Question
Can servants read other community graphs for coordination opportunities?

### Decision: **Graduated Read Access with Privacy Tiers**

### Rationale

**Access Model:**
```python
class CommunityPrivacy(Enum):
    PRIVATE = "private"        # No cross-community reads (default)
    SHARED = "shared"          # Read-only to trusted communities
    PUBLIC = "public"          # Read-only to all servants
    FEDERATED = "federated"    # Read/write coordination space

class CommunityConfig:
    id: str
    privacy_level: CommunityPrivacy
    trusted_communities: List[str]  # For SHARED level
    shared_entity_types: List[str]  # What can be read (e.g., ["Event", "Resource"])
    redacted_properties: List[str]  # What's hidden (e.g., ["phone_number", "address"])
```

**Example:**
```python
# Lower Puna Elders: SHARED with Pahoa Food Sovereignty
lower_puna_config = CommunityConfig(
    id="lower_puna_elders",
    privacy_level=CommunityPrivacy.SHARED,
    trusted_communities=["pahoa_food_sovereignty"],
    shared_entity_types=["Event", "Resource", "Organization"],  # NOT Person
    redacted_properties=["phone_number", "address", "medical_info"]
)

# Pahoa servant can query:
query = """
    MATCH (r:Resource {type: 'transport_van'})
    WHERE r.community_id = 'lower_puna_elders'
    AND r.available = true
    RETURN r.name, r.capacity  // ✅ Allowed
    // ❌ r.location, r.owner_phone would be redacted
"""
```

**Advantages:**
- ✅ **Privacy**: Default to private, opt-in to sharing
- ✅ **Flexibility**: Communities control what they share
- ✅ **Coordination**: Trusted communities can discover shared resources
- ✅ **Cultural safety**: Respects Hawaiian value of pono (righteousness/balance)
- ✅ **Consent-based**: Aligns with community-driven governance

**Cross-Community Coordination Flow:**
```
1. Pahoa garden servant detects surplus produce
2. Queries shared graphs for communities with food distribution events
3. Discovers Lower Puna elders meal coordination
4. Proposes coordination to BOTH communities
5. Creates FEDERATED graph space for joint planning
6. Joint servants coordinate in federated space
7. Results written back to each community's private graph
```

**Rejected Alternatives:**
1. **Full visibility**: ❌ Privacy concerns, potential for exploitation
2. **Zero visibility**: ❌ Misses coordination opportunities, creates silos
3. **Central shared graph only**: ❌ Loss of community autonomy

### Implementation Notes

**Graph Query with Privacy Filtering:**
```python
class PrivacyFilteredGraphitiClient:
    def query(self, cypher: str, requesting_community: str):
        # Parse query to identify target communities
        target_communities = extract_communities_from_query(cypher)

        # Check permissions
        for target in target_communities:
            config = load_community_config(target)
            if requesting_community not in config.trusted_communities:
                if config.privacy_level == CommunityPrivacy.PRIVATE:
                    raise PermissionError(f"Cannot read {target} graph")

            # Inject property redaction
            cypher = inject_redaction_filters(cypher, config.redacted_properties)

        # Execute filtered query
        return self.graphiti.execute(cypher)
```

---

## Decision 5: Persistence Strategy

### Question
Redis AOF/RDB for FalkorDB, or separate backup mechanism?

### Decision: **Dual Persistence - Redis RDB + Separate Graph Snapshots**

### Rationale

**Persistence Architecture:**
```
FalkorDB (Redis)
├── RDB snapshots: Every 6 hours → /data/falkordb/dump.rdb
├── AOF disabled: (Performance optimization for off-grid)
└── Manual sync on critical events

Separate Graph Backups
├── JSON exports: Daily → /backups/graphs/YYYY-MM-DD/
│   ├── lower_puna_elders_graph.json
│   ├── pahoa_food_sovereignty_graph.json
│   └── metadata.json (export timestamp, node/edge counts)
└── Format: Cypher CREATE statements (human-readable, restorable)
```

**Backup Schedule:**
```python
# RDB (automatic via Redis config)
save 900 1      # After 900 sec (15 min) if at least 1 key changed
save 300 10     # After 300 sec (5 min) if at least 10 keys changed
save 60 10000   # After 60 sec if at least 10000 keys changed

# Graph JSON exports (custom)
export_graphs_to_json()  # Daily at 2 AM HST
validate_backup()        # Checksums, node counts
prune_old_backups()      # Keep last 30 days
```

**Advantages:**
- ✅ **Fast recovery**: RDB for quick Redis restart
- ✅ **Human-readable backups**: JSON/Cypher for debugging, auditing
- ✅ **Version control**: JSON exports can be git-tracked (small graphs)
- ✅ **Migration**: JSON exports portable to other graph DBs
- ✅ **Disaster recovery**: Separate backup location protects against Redis corruption
- ✅ **Off-grid optimized**: RDB lighter than AOF (less disk I/O, lower power)

**Disaster Recovery Flow:**
```
Scenario: Solar battery dies, Redis crashes, RDB corrupted

1. Restart FalkorDB
2. Attempt RDB load → FAILS (corruption detected)
3. Fallback to latest JSON backup
4. Run restore script:
   for graph in backups/graphs/2025-11-19/*.json:
       import_graph_from_json(graph)
5. Validate node counts match backup metadata
6. Resume operations (lost < 24 hours of data)
```

**Rejected Alternatives:**

1. **AOF only**:
   - ❌ Large log files (high disk I/O)
   - ❌ Slower restart (replay entire log)
   - ❌ Higher power consumption (frequent writes)

2. **RDB only (no JSON exports)**:
   - ❌ Binary format (hard to debug)
   - ❌ Locked to Redis (no portability)
   - ❌ No human-readable audit trail

3. **External graph DB (Neo4j, etc.)**:
   - ❌ Higher resource usage (JVM overhead)
   - ❌ More complex deployment
   - ❌ FalkorDB-specific features (RedisGraph optimizations)

### Implementation Notes

**JSON Export Script:**
```python
# In shoghi/knowledge/backup.py
async def export_community_graph(community_id: str, output_dir: Path):
    graphiti = get_graphiti_client(community_id)

    # Export nodes
    nodes = await graphiti.execute("MATCH (n) RETURN n")
    nodes_json = [node_to_dict(n) for n in nodes]

    # Export relationships
    rels = await graphiti.execute("MATCH ()-[r]->() RETURN r")
    rels_json = [rel_to_dict(r) for r in rels]

    # Write to file
    backup_data = {
        "community_id": community_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "node_count": len(nodes_json),
        "edge_count": len(rels_json),
        "nodes": nodes_json,
        "relationships": rels_json
    }

    with open(output_dir / f"{community_id}_graph.json", "w") as f:
        json.dump(backup_data, f, indent=2)

    # Generate Cypher restore script
    with open(output_dir / f"{community_id}_restore.cypher", "w") as f:
        for node in nodes_json:
            f.write(generate_create_node_statement(node) + "\n")
        for rel in rels_json:
            f.write(generate_create_rel_statement(rel) + "\n")
```

**Redis Configuration (redis.conf):**
```
# RDB Persistence
dir /data/falkordb
dbfilename dump.rdb
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# AOF Disabled (performance)
appendonly no

# Memory Management
maxmemory 512mb              # Off-grid constraint
maxmemory-policy allkeys-lru  # Evict least recently used
```

---

## Summary of Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Graph Architecture** | Single FalkorDB + namespaces | Resource efficiency, cross-community coordination |
| **Vector Stores** | Hybrid (per-project primary + shared secondary) | Performance + deduplication |
| **Servant Spawning** | Phased (reactive → proactive) | Safety, trust-building, data quality |
| **Cross-Community Access** | Graduated read access with privacy tiers | Balance coordination + privacy |
| **Persistence** | RDB + JSON exports | Fast recovery + human-readable backups |

---

## Next Steps

1. **Implementation Order:**
   - Phase 1: FalkorDB deployment + Graphiti integration
   - Phase 2: Project-based servant isolation
   - Phase 3: Hybrid vector stores
   - Phase 4: Privacy-filtered cross-community queries
   - Phase 5: Proactive spawning (supervised)

2. **Validation Criteria:**
   - [ ] Servant spawn time < 2 seconds
   - [ ] Graph query latency < 10ms p50
   - [ ] Context assembly < 100ms
   - [ ] Zero context contamination between servants
   - [ ] Privacy filters prevent unauthorized cross-community access
   - [ ] Backup/restore tested monthly

3. **Documentation:**
   - Architecture diagrams (graph namespacing, vector store queries)
   - Deployment runbook (FalkorDB + Redis config)
   - Privacy configuration guide for communities
   - Disaster recovery procedures

---

**Approved By:** _(Pending)_
**Implementation Start:** _(Pending)_
**Target Completion:** _(Pending)_
