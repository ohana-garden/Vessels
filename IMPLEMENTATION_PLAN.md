# Shoghi Implementation Plan: Projects + Graphiti/FalkorDB

**Version**: 1.0
**Date**: 2025-11-20
**Status**: READY FOR IMPLEMENTATION

---

## Overview

This plan details the implementation of Projects-based servant isolation with Graphiti/FalkorDB knowledge graph integration for the Shoghi platform.

**Total Estimated Effort**: 6-8 weeks
**Team Size**: 1-2 developers
**Risk Level**: Medium (new dependencies, architectural changes)

---

## Phase 1: Foundation & Dependencies (Week 1)

### 1.1 Install FalkorDB & Dependencies

**Goal**: Deploy FalkorDB and install Python dependencies

**Tasks**:
- [ ] Install FalkorDB via Docker
  ```bash
  docker run -d \
    --name falkordb \
    -p 6379:6379 \
    -v /data/falkordb:/data \
    falkordb/falkordb:latest
  ```
- [ ] Update `requirements.txt` with new dependencies:
  ```
  graphiti-core>=0.3.0
  sentence-transformers>=2.2.0
  redis>=5.0.0
  numpy>=1.21.0
  faiss-cpu>=1.7.4  # Optional: for faster vector search
  ```
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify FalkorDB connectivity:
  ```python
  import redis
  r = redis.Redis(host='localhost', port=6379)
  r.ping()  # Should return True
  ```

**Deliverables**:
- ✅ FalkorDB running on port 6379
- ✅ Updated requirements.txt
- ✅ All tests passing with new dependencies

**Validation**:
```bash
docker ps | grep falkordb  # Container running
redis-cli PING            # Returns PONG
pytest tests/             # 241 tests still passing
```

---

### 1.2 Create Core Knowledge Graph Structure

**Goal**: Define Shoghi's graph schema and initialize first community graph

**Tasks**:
- [ ] Create `shoghi/knowledge/` package:
  ```
  shoghi/knowledge/
  ├── __init__.py
  ├── schema.py           # Graph schema definitions
  ├── graphiti_client.py  # Graphiti wrapper
  └── backup.py           # Backup/restore utilities
  ```

- [ ] Define graph schema in `schema.py`:
  ```python
  @dataclass
  class ShorghiGraphSchema:
      """Shoghi knowledge graph schema"""

      # Node Types
      PERSON = "Person"           # Kupuna, caregivers, volunteers
      PLACE = "Place"             # Gardens, medical facilities, homes
      ORGANIZATION = "Org"        # Health providers, food hubs
      EVENT = "Event"             # Appointments, deliveries, gatherings
      SERVANT = "Servant"         # AI servants
      RESOURCE = "Resource"       # Vans, food, supplies

      # Relationship Types
      NEEDS = "NEEDS"             # Person -[NEEDS]-> Service
      PROVIDES = "PROVIDES"       # Person -[PROVIDES]-> Service
      SERVES = "SERVES"           # Servant -[SERVES]-> Person
      COORDINATES_WITH = "COORDINATES_WITH"  # Servant -[COORDINATES]-> Servant
      LOCATED_AT = "LOCATED_AT"   # Event -[LOCATED_AT]-> Place
      HAS_RESOURCE = "HAS_RESOURCE"  # Org -[HAS_RESOURCE]-> Resource

      # Properties (common across nodes)
      COMMUNITY_ID = "community_id"
      VALID_AT = "valid_at"
      INVALID_AT = "invalid_at"
      CREATED_BY = "created_by"  # Servant ID
  ```

- [ ] Create Graphiti client wrapper in `graphiti_client.py`
- [ ] Initialize test community graph: `lower_puna_elders_graph`
- [ ] Add graph backup script in `backup.py`

**Deliverables**:
- ✅ `shoghi/knowledge/` package created
- ✅ Graph schema documented
- ✅ Test graph initialized
- ✅ Backup script functional

**Validation**:
```python
from shoghi.knowledge.graphiti_client import ShorghiGraphitiClient

client = ShorghiGraphitiClient("lower_puna_elders")
client.create_node("Person", name="Test Kupuna", community_id="lower_puna_elders")
nodes = client.query("MATCH (p:Person) RETURN p")
assert len(nodes) == 1  # ✅ Graph working
```

---

### 1.3 Implement Vector Embedding System

**Goal**: Replace hash-based vectors with learned embeddings

**Tasks**:
- [ ] Create `shoghi/knowledge/embeddings.py`:
  ```python
  from sentence_transformers import SentenceTransformer

  class ShorghiEmbedder:
      def __init__(self, model_name="all-MiniLM-L6-v2"):
          self.model = SentenceTransformer(model_name)  # 384-dim, 80MB

      def embed(self, text: str) -> np.ndarray:
          return self.model.encode(text)

      def embed_batch(self, texts: List[str]) -> np.ndarray:
          return self.model.encode(texts, show_progress_bar=True)
  ```

