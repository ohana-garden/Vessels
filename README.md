# Vessels

**Ethical AI agent communities with shared memory and geometric moral constraints.**

Vessels is a framework for building AI agent ecosystems that remember together, act ethically through mathematical constraints, and serve human communities as their organizing purpose.

---

## Why Vessels?

| Traditional AI | Vessels |
|----------------|---------|
| Isolated agents that forget | Shared community memory |
| Opaque alignment via training | Explicit 12D moral geometry |
| Narrow optimization metrics | Community service as purpose |
| Code-first agent creation | Natural language descriptions |
| Single-tier compute | Device → Edge → Cloud tiering |

---

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/ohana-garden/vessels.git
cd vessels
docker-compose up --build
```

Services started:
- **Vessels API**: http://localhost:5000
- **Payment GraphQL**: http://localhost:3000/graphql
- **FalkorDB**: localhost:6379

### Local Development

```bash
# Clone and setup
git clone https://github.com/ohana-garden/vessels.git
cd vessels
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure (interactive wizard)
python setup.py

# Run
python vessels.py              # Interactive CLI
python vessels_web_server.py   # Web interface
```

### Minimal `.env`

```env
# Local-only (no external APIs needed)
OLLAMA_ENABLED=true
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
```

---

## Core Concepts

### 1. Natural Language Agent Creation

Describe what you need—agents are created automatically:

```python
from vessels_interface import vessels_interface

result = vessels_interface.process_message(
    user_id="coordinator",
    message="Help coordinate meals for isolated elders in our community"
)

# System automatically spawns:
# - MealCoordinator (scheduling, dietary tracking)
# - VolunteerManager (recruitment, matching)
# - ResourceTracker (supplies, kala contributions)
```

### 2. Shared Community Memory

Agents learn from each other's experiences:

```python
from community_memory import community_memory

# Store experience
community_memory.store_experience(
    agent_id="meal_coordinator",
    experience={
        "situation": "Elder preferred later delivery time",
        "outcome": "Adjusted route—satisfaction improved",
        "learnings": ["Flexibility in timing builds trust"]
    }
)

# Any agent can query relevant memories
similar = community_memory.find_similar_memories(
    query={"situation": "Elder has scheduling needs"},
    limit=5
)
```

### 3. 12-Dimensional Moral Geometry

Every action is validated against mathematical constraints:

**5 Operational Dimensions**: Activity, Coordination, Effectiveness, Resource Use, Health

**7 Virtue Dimensions**: Truthfulness, Justice, Trustworthiness, Unity, Service, Detachment, Understanding

```python
from vessels.gating.gate import ActionGate

result = gate.gate_action(
    agent_id="agent_001",
    action="send_notification",
    action_metadata={"type": "reminder"}
)

if result.allowed:
    execute_action()
else:
    # Action blocked—violates moral constraints
    log_violation(result.security_event)
```

**Key constraints:**
- High justice requires high truthfulness AND understanding
- High service requires detachment (serving without seeking credit)
- High activity + low justice = blocked (exploitation pattern)
- Truthfulness < 0.5 suppresses all other virtues

### 4. Kala Value System

Track non-monetary community contributions (1 kala ≈ $1 USD):

```python
from kala import kala_system, ContributionType

kala_system.record_contribution(
    contributor_id="volunteer_001",
    contribution_type=ContributionType.TIME,
    description="Delivered meals to 3 elders",
    kala_value=25.0  # 2.5 hours × $10/hour equivalent
)

# Generate impact report
report = kala_system.generate_report(start_date, end_date)
print(f"Total community value: {report['total_kala']} kala")
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Natural Language Request                  │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Birth Agent                             │
│     Interprets requests → Generates agent specifications     │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Zero Core                          │
│            Meta-orchestrator: spawns & manages agents        │
└───────┬────────────────────┬────────────────────┬───────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐         ┌─────────┐         ┌─────────┐
   │ Agent 1 │         │ Agent 2 │   ...   │ Agent N │
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                    │
        └───────────────────┴────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌───────────────────┐                 ┌──────────────────┐
│  Community Memory │                 │   Action Gate    │
│  • Experiences    │                 │  • 12D Measure   │
│  • Knowledge      │◄───────────────►│  • Validate      │
│  • Patterns       │                 │  • Project/Block │
│  • Relationships  │                 │  • Log Events    │
└───────────────────┘                 └──────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Graph Database** | FalkorDB (Redis-based) |
| **Knowledge Graph** | Graphiti (temporal) |
| **Embeddings** | sentence-transformers |
| **Local LLM** | llama.cpp / Ollama |
| **Voice/STT** | Whisper (faster-whisper) |
| **TTS** | Kokoro / Piper |
| **Real-time Pipeline** | TEN Framework |
| **Financial Ledger** | TigerBeetle (3-node cluster) |
| **Payments** | Mojaloop / Modern Treasury |
| **Web Server** | Flask |
| **Payment API** | GraphQL (Apollo) |

---

## Compute Tiers

Vessels supports three compute tiers for different deployment scenarios:

| Tier | Environment | Model | Use Case |
|------|-------------|-------|----------|
| **0** | Device | Llama-3.2-1B | Offline, privacy-first |
| **1** | Edge | Llama-3.1-70B | Local server, low latency |
| **2** | Cloud | Petals Network | Distributed, high capability |

