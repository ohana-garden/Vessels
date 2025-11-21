# Agent Zero–Aligned Control Plane Schema

This schema proposes a new control-plane layout that fully aligns with Agent Zero features such as Model Context Protocol (MCP), agent-to-agent (A2A) links, Projects, Tools, and Instruments while explicitly integrating FalkorDB, Graphiti, Petals, and Nostr. It focuses on durable graph state, secure tool mediation, and composable agent lifecycles.

## Goals
- **Make MCP the default integration path** for all external systems so servants never talk to backends directly.
- **Treat Projects as first-class namespaces** for isolation, auditability, and policy enforcement.
- **Standardize Tools and Instruments** as declarative capabilities that can be scheduled, rate-limited, and audited.
- **Exploit the graph stack (FalkorDB + Graphiti)** for memory, topology, and policy evaluation instead of ad-hoc Python state.
- **Use A2A channels with Nostr-backed relays** so agents exchange signed intents and events across hosts.
- **Offer Petals as the shared model fabric** for heavy inference, keeping lightweight calls local.

## Core Entities
- **Project** — Owns servants, credentials, policies, and graph namespaces. Maps to a Graphiti namespace with FalkorDB as the backing store. Policies live as Graphiti rules and MCP policy documents.
- **Servant** — A Project-scoped agent with:
  - **MCP Client** configured to the Project’s broker, exposing Tools/Instruments.
  - **Graph Edge** to the Project namespace for reads/writes via Graphiti.
  - **A2A Identity** (Nostr keypair) used for authenticated inter-servant messaging.
  - **Workspace** (filesystem + secrets) tied to Project policies.
- **Tool** — Declarative capability exposed via MCP (e.g., `graph.query`, `nostr.publish`, `petals.generate`). Tools wrap specific Instruments and carry limits (rate, scope) plus audit metadata.
- **Instrument** — Concrete operation implementation (e.g., FalkorDB Cypher query, HTTP call to Petals, WebSocket to Nostr relay). Instruments are registered with the MCP broker and versioned.
- **Run** — Executions of a Tool/Instrument with inputs/outputs, logged to Graphiti as `Run` nodes linked to Servant and Project for lineage.
- **Channel** — A2A communication path (Nostr relay topic) with ACLs enforced at the MCP broker and validated by Nostr signatures.

### Why not make each Servant its own Project?
- **Projects aggregate shared policy and context.** Keeping multiple servants under one Project lets them share MCP tool registries, graph namespaces, and policy bundles while still isolating at the Servant level via namespaces, run lineage, and A2A keys. Making every servant a Project would fragment shared resources and force duplication of Tool/Instrument definitions.
- **Agent-to-agent collaboration benefits from Project scope.** A2A channels, Nostr relays, and Graphiti rules can be reused by servants within the same Project, enabling coordinated tasks without granting global trust. Separate Projects would need explicit cross-project federation and policy plumbing for even simple handoffs.
- **Security remains fine-grained without per-servant Projects.** Servant edges in Graphiti enforce namespace and policy checks; MCP broker policies can restrict per-servant Tool access; Nostr signatures remain per-servant. This preserves least privilege while avoiding per-servant infrastructure overhead.
- **Use per-servant Projects selectively.** When a servant must be fully air-gapped (e.g., handling export-controlled data), clone the Project scaffold and stand up a dedicated namespace, MCP broker, and A2A relay for that servant alone. Treat it as the exception, not the default, to keep operational complexity manageable.

## Data/Graph Model
- **Graphiti Schema (FalkorDB)**
  - Nodes: `Project`, `Servant`, `Tool`, `Instrument`, `Run`, `Resource`, `Policy`, `Channel`, `ExternalSystem` (e.g., Petals cluster, Nostr relay).
  - Relationships: 
    - `(:Project)-[:OWNS]->(:Servant|Tool|Instrument|Channel|Policy)`
    - `(:Servant)-[:USES]->(:Tool)`; `(:Tool)-[:IMPLEMENTS]->(:Instrument)`
    - `(:Run)-[:EXECUTED_BY]->(:Servant)`; `(:Run)-[:INVOKED]->(:Instrument)`; `(:Run)-[:WITHIN]->(:Project)`
    - `(:Servant)-[:COMMUNICATES_VIA]->(:Channel)`; `(:Channel)-[:BACKED_BY]->(:ExternalSystem {type: 'nostr'})`
    - `(:Tool)-[:BACKED_BY]->(:ExternalSystem {type: 'petals'|'falkordb'|'graphiti'})`
  - Policies evaluated through Graphiti hooks before write/read operations and encoded as rules on relationships.

## MCP-Centric Flow
1. **Project Bootstrap**
   - Create Graphiti namespace in FalkorDB; seed `Project` node, `Policy` nodes, and `ExternalSystem` descriptors for FalkorDB, Graphiti API, Petals endpoint, and Nostr relays.
   - Register MCP broker with Tools/Instruments definitions sourced from the graph (single source of truth).

2. **Servant Provisioning**
   - Agent Zero spawns a Servant with a Project-scoped MCP client and generates a Nostr keypair; store the public key in Graphiti linked to the Servant node.
   - Attach default Tools: `graph.query`, `graph.write`, `nostr.publish`, `nostr.subscribe`, `petals.generate`, `docs.search`, `web.fetch`, plus Project-specific Instruments.
   - Apply rate limits and policies via the MCP broker; refuse activation if required Tools are missing.