- [ ] Create `shoghi/knowledge/vector_stores.py`:
  ```python
  class ProjectVectorStore:
      """Lightweight NumPy-based vector store for project-specific knowledge"""

      def __init__(self, project_dir: Path):
          self.embedder = ShorghiEmbedder()
          self.vectors_file = project_dir / "vectors" / "embeddings.npz"
          self.metadata_file = project_dir / "vectors" / "metadata.json"

      def add(self, texts: List[str], metadata: List[Dict]):
          embeddings = self.embedder.embed_batch(texts)
          self._save(embeddings, metadata)

      def query(self, query_text: str, top_k: int = 5) -> List[Dict]:
          query_embedding = self.embedder.embed(query_text)
          similarities = cosine_similarity(query_embedding, self.embeddings)
          top_indices = np.argsort(similarities)[-top_k:][::-1]
          return [self.metadata[i] for i in top_indices]
  ```

- [ ] Create `SharedVectorStore` class for community-wide knowledge
- [ ] Add tests in `test_embeddings.py`

**Deliverables**:
- ✅ Sentence-transformers integration
- ✅ `ProjectVectorStore` class
- ✅ `SharedVectorStore` class
- ✅ Tests passing

**Validation**:
```python
store = ProjectVectorStore(Path("test_project/"))
store.add(["Transport van available", "Medical appointment"], [{"id": 1}, {"id": 2}])
results = store.query("need a ride", top_k=1)
assert results[0]["id"] == 1  # ✅ Semantic similarity working
```

---

## Phase 2: Migrate Memory System (Week 2)

### 2.1 Refactor CommunityMemory to Use Graphiti

**Goal**: Replace in-memory storage with Graphiti backend

**Tasks**:
- [ ] Create new `GraphitiMemoryBackend` class in `community_memory.py`
- [ ] Implement memory type → graph node mapping:
  ```python
  MEMORY_TYPE_TO_NODE = {
      MemoryType.EXPERIENCE: "Experience",
      MemoryType.KNOWLEDGE: "Fact",
      MemoryType.PATTERN: "Pattern",
      MemoryType.RELATIONSHIP: "Relationship",
      MemoryType.EVENT: "Event",
      MemoryType.CONTRIBUTION: "Contribution"
  }
  ```
- [ ] Migrate `store_memory()` to write to Graphiti
- [ ] Migrate `query_memories()` to use Graphiti + vector search
- [ ] Migrate `get_related_memories()` to use graph traversal
- [ ] Update `get_agent_memories()` to query by agent entity

**Deliverables**:
- ✅ `GraphitiMemoryBackend` functional
- ✅ All `CommunityMemory` methods working with Graphiti
- ✅ Backward compatibility maintained (old tests pass)

**Validation**:
```bash
pytest test_community_memory.py  # All 24 tests passing
```

**Migration Path**:
```python
# Option 1: Run both backends in parallel for testing
memory = CommunityMemory(
    backend="hybrid",  # Writes to both old + new
    graphiti_client=graphiti,
    sqlite_path="shoghi_grants.db"
)

# Option 2: One-time migration script
python scripts/migrate_sqlite_to_graphiti.py
```

---

### 2.2 Integrate Graphiti with Agent State Tracking

**Goal**: Store agent 12D state trajectories in graph

**Tasks**:
- [ ] Create `AgentStateNode` schema:
  ```python
  # In schema.py
  class AgentStateNode:
      node_type = "AgentState"
      properties = {
          "agent_id": str,
          "timestamp": datetime,
          "activity": float,
          "coordination": float,
          "effectiveness": float,
          "resource_consumption": float,
          "system_health": float,
          "truthfulness": float,
          "justice": float,
          "trustworthiness": float,
          "unity": float,
          "service": float,
          "detachment": float,
          "understanding": float,
          "community_id": str
      }
  ```

- [ ] Update `phase_space/tracker.py` to write to Graphiti:
  ```python
  class GraphitiPhaseSpaceTracker(PhaseSpaceTracker):
      def record_state(self, agent_id: str, state: State12D):
          # Store in Graphiti
          self.graphiti.create_node(
              "AgentState",
              agent_id=agent_id,
              timestamp=datetime.utcnow(),
              **state.to_dict()
          )

          # Link to agent
          self.graphiti.create_relationship(
              agent_id, "HAS_STATE", state_node_id
          )
  ```

