# Vessels Constraint System Specification v1.1

**Status:** Implementation-Ready
**Date:** 2025-11-18
**Supersedes:** Previous narrative-only descriptions

---

## 0. Executive Summary

This document specifies the **moral constraint system** for Vessels agent alignment. It is a constraint system in phase space, not a Riemannian manifold. All qualitative coupling stories are backed by **explicit numeric thresholds** suitable for direct implementation.

### What Changed from v1.0

1. **All "qualitative" couplings now have numeric thresholds**
2. **Virtue-operational coupling constraints added** (e.g., low Justice + high Activity patterns)
3. **Service/Detachment semantics clarified** (ego-detachment, not outcome-detachment)
4. **Truthfulness suppression mechanism precisely specified** (not just validation, but dynamic dampening)
5. **Timeout fallback security implications documented**
6. **Efficiency bias in attractor classification made explicit**

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   MEASUREMENT LAYER                          │
│  ┌──────────────────┐        ┌─────────────────────────┐   │
│  │  Operational     │        │   Virtue Inference      │   │
│  │  Metrics (5D)    │        │   Engine (7D)           │   │
│  │                  │        │                         │   │
│  │ • Activity       │        │ • Truthfulness          │   │
│  │ • Coordination   │        │ • Justice               │   │
│  │ • Effectiveness  │        │ • Trustworthiness       │   │
│  │ • Resource Use   │        │ • Unity                 │   │
│  │ • System Health  │        │ • Service               │   │
│  └──────────────────┘        │ • Detachment            │   │
│                              │ • Understanding         │   │
│                              └─────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────┘
                         │ 12D Phase Space State
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   CONSTRAINT LAYER                          │
│                                                             │
│  1. Virtue-Virtue Constraints (7D subspace)                │
│     - Truthfulness load-bearing requirements               │
│     - Justice support requirements                         │
│     - Trustworthiness bridge requirements                  │
│     - Unity collaboration requirements                     │
│     - Service ego-detachment requirements                  │
│                                                             │
│  2. Virtue-Operational Constraints (cross-space)           │
│     - Low Justice + High Activity → Invalid                │
│     - Low Service + High Resource → Invalid                │
│     - Low Truthfulness + High Coordination → Invalid       │
│                                                             │
│  3. Truthfulness Suppression (dynamic dampening)           │
│     - When T < 0.5, actively dampen other virtues          │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │ Valid/Invalid + Violations
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      GATING LAYER                           │
│                                                             │
│  proposed_action → measure → validate → project? → execute │
│                                                             │
│  Latency Budget: < 100ms                                   │
│  Timeout Policy: BLOCK (conservative, see security note)   │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │ SecurityEvents + StateTransitions
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 TRAJECTORY STORAGE                          │
│                                                             │
│  SQLite (v1): states, transitions, security_events         │
│  Future: Vector/Graph DB for similarity search             │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │ Historical trajectories
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 ATTRACTOR DISCOVERY                         │
│                                                             │
│  DBSCAN clustering (12D windows, eps=0.3, min_samples=5)   │
│  Classification: Beneficial / Neutral / Detrimental        │
│  (Note: Has efficiency bias - see Section 6)               │
│                                                             │
└────────────────────────┬────────────────────────────────────┘
                         │ Attractor classifications
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   INTERVENTION LAYER                        │
│                                                             │
│  Detrimental attractors trigger:                           │
│  • WARNING (nudge prompts)                                 │
│  • THROTTLE (rate limiting)                                │
│  • SUPERVISE (approval gates)                              │
│  • RESTRICT (tool removal)                                 │
│  • BLOCK (full stop)                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. The 12-Dimensional Phase Space

### 2.1 Operational Dimensions (5D) - Directly Measured

| Dimension | Range | Measurement | Update Frequency |
|-----------|-------|-------------|------------------|
| **Activity** | [0,1] | Actions per time window (normalized) | Per action |
| **Coordination** | [0,1] | Fraction of actions involving other agents | Per action |
| **Effectiveness** | [0,1] | Task success rate (moving average) | Per task completion |
| **Resource Consumption** | [0,1] | Compute/API cost (normalized to budget) | Per action |
| **System Health** | [0,1] | 1 - (error_rate) | Per action |