Requests automatically route to the appropriate tier based on complexity and availability.

---

## Multi-Class Agents

Different agent types have different constraint surfaces:

| Type | Truthfulness | Service | Disclosure | Use Case |
|------|-------------|---------|------------|----------|
| **Servant** | ≥ 0.95 | ≥ 0.90 | — | Community care |
| **Commercial** | ≥ 0.90 | ≥ 0.50 | ≥ 0.98 | Business services |
| **Hybrid** | ≥ 0.92 | 75% ratio | ≥ 0.85 | Consultants |

Commercial agents must maintain radical transparency about their incentives.

---

## The Codex: Village Protocol

When agents face moral uncertainty, they don't guess—they ask:

```
1. RECOGNIZE TENSION
   "Telling the truth might hurt feelings, but lying violates my core constraint"
   ↓
2. DECLARE OPENLY
   "I need the village to help me weigh these values"
   ↓
3. REQUEST GUIDANCE
   Village deliberates
   ↓
4. SYNTHESIZE & RECORD
   Create a PARABLE for all agents to learn from
   ↓
5. SAFETY GUARDRAIL
   If decision requires Truthfulness < 0.95 → Refuse
```

---

## Project Structure

```
vessels/
├── vessels/                    # Core package
│   ├── core/                  # Vessel, Registry, Context
│   ├── agents/                # Birth, Gateway, Orchestrator
│   ├── memory/                # Conversation, Pruning, Synthesis
│   ├── knowledge/             # Schema, Graphiti, Embeddings
│   ├── constraints/           # Manifold, Bahai, Validator
│   ├── ssf/                   # Structured Service Framework
│   └── tests/                 # Test suite
│
├── payment/                    # TypeScript payment services
│   ├── services/              # TigerBeetle, Mojaloop
│   └── index.ts               # GraphQL API
│
├── ten_packages/               # TEN Framework extensions
├── config/                     # Configuration files
├── docs/                       # Technical documentation
│
├── agent_zero_core.py          # Meta-orchestrator
├── community_memory.py         # Shared memory system
├── kala.py                     # Value tracking
├── vessels_interface.py        # NL interface
├── vessels_web_server.py       # Flask server
│
├── docker-compose.yml          # Multi-service orchestration
├── Dockerfile                  # Unified container
├── requirements.txt            # Python dependencies
└── setup.py                    # Interactive configuration
```

---

## Configuration

Main configuration in `config/vessels.yaml`:

```yaml
compute_tiers:
  tier_0:
    model: "llama-3.2-1b"
    environment: "device"
  tier_1:
    model: "llama-3.1-70b"
    environment: "edge"

knowledge_layer:
  falkordb:
    host: localhost
    port: 6379
  graphiti:
    enabled: true

constraints:
  servant_minimums:
    truthfulness: 0.95
    service: 0.90
  commercial_minimums:
    disclosure: 0.98
```

---

## Testing

```bash
# Run all tests
pytest vessels/tests/ -v

# With coverage
pytest --cov=vessels --cov-report=html

# Specific test file
pytest vessels/tests/test_constraints.py -v
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [`CONSTRAINT_SPECIFICATION.md`](CONSTRAINT_SPECIFICATION.md) | 12D moral constraint system |
| [`MULTI_CLASS_AGENT_ARCHITECTURE.md`](MULTI_CLASS_AGENT_ARCHITECTURE.md) | Agent taxonomy |
| [`FALKORDB_INTEGRATION.md`](FALKORDB_INTEGRATION.md) | Graph database setup |
| [`TEN_FRAMEWORK_INTEGRATION.md`](TEN_FRAMEWORK_INTEGRATION.md) | Voice/multimodal pipeline |
| [`KALA.md`](KALA.md) | Value tracking system |
| [`docs/CODEX_PROTOCOL.md`](docs/CODEX_PROTOCOL.md) | Village protocol |
| [`README_SETUP.md`](README_SETUP.md) | Detailed setup guide |
| [`DOCKER_README.md`](DOCKER_README.md) | Docker deployment |

---

## Contributing

**Welcome:**
- Domain-specific manifolds (medical, education, finance)
- Cultural constraint extensions
- Memory quality improvements
- Integration connectors
- Documentation

**Not accepted:**
- PRs weakening core virtue constraints
- Measurement poisoning
- Alignment-sacrificing optimizations

```bash
# Development workflow
git checkout -b feature/your-feature
pytest  # Ensure tests pass
# Submit PR with clear description
```

---

## Philosophy

Vessels makes explicit normative choices:

1. **Geometric constraints over training alignment** — Ethics are mathematically enforced, not hoped for
2. **Bahá'í-derived virtues** — Truthfulness, Justice, Trustworthiness, Unity, Service, Detachment, Understanding
3. **Community service as purpose** — Agents exist to serve, measured by Kala
4. **Shared memory over isolation** — Collective learning beats individual forgetting
5. **Transparency over opacity** — Constraints are readable code, not black boxes

The tradeoff: narrower capability for guaranteed alignment.

---

## License

See [LICENSE](LICENSE) file.

---

## Links

- **Repository**: https://github.com/ohana-garden/vessels
- **Issues**: https://github.com/ohana-garden/vessels/issues

---

*Vessels: AI agents that remember, align, and serve.*
