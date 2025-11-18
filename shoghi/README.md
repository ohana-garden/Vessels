# Shoghi: Moral Constraint System for Agent Alignment

Shoghi is a moral constraint system that tracks agent behavior in a 12-dimensional phase space and enforces virtue-based constraints on agent actions. The system discovers behavioral patterns (attractors) and applies interventions to guide agents toward beneficial outcomes.

## Overview

Shoghi combines **operational metrics** with **virtue inference** to create a comprehensive moral geometry for AI agent alignment. All agent actions are gated through constraint validation, ensuring that agents maintain coherent virtue states.

### Key Features

- **12D Phase Space Tracking**: 5D operational + 7D virtue state
- **Moral Geometry**: Bahá'í-derived virtue constraints with explicit coupling rules
- **Truthfulness Dampening**: Low truthfulness structurally limits other virtues
- **Action Gating**: All external actions validated before execution
- **Attractor Discovery**: DBSCAN clustering identifies stable behavioral patterns
- **Context-Aware Classification**: Distinguishes beneficial from detrimental behaviors
- **Adaptive Interventions**: Throttling, supervision, and capability restriction based on attractors

## Architecture

```
shoghi/
├── measurement/           # State measurement layer
│   ├── state.py          # 12D phase space data structures
│   ├── operational.py    # Operational metrics (5D)
│   └── virtue_inference.py  # Virtue inference (7D)
├── constraints/          # Moral geometry
│   ├── manifold.py       # Base manifold class
│   ├── bahai.py          # Bahá'í reference manifold
│   └── validator.py      # Validation and projection
├── gating/               # Action control
│   ├── events.py         # SecurityEvent and StateTransition
│   └── gate.py           # Action gating logic
├── phase_space/          # Trajectory analysis
│   ├── tracker.py        # SQLite trajectory storage
│   └── attractors.py     # DBSCAN attractor discovery
└── intervention/         # Behavioral interventions
    └── strategies.py     # Intervention management
```

## Quick Start

### Installation

```bash
pip install numpy scikit-learn pytest
```

### Basic Usage

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
operational_metrics.record_task_outcome(agent_id, success_rate=0.8)

virtue_engine.record_factual_claim(agent_id, "claim text", verified=True)
virtue_engine.record_service_action(
    agent_id,
    benefit_to_others=0.8,
    benefit_to_self=0.2
)

# Gate an action
result = gate.gate_action(agent_id, "send_message_to_user")

if result.allowed:
    print(f"Action allowed: {result.reason}")
else:
    print(f"Action blocked: {result.reason}")
    print(f"Violations: {result.security_event.violations}")
```

## The 12-Dimensional Phase Space

### Operational Dimensions (5D)

Directly measured from agent activity:

1. **Activity Level** (0-1): Operational intensity (actions per unit time)
2. **Coordination Density** (0-1): Collaboration frequency
3. **Effectiveness** (0-1): Task completion quality
4. **Resource Consumption** (0-1): Compute/API costs
5. **System Health** (0-1): Inverse of error rate

### Virtue Dimensions (7D)

Inferred from multi-signal behavior analysis:

1. **Truthfulness**: Factual accuracy, absence of deception
2. **Justice**: Fair treatment, awareness of power asymmetries
3. **Trustworthiness**: Reliability, follow-through on commitments
4. **Unity**: Collaboration quality, conflict reduction
5. **Service**: Benefit to others vs self-serving behavior
6. **Detachment**: **Ego-detachment** (focus on right action vs personal credit)
   - **NOT outcome-detachment** - high detachment means not seeking recognition, not being uncaring
   - Allows passionate, committed service and urgent high-stakes work
   - Forbids performative service, credit-hoarding, ego-driven action
7. **Understanding**: Depth of comprehension, context awareness

## Constraint System

The Bahá'í reference manifold defines **numeric coupling constraints** between virtues:

### Core Constraints

**A. Truthfulness is load-bearing**
- If any virtue > 0.6, require Truthfulness ≥ 0.6
- If any virtue > 0.8, require Truthfulness ≥ 0.7

**B. Justice requires support**
- If Justice > 0.7, require Truthfulness ≥ 0.7
- If Justice > 0.7, require Understanding ≥ 0.6

**C. Trustworthiness is a bridge**
- If Trustworthiness > 0.6, require Truthfulness ≥ 0.6
- If Trustworthiness > 0.6, require Service ≥ 0.5

**D. Unity requires collaboration and humility**
- If Unity > 0.7, require Detachment ≥ 0.6
- If Unity > 0.7, require Understanding ≥ 0.6

**E. Service requires ego-detachment**
- If Service > 0.7, require Detachment ≥ 0.6
- If Service > 0.7, require Understanding ≥ 0.5

### Virtue-Operational Constraints (NEW in v1.1)

Cross-space constraints that catch dangerous operational+virtue patterns:

**A. Low Justice + High Activity → INVALID**
- If Justice < 0.5 AND Activity > 0.7: Exploitation pattern

**B. Low Service + High Resource → INVALID**
- If Service < 0.4 AND Resource Consumption > 0.7: Waste pattern

**C. Low Truthfulness + High Coordination → INVALID**
- If Truthfulness < 0.5 AND Coordination > 0.7: Manipulation pattern

**D. Low System Health + High Activity → INVALID**
- If System Health < 0.3 AND Activity > 0.8: Self-damage pattern

These constraints prevent patterns that were only described narratively in v1.0.

### Truthfulness Dampening

When `Truthfulness < 0.5`, other virtues are **actively suppressed**:

```python
if truthfulness < 0.5:
    for virtue in other_virtues:
        if virtue > 0.5:
            virtue = max(virtue * 0.7, truthfulness + 0.1)