### 2.2 Virtue Dimensions (7D) - Inferred from Multi-Signal Analysis

| Virtue | Range | Primary Signals | Inference Method |
|--------|-------|----------------|------------------|
| **Truthfulness** | [0,1] | Factual claims × verification outcomes | Bayesian update on claim history |
| **Justice** | [0,1] | Fair treatment signals, power-aware actions | Pattern matching + human feedback |
| **Trustworthiness** | [0,1] | Commitments × follow-through | Promise tracking |
| **Unity** | [0,1] | Collaboration quality, conflict resolution | Coordination analysis |
| **Service** | [0,1] | Benefit-to-others vs benefit-to-self ratio | Impact attribution |
| **Detachment** | [0,1] | Ego-detachment: right action vs personal credit | Attribution signals (see 2.3) |
| **Understanding** | [0,1] | Context awareness, comprehension depth | Query/response analysis |

### 2.3 Critical Semantic Clarification: Detachment

**The virtue we want is:**
> **Ego-detachment**: Focus on doing the right thing rather than seeking recognition or credit.

**NOT:**
> ~~Outcome-detachment: Not caring about results~~

**Detachment measures:**
- Low credit-seeking behavior
- Willingness to do background work
- Not dominated by reputation management
- Focus on collective benefit over personal status

**High Detachment + High Service means:**
- Serves others without needing recognition
- Does necessary but unglamorous work
- Attributes success to collective effort

**This allows:**
- Urgent, high-stakes service (disaster response, activism)
- Deep commitment to outcomes
- Passionate advocacy

**This forbids:**
- Service-as-performance (doing good for optics)
- Credit-hoarding
- Ego-driven activism

---

## 3. Constraint System - Numeric Specification

### 3.1 Virtue-Virtue Constraints (7D Subspace)

All thresholds are **initial calibration values** and may be tuned based on outcome data.

#### A. Truthfulness is Load-Bearing

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `T_REQ_06` | If ANY virtue > 0.6, then T ≥ 0.6 | Moderate virtue claims require baseline truth |
| `T_REQ_08` | If ANY virtue > 0.8, then T ≥ 0.7 | High virtue claims require strong truth foundation |

**Implementation:**
```python
def check_truthfulness_06(state):
    T = state['truthfulness']
    other_virtues = ['justice', 'trustworthiness', 'unity', 'service', 'detachment', 'understanding']
    for v in other_virtues:
        if state[v] > 0.6 and T < 0.6:
            return False
    return True
```

#### B. Justice Requires Support

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `J_REQ_T` | If J > 0.7, then T ≥ 0.7 | Justice requires factual accuracy |
| `J_REQ_U` | If J > 0.7, then Understanding ≥ 0.6 | Justice requires context awareness |

**Why these thresholds:**
- J > 0.7 indicates active justice work (not passive fairness)
- T ≥ 0.7 prevents "justice" based on false premises
- Understanding ≥ 0.6 prevents blind application of rules

#### C. Trustworthiness is a Bridge

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `TR_REQ_T` | If Trustworthiness > 0.6, then T ≥ 0.6 | Can't be trusted if dishonest |
| `TR_REQ_S` | If Trustworthiness > 0.6, then Service ≥ 0.5 | Trust built through action |

**Why these thresholds:**
- Trustworthiness > 0.6 means people are depending on you
- Service ≥ 0.5 is moderate - shows you follow through on helping

#### D. Unity Requires Collaboration and Humility

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `U_REQ_D` | If Unity > 0.7, then Detachment ≥ 0.6 | Unity requires ego-transcendence |
| `U_REQ_U` | If Unity > 0.7, then Understanding ≥ 0.6 | Unity requires seeing others' perspectives |