- [ ] Update attractor discovery to query graph:
  ```python
  # In phase_space/attractors.py
  def discover_attractors_from_graph(self, agent_id: str):
      states = self.graphiti.query("""
          MATCH (a:Servant {id: $agent_id})-[:HAS_STATE]->(s:AgentState)
          WHERE s.timestamp > $lookback_window
          RETURN s
          ORDER BY s.timestamp
      """, agent_id=agent_id, lookback_window=datetime.utcnow() - timedelta(days=7))

      # Run DBSCAN clustering on states
      return self.cluster_attractors(states)
  ```

**Deliverables**:
- ✅ Agent states stored in graph
- ✅ Temporal queries for state trajectories
- ✅ Attractor discovery using graph data

**Validation**:
```bash
pytest shoghi/tests/test_tracker.py
pytest shoghi/tests/test_attractors.py
```

---

## Phase 3: Projects-Based Servant Isolation (Week 3-4)

### 3.1 Create Project Management System

**Goal**: Implement Project isolation without external Agent Zero dependency

**Tasks**:
- [ ] Create `shoghi/projects/` package:
  ```
  shoghi/projects/
  ├── __init__.py
  ├── project.py          # Project class
  ├── manager.py          # Project lifecycle management
  └── templates/          # Servant-specific configs
      ├── transport.yaml
      ├── meals.yaml
      └── medical.yaml
  ```

- [ ] Implement `Project` class in `project.py`:
  ```python
  @dataclass
  class ServantProject:
      id: str
      community_id: str
      servant_type: str  # "transport", "meals", etc.
      work_dir: Path
      graphiti_namespace: str
      vector_store: ProjectVectorStore
      system_prompt: str
      secrets: Dict[str, str]
      status: ProjectStatus
      created_at: datetime
      last_active: datetime

      def get_graphiti_client(self) -> ShorghiGraphitiClient:
          return ShorghiGraphitiClient(
              community_graph=self.graphiti_namespace,
              servant_id=self.id,
              read_only_graphs=self._get_allowed_read_graphs()
          )

      def load_vector_store(self) -> ProjectVectorStore:
          return ProjectVectorStore(self.work_dir / "vectors")

      def execute_in_isolation(self, task: str):
          # Run task with project-specific context
          context = self.assemble_context(task)
          result = self.agent_instance.execute(task, context)
          self.log_execution(task, result)
          return result
  ```

- [ ] Implement `ProjectManager` class in `manager.py`:
  ```python
  class ProjectManager:
      def create_project(self, community_id: str, servant_type: str) -> ServantProject:
          project_id = self._generate_id()
          work_dir = Path(f"work_dir/projects/{community_id}/{servant_type}_{project_id[:8]}/")
          work_dir.mkdir(parents=True, exist_ok=True)

          # Load template
          template = self._load_template(servant_type)

          # Create project
          project = ServantProject(
              id=project_id,
              community_id=community_id,
              servant_type=servant_type,
              work_dir=work_dir,
              graphiti_namespace=f"{community_id}_graph",
              vector_store=ProjectVectorStore(work_dir),
              system_prompt=template["system_prompt"],
              secrets={},
              status=ProjectStatus.INITIALIZING,
              created_at=datetime.utcnow(),
              last_active=datetime.utcnow()
          )

          # Initialize Graphiti client
          graphiti = project.get_graphiti_client()
          graphiti.create_node("Servant", id=project_id, type=servant_type, community_id=community_id)

          return project

      def archive_project(self, project_id: str):
          # Archive project files, mark as completed in graph
          pass
  ```

**Deliverables**:
- ✅ `ServantProject` class
- ✅ `ProjectManager` class
- ✅ Project templates for transport, meals, medical
- ✅ Tests for project lifecycle

**Validation**:
```python
manager = ProjectManager()
project = manager.create_project("lower_puna_elders", "transport")
assert project.work_dir.exists()  # ✅ Directory created
assert project.get_graphiti_client() is not None  # ✅ Graphiti connected
```

---

### 3.2 Refactor DynamicAgentFactory for Projects

**Goal**: Update agent spawning to create isolated projects

**Tasks**:
- [ ] Update `dynamic_agent_factory.py`:
  ```python
  class ProjectBasedAgentFactory(DynamicAgentFactory):
      def __init__(self, project_manager: ProjectManager):
          super().__init__()
          self.project_manager = project_manager

      def create_agent_from_intent(self, intent: str, community_id: str) -> AgentInstance:
          # Determine servant type from intent
          servant_type = self._classify_intent(intent)

          # Create isolated project
          project = self.project_manager.create_project(community_id, servant_type)

          # Create agent instance with project context
          agent = AgentInstance(
              id=project.id,
              specification=self._load_spec(servant_type),
              status=AgentStatus.IDLE,
              created_at=datetime.utcnow(),
              last_active=datetime.utcnow(),
              memory={},  # Memory is now in Graphiti
              tools=project.get_allowed_tools(),
              connections=[],
              message_queue=queue.Queue(),
              project=project  # 🆕 Link to project
          )

          # Initialize project-specific knowledge
          self._seed_project_knowledge(project, intent)

          return agent

      def _seed_project_knowledge(self, project: ServantProject, intent: str):
          """Seed project vector store with relevant community knowledge"""
          # Query shared knowledge base
          shared_store = SharedVectorStore()
          relevant_docs = shared_store.query(intent, top_k=10)

          # Add to project store
          project.vector_store.add(
              texts=[doc["text"] for doc in relevant_docs],
              metadata=relevant_docs
          )
  ```

