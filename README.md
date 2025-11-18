# Shoghi

Shoghi is an open-source agent-driven platform developed by Ohana Garden for community coordination, grant management, and contextual content generation. The repository contains an extensible Python codebase that implements conversational/assistant agents, content and memory subsystems, grant coordination tooling, and an optional web UI.

**NEW:** Shoghi now includes the **Ethical Agents Framework** - a breakthrough system for creating agents through natural voice conversation that learn, evolve, and reproduce. See [ETHICAL_AGENTS_FRAMEWORK.md](ETHICAL_AGENTS_FRAMEWORK.md) for the complete vision.

This README is a fresh, practical guide for developers and maintainers to get the project running, understand its architecture, and contribute effectively.

Table of contents
- Project overview
- Quick start
  - Prerequisites
  - Environment and install
  - Run locally (examples)
- Key modules and architecture
- Data and persistence
- Configuration
- Tests
- Deployment
- Contributing
- Important documentation & design artifacts
- License & contact

Project overview
Shoghi combines:
- agent frameworks and orchestration (agent_zero_core.py, dynamic_agent_factory.py)
- content generation and adaptive tooling (content_generation.py, adaptive_tools.py)
- a persistent community memory layer (community_memory.py)
- grant coordination / management features (grant_coordination_system.py, grant_coordination_fixed.py, KALA.md)
- connectors and UI glue (universal_connector.py, voice_interface.py, shoghi_web_server.py)
It is designed to be run as a local service or deployed in a containerized environment.

Quick start

Prerequisites
- Python 3.10+ (confirm local version)
- Git
- pip
- Optional: Docker & docker-compose for containerized deployments

Environment and install (recommended)
1. Clone repository
   git clone https://github.com/ohana-garden/shoghi.git
   cd shoghi

2. Create virtualenv and install
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

3. Copy env template and set secrets/config
   cp .env.example .env
   (Edit .env to add any API keys, DB locations, and other secret config)

Run locally — common entry points
- Run the demo harness:
  python demo_shoghi.py

- Run the Living Agents Framework demo (NEW):
  python demo_living_agents.py
  (Demonstrates contextual arrivals, agent creation, evolution, reproduction, multi-user coordination)

- Run the web server (if desired):
  python shoghi_web_server.py
  Then open the configured port (default in .env or server script)

- Run core agent program:
  python shoghi.py
  or use shoghi_fixed.py if you need the fixed branch behavior.

- For testing:
  pytest -q

Key modules and architecture

**Core Platform:**
- agent_zero_core.py — core agent orchestration; entrypoint for agent lifecycle
- dynamic_agent_factory.py — factory for creating agent instances dynamically
- content_generation.py — content generation pipeline and helpers
- community_memory.py — persistent memory & retrieval layer
- grant_coordination_system.py / grant_coordination_fixed.py — grant workflows and coordination logic
- kala.py & KALA.md — special KALA subsystem and design doc
- universal_connector.py — connectors to external systems/APIs
- voice_interface.py — voice UI helpers and integration
- shoghi_web_server.py — lightweight HTTP server to expose UI or API endpoints
- demo_shoghi.py — demonstration harness and examples
- Various scripts: deploy_shoghi.sh, deploy_fixed.sh, start_shoghi.sh

**Ethical Agents Framework** (NEW):
- shoghi_living_agents.py — Main integration API for living agents system
- context_engine.py — Contextual arrival and screen state determination
- conversational_agent_creation.py — Natural dialogue-based agent creation
- rich_agent_identity.py — Complete agent identity with learning & memory
- choreography_engine.py — Cinematic timing and pacing (TV/movie-like UX)
- conversation_orchestrator.py — Multi-agent dialogue management
- agent_evolution.py — Agent learning, evolution, and reproduction
- multi_user_coordination.py — Multi-user sessions with agent coordination
- ETHICAL_AGENTS_FRAMEWORK.md — Complete framework documentation

**Moral Constraint System** (shoghi/ subdirectory):
- shoghi/measurement/ — 5D operational + 7D virtue measurement
- shoghi/constraints/ — Bahá'í-inspired ethical constraints
- shoghi/gating/ — Action validation and blocking
- shoghi/phase_space/ — Trajectory tracking and attractor discovery
- shoghi/intervention/ — Intervention strategies for misaligned agents