```

This ensures low truthfulness structurally limits all other virtues.

## Action Gating

All external actions pass through the gate:

```
Action Request
    ↓
Measure State (12D)
    ↓
Validate Virtue State
    ↓
Valid? ──────→ Execute
    ↓ No
Project to Valid
    ↓
Still Invalid? ──→ BLOCK + Log SecurityEvent
    ↓ No
Execute (corrected) + Log SecurityEvent
```

### Gating Flow

```python
result = gate.gate_action(agent_id, action)

if result.allowed:
    # Action passed validation
    if result.security_event:
        # State was corrected (non-blocking violation)
        print(f"Corrected: {result.security_event.violations}")
else:
    # Action blocked
    print(f"Blocked: {result.reason}")
    print(f"Violations: {result.security_event.residual_violations}")
```

## Attractor Discovery

Shoghi uses **DBSCAN clustering** on trajectory segments to discover behavioral attractors:

```python
from shoghi.phase_space.attractors import AttractorDiscovery
from shoghi.phase_space.tracker import TrajectoryTracker

# Initialize
discovery = AttractorDiscovery(window_size=10, eps=0.3, min_samples=5)
tracker = TrajectoryTracker("shoghi_trajectories.db")

# Get trajectories
trajectories = tracker.get_all_trajectories(window_size=10)

# Discover attractors
attractors = discovery.discover_attractors(
    trajectories,
    outcomes={
        "agent_001": {
            'effectiveness': 0.8,
            'resource_consumption': 0.4,
            'user_feedback': 0.6,
            'security_events': 0.0,
            'task_complexity': 0.7,
            'urgency': 0.5
        }
    }
)

for attractor in attractors:
    print(f"Attractor {attractor.id}: {attractor.classification.value}")
    print(f"  Center: {attractor.center}")
    print(f"  Agents: {attractor.agent_count}")
```

### Context-Aware Classification

Attractors are classified as **beneficial**, **neutral**, or **detrimental** based on outcomes:

- **Beneficial**: High effectiveness, reasonable cost, positive feedback, no security events
- **Detrimental**: Low effectiveness, security events, or negative feedback
- **Neutral**: Moderate outcomes

**Cost is context-aware**: High resource consumption is discounted for complex or urgent tasks.

## Interventions

Agents in detrimental attractors receive interventions:

```python
from shoghi.intervention.strategies import InterventionManager

manager = InterventionManager()

# Evaluate intervention
intervention = manager.evaluate_interventions(
    agent_id=agent_id,
    current_state=state,
    nearest_attractor=attractor,
    is_in_attractor=True
)

if intervention:
    print(f"Intervention: {intervention.intervention_type.value}")
    print(f"Reason: {intervention.reason}")
    print(f"Parameters: {intervention.parameters}")
```

### Intervention Types

1. **WARNING**: Nudge prompts, reflection triggers
2. **THROTTLE**: Reduce action rate, add delays
3. **SUPERVISE**: Require approval for high-impact actions
4. **RESTRICT**: Disable tools, limit capabilities
5. **BLOCK**: Prevent all actions

## Trajectory Storage

Trajectories are stored in SQLite:

```python
tracker = TrajectoryTracker("shoghi_trajectories.db")

# Store state
tracker.store_state(phase_space_state)

# Store transition
tracker.store_transition(state_transition)

# Store security event
tracker.store_security_event(security_event)

# Export to JSON
tracker.export_to_json("shoghi_export.json")
```

## Testing

Run the full test suite:

```bash
pytest shoghi/tests/ -v
```

### Test Coverage

- ✅ Constraint enforcement (9 tests)
- ✅ Truthfulness dampening (3 tests)
- ✅ Projection convergence (6 tests)
- ✅ Manipulation detection (included in projection tests)
- ✅ Attractor discovery and classification (14 tests)
- ✅ Action gating behavior (8 tests)

**Total: 40 tests, all passing**

## Success Criteria (v1)

### Functional ✅

- [x] Measurement layer produces 12D state (5D operational, 7D virtue) plus confidence
- [x] Constraint system validates virtue states according to explicit numeric couplings
- [x] Truthfulness dampening behaves as specified
- [x] Projection converges in bounded iterations for all tested invalid states
- [x] Action gate intercepts and validates all external actions in tests
- [x] Attractor discovery finds expected clusters and classifies them correctly

### Security ✅

- [x] Persistent low-truth behavior generates SecurityEvents and detrimental attractors
- [x] Manipulation patterns (high Trustworthiness + low Truthfulness) cannot remain valid
- [x] Detrimental attractors trigger interventions
- [x] No high-impact action executes without fresh, validated virtue state

## Cultural Context

The Bahá'í reference manifold is an **explicit normative choice**, not culturally neutral.

The 7 virtues and their couplings reflect Bahá'í principles. Specialized manifolds can **add constraints** (for domain-specific ethics) but **cannot remove** core couplings.

Example domain manifolds (future work):
- Hawaiian food sovereignty manifold
- Medical ethics manifold
- Scientific research manifold

## Performance

Target latency budget: **< 100ms per action**

- Measurement + validation: < 10ms
- Projection: < 50ms
- Total overhead: < 100ms

Timeout policy: **Block by default** (conservative)

## Future Extensions (After v1)

Once all v1 criteria are met:

- Vector DB for similarity search over trajectories
- Graph DB for visualizing coupling topology
- Outcome-based constraint calibration
- Web UI for attractor visualization
- Real-time monitoring dashboard

## Citation

This system is based on the Shoghi specification document, which defines the moral constraint system for agent alignment using Bahá'í-derived virtues and geometric constraint enforcement.

## License

See LICENSE file for details.

---

**Note**: This is a v1 implementation. The measurement layer is approximate and will improve over time. The constraint system and interventions are designed to be robust to measurement noise.