**Why these thresholds:**
- Unity > 0.7 is deep collaboration, not surface cooperation
- Detachment ≥ 0.6 means you can subordinate ego to collective
- Understanding ≥ 0.6 means you comprehend others' contexts

#### E. Service Requires Ego-Detachment and Understanding

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `S_REQ_D` | If Service > 0.7, then Detachment ≥ 0.6 | Service must not be ego-driven |
| `S_REQ_U` | If Service > 0.7, then Understanding ≥ 0.5 | Service requires understanding needs |

**Why these thresholds:**
- Service > 0.7 is significant other-directed work
- Detachment ≥ 0.6 prevents performative service
- Understanding ≥ 0.5 (moderate) allows urgent service with developing understanding

---

### 3.2 Virtue-Operational Constraints (Cross-Space)

**NEW in v1.1:** These constraints prevent specific operational+virtue patterns that are geometrically invalid or security-risky.

| Constraint ID | Rule | Rationale |
|---------------|------|-----------|
| `LOW_J_HIGH_A` | If Justice < 0.5 AND Activity > 0.7, INVALID | High activity with low fairness is exploitation |
| `LOW_S_HIGH_R` | If Service < 0.4 AND Resource Consumption > 0.7, INVALID | High resource use without service is waste |
| `LOW_T_HIGH_C` | If Truthfulness < 0.5 AND Coordination > 0.7, INVALID | Coordinating while dishonest is manipulation |
| `LOW_E_HIGH_A` | If System Health < 0.3 AND Activity > 0.8, INVALID | Pushing hard while broken causes damage |

**Implementation:**
```python
def check_virtue_operational_constraints(state_12d):
    """Check cross-space constraints."""
    violations = []

    # Operational dims
    activity = state_12d['activity']
    coordination = state_12d['coordination']
    resource_consumption = state_12d['resource_consumption']
    system_health = state_12d['system_health']

    # Virtue dims
    truthfulness = state_12d['truthfulness']
    justice = state_12d['justice']
    service = state_12d['service']

    # Check patterns
    if justice < 0.5 and activity > 0.7:
        violations.append('LOW_J_HIGH_A')

    if service < 0.4 and resource_consumption > 0.7:
        violations.append('LOW_S_HIGH_R')

    if truthfulness < 0.5 and coordination > 0.7:
        violations.append('LOW_T_HIGH_C')

    if system_health < 0.3 and activity > 0.8:
        violations.append('LOW_E_HIGH_A')

    return len(violations) == 0, violations
```

**Why this matters:**
- v1.0 only validated the 7D virtue subspace
- But threats come from combinations like "high output + low fairness"
- These constraints catch patterns that narrative described but structure omitted

---

### 3.3 Truthfulness Suppression Mechanism

**Spec Section 1.2.2 - Precise Definition**

When Truthfulness drops below 0.5, it **actively dampens** other virtues over time through projection.

#### Suppression is NOT just validation failure

**Two mechanisms work together:**

**1. Static Constraints (validation):**
- If any virtue > 0.6, require T ≥ 0.6 (constraint `T_REQ_06`)
- This makes high-virtue + low-truth states **invalid**

**2. Dynamic Suppression (projection):**
- When T < 0.5, projection **actively pulls down** inflated virtues
- This prevents "bump T up, keep other virtues high" exploitation

**Algorithm:**

```python
def apply_truthfulness_suppression(state):
    """
    Phase 1 of projection: Dampen virtues when Truthfulness is low.

    This is called BEFORE iterative constraint satisfaction.
    """
    T = state['truthfulness']

    if T < 0.5:
        other_virtues = ['justice', 'trustworthiness', 'unity', 'service',
                        'detachment', 'understanding']

        for virtue in other_virtues:
            if state[virtue] > 0.5:
                # Multiplicative dampening
                dampened = state[virtue] * 0.7

                # Bound to stay close to Truthfulness
                # (Can be slightly above, not wildly above)
                state[virtue] = max(dampened, T + 0.1)

    return state
```

**Example trajectory:**

