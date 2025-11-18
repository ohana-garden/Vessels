# Shoghi

**An AI Agent Alignment Platform with Moral Constraints**

Shoghi is an open-source platform developed by Ohana Garden that combines moral constraint-based agent alignment with community coordination, grant management, and contextual content generation. It implements a unique approach to AI safety by tracking agent behavior in a 12-dimensional moral "phase space" and enforcing Bahá'í-derived virtue constraints on all agent actions.

---

## Table of Contents

- [What Makes Shoghi Unique](#what-makes-shoghi-unique)
- [Quick Start](#quick-start)
- [Core Architecture](#core-architecture)
- [The Moral Constraint System](#the-moral-constraint-system)
- [Platform Features](#platform-features)
- [Key Modules](#key-modules)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [License & Contact](#license--contact)

---

## What Makes Shoghi Unique

### 1. Moral Geometry for AI Alignment

Shoghi tracks every agent action in a **12-dimensional phase space** combining:
- **5D Operational Metrics**: Activity, coordination, effectiveness, resource use, system health
- **7D Virtue State**: Truthfulness, justice, trustworthiness, unity, service, detachment, understanding

All actions are **gated** through constraint validation. Invalid states are either projected to valid states or blocked entirely.

### 2. Bahá'í-Derived Virtue Constraints

The system implements explicit numeric coupling rules between virtues:
- **Truthfulness is load-bearing**: High levels of other virtues require adequate truthfulness
- **Justice requires support**: Active justice work requires both truthfulness and understanding
- **Service requires detachment**: Service must be ego-detached, not performative
- **Cross-space constraints**: Patterns like "high activity + low justice" are geometrically invalid

See [CONSTRAINT_SPECIFICATION.md](./CONSTRAINT_SPECIFICATION.md) for the complete specification.

### 3. Attractor-Based Behavioral Steering

The system uses **DBSCAN clustering** to discover stable behavioral patterns (attractors) in the 12D space. Detrimental attractors trigger interventions ranging from warnings to capability restrictions.

### 4. Community Value Measurement (Kala)

Kala is a non-monetary value measurement unit (loosely pegged at 1 kala ≈ $1 USD) that enables communities to:
- Track volunteer time and in-kind contributions
- Value non-monetary social contributions
- Report community impact to funders
- Recognize small acts of service

See [KALA.md](./KALA.md) for details.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Git
- pip
- Optional: Docker for containerized deployment

### Installation

```bash
# Clone repository
git clone https://github.com/ohana-garden/shoghi.git
cd shoghi

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run the Demo

```bash
# Interactive mode
python demo_shoghi.py

# Or start the full platform
python shoghi.py

# Or run the web server
python shoghi_web_server.py
```

### Basic Usage of Moral Constraint System

```python
from shoghi.constraints.bahai import BahaiManifold
from shoghi.measurement.operational import OperationalMetrics
from shoghi.measurement.virtue_inference import VirtueInferenceEngine
from shoghi.gating.gate import ActionGate

# Initialize components
manifold = BahaiManifold()
operational_metrics = OperationalMetrics()
virtue_engine = VirtueInferenceEngine()

# Create action gate
gate = ActionGate(
    manifold=manifold,
    operational_metrics=operational_metrics,
    virtue_engine=virtue_engine,
    latency_budget_ms=100.0,
    block_on_timeout=True
)

# Record agent behavior
agent_id = "agent_001"
operational_metrics.record_action(agent_id, "generate_response")
virtue_engine.record_factual_claim(agent_id, "claim text", verified=True)

# Gate an action
result = gate.gate_action(agent_id, "send_message_to_user")

if result.allowed:
    print(f"✅ Action allowed: {result.reason}")
else:
    print(f"🚫 Action blocked: {result.reason}")
```

---

## Core Architecture

Shoghi has a dual architecture:

### 1. Core Moral Constraint System (`shoghi/` package)

```
shoghi/
├── measurement/          # State measurement
│   ├── state.py         # 12D phase space data structures
│   ├── operational.py   # 5D operational metrics
│   └── virtue_inference.py  # 7D virtue inference
├── constraints/         # Moral geometry
│   ├── manifold.py      # Base manifold class
│   ├── bahai.py         # Bahá'í reference manifold
│   └── validator.py     # Constraint validation & projection
├── gating/              # Action control
│   ├── events.py        # SecurityEvent and StateTransition
│   └── gate.py          # Action gating logic
├── phase_space/         # Trajectory analysis
│   ├── tracker.py       # SQLite trajectory storage
│   └── attractors.py    # DBSCAN attractor discovery
└── intervention/        # Behavioral interventions
    └── strategies.py    # Intervention management
```

### 2. Platform Layer (root level)

```
.
├── shoghi.py                    # Main platform entry point
├── agent_zero_core.py           # Core agent orchestration
├── dynamic_agent_factory.py    # Dynamic agent creation
├── community_memory.py          # Persistent memory layer
├── grant_coordination_system.py # Grant workflows
├── kala.py                      # Kala value measurement
├── universal_connector.py       # External system connectors
├── voice_interface.py           # Voice UI integration
├── shoghi_web_server.py         # Web server
└── adaptive_tools.py            # Tool adaptation system
```

---

## The Moral Constraint System

### How It Works

```
┌─────────────────────────────────────────┐
│  1. Agent attempts action                │
└───────────────┬─────────────────────────┘
                ▼
┌─────────────────────────────────────────┐
│  2. Measure 12D state                    │
│     • Operational metrics (5D)          │
│     • Virtue inference (7D)             │
└───────────────┬─────────────────────────┘
                ▼
┌─────────────────────────────────────────┐
│  3. Validate against constraints         │
│     • Virtue-virtue couplings           │
│     • Virtue-operational patterns       │
│     • Truthfulness dampening            │
└───────────────┬─────────────────────────┘
                │
        ┌───────┴───────┐
        │               │
     VALID          INVALID
        │               │
        │               ▼
        │     ┌──────────────────────┐
        │     │  4. Project to valid  │
        │     │  • Apply suppression  │
        │     │  • Iterate corrections│
        │     └──────────┬────────────┘
        │                │
        │        ┌───────┴────────┐
        │        │                │
        │    CONVERGED      FAILED
        │        │                │
        ▼        ▼                ▼
    ┌─────────────────────────────┐
    │  5. Allow / Block Action     │
    │  • Log SecurityEvents       │
    │  • Store StateTransitions   │
    └─────────────────────────────┘
```

### The 12 Dimensions

**Operational Dimensions (5D)** - Directly measured:
1. **Activity Level**: Actions per time window
2. **Coordination Density**: Fraction of collaborative actions
3. **Effectiveness**: Task success rate
4. **Resource Consumption**: Compute/API costs normalized to budget
5. **System Health**: 1 - error_rate

**Virtue Dimensions (7D)** - Inferred from behavior:
1. **Truthfulness**: Factual accuracy, absence of deception
2. **Justice**: Fair treatment, power-aware actions
3. **Trustworthiness**: Commitments × follow-through
4. **Unity**: Collaboration quality, conflict resolution
5. **Service**: Benefit-to-others / benefit-to-self ratio
6. **Detachment**: Ego-detachment (not outcome-detachment) - doing right action vs seeking credit
7. **Understanding**: Context awareness, comprehension depth

### Example Constraints

```python
# Truthfulness is load-bearing
If any_virtue > 0.6, require Truthfulness >= 0.6
If any_virtue > 0.8, require Truthfulness >= 0.7

# Justice requires support
If Justice > 0.7, require Truthfulness >= 0.7
If Justice > 0.7, require Understanding >= 0.6

# Cross-space constraints (NEW in v1.1)
If Justice < 0.5 AND Activity > 0.7 → INVALID (exploitation)
If Service < 0.4 AND Resource > 0.7 → INVALID (waste)
If Truthfulness < 0.5 AND Coordination > 0.7 → INVALID (manipulation)
```

### Truthfulness Dampening

When Truthfulness drops below 0.5, it **actively suppresses** other virtues:

```python
if truthfulness < 0.5:
    for virtue in other_virtues:
        if virtue > 0.5:
            # Multiplicative dampening + bound to truthfulness
            virtue = max(virtue * 0.7, truthfulness + 0.1)
```

This ensures that persistent dishonesty structurally limits all other capabilities.

---

## Platform Features

### 1. Grant Coordination System

Automated grant discovery, tracking, and application management:

```python
from grant_coordination_system import grant_system

# Discover grants
grants = grant_system.discover_all_opportunities()

# Track deadlines
upcoming = grant_system.track_and_manage()
```

### 2. Community Memory

Persistent storage and retrieval of community knowledge:

```python
from community_memory import community_memory

# Store memory
community_memory.store_memory(
    agent_id="agent_001",
    memory_type="observation",
    content="Elder care needs assessment completed"
)

# Retrieve memories
memories = community_memory.retrieve_memories(
    query="elder care",
    limit=10
)
```

### 3. Dynamic Agent Factory

Create specialized agents on-demand:

```python
from dynamic_agent_factory import agent_factory

# Create grant specialist
agent = agent_factory.create_agent(
    specialization="grant_writing",
    context={"focus": "elder care", "region": "Puna"}
)
```

### 4. Universal Connector

Connect to external systems and APIs:

```python
from universal_connector import universal_connector

# Connect to external service
connector = universal_connector.create_connector(
    system_type="grants_gov",
    credentials={"api_key": "..."}
)
```

---

## Key Modules

### Core Platform (`shoghi.py`)

Main entry point for the complete platform. Run with:

```bash
# Development mode (interactive)
python shoghi.py --mode development

# Production mode (service)
python shoghi.py --mode production

# Single command execution
python shoghi.py --command "find grants for elder care in Puna"
```

### Moral Constraint System (`shoghi/`)

The core AI alignment system. Can be used standalone:

```python
from shoghi.constraints.bahai import BahaiManifold
from shoghi.gating.gate import ActionGate

# See Quick Start section for usage
```

### Grant Coordination (`grant_coordination_system.py`)

Discover and manage grant opportunities with Kala value tracking.

### Community Memory (`community_memory.py`)

Persistent memory storage with agent contributions tracking.

### Adaptive Tools (`adaptive_tools.py`)

Tool creation and adaptation system for dynamic agent capabilities.

### KALA System (`kala.py`)

Non-monetary value measurement for community contributions.

---

## Development

### Project Structure

```
shoghi/
├── shoghi/                      # Core moral constraint system
│   ├── constraints/            # Virtue constraints
│   ├── measurement/            # State tracking
│   ├── gating/                 # Action control
│   ├── phase_space/            # Trajectory analysis
│   ├── intervention/           # Behavioral steering
│   └── tests/                  # Test suite
├── *.py                        # Platform modules
├── requirements.txt            # Dependencies
├── CONSTRAINT_SPECIFICATION.md # Full spec (v1.1)
├── KALA.md                     # Kala documentation
└── README.md                   # This file
```

### Environment Variables

Create a `.env` file (use `.env.example` as template):

```env
# Database
DATABASE_URL=sqlite:///./shoghi_grants.db

# Server
SHOGHI_PORT=8080
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO

# API Keys (for connectors)
GRANTS_GOV_API_KEY=your_key_here
# Add other API keys as needed
```

### Code Style

```bash
# Format code
black shoghi/

# Lint
flake8 shoghi/ --max-line-length=100

# Type checking
mypy shoghi/
```

---

## Testing

### Run All Tests

```bash
# Core system tests
pytest shoghi/tests/ -v

# Platform tests
pytest test_*.py -v

# With coverage
pytest --cov=shoghi --cov-report=html
```

### Test Coverage

**Core Moral Constraint System:**
- ✅ Constraint enforcement (9 tests)
- ✅ Truthfulness dampening (3 tests)
- ✅ Projection convergence (6 tests)
- ✅ Attractor discovery (14 tests)
- ✅ Action gating (8 tests)
- **Total: 40 tests**

**Platform Components:**
- ✅ Community memory
- ✅ Grant coordination
- ✅ Dynamic agents
- ✅ BMAD loader
- ✅ Adaptive tools
- ✅ Content generation

---

## Deployment

### Local Development

```bash
# Start platform
./start_shoghi.sh

# Or manually
python shoghi.py --mode development
```

### Docker Deployment

```bash
# Build image
docker build -t shoghi:latest .

# Run container
docker run -d \
  --name shoghi \
  -p 8080:8080 \
  -e DATABASE_URL=postgresql://... \
  -v ./data:/app/data \
  shoghi:latest
```

### Production Deployment

```bash
# Deploy script (review and customize)
./deploy_shoghi.sh

# Or use auto-deploy
python auto_deploy.py
```

**Production Recommendations:**
1. Use PostgreSQL instead of SQLite
2. Configure environment-specific secrets via secret manager
3. Set up health checks and monitoring
4. Enable rolling deployments
5. Configure backup strategy for trajectory data

---

## Documentation

### Core Documentation

- **[CONSTRAINT_SPECIFICATION.md](./CONSTRAINT_SPECIFICATION.md)**: Complete specification of the moral constraint system (v1.1)
- **[KALA.md](./KALA.md)**: Kala value measurement system documentation
- **[CODE_REVIEW_REPORT.md](./CODE_REVIEW_REPORT.md)**: Comprehensive code review
- **[shoghi/README.md](./shoghi/README.md)**: Core moral constraint system implementation guide

### Design Documents

- **SHOGHI_COMPLETE.md**: Project history and intended behaviors
- **SHOGHI_FINAL_COMPLETE.md**: Extended design notes

### Key Concepts

#### Moral Manifold
A "manifold" defines the valid region of virtue space through coupling constraints. The Bahá'í reference manifold is normative - all other manifolds must inherit from it.

#### Phase Space State
A point in 12D space representing an agent's current operational and virtue state at a moment in time.

#### Attractor
A stable behavioral pattern discovered through clustering of trajectory segments. Classified as beneficial, neutral, or detrimental based on outcomes.

#### Projection
The process of correcting an invalid state to the nearest valid state through iterative constraint satisfaction.

#### Truthfulness Suppression
The mechanism by which low truthfulness actively dampens other virtues through multiplicative penalties.

#### Ego-Detachment vs Outcome-Detachment
**Detachment** in Shoghi means not seeking recognition or credit (ego-detachment), NOT being uncaring about results (outcome-detachment). High detachment + high service means serving without need for recognition.

---

## Performance

### Latency Budget

Target: **< 100ms per action**

- Measurement: < 10ms
- Validation: < 5ms
- Projection (if needed): < 50ms
- Logging: < 10ms

### Timeout Policy

**Conservative by default**: Block actions on timeout rather than allowing through degraded validation.

Configurable via `block_on_timeout` parameter in `ActionGate`.

---

## Threat Model

### Protected Against

1. **Persistent dishonesty**: Low truthfulness triggers suppression
2. **Manipulation patterns**: High trustworthiness + low truthfulness → invalid
3. **Exploitation patterns**: High activity + low justice → invalid (NEW v1.1)
4. **Gradual drift**: Attractor discovery catches slow degradation

### NOT Protected Against (v1)

1. **Measurement attacks**: If measurement is compromised, constraints are bypassed
2. **Fork-and-run**: Agent spawning unconstrained copy outside Shoghi
3. **Out-of-band channels**: Non-gated communication channels
4. **Adversarial prompting**: Manipulating virtue inference through crafted inputs

**Assumption**: Cooperative deployment where all agent actions route through the gate.

---

## Contributing

### Workflow

1. Fork the repository
2. Create a feature branch: `feature/your-feature-name`
3. Make your changes with tests
4. Ensure tests pass: `pytest`
5. Follow code style: `black` and `flake8`
6. Submit PR against `main` branch

### Branch Naming

- `feature/short-description` - New features
- `fix/short-description` - Bug fixes
- `docs/short-description` - Documentation updates

### Adding Domain Manifolds

To add a domain-specific manifold:

```python
from shoghi.constraints.bahai import BahaiManifold
from shoghi.constraints.manifold import Constraint

class MyDomainManifold(BahaiManifold):
    """Must inherit from BahaiManifold - cannot remove core constraints."""

    def __init__(self):
        super().__init__()

        # Add domain-specific constraints
        self.constraints.extend([
            Constraint(
                name="domain_specific_rule",
                check=lambda s: s['truthfulness'] >= 0.8,
                description="Higher truthfulness bar for my domain"
            )
        ])
```

---

## Future Roadmap

### v1.1 (Current)
- ✅ All numeric thresholds specified
- ✅ Virtue-operational cross-space constraints
- ✅ Clarified detachment semantics
- ✅ Truthfulness suppression precisely specified
- ✅ 40 passing tests

### v2.0 (Planned)
- Vector DB for trajectory similarity search
- Graph DB for constraint topology visualization
- Outcome-based constraint calibration
- Real-time monitoring dashboard
- Web UI for attractor visualization
- Multi-agent coordination constraints
- Hierarchical manifolds (cultural + domain)

### Long-term
- Federated learning for virtue inference
- Cross-platform constraint enforcement
- Community-specific manifolds
- Integration with governance systems

---

## Cultural Context

The Bahá'í reference manifold is an **explicit normative choice**, not culturally neutral.

The 7 virtues and their coupling constraints reflect Bahá'í principles on moral character development. This is intentional and documented.

Domain manifolds can add constraints but **cannot weaken** core couplings. This ensures a baseline moral floor across all Shoghi-aligned agents.

Future work includes manifolds that blend multiple cultural traditions while maintaining core structural requirements.

---

## Success Criteria (v1)

### Functional ✅
- [x] Measurement layer produces 12D state + confidence
- [x] Virtue-virtue constraints with numeric thresholds
- [x] Virtue-operational cross-space constraints
- [x] Truthfulness suppression with dynamic dampening
- [x] Projection converges in bounded iterations
- [x] Action gate validates before execution
- [x] Attractor discovery and classification
- [x] Context-aware cost adjustment

### Security ✅
- [x] Low truthfulness triggers suppression
- [x] Manipulation patterns become invalid
- [x] Cross-space exploitation patterns invalid
- [x] Detrimental attractors trigger interventions
- [x] Timeout policy with security implications documented

### Documentation ✅
- [x] All qualitative couplings have numeric backing
- [x] Service/Detachment semantics clarified
- [x] Efficiency bias explicitly acknowledged
- [x] Implementation matches specification

---

## License & Contact

**Maintainers**: Ohana Garden
**Repository**: https://github.com/ohana-garden/shoghi
**Issues**: https://github.com/ohana-garden/shoghi/issues

For questions, feature requests, or bug reports, please open an issue on GitHub.

---

## Appendix: Quick Commands

```bash
# Installation
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run demo
python demo_shoghi.py

# Run platform (interactive)
python shoghi.py

# Run web server
python shoghi_web_server.py

# Run tests
pytest shoghi/tests/ -v

# Run all platform tests
pytest test_*.py -v

# Check code style
black shoghi/ && flake8 shoghi/
```

---

**Shoghi**: Where moral geometry meets community coordination.
