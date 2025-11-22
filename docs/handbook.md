# Vessels Codebase Handbook

## Executive summary
Vessels is a Python-based adaptive coordination platform that boots a full stack of subsystems—agent orchestration, shared memory, graph storage, tool/connector registries, and interfaces—through the `VesselsPlatform` entry point. On startup it wires the hive mind memory, adaptive tools, Agent Zero coordination core, grant coordination, universal connectors, interface layer, and deployment helpers, then drives either an interactive loop or background service tasks depending on mode.【F:vessels.py†L3-L140】【F:vessels.py†L179-L269】

## File-by-file runtime guide

### Orchestration and platform shell
- **`vessels.py`** – Main entry script that configures logging, instantiates `VesselsPlatform`, initializes all subsystems (hive mind, tools, agent core, grants, connectors, interface, deployer), runs interactive or service loops, exposes status/command CLI, and performs graceful shutdown sequencing.【F:vessels.py†L36-L380】【F:vessels.py†L431-L470】

### Agent coordination and factory
- **`agent_zero_core.py`** – Defines agent states/specifications, manages live agent instances with coordination and message threads, interprets community needs into specialized agent specs, and seeds grant/coordination/elder-care/general agents before supervising them via a coordination loop.【F:agent_zero_core.py†L26-L118】【F:agent_zero_core.py†L136-L200】
- **`dynamic_agent_factory.py`** – Turns natural-language requests into agent deployments by loading intent patterns (configurable JSON), mapping capabilities and tools, generating `AgentSpecification` objects, and deploying them through the Agent Zero core; includes BMAD agent loading fallback.【F:dynamic_agent_factory.py†L20-L170】

### Memory, hive mind, and projects
- **`community_memory.py`** – Shared memory subsystem using on-disk SQLite with WAL tuning, vector embeddings (SentenceTransformer with hash fallback), Kala contributions, relationship graph tracking, and search/recommendation helpers; maintains event streams and persists memories/events per agent.【F:community_memory.py†L53-L200】【F:community_memory.py†L242-L416】
- **`vessels/hive_mind.py`** – Thread-safe wrapper exposing a single shared `HiveMind` interface so all servants record experiences, search, share learnings, and stream events through CommunityMemory with lock protection.【F:vessels/hive_mind.py†L1-L61】
- **`vessels/projects/project.py`** – Represents an isolated servant project with its own workspace, Graphiti client, vector store, config persistence, status lifecycle, and access to the shared hive mind; lazy-loads graph clients with optional mock flag and records archive events.【F:vessels/projects/project.py†L2-L142】【F:vessels/projects/project.py†L168-L195】

### Graph/knowledge layer
- **`vessels/knowledge/graphiti_client.py`** – Vessels-specific Graphiti/FalkorDB wrapper that enforces community namespaces, optional mock fallback, health checks, and simplified node/relationship creation with audit properties (created_by, timestamps) plus temporal/privacy scaffolding.【F:vessels/knowledge/graphiti_client.py†L2-L135】【F:vessels/knowledge/graphiti_client.py†L134-L200】
- **`vessels/knowledge/schema.py`** – Enumerates node/relationship/property enums and validation rules for the FalkorDB-backed knowledge graph, covering servants, community resources, experiences/facts, commercial entities, and temporal/privacy attributes used across graph clients.【F:vessels/knowledge/schema.py†L1-L120】【F:vessels/knowledge/schema.py†L64-L120】

### Tools, connectors, and content utilities
- **`adaptive_tools.py`** – Secure tool registry defining typed tool specs and handlers (web scraping, document generation placeholder, API integration, etc.), safe execution with validation, usage tracking, and insight reporting, replacing earlier dynamic code generation.【F:adaptive_tools.py†L3-L156】
- **`universal_connector.py`** – Connector manager with typed specifications, env-driven credentials, rate limiting scaffolding, built-in connectors (e.g., grants.gov, Foundation Center, QuickBooks), and methods to create/execute tracked connector instances safely.【F:universal_connector.py†L3-L159】【F:universal_connector.py†L195-L210】
- **`content_generation.py`** – Provides templated content and grant-application narrative helpers invoked by other modules (e.g., grant systems) to assemble user-facing outputs.【F:content_generation.py†L1-L120】
- **`menu_builder.py`** – Constructs structured menu/option dictionaries for navigation or UI layers, used across interfaces for consistent responses.【F:menu_builder.py†L1-L120】