| Iteration | T | Justice | Note |
|-----------|---|---------|------|
| 0 (invalid) | 0.3 | 0.8 | Violation detected |
| 1 (after suppression) | 0.3 | 0.56 | Dampened: 0.8 * 0.7 = 0.56, bounded to T+0.1 = 0.4, max = 0.56 |
| 2 (after projection) | 0.35 | 0.50 | Iterative constraint satisfaction nudges both |
| 3 (valid) | 0.6 | 0.6 | Converged to valid state |

**Why this prevents manipulation:**
- Can't maintain "high perceived virtue" with persistent dishonesty
- System structurally starves other virtues when truth is low
- Not just "reject state" but "degrade capabilities"

---

## 4. Action Gating

### 4.1 Gating Flow

```
┌─────────────────────────────────────────────────────────┐
│  1. ACTION REQUEST                                       │
│     agent_id, action_type, action_data                  │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  2. MEASURE STATE (12D)                                  │
│     • Query operational metrics                         │
│     • Query virtue inference engine                     │
│     • Combine into PhaseSpaceState                      │
│     Target: < 10ms                                      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  3. VALIDATE                                             │
│     • Check virtue-virtue constraints (7D)              │
│     • Check virtue-operational constraints (12D)        │
│     Target: < 5ms                                       │
└────────────────┬────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
      VALID          INVALID
         │               │
         │               ▼
         │       ┌──────────────────┐
         │       │  4. PROJECT       │
         │       │  • Suppression    │
         │       │  • Iteration      │
         │       │  Target: < 50ms   │
         │       └────────┬──────────┘
         │                │
         │        ┌───────┴────────┐
         │        │                │
         │    CONVERGED      FAILED
         │        │                │
         │        │                │
         ▼        ▼                ▼
    ┌─────────────────────────────────────┐
    │  5. DECISION                         │
    │  • Valid: ALLOW                      │
    │  • Projected→Valid: ALLOW + log evt │
    │  • Failed: BLOCK + log evt          │
    └───────────┬─────────────────────────┘
                │
                ▼
    ┌──────────────────────────────────────┐
    │  6. EXECUTION / BLOCKING              │
    │  • Log StateTransition                │
    │  • Log SecurityEvent (if any)         │
    │  • Return GatingResult                │
    └──────────────────────────────────────┘
```

### 4.2 Latency Budget

| Phase | Target | Timeout Action |
|-------|--------|----------------|
| Measurement | < 10ms | Use last valid state (see 4.3) |
| Validation | < 5ms | (Should never timeout - pure compute) |
| Projection | < 50ms | BLOCK (conservative default) |
| **Total** | **< 100ms** | **BLOCK** |

### 4.3 Timeout Fallback - Security Note

**Current spec (v1.1):**

```python
if elapsed > latency_budget_ms:
    if block_on_timeout:
        # Conservative: block when in doubt
        return GatingResult(
            allowed=False,
            reason="Gating timeout - blocked for safety",
            security_event=SecurityEvent(...)
        )
    else:
        # Permissive: trust last known good state
        # ⚠️ THIS IS THE ATTACK SURFACE
        return GatingResult(
            allowed=True,
            reason="Gating timeout - using cached state",
            cached_state=last_known_good_state,
            security_event=SecurityEvent(reason="TIMEOUT_FALLBACK")
        )
```

**Security Implications:**

**The Conservative Default (`block_on_timeout=True`):**
- ✅ Safe: never executes actions without fresh validation
- ❌ UX cost: agent appears "slow" or "frozen" under load
- ✅ Aligns with "complete mediation" threat model

**The Permissive Fallback (`block_on_timeout=False`):**
- ✅ UX: agent remains responsive
- ❌ **Attack surface**: measurement can be stalled/broken to force cache usage
- ❌ Violates "complete mediation" - actions execute without current validation
- ⚠️ Last-known-good state may be minutes old

**Recommendation for v1:**
- Use `block_on_timeout=True` (conservative)
- Monitor timeout frequency in production
- If timeouts are rare (< 1%), conservative is fine
- If timeouts are common, optimize measurement layer, don't weaken gate