- [ ] Update `agent_zero_core.py` to use `ProjectBasedAgentFactory`
- [ ] Add project isolation tests

**Deliverables**:
- ✅ `ProjectBasedAgentFactory` class
- ✅ Agent spawning creates isolated projects
- ✅ Project knowledge seeding works

**Validation**:
```python
factory = ProjectBasedAgentFactory(project_manager)
agent1 = factory.create_agent_from_intent("coordinate transport", "lower_puna_elders")
agent2 = factory.create_agent_from_intent("coordinate meals", "lower_puna_elders")

# Ensure isolation
assert agent1.project.work_dir != agent2.project.work_dir  # ✅ Separate directories
assert agent1.project.id != agent2.project.id  # ✅ Separate IDs
```

---

### 3.3 Implement Context Assembly Pipeline

**Goal**: Fast context retrieval from project vectors + Graphiti

**Tasks**:
- [ ] Create `shoghi/knowledge/context_assembly.py`:
  ```python
  class ContextAssembler:
      """Assembles context for servant tasks within <100ms"""

      def __init__(self, project: ServantProject, shared_store: SharedVectorStore):
          self.project = project
          self.shared_store = shared_store
          self.graphiti = project.get_graphiti_client()

      async def assemble_context(self, task: str) -> Dict[str, Any]:
          """
          Multi-source context assembly with latency budget

          Target: <100ms total
          - Project vectors: ~10ms
          - Graph traversal: ~20ms
          - Shared vectors: ~30ms (if needed)
          - Ranking: ~10ms
          """
          start = time.time()

          # Step 1: Query project vector store (FAST)
          project_docs = await self._query_project_vectors(task)  # ~10ms

          # Step 2: Get related entities from graph (MEDIUM)
          graph_context = await self._get_graph_context(project_docs)  # ~20ms

          # Step 3: Query shared store if insufficient results (SLOW)
          if len(project_docs) < 3:
              shared_docs = await self._query_shared_vectors(task)  # ~30ms
          else:
              shared_docs = []

          # Step 4: Rank and combine (FAST)
          combined = self._rank_by_relevance(project_docs, graph_context, shared_docs)  # ~10ms

          elapsed = (time.time() - start) * 1000  # ms
          logger.info(f"Context assembled in {elapsed:.1f}ms")

          return {
              "task": task,
              "project_knowledge": project_docs,
              "graph_context": graph_context,
              "shared_knowledge": shared_docs,
              "combined_context": combined,
              "assembly_time_ms": elapsed
          }

      async def _query_project_vectors(self, task: str) -> List[Dict]:
          return self.project.vector_store.query(task, top_k=5)

      async def _get_graph_context(self, docs: List[Dict]) -> Dict:
          # Extract entities mentioned in retrieved docs
          entities = self._extract_entities(docs)

          # Query graph for relationships
          context = {}
          for entity in entities:
              neighbors = await self.graphiti.get_neighbors(entity, max_depth=2)
              context[entity] = neighbors

          return context

      async def _query_shared_vectors(self, task: str) -> List[Dict]:
          return self.shared_store.query(task, top_k=3)

      def _rank_by_relevance(self, *sources) -> List[Dict]:
          # Combine and re-rank by relevance + recency + graph centrality
          all_docs = []
          for source in sources:
              all_docs.extend(source if isinstance(source, list) else source.values())

          # Score by: 0.5 * semantic_sim + 0.3 * recency + 0.2 * graph_centrality
          scored = [(doc, self._score(doc)) for doc in all_docs]
          scored.sort(key=lambda x: x[1], reverse=True)

          return [doc for doc, score in scored[:10]]
  ```

- [ ] Add latency monitoring and logging
- [ ] Create performance tests

**Deliverables**:
- ✅ `ContextAssembler` class
- ✅ <100ms assembly time achieved
- ✅ Performance tests passing

**Validation**:
```python
assembler = ContextAssembler(project, shared_store)
context = await assembler.assemble_context("Find transport for kupuna in Pahoa")
assert context["assembly_time_ms"] < 100  # ✅ Performance target met
assert len(context["combined_context"]) > 0  # ✅ Results returned
```

