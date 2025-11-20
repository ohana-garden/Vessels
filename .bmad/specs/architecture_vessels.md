---
id: ARCH-001
title: Vessels System Architecture
author: Stephen
date: 2025-11-11
---

## Architecture Overview

Vessels’s architecture can be visualized as a multi-layer system:

- **User Interface Layer**: provides a voice-first web interface and CLI. Uses Flask and websockets for asynchronous communication and serves content via HTML and CSS.
- **Agent Orchestration Layer**: coordinates specialized agents using dynamic_agent_factory and agent_zero_core. Each agent is a micro-service implementing a single responsibility, described by BMAD agent definition files (analyst, architect, developer, etc.).
- **Task Execution Layer**: implements domain logic for grant discovery, elder care, community memory and connectivity. Contains modules like grant_coordination_system, community_memory, dynamic agent tasks, and content_generation.
- **Infrastructure Layer**: manages deployment, packaging, and runtime environment (Docker, auto_deploy script, start_vessels.sh). Includes the universal connector, voice interface integration and network resilience.
- **BMAD Artifacts Layer**: stores BMAD-specific metadata (agent specs, story files, control manifests, PRDs) in the .bmad folder.

### Component Diagram (textual)

```
[User] → [Web Server (Flask)] ↔ [Agent Orchestrator] ↔ [Specialized Agents (Analyst, Architect, Developer, Tester, Deployer)] ↔ [Task Modules] ↔ [Data Stores]
```

### Data Flow

1. **Input**: Users interact via the voice interface or CLI. Requests are captured by the web server.
2. **Orchestration**: The agent orchestrator interprets the request and loads relevant agent definitions from `.bmad/agents`. It spawns the necessary agents.
3. **Execution**: Each agent uses context shards and story files from `.bmad/stories` to generate code, tasks, and content. Agents coordinate to implement features like grant discovery or elder care protocols.
4. **Persistence**: Results and metrics are stored in community_memory and local SQLite databases. Additional metrics are recorded for BMAD evaluation.
5. **Output**: The orchestrator assembles responses (cards, subtitles, protocols) and sends them back to the user interface.

### Key Design Principles

- **Modularity**: Every component is a micro-service or agent with a single responsibility.
- **Resilience**: Network requests use timeouts and retries. Data persistence ensures state is not lost across sessions.
- **Extensibility**: New agents and story files can be added to `.bmad` without changing core code.
- **Transparency**: Documented PRDs, architecture diagrams, story files and control manifests provide traceability and auditability.
- **User-Centric Design**: The voice-first interface and culturally contextual language ensure the system meets community needs.