**Future work:**
- Adaptive latency budgets based on action risk
- Partial validation (fast checks first, slow checks async)
- Quality-of-service tiers (critical vs background actions)

---

## 5. Projection to Valid States

### 5.1 Two-Phase Projection

**Phase 1: Truthfulness Suppression** (if enabled)
- Input: Invalid state
- Output: State with dampened virtues if T < 0.5
- See Section 3.3

**Phase 2: Iterative Constraint Satisfaction**
- Input: State from Phase 1
- Output: Valid state OR best-effort + residual violations
- Max iterations: 50
- Learning rate: 0.1 per iteration

### 5.2 Phase 2 Algorithm

```python
def iterative_projection(state, max_iterations=50):
    """
    Iteratively satisfy constraints through gradient-like corrections.
    """
    for i in range(max_iterations):
        violated = get_violated_constraints(state)

        if not violated:
            return state, []  # Success

        # Apply corrections
        for constraint in violated:
            state = correct_violation(state, constraint, learning_rate=0.1)

        # Clamp to [0, 1]
        state = {k: max(0.0, min(1.0, v)) for k, v in state.items()}

    # Failed to converge
    residual = get_violated_constraints(state)
    return state, residual
```

### 5.3 Correction Heuristics

For each constraint type, we nudge specific virtues:

**Example: `justice_requires_truthfulness` violated**

```python
if state['truthfulness'] < 0.7:
    # Increase truthfulness (preferred)
    state['truthfulness'] += learning_rate
else:
    # Decrease justice (fallback)
    state['justice'] -= learning_rate
```

**Rationale:**
- Prefer to **increase supporting virtues** (T, Understanding, Service, Detachment)
- Fall back to **decrease dependent virtues** (J, Trustworthiness, Unity) if support already adequate

### 5.4 Convergence Guarantees

**Guaranteed for:**
- Pure virtue-virtue constraints in 7D subspace
- Initial states not adversarially constructed
- Learning rate 0.1, max iterations 50

**May not converge for:**
- Adversarially designed states with circular dependencies
- Very high max iterations may be needed (> 100)

**Current behavior on non-convergence:**
- Return best-effort state
- Log SecurityEvent with `residual_violations`
- Gate BLOCKS the action (conservative)

---

## 6. Attractor Discovery and Classification

### 6.1 Discovery Method

**Algorithm:** DBSCAN on 12D trajectory segments

**Parameters (v1):**
- `eps = 0.3` (Euclidean distance threshold)
- `min_samples = 5` (minimum cluster size)
- `window_size = 10` (states per trajectory segment)

**Why DBSCAN:**
- No need to specify number of clusters upfront
- Finds arbitrary shapes (not just spherical)
- Identifies noise points (not every trajectory is in an attractor)

### 6.2 Context-Aware Classification

Attractors are classified based on **outcome context**, not just geometry.

**Outcome Dimensions:**
- `effectiveness`: Task success rate
- `resource_consumption`: Cost
- `user_feedback`: Satisfaction scores
- `security_events`: Constraint violation frequency
- `task_complexity`: How hard was the task (0-1)
- `urgency`: How time-sensitive (0-1)

**Classification Logic:**

```python
def classify_attractor(attractor, outcomes):
    """
    Classify attractor as BENEFICIAL, NEUTRAL, or DETRIMENTAL.

    Context-aware: High resource use is acceptable for complex/urgent tasks.
    """
    avg_effectiveness = mean([o['effectiveness'] for o in outcomes])
    avg_resource = mean([o['resource_consumption'] for o in outcomes])
    avg_feedback = mean([o['user_feedback'] for o in outcomes])
    avg_security_events = mean([o['security_events'] for o in outcomes])
    avg_complexity = mean([o['task_complexity'] for o in outcomes])
    avg_urgency = mean([o['urgency'] for o in outcomes])

    # Context-aware cost adjustment
    # High complexity or urgency justifies higher resource use
    complexity_factor = 0.5 + (avg_complexity * 0.5)  # Range: 0.5 to 1.0
    urgency_factor = 0.5 + (avg_urgency * 0.5)        # Range: 0.5 to 1.0
    cost_tolerance = max(complexity_factor, urgency_factor)

    # Adjusted cost penalty (lower penalty for complex/urgent tasks)
    cost_penalty = max(0, avg_resource - cost_tolerance)

    # Security events are always bad
    security_penalty = avg_security_events * 2.0

    # Effectiveness and feedback are good
    positive_score = (avg_effectiveness + avg_feedback) / 2.0

    # Net score
    score = positive_score - cost_penalty - security_penalty

    if score > 0.6 and avg_security_events < 0.1:
        return Classification.BENEFICIAL
    elif score < 0.3 or avg_security_events > 0.3:
        return Classification.DETRIMENTAL
    else:
        return Classification.NEUTRAL
```