3. **Task Execution**
   - Servant receives a task; resolves capabilities to Tools (via MCP registry). Each invocation creates a `Run` node with inputs/outputs stored in FalkorDB for audit.
   - For graph operations, calls `graphiti_core` over MCP; Graphiti enforces namespace and evaluates policies before touching FalkorDB.
   - For heavy model calls, the `petals.generate` Tool routes prompts to the Petals cluster; responses cached as `Resource` nodes linked to Runs.
   - Inter-servant coordination uses A2A: Servant signs a Nostr event containing the intent, publishes through the `Channel` Tool; recipients validate signature and Project membership via Graphiti lookup.

4. **Learning & Memory**
   - Replace ad-hoc in-memory histories with Graphiti-backed trajectories: `Run` nodes plus summarized embeddings stored as `Resource` nodes (embedding jobs can be Tools pointing to Petals or local models).
   - Similarity search uses FalkorDB vector indexes; MCP exposes `memory.search` Tool so all servants share the same retrieval interface.

## Tool & Instrument Catalog (Examples)
- **Graphiti/FalkorDB**
  - Tool: `graph.query` → Instrument: `graphiti_core.query` (Cypher/GraphQL over MCP)
  - Tool: `graph.write` → Instrument: `graphiti_core.mutate`
- **Petals**
  - Tool: `petals.generate` → Instrument: `petals.rpc.forward` (with model name and max tokens)
  - Tool: `petals.embed` → Instrument: `petals.rpc.embed` (optional, fallback to local)
- **Nostr / A2A**
  - Tool: `nostr.publish` → Instrument: `nostr.relay.send`
  - Tool: `nostr.subscribe` → Instrument: `nostr.relay.listen`
- **Coordination & Ops**
  - Tool: `project.policy.check` → Instrument: Graphiti rule evaluation
  - Tool: `tool.registry.refresh` → Instrument: MCP broker reload from Graphiti definitions
  - Tool: `resource.fetch` → Instrument: `universal_connector.fetch` (HTTP/API), with policy filters

## Operational Guardrails
- **No silent mock fallback**: Initialization fails fast if Graphiti/FalkorDB or Petals clients are missing; Agent Zero surfaces readiness status per Project.
- **Policy-first**: Tool access requires Graphiti-backed policy checks; A2A messages must carry Nostr signatures verified against Project membership.
- **Observability**: All Tool runs emit structured events into Graphiti and a log sink (OpenTelemetry-friendly) keyed by Run IDs.
- **Recovery**: MCP broker maintains health of Instruments; unhealthy Instruments are quarantined and Servants receive degraded capability sets.

## Scaling Path (10k servants now, trillions later)
- **Stateless servant runtimes**: Keep Servants disposable; persist all state (runs, resources, policies, memory) to FalkorDB/Graphiti and external object stores so Servants can be horizontally auto-scaled and pre-empted.
- **Multi-tenant MCP broker sharding**: Partition Projects across MCP broker pools; brokers expose only the Tools/Instruments for the Projects they serve. Use consistent hashing of Project IDs to assign brokers and support zero-downtime rebalance.
- **Graph namespace partitioning**: Allocate a FalkorDB/Graphiti namespace per Project and shard namespaces across graph clusters. Use read replicas for fan-out queries and write quorums for durability. Keep Tool registration cached at the broker to reduce graph round-trips.
- **Tool/Instrument catalogs as code**: Store Tool/Instrument definitions in Graphiti but cache compiled registries at the broker layer; invalidate via signed Nostr events (`tool.registry.refresh`) to avoid thundering herds during mass servant startups.
- **Petals and model fabric scaling**: Treat Petals endpoints as Instruments with health/latency scoring. Brokers route Servants to the nearest healthy Petals shard; store large outputs in object storage and reference them as `Resource` nodes to keep graph payloads small.
- **A2A/Nostr fan-out**: Use multiple Nostr relays per Project with per-channel rate limits; Servants subscribe to project-specific relays only. For global broadcast, employ a relay mesh with signed envelopes referencing graph IDs rather than large payloads.
- **Placement-aware scheduling**: Co-locate Servants with their assigned MCP broker and primary graph shard to minimize latency; embed placement hints in the Project node so orchestrators can schedule intelligently.
- **Control-plane elasticity**: Track Servant concurrency and Tool invocation rates via Run nodes; auto-scale brokers, relays, and Petals shards based on demand while enforcing per-Project quotas stored in Graphiti policies.

## Migration Steps from Current State
1. **Promote Graphiti to the primary data path** and remove mock fallbacks; ensure FalkorDB is provisioned per Project namespace.
2. **Wrap existing helpers** (`community_memory`, grant tools, universal connector) as MCP Instruments and register them as Tools in Graphiti.
3. **Add Nostr identity/A2A module** to replace ad-hoc message queues; persist keys and channels in Graphiti.
4. **Introduce Petals-backed Tools** for generation/embedding; add caching of outputs into `Resource` nodes.
5. **Wire Agent Zero spawning** to Project-scoped MCP clients and policy checks before activation; refuse to spawn when mandatory Tools are unavailable.
6. **Backfill Runs and policies** for observability: every task execution should create `Run` nodes with linkage to Servants, Tools, Instruments, and Resources.