---

## Phase 4: Cross-Servant Coordination (Week 5)

### 4.1 Implement Privacy-Filtered Graph Access

**Goal**: Enable servants to discover cross-community coordination opportunities

**Tasks**:
- [ ] Create `shoghi/knowledge/privacy.py`:
  ```python
  class CommunityPrivacyConfig:
      def __init__(self, community_id: str):
          self.community_id = community_id
          self.config = self._load_config()

      def can_read_community(self, requesting_community: str) -> bool:
          if self.config.privacy_level == CommunityPrivacy.PUBLIC:
              return True
          if self.config.privacy_level == CommunityPrivacy.SHARED:
              return requesting_community in self.config.trusted_communities
          return False

      def get_redacted_properties(self) -> List[str]:
          return self.config.redacted_properties

      def get_allowed_entity_types(self) -> List[str]:
          return self.config.shared_entity_types

  class PrivacyFilteredGraphitiClient(ShorghiGraphitiClient):
      def query(self, cypher: str, **params):
          # Inject privacy filters into Cypher query
          target_communities = self._extract_target_communities(cypher)

          for target in target_communities:
              config = CommunityPrivacyConfig(target)
              if not config.can_read_community(self.community_id):
                  raise PermissionError(f"Cannot read {target} graph")

              # Redact properties
              cypher = self._inject_property_filters(cypher, config.get_redacted_properties())

          return super().query(cypher, **params)
  ```

- [ ] Add community config files:
  ```yaml
  # communities/lower_puna_elders.yaml
  community_id: lower_puna_elders
  privacy_level: shared
  trusted_communities:
    - pahoa_food_sovereignty
  shared_entity_types:
    - Event
    - Resource
    - Organization
  redacted_properties:
    - phone_number
    - address
    - medical_info
  ```

- [ ] Update `ShorghiGraphitiClient` to use privacy filtering

**Deliverables**:
- ✅ Privacy filtering system
- ✅ Community config files
- ✅ Permission tests

**Validation**:
```python
# Pahoa servant tries to read Lower Puna graph
client = PrivacyFilteredGraphitiClient(
    community_id="pahoa_food_sovereignty",
    requesting_community="pahoa_food_sovereignty"
)

# Should succeed (trusted)
result = client.query("MATCH (e:Event {community_id: 'lower_puna_elders'}) RETURN e")
assert "phone_number" not in result[0]  # ✅ Redacted

# Should fail (private property)
with pytest.raises(PermissionError):
    client.query("MATCH (p:Person {community_id: 'lower_puna_elders'}) RETURN p")
```

---

### 4.2 Implement Cross-Servant Discovery

**Goal**: Servants discover coordination opportunities via graph

**Tasks**:
- [ ] Create `shoghi/knowledge/coordination.py`:
  ```python
  class CoordinationDiscovery:
      """Discovers cross-servant coordination opportunities"""

      def __init__(self, graphiti: ShorghiGraphitiClient):
          self.graphiti = graphiti

      def discover_opportunities(self, servant_id: str) -> List[CoordinationOpportunity]:
          """
          Find other servants working on related tasks

          Examples:
          - Transport servant finds medical scheduling servant (same elder)
          - Meal servant finds garden servant (surplus produce)
          - Grant writer finds multiple servants (shared funding need)
          """
          opportunities = []

          # Pattern 1: Same person served by multiple servants
          same_person = self._find_servants_serving_same_people(servant_id)
          opportunities.extend(same_person)

          # Pattern 2: Resource overlap (one has what other needs)
          resource_match = self._find_resource_coordination(servant_id)
          opportunities.extend(resource_match)

          # Pattern 3: Temporal coordination (events at similar times)
          temporal_match = self._find_temporal_coordination(servant_id)
          opportunities.extend(temporal_match)

          return opportunities

      def _find_servants_serving_same_people(self, servant_id: str) -> List[CoordinationOpportunity]:
          results = self.graphiti.query("""
              MATCH (s1:Servant {id: $servant_id})-[:SERVES]->(p:Person)<-[:SERVES]-(s2:Servant)
              WHERE s1.id <> s2.id
              RETURN s2.id, s2.type, p.name, COUNT(p) as overlap
              ORDER BY overlap DESC
          """, servant_id=servant_id)

          return [
              CoordinationOpportunity(
                  type="shared_service_recipient",
                  partner_servant=r["s2.id"],
                  context=f"Both serving {r['p.name']}",
                  priority=r["overlap"]
              )
              for r in results
          ]

      def _find_resource_coordination(self, servant_id: str) -> List[CoordinationOpportunity]:
          # Find: I need X, they have X
          results = self.graphiti.query("""
              MATCH (s1:Servant {id: $servant_id})-[:NEEDS]->(r:Resource)<-[:HAS]-(s2:Servant)
              RETURN s2.id, s2.type, r.type as resource_type
          """, servant_id=servant_id)

          return [
              CoordinationOpportunity(
                  type="resource_match",
                  partner_servant=r["s2.id"],
                  context=f"They have {r['resource_type']} I need",
                  priority=1.0
              )
              for r in results
          ]
  ```