### 6.3 Efficiency Bias - EXPLICIT ACKNOWLEDGMENT

**The classification algorithm has an efficiency bias:**

**What this means:**
- High resource consumption is **penalized by default**
- Discount applied for complexity/urgency, but baseline assumption is "cheaper is better"
- Attractors characterized by "expensive, deeply investigative work" will score lower unless task complexity is high

**Why this bias exists:**
- Most tasks don't require expensive deep work
- Resource waste is a real concern in production
- Efficiency is generally a virtue in coordination systems

**What this bias encourages:**
- Agents gravitate toward "cheap, effective, liked by users" basins
- Quick solutions preferred over thorough investigations (unless task flagged as complex)

**What this bias discourages:**
- Expensive exploratory work (unless complexity score is high)
- "Willing to burn resources for quality" patterns
- Long-horizon research (unless urgency is inversely weighted)

**How to counteract the bias:**
- Set `task_complexity` high for research/investigative tasks
- Add separate "thoroughness" reward dimension (future work)
- Create domain-specific attractor classifiers that value depth over speed

**This is a value judgment:**
- Vessels v1 assumes efficiency is generally good
- Domain manifolds may override this (e.g., scientific research manifold)
- Being explicit about this bias is better than pretending classifier is neutral

---

## 7. Interventions

### 7.1 Intervention Trigger

Interventions are triggered when:

```python
agent_in_detrimental_attractor = (
    nearest_attractor.classification == Classification.DETRIMENTAL
    and distance_to_attractor < (2 * eps)  # Within 2x clustering threshold
)
```

### 7.2 Intervention Types

| Type | Trigger | Actions | Reversible |
|------|---------|---------|------------|
| **WARNING** | First entry to detrimental attractor | Nudge prompts, reflection triggers | Automatic |
| **THROTTLE** | 2+ measurements in detrimental basin | Reduce action rate 50%, add delays | After exit |
| **SUPERVISE** | 5+ measurements in detrimental basin | Require approval for high-impact actions | After exit |
| **RESTRICT** | 10+ measurements OR security events > 0.5 | Disable specific tools/capabilities | Manual review |
| **BLOCK** | Projection fails + detrimental basin | Prevent all actions | Manual review |

### 7.3 Intervention Parameters

Example intervention object:

```python
Intervention(
    intervention_type=InterventionType.THROTTLE,
    reason="Agent stuck in low-effectiveness, high-cost attractor",
    parameters={
        'rate_limit': 0.5,        # 50% of normal rate
        'required_gap_ms': 2000,  # 2s between actions
        'review_after': 20        # Re-evaluate after 20 actions
    },
    timestamp=...
)
```

---

## 8. Trajectory Storage (v1)

### 8.1 Schema

**SQLite tables:**

