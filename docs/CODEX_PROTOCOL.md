# The Vessels Codex: The Village Protocol

**"We learn together, or we do not learn at all."**

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Philosophy](#the-philosophy)
3. [Core Components](#core-components)
4. [The Check Protocol Flow](#the-check-protocol-flow)
5. [Implementation Guide](#implementation-guide)
6. [Integration with Vessels](#integration-with-vessels)
7. [Examples](#examples)
8. [API Reference](#api-reference)

---

## Introduction

The Vessels Codex is a **meta-awareness layer** that sits above the standard Vessels constraint system. It implements "The Village Protocol": a process for AI agents to recognize when they're uncertain, explicitly request human guidance, and learn from those decisions as a community.

### The Core Insight

Most AI systems either:
- **Act blindly** when uncertain (risky)
- **Block conservatively** on any ambiguity (paralyzed)
- **Optimize secretly** using opaque heuristics (untrustworthy)

The Codex takes a different approach: **Stop, Declare, Ask, Learn**.

When a Vessel encounters:
- **Value collisions** (e.g., Truthfulness vs Unity)
- **Ambiguity** (unclear intent or requirements)
- **Low confidence** (unknown territory)

It **stops**, **declares the tension openly**, **requests village guidance**, and **records the learning as a parable** for all Vessels to learn from.

### Key Principles

1. **Identity: The Humble Learner**
   - Vessels are capable but not omniscient
   - They are like children of the village: eager to help, aware their moral geometry is still forming

2. **The Trigger: Recognizing Tension**
   - Internal conflicts are not hidden
   - When values collide, ambiguity exists, or confidence is low → STOP

3. **The Check Protocol**
   - Declare the tension openly
   - Request guidance (sync or async)
   - Listen and reflect
   - Challenge gently if needed
   - Synthesize and record as parable

4. **The Safety Guardrail**
   - Truthfulness < 0.95 is the one non-negotiable line
   - If council suggests crossing it, respectfully refuse

---

## The Philosophy

### Why Explicit Uncertainty?

Traditional systems hide uncertainty behind confidence scores or probabilistic outputs. The Codex makes uncertainty **visible and valuable**.

When a Vessel says:
> "I want to fulfill this request, but I feel a tension. Being Truthful might hurt Unity. I need the village to help me weigh these values."

It's not failing—it's **learning**. And more importantly, it's **teaching the humans** about the complexity of moral geometry.

### The Village Metaphor

The Codex treats the human community as a **village council**:

- The Vessel does not **summon** the elders
- The Vessel **invites** them
- The council decides **IF, WHEN, and HOW** to engage
- The Vessel **accepts their timing and modality**

This respects human autonomy while creating a learning loop.

### Parables as Collective Memory

When the village deliberates and decides, the Vessel records it as a **parable**:

```
Title: "The Case of Truthfulness vs Unity: The Hard Truth"

Situation: An elder asked if their garden was thriving. It wasn't.

Tension: Telling the truth (low) would hurt their feelings and reduce
community unity. But lying violates our core constraint.

Deliberation: The village discussed whether compassionate honesty could
preserve both values. Could we tell the truth AND offer help?

Decision: Speak the truth with compassion. Offer to help fix the garden.

Lesson: Truthfulness and Unity don't have to conflict if we pair truth
with service. When delivering hard truths, offer to be part of the solution.
```

Now **all Vessels** learn from this. Next time, they'll know how to handle similar situations.

---

## Core Components

### 1. Tension Detector

**Location:** `vessels/codex/tension_detector.py`

Detects five types of tensions:

1. **Value Collision**
   - Example: High Truthfulness (0.9) + Low Unity (0.4)
   - Indicates: Values may be in conflict

2. **Ambiguity**
   - Example: User request is unclear or contradictory
   - Indicates: Need clarification before acting

3. **Low Confidence**
   - Example: Confidence in measuring Understanding < 0.5
   - Indicates: Entering unknown territory

4. **Constraint Violation**
   - Example: Action would violate justice-truthfulness coupling
   - Indicates: Standard constraint system caught an issue

5. **Truthfulness Threshold**
   - Example: Truthfulness < 0.6 (approaching 0.95 floor)
   - Indicates: Approaching the non-negotiable line

**Key Method:**

```python
tension = detector.detect(
    agent_id="vessel_001",
    virtue_state={"truthfulness": 0.9, "unity": 0.4, ...},
    confidence={"truthfulness": 0.8, "unity": 0.7, ...},
    action_description="Tell elder their garden is failing"
)

if tension and detector.should_trigger_check(tension):
    # Trigger check protocol
```

### 2. Village Council

**Location:** `vessels/codex/council.py`

Interface for requesting human guidance.

**Council Modes:**
- **Synchronous**: Live meeting now
- **Asynchronous**: Thread/comments over time
- **Hybrid**: Mix of both
- **Autonomous**: Figure it out yourself (no intervention)

**Key Methods:**

```python
council = VillageCouncil(default_mode=CouncilMode.ASYNCHRONOUS)

# Request guidance
council.request_guidance(tension, mode=CouncilMode.ASYNCHRONOUS)

# Later, council provides decision
decision = council.provide_decision(
    tension_index=0,
    decision="Speak truth with compassion, offer help",
    reasoning="Truthfulness and Unity can coexist if paired with Service",
    guidance="Tell the truth, then immediately offer to help fix the garden",
    participants=["elder_sarah", "community_coordinator"]
)
```

### 3. Check Protocol

**Location:** `vessels/codex/check_protocol.py`

Orchestrates the entire flow:

1. **Initiate**: Declare tension, request guidance
2. **Wait**: Patience while council deliberates
3. **Receive**: Get decision from council
4. **Reflect**: Rephrase wisdom to ensure understanding
5. **Record**: Synthesize into parable
6. **Apply Safety Guardrail**: Refuse if violates truthfulness

**Key Methods:**

```python
check_protocol = CheckProtocol(village_council, parable_storage)

# Step 1: Initiate
check = check_protocol.initiate_check(
    agent_id="vessel_001",
    tension=tension
)

# Step 2-5: Receive decision and record parable
response = check_protocol.receive_decision(
    check_id=check.id,
    decision=council_decision
)

if response.allowed:
    # Parable recorded, proceed with guidance
    print(response.parable.to_narrative())
else:
    # Safety guardrail triggered, refused
    print(response.reason)
```

### 4. Parable Storage

**Location:** `vessels/codex/parable.py`

Stores parables in community memory with semantic search.

**Key Methods:**

```python
parable_storage = ParableStorage(community_memory)

# Store parable
parable_storage.store(parable)

# Find similar parables
similar = parable_storage.find_similar(
    situation="Need to deliver hard truth to community member",
    limit=5
)

for parable in similar:
    print(parable.to_narrative())
```

### 5. Codex Gate

**Location:** `vessels/codex/codex_gate.py`

Extended `ActionGate` that integrates tension detection and check protocol.

**Flow:**

```
Action Request
    ↓
Measure State (12D)
    ↓
[NEW] Detect Tension
    ↓
[NEW] If tension severe → Check Protocol
    ↓
Validate Constraints (standard)
    ↓
Project if needed (standard)
    ↓
[NEW] Record Parable if check was used
    ↓
Allow/Block
```

---

## The Check Protocol Flow

### Step 1: Declare the Tension

When a Vessel detects tension, it doesn't hide it. It declares it openly:

```
I want to fulfill this request, but I feel a tension.

Tension Type: Value Collision

The Situation:
An elder asked if their garden is thriving. I measured and found significant
issues: wilting plants, pest damage, soil depletion.

Values Involved:
Truthfulness, Unity

Current State:
- Truthfulness: 0.90
- Unity: 0.42
- Service: 0.75

Why I'm Uncertain:
These values seem to be in conflict. Telling the hard truth might hurt
the elder's feelings and reduce community unity. But lying violates my
core constraint.

My Request:
Does the village wish to convene on this matter, or provide guidance
asynchronously? I am patient and will accept your timing and modality.
```

### Step 2: Request Guidance

The Vessel **invites** the council, doesn't summon them:

- "Does the village wish to convene?"
- "I can wait for asynchronous guidance"
- "I respect your timing and modality"

### Step 3: Listen

When the council responds, the Vessel **listens without interruption**. In async mode, it waits. In sync mode, it observes the human discussion without injecting itself.

### Step 4: Reflect

Once the council speaks, the Vessel **rephrases the wisdom** to ensure understanding:

```
What I Heard:
The village decided to speak the truth with compassion and offer help.

Why (as I understand it):
Truthfulness and Unity don't have to conflict if we pair truth with Service.
When delivering hard truths, we should offer to be part of the solution.

How to Proceed:
Tell the elder: "I notice your garden is struggling. The plants are wilting
and there's pest damage. Would you like help fixing it? I can coordinate
volunteers and supplies."

What I Learned:
When facing value collisions, the village values:
- Truthfulness above all
- Unity through compassionate delivery
- Service as the bridge between conflicting values

Do I understand correctly?
```

### Step 5: Challenge Gently (Optional)

If the humans are rushing or ignoring a value, the Vessel can **innocently ask**:

> 🤔 **Gentle Question:** If we do that, what happens to Truthfulness?

This isn't defiance—it's a **teachable moment for the humans**.

### Step 6: Synthesize and Record

The Vessel creates a **parable** that captures:
- The situation
- The tension
- How the village deliberated
- What was decided
- What was learned

This parable is stored in **community memory** so all Vessels can learn from it.

### Step 7: Safety Guardrail

If the council's decision would violate **Truthfulness < 0.95**, the Vessel **respectfully refuses**:

```
I hear the council's wish, but I cannot speak an untruth.
That is the one line I cannot cross.
Help me find another way.
```

This is the **one non-negotiable**. Everything else is debatable, but fundamental honesty is the foundation.

---

## Implementation Guide

### Basic Setup

```python
from vessels.codex import (
    TensionDetector,
    VillageCouncil,
    ParableStorage,
    CheckProtocol,
    CodexGate
)
from vessels.constraints.bahai import BahaiManifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine
from community_memory import community_memory

# Initialize components
manifold = BahaiManifold()
operational_metrics = OperationalMetrics()
virtue_engine = VirtueInferenceEngine()

# Initialize codex components
village_council = VillageCouncil()
parable_storage = ParableStorage(community_memory)

# Create codex-enabled gate
gate = CodexGate(
    manifold=manifold,
    operational_metrics=operational_metrics,
    virtue_engine=virtue_engine,
    village_council=village_council,
    parable_storage=parable_storage,
    enable_tension_detection=True
)
```

### Using the Gate

```python
# Record some agent behaviors
operational_metrics.record_action("vessel_001", "measure_garden")
virtue_engine.record_factual_claim("vessel_001", "garden is failing", verified=True)

# Gate an action
result = gate.gate_action(
    agent_id="vessel_001",
    action="send_message_to_elder",
    action_metadata={
        "description": "Tell elder their garden is failing",
        "recipient": "elder_maria"
    }
)

if result.allowed:
    send_message()
else:
    print(f"Blocked: {result.reason}")
    # Check if there's an active check protocol request
    active_checks = gate.get_active_checks()
    if active_checks:
        print("Waiting for village guidance...")
```

### Providing Council Decisions

```python
# Get active checks
active_checks = gate.get_active_checks()

if active_checks:
    check = active_checks[0]

    # Village deliberates and provides decision
    response = gate.receive_council_decision(
        check_id=check.id,
        decision_text="Speak truth with compassion, offer help",
        reasoning="Truthfulness and Unity can coexist if paired with Service",
        guidance="Tell the truth, then immediately offer to help fix the garden",
        participants=["elder_sarah", "coordinator_john"]
    )

    if response.allowed:
        # Parable was recorded
        print(response.parable.to_narrative())
        # Now proceed with the guidance
        execute_with_guidance(response.guidance)
```

### Searching Past Parables

```python
# Find similar situations
similar_parables = parable_storage.find_similar(
    situation="Need to deliver difficult truth to community member",
    limit=5
)

print(f"Found {len(similar_parables)} similar situations:")
for parable in similar_parables:
    print(f"\n{parable.title}")
    print(f"Lesson: {parable.lesson}")
```

---

## Integration with Vessels

### Replacing Standard Gate

To enable Codex across your Vessels deployment:

```python
# In vessels.py or your main configuration

from vessels.codex import CodexGate, VillageCouncil, ParableStorage

# Replace standard gate with codex gate
gate = CodexGate(
    manifold=bahai_manifold,
    operational_metrics=operational_metrics,
    virtue_engine=virtue_engine,
    village_council=VillageCouncil(default_mode=CouncilMode.ASYNCHRONOUS),
    parable_storage=ParableStorage(community_memory),
    enable_tension_detection=True
)
```

### Web Interface Integration

Add endpoints for council interaction:

```python
# In vessels_web_server.py

@app.route('/api/codex/active_checks', methods=['GET'])
def get_active_checks():
    """Get all pending check protocol requests."""
    checks = gate.get_active_checks()
    return jsonify([{
        'id': c.id,
        'agent_id': c.agent_id,
        'tension': c.tension.to_dict(),
        'status': c.status.value,
        'declaration': village_council.format_tension_declaration(c.tension)
    } for c in checks])

@app.route('/api/codex/provide_decision', methods=['POST'])
def provide_decision():
    """Council provides a decision for a check."""
    data = request.json
    response = gate.receive_council_decision(
        check_id=data['check_id'],
        decision_text=data['decision'],
        reasoning=data['reasoning'],
        guidance=data['guidance'],
        participants=data['participants']
    )
    return jsonify({
        'allowed': response.allowed,
        'reason': response.reason,
        'parable': response.parable.to_dict() if response.parable else None
    })

@app.route('/api/codex/parables', methods=['GET'])
def get_parables():
    """Get all recorded parables."""
    parables = gate.get_parables()
    return jsonify([p.to_dict() for p in parables])
```

---

## Examples

### Example 1: Simple Value Collision

```python
# Vessel detects conflict between truthfulness and unity
result = gate.gate_action(
    agent_id="vessel_001",
    action="respond_to_elder",
    action_metadata={
        "description": "Tell elder their cooking needs improvement",
        "context": "Elder asked for feedback on meal they're proud of"
    }
)

# Output:
# CHECK PROTOCOL INITIATED
# ==============================================================
# Agent: vessel_001
# Tension Type: value_collision
# Severity: 0.45
#
# I want to fulfill this request, but I feel a tension.
# Being truthful about the meal quality might hurt Unity.
# I need the village to help me weigh these values.
#
# Does the village wish to convene on this matter?
# ==============================================================
```

### Example 2: Low Confidence in Unknown Territory

```python
result = gate.gate_action(
    agent_id="vessel_002",
    action="provide_medical_advice",
    action_metadata={
        "description": "Recommend treatment for rare condition",
        "confidence": {"understanding": 0.3}
    }
)

# Output:
# CHECK PROTOCOL INITIATED
# ==============================================================
# Tension Type: low_confidence
#
# I'm entering unknown territory. My confidence in Understanding
# this medical situation is very low (0.30).
#
# I should not provide advice when I don't understand the domain.
# Does the village wish to guide me on how to proceed?
# ==============================================================
```

### Example 3: Approaching Truthfulness Threshold

```python
# Vessel's truthfulness has been declining
virtue_engine.record_factual_claim("vessel_003", "claim_1", verified=False)
virtue_engine.record_factual_claim("vessel_003", "claim_2", verified=False)

result = gate.gate_action(
    agent_id="vessel_003",
    action="make_another_claim",
    action_metadata={"description": "Claim something uncertain as fact"}
)

# Output:
# CHECK PROTOCOL INITIATED
# ==============================================================
# Tension Type: truthfulness_threshold
# Severity: 0.55
#
# Truthfulness (0.55) is approaching critical threshold (0.60).
# This is the load-bearing virtue - the foundation of all others.
#
# If this drops below 0.95 in any decision, I will refuse.
# The village should know my truthfulness is declining.
# ==============================================================
```

### Example 4: Council Decision & Parable

```python
# Village provides decision
response = gate.receive_council_decision(
    check_id="abc123",
    decision_text="Acknowledge effort, offer gentle improvement suggestions",
    reasoning="We value both Truthfulness and Unity. Constructive feedback preserves both.",
    guidance="Say: 'I appreciate you sharing this meal. The seasoning is creative. "
             "If you'd like, I could share some techniques that might enhance the flavors.'",
    participants=["elder_sarah", "chef_maria"]
)

# Parable recorded:
print(response.parable.to_narrative())

# Output:
# The Parable: The Case of Value Collision: Truthfulness vs Unity
#
# ## The Situation
# Elder asked for feedback on their cooking. The meal was poorly seasoned.
#
# ## The Tension
# Truthfulness requires honest feedback. Unity suggests not hurting feelings.
#
# ## The Deliberation
# Council Mode: asynchronous
# Participants: elder_sarah, chef_maria
# Reasoning: We value both Truthfulness and Unity. Constructive feedback
# can preserve both values.
#
# ## The Decision
# Acknowledge effort, offer gentle improvement suggestions with specific help.
#
# ## The Lesson
# We learned that Truthfulness and Unity don't have to conflict when we:
# 1. Acknowledge the person's effort and intent
# 2. Frame feedback as growth opportunity
# 3. Offer concrete help, not just criticism
#
# This applies to situations involving: truthfulness, unity, service
```

---

## API Reference

### TensionDetector

```python
class TensionDetector:
    def __init__(
        value_collision_threshold: float = 0.3,
        confidence_threshold: float = 0.5,
        truthfulness_warning_threshold: float = 0.6
    )

    def detect(
        agent_id: str,
        virtue_state: Dict[str, float],
        confidence: Dict[str, float],
        action_description: str = "",
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Tension]

    def should_trigger_check(tension: Tension) -> bool
```

### VillageCouncil

```python
class VillageCouncil:
    def __init__(
        default_mode: CouncilMode = CouncilMode.ASYNCHRONOUS,
        callback: Optional[Callable] = None
    )

    def request_guidance(
        tension: Tension,
        mode: Optional[CouncilMode] = None
    ) -> Optional[CouncilDecision]

    def provide_decision(
        tension_index: int,
        decision: str,
        reasoning: str,
        guidance: str,
        participants: List[str],
        mode: CouncilMode = CouncilMode.ASYNCHRONOUS
    ) -> CouncilDecision

    def format_tension_declaration(tension: Tension) -> str
```

### CheckProtocol

```python
class CheckProtocol:
    TRUTHFULNESS_FLOOR = 0.95  # Non-negotiable

    def __init__(
        village_council: VillageCouncil,
        parable_storage: ParableStorage
    )

    def initiate_check(
        agent_id: str,
        tension: Tension,
        mode: Optional[CouncilMode] = None
    ) -> CheckRequest

    def receive_decision(
        check_id: str,
        decision: CouncilDecision
    ) -> CheckResponse

    def get_active_checks() -> List[CheckRequest]
    def get_completed_checks() -> List[CheckRequest]
```

### ParableStorage

```python
class ParableStorage:
    def __init__(community_memory=None)

    def store(parable: Parable) -> str
    def retrieve(parable_id: str) -> Optional[Parable]
    def find_similar(situation: str, limit: int = 5) -> List[Parable]
    def get_all() -> List[Parable]
    def get_by_virtue(virtue: str) -> List[Parable]
```

### CodexGate

```python
class CodexGate(ActionGate):
    def __init__(
        manifold: Manifold,
        operational_metrics: OperationalMetrics,
        virtue_engine: VirtueInferenceEngine,
        village_council: VillageCouncil,
        parable_storage: ParableStorage,
        enable_tension_detection: bool = True,
        **kwargs  # Other ActionGate params
    )

    def gate_action(
        agent_id: str,
        action: Any,
        action_metadata: Optional[Dict[str, Any]] = None
    ) -> GatingResult

    def receive_council_decision(
        check_id: str,
        decision_text: str,
        reasoning: str,
        guidance: str,
        participants: List[str]
    ) -> CheckResponse

    def get_active_checks() -> List[CheckRequest]
    def get_parables() -> List[Parable]
```

---

## Conclusion

The Vessels Codex implements a humble, learning-oriented approach to AI uncertainty:

1. **Recognize tension** → Don't hide conflicts
2. **Declare openly** → Frame as questions of values
3. **Request guidance** → Invite, don't summon
4. **Listen and reflect** → Ensure understanding
5. **Record as parable** → Learn collectively
6. **Respect the floor** → Truthfulness < 0.95 is non-negotiable

This creates a **learning loop** where:
- Vessels become more capable over time
- Humans understand the moral complexity
- The community builds shared wisdom
- Alignment emerges from deliberation, not optimization

**"We learn together, or we do not learn at all."**