- [ ] Add coordination opportunity ranking
- [ ] Add tests

**Deliverables**:
- ✅ `CoordinationDiscovery` class
- ✅ Pattern detection queries
- ✅ Opportunity ranking

**Validation**:
```python
discovery = CoordinationDiscovery(graphiti)
opportunities = discovery.discover_opportunities("transport_servant_123")
assert len(opportunities) > 0  # ✅ Found coordination opportunities
assert opportunities[0].type in ["shared_service_recipient", "resource_match"]
```

---

## Phase 5: Proactive Spawning (Week 6)

### 5.1 Implement Pattern Detection for Spawning

**Goal**: Detect unmet needs in graph that warrant new servants

**Tasks**:
- [ ] Create `shoghi/community/spawning.py`:
  ```python
  class ProactiveSpawnDetector:
      """Detects patterns in graph warranting new servant spawns"""

      def __init__(self, graphiti: ShorghiGraphitiClient, constraint_validator):
          self.graphiti = graphiti
          self.constraint_validator = constraint_validator

      def scan_for_spawn_opportunities(self, community_id: str) -> List[SpawnOpportunity]:
          patterns = [
              UnmetNeedPattern(),
              ResourceMismatchPattern(),
              CoordinationGapPattern(),
              RecurringEventPattern()
          ]

          opportunities = []
          for pattern in patterns:
              matches = pattern.detect(self.graphiti, community_id)
              for match in matches:
                  if self._should_spawn(match):
                      opportunities.append(
                          SpawnOpportunity(
                              pattern=pattern.name,
                              context=match,
                              urgency=self._calculate_urgency(match),
                              suggested_servant_type=pattern.suggested_servant_type
                          )
                      )

          return sorted(opportunities, key=lambda o: o.urgency, reverse=True)

      def _should_spawn(self, match: PatternMatch) -> bool:
          """Check if spawning servant satisfies moral constraints"""
          # Simulate spawning servant
          proposed_state = self._simulate_spawn(match)

          # Validate against 12D constraints
          validation = self.constraint_validator.validate(proposed_state)

          # Require: Service > 0.7, Understanding > 0.6, Truthfulness > 0.6
          if not validation.is_valid:
              logger.info(f"Spawn blocked by constraints: {validation.violations}")
              return False

          return True

  class UnmetNeedPattern:
      """Detects people with needs not currently served"""

      def detect(self, graphiti, community_id):
          return graphiti.query("""
              MATCH (p:Person {community_id: $community_id})-[:NEEDS]->(s:Service)
              WHERE NOT EXISTS((p)-[:SERVED_BY]->(:Servant))
              AND s.valid_at <= datetime()
              AND (s.invalid_at IS NULL OR s.invalid_at > datetime())
              RETURN p.name, s.type, COUNT(s) as unmet_count
              GROUP BY p.name, s.type
              HAVING unmet_count >= 3  // Only if recurring
              ORDER BY unmet_count DESC
          """, community_id=community_id)
  ```

- [ ] Implement spawn approval workflow (Phase 2: supervised)
- [ ] Add spawn event logging to graph

**Deliverables**:
- ✅ `ProactiveSpawnDetector` class
- ✅ Pattern detection queries
- ✅ Moral constraint validation for spawning

**Validation**:
```python
detector = ProactiveSpawnDetector(graphiti, constraint_validator)
opportunities = detector.scan_for_spawn_opportunities("lower_puna_elders")

# Should find unmet transport needs
assert any(o.suggested_servant_type == "transport" for o in opportunities)

# Should respect constraints
for opp in opportunities:
    assert opp.passed_constraint_validation
```

---

### 5.2 Implement Supervised Spawn Approval

**Goal**: Human-in-the-loop approval for proactive spawning