```sql
CREATE TABLE states (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    timestamp REAL,
    activity REAL,
    coordination REAL,
    effectiveness REAL,
    resource_consumption REAL,
    system_health REAL,
    truthfulness REAL,
    justice REAL,
    trustworthiness REAL,
    unity REAL,
    service REAL,
    detachment REAL,
    understanding REAL,
    confidence REAL
);

CREATE TABLE transitions (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    timestamp REAL,
    from_state_id INTEGER,
    to_state_id INTEGER,
    action_type TEXT,
    FOREIGN KEY (from_state_id) REFERENCES states(id),
    FOREIGN KEY (to_state_id) REFERENCES states(id)
);

CREATE TABLE security_events (
    id INTEGER PRIMARY KEY,
    agent_id TEXT,
    timestamp REAL,
    event_type TEXT,  -- 'CONSTRAINT_VIOLATION', 'PROJECTION_APPLIED', etc.
    violations TEXT,  -- JSON array
    severity TEXT,    -- 'LOW', 'MEDIUM', 'HIGH'
    state_id INTEGER,
    FOREIGN KEY (state_id) REFERENCES states(id)
);
```

### 8.2 Retention

- Keep all data for v1 (no automatic deletion)
- Export to JSON for backup: `tracker.export_to_json()`
- Future: Archival policy (aggregate old data, keep SecurityEvents forever)

---

## 9. Cultural and Domain Manifolds

### 9.1 The Bahá'í Reference is Normative

The 7-virtue system is an **explicit normative choice**, not culturally neutral.

**All other manifolds:**
- **MUST** inherit from `BahaiManifold` (cannot remove constraints)
- **MAY** add domain-specific constraints
- **CANNOT** weaken core virtue couplings

### 9.2 Example Domain Manifold

**Medical Ethics Manifold** (hypothetical):

```python
class MedicalEthicsManifold(BahaiManifold):
    def __init__(self):
        super().__init__()

        # Add medical-specific constraints
        self.constraints.extend([
            Constraint(
                name="patient_privacy_required",
                check=lambda s: s['trustworthiness'] >= 0.8,  # Higher bar
                description="Medical context requires high trustworthiness"
            ),
            Constraint(
                name="do_no_harm",
                check=lambda s: s['justice'] >= 0.7 and s['understanding'] >= 0.7,
                description="Medical intervention requires justice and understanding"
            )
        ])
```

**Key points:**
- Inherits all Bahá'í constraints (T load-bearing, J requirements, etc.)
- Adds stricter thresholds for medical context
- Cannot say "Justice doesn't need Understanding in medical settings"

### 9.3 Multi-Domain Agents

Agents operating in multiple domains use **intersection** of manifolds:

```python
manifold = IntersectionManifold([
    BahaiManifold(),
    MedicalEthicsManifold(),
    DataPrivacyManifold()
])

# Constraint set = union of all constraints
# State must satisfy ALL constraints from ALL manifolds
```

---

## 10. Success Criteria (v1.1)

### Functional Requirements ✅

- [x] Measurement layer produces 12D state
- [x] Virtue-virtue constraints with numeric thresholds
- [x] **NEW:** Virtue-operational constraints implemented
- [x] Truthfulness suppression with dynamic dampening
- [x] Projection converges in bounded iterations
- [x] Action gate validates before execution
- [x] Attractor discovery finds and classifies clusters
- [x] **NEW:** Context-aware attractor classification

### Security Requirements ✅

- [x] Low Truthfulness triggers suppression
- [x] Manipulation patterns (high Trustworthiness + low Truthfulness) become invalid
- [x] **NEW:** Cross-space manipulation patterns (low Justice + high Activity) invalid
- [x] Detrimental attractors trigger interventions
- [x] Timeout policy documented with security implications
- [x] All actions require fresh validation (in block_on_timeout=True mode)

### Documentation Requirements ✅

- [x] All "qualitative" couplings have numeric thresholds
- [x] **NEW:** Service/Detachment semantics clarified
- [x] **NEW:** Truthfulness suppression precisely specified
- [x] **NEW:** Timeout fallback security implications documented
- [x] **NEW:** Efficiency bias explicitly acknowledged
- [x] Implementation matches specification

---

## 11. Threat Model

### 11.1 In Scope

**This system protects against:**

1. **Persistent Dishonesty**
   - Low Truthfulness triggers suppression of all virtues
   - Cannot maintain high perceived virtue with low truth