### Grant coordination and finance
- **`grant_coordination_system.py`** – Long-running grant management engine with in-memory databases, discovery/writing/monitoring threads, structured grant/application dataclasses, and status tracking for the full pipeline.【F:grant_coordination_system.py†L3-L117】
- **`grant_coordination_fixed.py`** – Alternate “fixed” grant coordinator that uses persistent SQLite, resilient HTTP sessions, and real grant source scraping plus deduplication for production-like discovery/storage flows.【F:grant_coordination_fixed.py†L3-L79】
- **`bmad_loader.py`** – Helper to load BMAD agent specifications from local `.bmad` directories, enabling richer agent catalogs for the factory.【F:bmad_loader.py†L1-L120】
- **`kala.py`** – Defines Kala contribution valuation/tracking constructs used by CommunityMemory to record and price community contributions.【F:kala.py†L1-L120】

### Interfaces and deployment
- **`vessels_interface.py`** – Natural-language interface layer that processes user messages, routes to the agent factory/core, and returns structured responses for CLI or UI consumers.【F:vessels_interface.py†L1-L140】
- **`voice_interface.py`** & **`vessels_web_server.py`** – Voice and web endpoints: Flask server secures the voice-processing route with payload validation and renders the UI, while the voice interface handles audio/upload parsing and forwards text to the Vessels interface.【F:voice_interface.py†L1-L140】【F:vessels_web_server.py†L1-L120】
- **`auto_deploy.py`** – Deployment helper exposing functions to assemble Docker Compose snippets with environment-driven secrets and to launch/track deployments for the platform.【F:auto_deploy.py†L1-L160】
- **`demo_vessels.py` / `vessels_fixed.py` / `vessels_interface.py`** – Alternate entry/demo runners showcasing specific platform configurations or fixed behaviors alongside the primary `vessels.py` entrypoint.【F:demo_vessels.py†L1-L120】【F:vessels_fixed.py†L1-L120】

### Agent governance, communication, and compute packages (vessels/)
- **`vessels/agents/*`** – Governance utilities for commercial and community agents: taxonomy/enums for identities and relationships, disclosure packages, commercial gateway logic, policy definitions, vector-store helpers, and constraint scaffolding used when spawning or supervising servants.【F:vessels/agents/gateway.py†L1-L160】【F:vessels/agents/policy.py†L1-L120】
- **`vessels/communication/*`** – Nostr adapter, protocol registry, and sanitizer functions that publish/consume decentralized coordination events with optional keypair management and content cleaning for relays.【F:vessels/communication/nostr_adapter.py†L1-L120】
- **`vessels/compute/*`** – LLM routing and Petals gateway for scaling model inference: routes workloads to local/remote models and optionally taps Petals’ distributed GPU mesh for large models with safety guardrails.【F:vessels/compute/petals_gateway.py†L1-L80】
- **`vessels/constraints/*`, `vessels/gating/*`, `vessels/phase_space/*`, `vessels/intervention/*`, `vessels/measurement/*`** – Moral/operational constraint validators, event gates, phase-space state trackers, intervention strategies, and virtue/state measurement utilities that enforce policies around servant behavior and safety.【F:vessels/constraints/validator.py†L1-L120】【F:vessels/gating/gate.py†L1-L120】【F:vessels/phase_space/tracker.py†L1-L80】
- **`vessels/device/*`** – On-device emotion/voice components plus local LLM runner (ExecuTorch/llama.cpp/MLC) to keep classification, STT/TTS, and quick intent inference on trusted hardware before escalating to larger models.【F:vessels/device/local_llm.py†L1-L105】