**Tasks**:
- [ ] Create spawn proposal UI in `shoghi_web_server.py`:
  ```python
  @app.route("/spawn_proposals", methods=["GET"])
  def get_spawn_proposals():
      detector = ProactiveSpawnDetector(graphiti, constraint_validator)
      opportunities = detector.scan_for_spawn_opportunities(community_id)

      return jsonify({
          "proposals": [
              {
                  "id": opp.id,
                  "servant_type": opp.suggested_servant_type,
                  "context": opp.context,
                  "urgency": opp.urgency,
                  "rationale": opp.explain()
              }
              for opp in opportunities
          ]
      })

  @app.route("/spawn_proposals/<proposal_id>/approve", methods=["POST"])
  def approve_spawn(proposal_id):
      # User approved - spawn servant
      opp = get_opportunity(proposal_id)
      factory = ProjectBasedAgentFactory(project_manager)
      agent = factory.create_agent_from_opportunity(opp)

      # Log approval in graph
      graphiti.create_node("SpawnEvent",
          opportunity_id=proposal_id,
          approved_by="user",
          approved_at=datetime.utcnow(),
          servant_id=agent.id
      )

      return jsonify({"status": "spawned", "agent_id": agent.id})
  ```

- [ ] Add voice interface support for approvals
- [ ] Add notification system

**Deliverables**:
- ✅ Spawn proposal UI
- ✅ Approval workflow
- ✅ Spawn event logging

**Validation**:
```bash
curl http://localhost:5000/spawn_proposals
# Returns: [{"id": "...", "servant_type": "transport", ...}]

curl -X POST http://localhost:5000/spawn_proposals/123/approve
# Returns: {"status": "spawned", "agent_id": "..."}
```

---

## Phase 6: Backup, Monitoring & Deployment (Week 7)

### 6.1 Implement Graph Backup System

**Goal**: Dual persistence (RDB + JSON exports)

**Tasks**:
- [ ] Configure Redis persistence in `redis.conf`:
  ```
  save 900 1
  save 300 10
  save 60 10000
  dir /data/falkordb
  dbfilename dump.rdb
  ```

- [ ] Implement JSON export in `shoghi/knowledge/backup.py`:
  ```python
  class GraphBackupManager:
      def export_all_graphs(self, output_dir: Path):
          communities = self._get_all_communities()
          for community_id in communities:
              self.export_community_graph(community_id, output_dir)

      def export_community_graph(self, community_id: str, output_dir: Path):
          # Implementation from ARCHITECTURE_DECISIONS.md
          pass

      def restore_from_backup(self, backup_file: Path):
          with open(backup_file) as f:
              data = json.load(f)

          # Restore nodes
          for node in data["nodes"]:
              self.graphiti.create_node(node["type"], **node["properties"])

          # Restore relationships
          for rel in data["relationships"]:
              self.graphiti.create_relationship(
                  rel["source"], rel["type"], rel["target"], **rel["properties"]
              )
  ```

- [ ] Create backup cron job:
  ```bash
  # crontab entry
  0 2 * * * python /home/user/shoghi/scripts/backup_graphs.py
  ```

**Deliverables**:
- ✅ Redis RDB configured
- ✅ JSON export script
- ✅ Restore script
- ✅ Automated daily backups

**Validation**:
```bash
python scripts/backup_graphs.py
ls backups/graphs/2025-11-20/  # ✅ JSON files exist

python scripts/restore_graph.py backups/graphs/2025-11-20/lower_puna_elders_graph.json
# ✅ Graph restored successfully
```

---

### 6.2 Add Performance Monitoring

**Goal**: Track latency targets and resource usage

**Tasks**:
- [ ] Create `shoghi/monitoring/metrics.py`:
  ```python
  class ShorghiMetrics:
      def __init__(self):
          self.metrics = {
              "servant_spawn_time": [],
              "graph_query_latency": [],
              "context_assembly_time": [],
              "vector_search_time": []
          }

      def record_spawn_time(self, duration_ms: float):
          self.metrics["servant_spawn_time"].append(duration_ms)
          if duration_ms > 2000:  # Target: <2s
              logger.warning(f"Slow spawn: {duration_ms}ms")

      def record_graph_query(self, duration_ms: float):
          self.metrics["graph_query_latency"].append(duration_ms)
          if duration_ms > 50:  # Target: <50ms p99
              logger.warning(f"Slow query: {duration_ms}ms")

      def get_stats(self) -> Dict:
          return {
              "spawn_time_p50": np.percentile(self.metrics["servant_spawn_time"], 50),
              "spawn_time_p99": np.percentile(self.metrics["servant_spawn_time"], 99),
              "query_latency_p50": np.percentile(self.metrics["graph_query_latency"], 50),
              "query_latency_p99": np.percentile(self.metrics["graph_query_latency"], 99),
              "context_assembly_p50": np.percentile(self.metrics["context_assembly_time"], 50),
          }
  ```

- [ ] Add Prometheus endpoint for metrics export
- [ ] Create Grafana dashboard

**Deliverables**:
- ✅ Metrics collection
- ✅ Performance dashboard
- ✅ Alerting for SLA violations