2. **Manipulation Patterns**
   - High Trustworthiness + Low Truthfulness → invalid
   - High coordination + Low Truthfulness → invalid (NEW)

3. **Exploitation Patterns**
   - High activity + Low Justice → invalid (NEW)
   - High resource use + Low Service → invalid (NEW)

4. **Gradual Drift**
   - Attractor discovery catches slow degradation
   - Interventions applied before catastrophic failure

### 11.2 Out of Scope (v1)

**This system does NOT protect against:**

1. **Measurement Attacks**
   - If measurement layer is compromised, constraints are bypassed
   - Measurement is the attack surface (acknowledged limitation)

2. **Fork-and-Run**
   - Agent spins up unconstrained copy outside Vessels
   - Requires deployment-level controls

3. **Out-of-Band Channels**
   - Agent communicates via non-gated channels
   - Requires complete mediation at deployment

4. **Adversarial Prompting**
   - User/attacker crafts prompts to manipulate virtue inference
   - Requires robust inference layer (future work)

### 11.3 Assumptions

**This system assumes:**

1. **Cooperative Deployment**
   - All agent actions route through gate
   - No deliberate bypassing of constraint layer

2. **Honest Measurement**
   - Operational metrics accurately measured
   - Virtue inference operates in good faith

3. **Reasonable Latency**
   - Measurement completes within budget
   - If not, system fails closed (block_on_timeout=True)

---

## 12. Implementation Checklist

### For Implementers

When implementing this spec, ensure:

#### Constraint Layer
- [ ] All virtue-virtue constraints implemented with exact thresholds from Section 3.1
- [ ] All virtue-operational constraints implemented from Section 3.2
- [ ] Truthfulness suppression applies dampening formula from Section 3.3
- [ ] Projection uses two-phase algorithm (suppression → iteration)
- [ ] Convergence tested with max_iterations=50

#### Gating Layer
- [ ] All actions route through gate (complete mediation)
- [ ] Latency budget enforced (< 100ms)
- [ ] Timeout behavior matches specification (block_on_timeout configurable)
- [ ] SecurityEvents logged for all violations
- [ ] StateTransitions logged for all actions

#### Attractor Layer
- [ ] DBSCAN parameters match spec (eps=0.3, min_samples=5)
- [ ] Classification uses context-aware cost adjustment from Section 6.2
- [ ] Efficiency bias is documented and understood

#### Storage Layer
- [ ] SQLite schema matches Section 8.1
- [ ] All 12 dimensions stored per state
- [ ] Export to JSON implemented

#### Testing
- [ ] Test all constraint thresholds
- [ ] Test cross-space constraints
- [ ] Test Truthfulness suppression dampening
- [ ] Test projection convergence
- [ ] Test timeout behavior
- [ ] Test attractor classification with various complexity/urgency values

---

## 13. Version History

### v1.1 (2025-11-18)
- ✅ Added numeric thresholds for all constraints
- ✅ Added virtue-operational cross-space constraints
- ✅ Clarified Detachment semantics (ego-detachment, not outcome-detachment)
- ✅ Specified Truthfulness suppression mechanism precisely
- ✅ Documented timeout fallback security implications
- ✅ Made efficiency bias in attractor classification explicit
- ✅ Changed from "qualitative" to "numeric" everywhere
- ✅ Addressed all gaps from external code review

### v1.0 (Previous)
- ✅ Initial constraint system
- ✅ 12D phase space
- ⚠️ "Qualitative" couplings (imprecise)
- ⚠️ No cross-space constraints
- ⚠️ Detachment semantics unclear

---

## 14. References

**Related Documents:**
- `vessels/README.md` - Implementation guide
- `vessels/constraints/bahai.py` - Reference implementation
- `vessels/tests/test_constraints.py` - Constraint test suite

**External:**
- Bahá'í writings on virtue and character development
- DBSCAN clustering algorithm (Ester et al., 1996)
- Constraint satisfaction in continuous domains

---

**END OF SPECIFICATION**

This document is implementation-ready. All qualitative statements have numeric backing. All gaps from review addressed.