Data & persistence
- shoghi_grants.db — example SQLite DB present in repo. Production deployments should move to a proper RDBMS and configure DATABASE_URL accordingly.
- community_memory.py contains storage/hydration logic; review/replace with a scalable store for production.

Configuration
- requirements.txt lists runtime dependencies.
- Provide these environment variables at minimum (examples):
  - DATABASE_URL — e.g., sqlite:///./shoghi_grants.db or Postgres URI
  - SHOGHI_PORT — port for web server
  - LOG_LEVEL — INFO / DEBUG / WARNING
  - Any third-party API keys used by connectors

- **For Ethical Agents Framework with LLM (optional but recommended):**
  - LLM_PROVIDER — "anthropic", "openai", or "local" (default: "local")
  - ANTHROPIC_API_KEY — your Anthropic Claude API key (if using Anthropic)
  - OPENAI_API_KEY — your OpenAI API key (if using OpenAI)
  - Note: Framework works without LLM using template-based responses

- Add a .env.example for easy onboarding (if not present).

Testing
- Unit tests are included as test_*.py files. Run:
  pytest tests/  (or pytest -q in the repo root)
- Add CI workflow (.github/workflows/) to run tests on PRs.

Deployment
- Two deploy scripts exist: deploy_shoghi.sh and deploy_fixed.sh. They are a starting point; review and containerize as needed.
- Suggested flow for production:
  - Containerize app (Dockerfile)
  - Use environment-specific secrets via a secret manager
  - Migrate DB to Postgres and run migrations
  - Configure health checks and rolling deploys

Contributing
- Workflow: create a branch on your fork, open a PR against merge/all-into-main for integration, or main after review.
  - Branch naming: feature/<short-desc>, fix/<short-desc>, docs/<short-desc>
  - Include tests for new behavior
  - Follow code style (black / flake8) and add minimal changelog entry
- If you’re a maintainer: use the integration branch merge/all-into-main to aggregate incoming feature branches before merging to main.

Important documentation & design artifacts
- **ETHICAL_AGENTS_FRAMEWORK.md** — Complete vision and documentation for the living agents system (NEW)
- KALA.md — subsystem documentation for KALA value measurement
- SHOGHI_COMPLETE.md and SHOGHI_FINAL_COMPLETE.md — larger design/notes that document the project history and intended behaviors
- shoghi/README.md — Moral constraint system documentation
- Review these files to understand design trade-offs and historical context before making large changes.

Quick start with Ethical Agents Framework
```python
from shoghi_living_agents import ShoghiLivingAgents

# Initialize
shoghi = ShoghiLivingAgents()

# User arrives (biometric recognition)
arrival = await shoghi.user_arrives(user_id="user_123")
# → Returns contextual conversation already in progress

# Create agent through conversation
creation = shoghi.start_agent_creation(user_id="user_123")
result = await shoghi.process_creation_input(
    creation.creation_id,
    "We need help caring for our elders"
)
# → Agent guides through kuleana, persona, skills, knowledge, lore, ethics

# Multi-user session
session = await shoghi.create_multi_user_session(
    host_id="user_123",
    title="Community Planning",
    session_type="coordination"
)
# → Multiple humans watch their agents coordinate
```

See ETHICAL_AGENTS_FRAMEWORK.md for complete examples and scenarios.

Next improvements (recommended)
- Create .env.example with documented variables
- Add a Dockerfile and docker-compose for a reproducible dev environment
- Add automated test workflow (.github/actions) to run tests and linters on PRs
- Centralize configuration and secrets handling
- Split big modules into smaller packages for maintainability

License & contact
- Add a LICENSE file (MIT or other preferred license) if not already present.
- Maintainers: Ohana Garden — https://github.com/ohana-garden
- For questions, open an issue in this repo.

Appendix: commands summary
- Install: python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
- Run demo: python demo_shoghi.py
- Run server: python shoghi_web_server.py
- Tests: pytest -q