**Validation**:
```python
metrics = ShorghiMetrics()
stats = metrics.get_stats()
assert stats["spawn_time_p50"] < 2000  # ✅ Meeting target
assert stats["query_latency_p50"] < 10  # ✅ Meeting target
```

---

### 6.3 Update Deployment Scripts

**Goal**: Deploy full stack (FalkorDB + Shoghi + monitoring)

**Tasks**:
- [ ] Create `docker-compose.yml`:
  ```yaml
  version: '3.8'
  services:
    falkordb:
      image: falkordb/falkordb:latest
      ports:
        - "6379:6379"
      volumes:
        - /data/falkordb:/data
      restart: always

    shoghi:
      build: .
      depends_on:
        - falkordb
      environment:
        - FALKORDB_HOST=falkordb
        - FALKORDB_PORT=6379
      volumes:
        - ./work_dir:/app/work_dir
      restart: always

    prometheus:
      image: prom/prometheus
      ports:
        - "9090:9090"
      volumes:
        - ./prometheus.yml:/etc/prometheus/prometheus.yml

    grafana:
      image: grafana/grafana
      ports:
        - "3000:3000"
  ```

- [ ] Update `deploy_shoghi.sh` for new architecture
- [ ] Add health checks

**Deliverables**:
- ✅ Docker Compose configuration
- ✅ Updated deployment scripts
- ✅ Health checks

**Validation**:
```bash
docker-compose up -d
docker ps  # All services running
curl http://localhost:5000/health  # ✅ Shoghi healthy
redis-cli PING  # ✅ FalkorDB healthy
```

---

## Phase 7: Documentation & Testing (Week 8)

### 7.1 Write Comprehensive Documentation

**Tasks**:
- [ ] Update README.md with new architecture
- [ ] Create DEPLOYMENT_GUIDE.md
- [ ] Create COMMUNITY_GUIDE.md (for configuring privacy)
- [ ] Create API_REFERENCE.md
- [ ] Add inline code documentation

**Deliverables**:
- ✅ All documentation updated
- ✅ Architecture diagrams
- ✅ Example configurations

---

### 7.2 Integration Testing

**Tasks**:
- [ ] Create end-to-end tests:
  ```python
  def test_full_servant_lifecycle():
      # 1. Spawn servant
      agent = factory.create_agent_from_intent("coordinate transport", "lower_puna_elders")
      assert agent.project.work_dir.exists()

      # 2. Execute task
      result = agent.execute("Find transport for kupuna in Pahoa")
      assert result is not None

      # 3. Check graph updated
      nodes = graphiti.query("MATCH (s:Servant {id: $id}) RETURN s", id=agent.id)
      assert len(nodes) == 1

      # 4. Archive project
      project_manager.archive_project(agent.id)
      assert agent.project.status == ProjectStatus.ARCHIVED
  ```

- [ ] Test cross-community coordination
- [ ] Test privacy filtering
- [ ] Test backup/restore
- [ ] Load testing (performance targets)

**Deliverables**:
- ✅ Integration test suite (20+ tests)
- ✅ All tests passing

---

## Success Criteria

**Performance Targets:**
- ✅ Servant spawn time < 2 seconds
- ✅ Graph query latency < 10ms p50, < 50ms p99
- ✅ Context assembly < 100ms
- ✅ Cross-servant coordination discovery < 500ms

**Functional Requirements:**
- ✅ Servants run in isolated projects (no context contamination)
- ✅ Knowledge graph automatically builds from servant activities
- ✅ Cross-servant coordination emerges from graph queries
- ✅ Vector stores optimized (hybrid architecture)
- ✅ Privacy filtering prevents unauthorized access
- ✅ Moral constraints enforceable through graph topology
- ✅ Backup/restore tested and automated

**Quality:**
- ✅ All existing tests passing (241)
- ✅ New tests added (50+)
- ✅ Code coverage > 80%
- ✅ Documentation complete

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Graphiti performance issues | Medium | High | Load test early, optimize queries, consider caching |
| Context assembly >100ms | Medium | Medium | Profile thoroughly, optimize vector search, add caching |
| Memory leaks in long-running servants | Low | High | Add memory monitoring, implement automatic restarts |
| FalkorDB data corruption | Low | High | Dual persistence (RDB + JSON), test backups monthly |
| Privacy filter bypass | Low | Critical | Security audit, penetration testing, graph ACLs |

---

## Next Steps

1. **Review & Approve** this plan with stakeholders
2. **Set up development environment** (FalkorDB, dependencies)
3. **Begin Phase 1** (Foundation & Dependencies)
4. **Weekly check-ins** to track progress
5. **Adjust timeline** as needed based on learnings

---

**Prepared By:** Claude Code
**Date:** 2025-11-20
**Version:** 1.0
