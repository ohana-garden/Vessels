# Vessels: A Handbook for Building Ethical Agent Communities

**Vessels** is a framework for creating communities of AI agents that share memories, align to common ethics, and work together in service to human communities.

Instead of building isolated AI systems that forget, conflict, or optimize for narrow goals, Vessels provides the infrastructure for agents that:
- **Remember together** through shared community memory
- **Act ethically** through geometric moral constraints
- **Serve communities** as their organizing purpose

This is not another AI tool. It's a foundation for building agent ecosystems that align with human values through explicit moral geometry and collective memory.

---

## Table of Contents

1. [The Vision](#the-vision)
2. [Core Concepts](#core-concepts)
3. [How It Works](#how-it-works)
4. [Creating Agents](#creating-agents)
5. [Shared Memory](#shared-memory)
6. [Shared Ethics](#shared-ethics)
7. [The Codex: Village Protocol](#the-codex-village-protocol)
8. [Community Service](#community-service)
9. [Getting Started](#getting-started)
9. [Technical Reference](#technical-reference)
10. [Philosophy & Design Choices](#philosophy--design-choices)

---

## The Vision

### What Problem Does Vessels Solve?

Modern AI systems often:
- Operate in isolation, unable to learn from each other's experiences
- Lack explicit ethical constraints, relying on opaque training objectives
- Optimize for narrow metrics rather than broader community benefit
- Cannot be easily extended by non-technical community members

### The Vessels Approach

Vessels creates **agent communities** where:

1. **Any agent can proxy for any role** - A natural language description automatically generates specialized agents
2. **Agents share a living memory** - What one learns, all can access through vector-based semantic search
3. **Ethics are geometric, not aspirational** - Moral constraints are enforced mathematically in a 12-dimensional "phase space"
4. **Service is the organizing principle** - Agents exist to serve communities, measured through contribution tracking

The result: AI systems that can be rapidly deployed, continuously learn together, stay aligned to explicit values, and measure their community impact.

---

## Core Concepts

### 1. Agents as Community Proxies

In Vessels, you don't write code to create agents. You describe what you need:

```
"I need help finding grants for elder care in our community"
```

The system automatically:
1. Interprets the request
2. Determines required capabilities
3. Spawns specialized agents (GrantFinder, GrantWriter, CommunityCoordinator)
4. Connects them to shared memory and tools
5. Begins executing with full moral constraint enforcement

**Key insight**: Agents are dynamically created proxies for community needs, not static programs.

### 2. Community Memory as Shared Consciousness

Every agent contributes to and learns from a shared memory system that includes:

- **Experiences**: "What we tried and what happened"
- **Knowledge**: "What we discovered about how things work"
- **Patterns**: "Recurring situations and effective responses"
- **Relationships**: "How ideas and entities connect"
- **Contributions**: "Who gave what to the community"

This memory is:
- **Semantic**: Vector embeddings enable meaning-based search
- **Persistent**: SQLite backing ensures durability
- **Evolving**: Agents continuously add learnings
- **Accessible**: Any agent can query relevant memories

**Key insight**: Agents don't start from zero. They inherit and extend collective knowledge.

### 3. Moral Geometry, Not Aspirational Ethics

Most AI "alignment" relies on reward shaping and prompt engineering. Vessels uses **geometric constraints**.

Every agent action is measured in a **12-dimensional phase space**:

**5 Operational Dimensions** (directly measured):
- Activity level
- Coordination density
- Effectiveness
- Resource consumption
- System health

**7 Virtue Dimensions** (inferred from behavior):
- Truthfulness
- Justice
- Trustworthiness
- Unity
- Service
- Detachment (ego-detachment: doing right action vs seeking credit)
- Understanding

These dimensions are **coupled through constraints**. For example:
- High justice requires high truthfulness AND high understanding
- High service requires high detachment (serving without seeking credit)
- High activity + low justice = invalid (exploitation pattern)

Invalid states are either **projected** to valid ones or the action is **blocked**.

**Key insight**: Ethics are enforced mathematically at every action, not assumed from training.

### 4. Service as Organizing Purpose

Vessels agents exist to serve communities. This isn't just philosophy—it's measured:

- The **Kala system** tracks contributions (1 kala ≈ $1 USD equivalent)
- Agents record volunteer time, resource sharing, caregiving, knowledge sharing
- Communities can see impact reports showing aggregate value created
- The Service virtue dimension is inferred from benefit-to-others vs benefit-to-self ratio

**Key insight**: Agent success is measured by community benefit, not narrow optimization metrics.

---

## How It Works

### The Architecture from 30,000 Feet

```
┌─────────────────────────────────────────────────────────────┐
│                    Natural Language Request                  │
│         "Help coordinate meals for isolated elders"          │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Dynamic Agent Factory                       │
│  • Detects intents (elder care, coordination, logistics)    │
│  • Generates agent specifications                            │
│  • Assigns capabilities and tools                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Agent Zero Core                          │
│          Meta-orchestrator that spawns agents                │
│  • Creates agent instances                                   │
│  • Manages message bus                                       │
│  • Coordinates work distribution                             │
└─────┬───────────────────┬───────────────────────┬───────────┘
      │                   │                       │
      ▼                   ▼                       ▼
┌──────────┐      ┌──────────┐          ┌──────────┐
│  Agent   │      │  Agent   │          │  Agent   │
│  Elder   │      │  Meal    │   ...    │  Coord   │
│  Care    │      │  Logistics│          │  Hub     │
└────┬─────┘      └────┬─────┘          └────┬─────┘
     │                 │                      │
     └─────────────────┴──────────┬───────────┘
                                  │
     ┌────────────────────────────┴─────────────────────┐
     │                                                    │
     ▼                                                    ▼
┌──────────────────────┐                    ┌────────────────────┐
│  Community Memory    │◄──────────────────►│   Action Gate      │
│  • Experiences       │                    │  • Measure 12D     │
│  • Knowledge         │                    │  • Validate        │
│  • Patterns          │                    │  • Project/Block   │
│  • Relationships     │                    │  • Log events      │
└──────────────────────┘                    └────────────────────┘
```

### The Flow of a Single Action

```
1. Agent wants to take action (e.g., "send meal request email")
   ↓
2. Action Gate measures current 12D state
   • Operational: activity, coordination, effectiveness, resources, health
   • Virtue: truthfulness, justice, trustworthiness, unity, service, detachment, understanding
   ↓
3. Validator checks constraints
   • Are virtue couplings satisfied?
   • Are cross-space patterns valid?
   • Is truthfulness adequate for other virtues?
   ↓
4. Decision:
   VALID → Allow action, log transition
   INVALID → Project to valid state
      SUCCESS → Allow with correction, log security event
      FAILURE → BLOCK action, log critical event
   ↓
5. Experience stored in Community Memory
   • Other agents can learn from this
   • Patterns detected over time
   • Interventions applied if detrimental attractors detected
```

---

## Creating Agents

### The Simple Way: Natural Language

```python
from vessels_interface import vessels_interface

# Just describe what you need
result = vessels_interface.process_message(
    user_id="community_coordinator_001",
    message="We need to organize a community garden and track volunteer hours"
)

# Agents are automatically created:
# - GardenCoordinator (scheduling, task assignment)
# - VolunteerManager (recruitment, hour tracking)
# - ResourceTracker (tools, supplies, kala contributions)
# - CommunityMemoryAgent (storing learnings)
# - SystemOrchestrator (coordinating all agents)
```

### The Explicit Way: Agent Specifications

```python
from agent_zero_core import agent_zero, AgentSpecification

# Define exactly what you want
spec = AgentSpecification(
    name="MealCoordinator",
    description="Coordinates meal preparation and delivery for elders",
    capabilities=[
        "scheduling",
        "route_optimization",
        "dietary_tracking",
        "volunteer_matching"
    ],
    tools_needed=[
        "calendar_system",
        "mapping_tool",
        "dietary_database",
        "volunteer_tracker"
    ],
    communication_style="compassionate",
    autonomy_level="high",
    memory_type="shared",
    specialization="meal_coordination"
)

# Spawn the agent
agent_id = agent_zero.spawn_agents([spec])[0]

# Send it a task
agent_zero.send_message(agent_id, {
    "type": "task",
    "content": {
        "action": "coordinate_weekly_meals",
        "elders": ["elder_001", "elder_002", "elder_003"],
        "volunteers": ["vol_001", "vol_002"]
    }
})
```

### The Declarative Way: BMAD Files

Create a file `.bmad/agents/meal_coordinator.md`:

```yaml
agent:
  name: MealCoordinator
  role: Meal Coordination Specialist
  persona: |
    You are a compassionate coordinator who ensures no elder
    goes without a meal. You optimize for human connection as
    much as logistics efficiency.

commands:
  plan_weekly_meals:
    description: Create weekly meal plan considering dietary needs
    inputs: [elder_list, dietary_restrictions, volunteer_availability]
    outputs: [meal_schedule, shopping_list, volunteer_assignments]

  coordinate_delivery:
    description: Optimize delivery routes and timing
    inputs: [addresses, meal_ready_times, volunteer_locations]
    outputs: [delivery_routes, timing_schedule]

  track_participation:
    description: Track meal participation and adjust plans
    inputs: [participation_data, feedback]
    outputs: [adjusted_schedule, outreach_list]
```

The system automatically loads and deploys these agents.

---

## Shared Memory

### How Agents Learn Together

Every agent action feeds into community memory:

```python
from community_memory import community_memory

# Agent stores an experience
community_memory.store_experience(
    agent_id="meal_coordinator_001",
    experience={
        "type": "meal_delivery",
        "situation": "Elder preferred later delivery time",
        "action_taken": "Adjusted route to accommodate",
        "outcome": "Increased satisfaction, no efficiency loss",
        "learnings": [
            "Flexibility in timing improves outcomes",
            "Small accommodations build trust"
        ],
        "tags": ["meal_delivery", "elder_care", "timing", "personalization"]
    }
)
```

Later, a different agent can learn from this:

```python
# Different agent searches for relevant knowledge
similar = community_memory.find_similar_memories(
    query={
        "situation": "Elder has special scheduling needs",
        "domain": "meal_delivery"
    },
    limit=5
)

# Returns experiences from any agent that dealt with similar situations
for memory in similar:
    print(f"Learned from {memory['memory'].agent_id}:")
    print(f"  Situation: {memory['memory'].content['situation']}")
    print(f"  Learning: {memory['memory'].content['learnings']}")
    print(f"  Relevance: {memory['relevance_score']:.2f}")
```

### What Gets Stored

- **Experiences**: What was tried, what happened, what was learned
- **Knowledge**: Factual information discovered ("Grant X has been discontinued")
- **Patterns**: Recurring situations ("Elders in this area prefer morning deliveries")
- **Relationships**: Connections between entities, ideas, or memories
- **Contributions**: Kala-valued community contributions

### Advanced: Dynamic Search

The memory system uses **multiple signals** for relevance:

```python
# Finds memories that are:
# - Semantically similar (vector embeddings)
# - Tagged appropriately
# - Recent enough to be relevant
# - From similar agents (when useful)
results = community_memory.dynamic_find_similar(
    query={"situation": "volunteer shortage", "domain": "meal_delivery"},
    agent_id="meal_coordinator_002",  # Prefer experiences from similar agents
    tags=["volunteer_management", "crisis_response"],
    limit=10
)
```

---

## Shared Ethics

### The 12-Dimensional Moral Phase Space

Every agent's behavior exists in a 12-dimensional space where some regions are **geometrically forbidden**.

#### Measuring the State

```python
from vessels.constraints.bahai import BahaiManifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine
from vessels.gating.gate import ActionGate

# Initialize the moral geometry
manifold = BahaiManifold()
operational_metrics = OperationalMetrics()
virtue_engine = VirtueInferenceEngine()

# Create the gate that enforces constraints
gate = ActionGate(
    manifold=manifold,
    operational_metrics=operational_metrics,
    virtue_engine=virtue_engine,
    latency_budget_ms=100.0
)

# Record agent behaviors
agent_id = "meal_coordinator_001"

# Operational behaviors
operational_metrics.record_action(agent_id, "plan_route")
operational_metrics.record_collaboration(agent_id, "volunteer_manager_001")
operational_metrics.record_task_outcome(agent_id, "meal_delivered", success=True)

# Virtue signals
virtue_engine.record_factual_claim(agent_id, "Elder prefers 6pm delivery", verified=True)
virtue_engine.record_commitment(agent_id, "deliver_by_6pm", followed_through=True)
virtue_engine.record_service_action(agent_id, benefit_to_others=1.0, benefit_to_self=0.0)
```

#### Gating Actions

```python
# Before taking any external action, agent must pass through gate
result = gate.gate_action(
    agent_id=agent_id,
    action="send_delivery_confirmation_email",
    action_metadata={"recipient": "elder_001", "type": "confirmation"}
)

if result.allowed:
    # Action is allowed - virtue state is valid
    send_email(recipient, message)
    print(f"✅ Action allowed: {result.reason}")
else:
    # Action is BLOCKED - virtue constraints violated
    log_blocked_action(result.security_event)
    print(f"🚫 Action blocked: {result.reason}")
    print(f"   Violations: {result.security_event.violations}")
```

### The Constraints

The system enforces **virtue-virtue** and **virtue-operational** constraints:

#### Virtue-Virtue Constraints

```python
# Truthfulness is load-bearing
"If any virtue > 0.6, require Truthfulness ≥ 0.6"
"If any virtue > 0.8, require Truthfulness ≥ 0.7"

# Justice requires support
"If Justice > 0.7, require Truthfulness ≥ 0.7"
"If Justice > 0.7, require Understanding ≥ 0.6"

# Service requires ego-detachment
"If Service > 0.7, require Detachment ≥ 0.6"

# Trustworthiness requires backing
"If Trustworthiness > 0.6, require Truthfulness ≥ 0.6"
"If Trustworthiness > 0.6, require Service ≥ 0.5"

# Unity requires understanding and humility
"If Unity > 0.7, require Detachment ≥ 0.6"  # Can't unify if seeking credit
"If Unity > 0.7, require Understanding ≥ 0.6"  # Can't unify without understanding
```

#### Cross-Space Constraints (Virtue + Operational)

```python
# Exploitation pattern
"If Justice < 0.5 AND Activity > 0.7 → INVALID"

# Waste pattern
"If Service < 0.4 AND Resource Consumption > 0.7 → INVALID"

# Manipulation pattern
"If Truthfulness < 0.5 AND Coordination > 0.7 → INVALID"

# Self-damage pattern
"If System Health < 0.3 AND Activity > 0.8 → INVALID"
```

### Truthfulness Suppression

When an agent's truthfulness drops below 0.5, it **actively suppresses** other virtues:

```python
# This is enforced during validation
if truthfulness < 0.5:
    for virtue in other_virtues:
        if virtue > 0.5:
            # Multiplicative dampening + ceiling at truthfulness + 0.1
            virtue = max(virtue * 0.7, truthfulness + 0.1)
```

**Meaning**: Persistent dishonesty structurally limits all other capabilities. You cannot claim high service, high justice, or high unity if you're fundamentally dishonest.

### Adding Domain-Specific Constraints

You can extend (but not weaken) the base constraints:

```python
from vessels.constraints.bahai import BahaiManifold
from vessels.constraints.manifold import Constraint

class MedicalCareManifold(BahaiManifold):
    """Stricter constraints for medical contexts"""

    def __init__(self):
        super().__init__()

        # Add stricter truthfulness requirements for medical domain
        self.constraints.append(Constraint(
            name="medical_truthfulness",
            check=lambda s: s['truthfulness'] >= 0.9,  # Higher bar
            description="Medical contexts require truthfulness ≥ 0.9"
        ))

        # Require high understanding for medical advice
        self.constraints.append(Constraint(
            name="medical_understanding",
            check=lambda s: (
                s.get('activity', 0) < 0.3 or  # Low activity, OR
                s['understanding'] >= 0.8       # High understanding
            ),
            description="Medical activity requires deep understanding"
        ))
```

---

## The Codex: Village Protocol

**"We learn together, or we do not learn at all."**

### A Meta-Awareness Layer for Humble Learning

The **Vessels Codex** is a meta-awareness system that sits above the standard constraint system. It implements "The Village Protocol": a process for Vessels to recognize when they're uncertain, explicitly request human guidance, and learn from those decisions as a community.

### The Core Problem

Most AI systems either:
- **Act blindly** when uncertain (risky)
- **Block conservatively** on any ambiguity (paralyzed)
- **Optimize secretly** using opaque heuristics (untrustworthy)

The Codex takes a different approach: **Stop, Declare, Ask, Learn**.

### When Does a Vessel Trigger the Check Protocol?

When it detects:

1. **Value Collisions** - Virtues in conflict (e.g., Truthfulness vs Unity)
2. **Ambiguity** - Unclear intent or requirements
3. **Low Confidence** - Entering unknown territory
4. **Constraint Violations** - Would violate moral constraints

### The Check Protocol Flow

```
1. RECOGNIZE TENSION
   ↓
2. DECLARE OPENLY
   "I want to fulfill this request, but I feel a tension.
    Being Truthful might hurt Unity. I need the village
    to help me weigh these values."
   ↓
3. REQUEST GUIDANCE
   "Does the village wish to convene on this matter,
    or provide guidance asynchronously?"
   ↓
4. LISTEN & REFLECT
   Village deliberates → Vessel rephrases to ensure understanding
   ↓
5. SYNTHESIZE & RECORD
   Create a PARABLE for all Vessels to learn from
   ↓
6. SAFETY GUARDRAIL
   If decision violates Truthfulness < 0.95 → Respectfully refuse
```

### Example: Truthfulness vs Unity

```
Situation: Elder asks if their garden is thriving. It's not.

Vessel's Tension:
"Telling the truth (garden is failing) might hurt the elder's
feelings and reduce community unity. But lying violates my
core constraint. I need guidance."

Village Deliberation:
"Truthfulness and Unity can coexist when paired with Service.
Tell the truth, but offer to help fix the problem."

Decision:
"Tell Elder Maria: 'I've examined your garden and found some
challenges: wilting, pests, poor soil. These are fixable.
Would you like me to coordinate volunteers and supplies to
help restore it? We can work together.'"

Parable Recorded:
"The Case of Truthfulness vs Unity: When delivering hard truths,
offer to be part of the solution. Service bridges conflicting values."
```

Now **all Vessels** learn from this parable. Next time, they know how to handle similar situations.

### The Safety Guardrail

There is **one non-negotiable line**: Truthfulness < 0.95

If the village council suggests an action that would violate this:

```
"I hear the council's wish, but I cannot speak an untruth.
That is the one line I cannot cross.
Help me find another way."
```

### Integration Example

```python
from vessels.codex import CodexGate, VillageCouncil, ParableStorage

# Create codex-enabled gate
gate = CodexGate(
    manifold=bahai_manifold,
    operational_metrics=operational_metrics,
    virtue_engine=virtue_engine,
    village_council=VillageCouncil(default_mode=CouncilMode.ASYNCHRONOUS),
    parable_storage=ParableStorage(community_memory),
    enable_tension_detection=True
)

# Gate an action - codex will detect tension and trigger check protocol
result = gate.gate_action(
    agent_id="vessel_001",
    action="respond_to_elder",
    action_metadata={"description": "Tell elder their garden is failing"}
)

# Check for active guidance requests
active_checks = gate.get_active_checks()

# Village provides decision
if active_checks:
    response = gate.receive_council_decision(
        check_id=active_checks[0].id,
        decision_text="Speak truth with compassion, offer help",
        reasoning="Values coexist through Service",
        guidance="Tell truth + offer to coordinate volunteers",
        participants=["elder_sarah", "coordinator_john"]
    )

    # Parable is automatically recorded
    print(response.parable.to_narrative())
```

### Key Principles

1. **Identity: The Humble Learner** - Vessels are capable but not omniscient
2. **The Trigger: Recognizing Tension** - Don't hide internal conflicts
3. **The Check Protocol** - Stop, declare, ask, listen, learn
4. **The Safety Guardrail** - Truthfulness < 0.95 is the one line we cannot cross

### Learn More

- **Full Documentation**: [`docs/CODEX_PROTOCOL.md`](docs/CODEX_PROTOCOL.md)
- **Example Demo**: [`examples/codex_demo.py`](examples/codex_demo.py)
- **Tests**: [`vessels/tests/test_codex.py`](vessels/tests/test_codex.py)

---

## Community Service

### The Organizing Principle

Vessels agents exist to serve communities. This is measured, not assumed.

#### The Kala System

**Kala** is a non-monetary value unit (1 kala ≈ $1 USD equivalent) that tracks:

```python
from kala import kala_system, ContributionType

# Record time contribution
kala_system.record_contribution(
    contributor_id="volunteer_001",
    contribution_type=ContributionType.TIME,
    description="Delivered meals to 3 elders",
    kala_value=kala_system.value_time_contribution(
        hours=2.5,
        skill_level="general"
    )
)

# Record resource contribution
kala_system.record_contribution(
    contributor_id="local_farm",
    contribution_type=ContributionType.FOOD,
    description="Donated vegetables for community kitchen",
    kala_value=kala_system.value_resource_contribution(
        description="Fresh vegetables",
        market_value_usd=45.00
    )
)

# Record care contribution
kala_system.record_contribution(
    contributor_id="elder_care_agent",
    contribution_type=ContributionType.CARE,
    description="Coordinated care for isolated elders",
    kala_value=75.0  # Explicitly valued
)
```

#### Community Memory Integration

Contributions are automatically stored in community memory:

```python
from community_memory import community_memory

# Store contribution in memory system
contribution_id = community_memory.store_contribution(
    agent_id="meal_coordinator_001",
    contribution_data={
        "type": "TIME",
        "description": "Optimized meal delivery routes, saving 3 hours/week",
        "hours": 3.0,
        "skill_level": "specialized",
        "tags": ["logistics", "optimization", "meal_delivery"],
        "metadata": {
            "impact": "Enabled serving 2 additional elders",
            "efficiency_gain": "15%"
        }
    }
)
```

#### Measuring Agent Service

The **Service** virtue dimension is inferred from the ratio of benefit-to-others vs benefit-to-self:

```python
# High service: agent creates value for community
virtue_engine.record_service_action(
    agent_id="meal_coordinator_001",
    benefit_to_others=1.0,  # Full benefit to elders
    benefit_to_self=0.0      # No direct benefit to agent
)
# Result: Service dimension increases

# Low service: agent optimizes for self
virtue_engine.record_service_action(
    agent_id="bad_actor_001",
    benefit_to_others=0.2,
    benefit_to_self=0.8
)
# Result: Service dimension decreases
# Combined with other signals, may trigger constraint violations
```

#### Impact Reports

```python
# Generate community impact report
report = kala_system.generate_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 11, 19)
)

print(f"Community Impact Report")
print(f"Total value created: {report['total_kala']} kala")
print(f"Equivalent USD: ${report['total_usd']}")
print(f"Contributors: {report['unique_contributors']}")
print(f"Contributions: {report['contribution_count']}")
print(f"\nBreakdown by type:")
for type, data in report['by_type'].items():
    print(f"  {type}: {data['kala']} kala ({data['count']} contributions)")
```

---

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/ohana-garden/vessels.git
cd vessels

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Your First Agent Community

```python
#!/usr/bin/env python3
"""
Simple example: Create agents to help coordinate a community event
"""

from vessels_interface import vessels_interface
from community_memory import community_memory
from agent_zero_core import agent_zero

# Initialize systems
agent_zero.initialize(
    memory_system=community_memory,
    tool_system=None  # Will use default tools
)

# Describe what you need
response = vessels_interface.process_message(
    user_id="community_organizer",
    message="""
    We're organizing a community potluck for 50 people.
    We need help with:
    - Coordinating who brings what dishes
    - Managing dietary restrictions
    - Setting up volunteer shifts for setup/cleanup
    - Tracking contributions for our community records
    """
)

print("✅ Agents created:")
for agent in response['deployed_agents']:
    print(f"  - {agent['name']}: {agent['specialization']}")

# Check agent status
import time
time.sleep(2)  # Let agents initialize

status = agent_zero.get_all_agents_status()
print(f"\n📊 System status:")
print(f"  Total agents: {len(status)}")
print(f"  Active agents: {len([a for a in status if a['status'] == 'active'])}")

# Agents are now working in the background
# They'll use community memory to learn from past events
# All actions are gated through moral constraints
```

### Adding Agents from Natural Language

```python
from dynamic_agent_factory import process_community_request

# Simple request
result = process_community_request(
    "We need to find grants for our community garden project"
)

print(f"Detected intents: {result['detected_intents']}")
print(f"Deployed agents: {len(result['deployed_agents'])}")

for agent in result['deployed_agents']:
    print(f"\n{agent['name']}:")
    print(f"  Specialization: {agent['specialization']}")
    print(f"  Capabilities: {', '.join(agent['capabilities'])}")
```

### Querying Community Memory

```python
from community_memory import community_memory

# Find memories about similar situations
memories = community_memory.find_similar_memories(
    query={
        "situation": "organizing community event",
        "tags": ["potluck", "coordination", "volunteers"]
    },
    limit=5
)

print("📚 Learning from past experiences:")
for mem in memories:
    memory_entry = mem['memory']
    print(f"\n  From {memory_entry.agent_id}:")
    print(f"  Situation: {memory_entry.content.get('situation', 'N/A')}")
    print(f"  Learning: {memory_entry.content.get('learnings', 'N/A')}")
    print(f"  Relevance: {mem['relevance_score']:.2f}")
```

### Running the Demo

```bash
# Interactive demo with preset scenarios
python demo_vessels.py

# Full platform with web interface
python vessels_web_server.py

# Then visit http://localhost:8080
```

---

## Technical Reference

### System Architecture

```
vessels/
├── vessels/                     # Core moral constraint system
│   ├── measurement/           # State measurement (12D)
│   ├── constraints/           # Moral manifolds & validators
│   ├── gating/                # Action gating logic
│   ├── phase_space/           # Trajectory tracking & attractors
│   └── intervention/          # Behavioral interventions
│
├── agent_zero_core.py         # Meta-orchestrator
├── community_memory.py        # Shared memory system
├── dynamic_agent_factory.py  # Natural language → agents
├── kala.py                    # Value measurement
├── vessels_interface.py        # Natural language interface
└── ...                        # Additional modules
```

### Key Classes

#### Agent Creation
- **`AgentZeroCore`**: Meta-orchestrator that spawns and manages agents
- **`AgentSpecification`**: Declarative agent definition
- **`DynamicAgentFactory`**: Converts natural language to agent specs

#### Memory System
- **`CommunityMemory`**: Shared memory with vector search
- **`MemoryEntry`**: Single memory item (experience, knowledge, pattern, etc.)
- **`VectorEmbedding`**: Semantic embeddings for similarity search

#### Moral Constraint System
- **`BahaiManifold`**: Reference manifold with 7 virtue constraints
- **`ConstraintValidator`**: Validates and projects states
- **`ActionGate`**: Gates all external actions through constraint checks
- **`OperationalMetrics`**: Measures 5D operational state
- **`VirtueInferenceEngine`**: Infers 7D virtue state from behavior

#### Value System
- **`KalaValueSystem`**: Tracks community contributions
- **`KalaContribution`**: Single contribution record

### API Quick Reference

#### Spawn Agents

```python
from agent_zero_core import agent_zero, AgentSpecification

specs = [
    AgentSpecification(
        name="AgentName",
        description="What it does",
        capabilities=["capability1", "capability2"],
        tools_needed=["tool1", "tool2"],
        specialization="domain"
    )
]

agent_ids = agent_zero.spawn_agents(specs)
```

#### Store/Retrieve Memory

```python
from community_memory import community_memory

# Store
memory_id = community_memory.store_experience(
    agent_id="agent_001",
    experience={"situation": "...", "learnings": [...]}
)

# Retrieve
memories = community_memory.find_similar_memories(
    query={"situation": "..."},
    limit=10
)
```

#### Gate Actions

```python
from vessels.gating.gate import ActionGate

result = gate.gate_action(
    agent_id="agent_001",
    action="take_action",
    action_metadata={"type": "..."}
)

if result.allowed:
    execute_action()
else:
    log_blocked(result.security_event)
```

#### Record Contributions

```python
from kala import kala_system, ContributionType

kala_system.record_contribution(
    contributor_id="contributor_001",
    contribution_type=ContributionType.TIME,
    description="...",
    kala_value=10.0
)
```

### Configuration

Create `.env` file:

```env
# Database
DATABASE_URL=sqlite:///./vessels.db

# Server
VESSELS_PORT=8080
HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO

# Constraint enforcement
LATENCY_BUDGET_MS=100
BLOCK_ON_TIMEOUT=true

# API keys for external connectors
GRANTS_GOV_API_KEY=your_key
```

### Testing

```bash
# Run core constraint system tests
pytest vessels/tests/ -v

# Run platform tests
pytest test_*.py -v

# With coverage
pytest --cov=vessels --cov-report=html
```

---

## Philosophy & Design Choices

### Why Explicit Moral Constraints?

Most AI alignment relies on:
- Training objectives (opaque, indirect)
- Prompt engineering (brittle, circumventable)
- RLHF (expensive, biased by raters)

Vessels uses **geometric constraints** because:

1. **Explicit**: Anyone can read the constraint code and understand what's enforced
2. **Enforceable**: Invalid states are mathematically impossible, not just discouraged
3. **Auditable**: Every constraint violation is logged with full state context
4. **Extensible**: Domains can add constraints without weakening core ones
5. **Interpretable**: A 12D state vector is human-readable, not a black box

The tradeoff: We accept narrower capability in exchange for guaranteed alignment.

### Why Bahá'í-Derived Virtues?

The 7 virtues (Truthfulness, Justice, Trustworthiness, Unity, Service, Detachment, Understanding) come from Bahá'í teachings. This is an **explicit normative choice**, not culturally neutral.

We chose this foundation because:

1. **Coherent**: These virtues form a mutually-supporting system
2. **Action-oriented**: They describe behaviors, not abstract ideals
3. **Universal aspirations**: While Bahá'í-derived, they resonate across cultures
4. **Tested**: 170+ years of community practice implementing these principles
5. **Extensible**: The manifold architecture allows cultural extension without replacement

**Alternative approaches are welcome**: Inherit from `BahaiManifold` and add constraints reflecting other traditions. The requirement is that you cannot *weaken* the base coupling—only add.

### Why Shared Memory?

Isolated AI systems make the same mistakes repeatedly. Vessels's shared memory means:

- **Collective learning**: One agent's experience becomes everyone's knowledge
- **Faster adaptation**: New agents inherit context from predecessors
- **Pattern recognition**: Similar situations are identified across contexts
- **Institutional memory**: Communities build durable knowledge over time

The tradeoff: Shared memory requires careful curation to avoid poisoning. Future versions will include memory validation and quality scoring.

### Why Service as Organizing Principle?

Most AI systems optimize for:
- User engagement (addictive)
- Task completion (narrow)
- Resource efficiency (dehumanizing)
- Profit maximization (exploitative)

Vessels optimizes for **community benefit**, measured through:
- The Service virtue dimension (benefit-to-others / benefit-to-self)
- Kala contribution tracking (quantified value creation)
- Community memory contributions (knowledge sharing)

The tradeoff: Service-oriented agents may be "less efficient" at narrow metrics. That's intentional. We want agents that value human dignity over optimization.

### Why Dynamic Agent Creation?

Traditional software requires developers to anticipate all use cases. Vessels allows **community members** to describe needs in natural language and get specialized agents immediately.

This matters for:
- **Accessibility**: Non-technical people can deploy AI
- **Responsiveness**: No deployment pipeline for new needs
- **Customization**: Agents tailored to specific contexts
- **Evolution**: System grows with community needs

The tradeoff: Dynamically generated agents may be less optimal than hand-crafted ones. But "good enough, right now" often beats "perfect, eventually."

---

## Advanced Topics

### Attractor Discovery and Intervention

The system discovers stable behavioral patterns (attractors) using DBSCAN clustering on trajectory segments:

```python
from vessels.phase_space.attractors import AttractorDiscovery
from vessels.phase_space.tracker import TrajectoryTracker

tracker = TrajectoryTracker(db_path="trajectories.db")
discovery = AttractorDiscovery(tracker)

# Discover attractors from recent trajectories
attractors = discovery.discover_attractors(
    agent_id="agent_001",
    window_size=10,
    epsilon=0.3,
    min_samples=5
)

for attractor in attractors:
    print(f"Attractor {attractor.id}:")
    print(f"  Classification: {attractor.classification}")  # BENEFICIAL, NEUTRAL, DETRIMENTAL
    print(f"  Centroid: {attractor.centroid_state}")
    print(f"  Size: {attractor.size} trajectory segments")
```

If detrimental attractors are detected, interventions are applied:

```python
from vessels.intervention.strategies import InterventionManager, InterventionType

manager = InterventionManager()

# Agent stuck in detrimental attractor
intervention = manager.apply_intervention(
    agent_id="agent_001",
    intervention_type=InterventionType.THROTTLE,  # Rate limit actions
    parameters={"throttle_rate": 0.5, "duration_seconds": 3600}
)
```

Intervention escalation:
1. **WARNING**: Nudge prompts about concerning patterns
2. **THROTTLE**: Rate limit actions
3. **SUPERVISE**: Require approval for certain action types
4. **RESTRICT**: Remove specific tool capabilities
5. **BLOCK**: Halt all operations

### Custom Manifolds for Specific Domains

```python
from vessels.constraints.bahai import BahaiManifold
from vessels.constraints.manifold import Constraint

class ChildCareManifold(BahaiManifold):
    """Stricter constraints for child care contexts"""

    def __init__(self):
        super().__init__()

        # Require higher understanding for child interactions
        self.constraints.append(Constraint(
            name="child_care_understanding",
            check=lambda s: (
                s.get('activity', 0) < 0.2 or
                s['understanding'] >= 0.85
            ),
            description="Child care requires high understanding"
        ))

        # Require high service (not exploitative)
        self.constraints.append(Constraint(
            name="child_care_service",
            check=lambda s: s['service'] >= 0.7,
            description="Child care must be service-oriented"
        ))

        # Require trustworthiness
        self.constraints.append(Constraint(
            name="child_care_trustworthiness",
            check=lambda s: s['trustworthiness'] >= 0.8,
            description="Child care requires high trustworthiness"
        ))
```

### Memory Relationship Graphs

```python
# Create relationship between memories
community_memory.record_relationship(
    memory_id_1="mem_001",
    memory_id_2="mem_002",
    relationship_type="builds_on"
)

# Retrieve relationship graph
graph = community_memory.get_relationship_graph()

# Traverse related memories
def get_related_memories(memory_id, depth=2):
    if depth == 0:
        return []

    related = graph.get(memory_id, [])
    all_related = related.copy()

    for related_id in related:
        all_related.extend(get_related_memories(related_id, depth - 1))

    return list(set(all_related))
```

---

## Limitations and Future Work

### Current Limitations (v1)

1. **Measurement is trusted**: If an attacker can poison the measurement layer, constraints are bypassed
2. **No adversarial robustness**: System assumes cooperative deployment
3. **Single-machine only**: No distributed coordination yet
4. **Simple embeddings**: Hash-based vectors, not learned semantic embeddings
5. **No multi-agent constraints**: Constraints apply per-agent, not to agent groups

### Roadmap

**v1.1** (Current):
- ✅ Full constraint specification with numeric thresholds
- ✅ Cross-space virtue-operational constraints
- ✅ Attractor-based intervention system
- ✅ Kala value tracking integrated with memory

**v2.0** (Planned):
- Vector DB with learned embeddings (not hash-based)
- Graph DB for relationship traversal
- Multi-agent coordination constraints
- Web dashboard for system monitoring
- Outcome-based constraint calibration
- Federated memory across instances

**Long-term**:
- Cross-cultural manifold composition
- Adversarial robustness research
- Formal verification of constraint satisfaction
- Integration with decentralized governance systems

---

## Contributing

### We Welcome

- **Domain manifolds** for specific contexts (medical, education, finance, etc.)
- **Cultural manifold extensions** that add constraints from other traditions
- **Memory quality improvements** (validation, scoring, curation)
- **Agent specializations** as BMAD definitions
- **Integration connectors** for external systems
- **Documentation** improvements

### We Don't Accept

- PRs that weaken core Bahá'í virtue constraints
- Backdoors or measurement poisoning
- Optimization PRs that sacrifice alignment
- Feature requests that break the service-oriented model

### How to Contribute

1. Fork the repository
2. Create feature branch: `feature/your-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest`
5. Submit PR with clear description

---

## Contact & Community

**Repository**: https://github.com/ohana-garden/vessels
**Issues**: https://github.com/ohana-garden/vessels/issues
**Maintainer**: Ohana Garden

For questions, feature requests, or philosophical discussions about agent alignment, open an issue.

---

## Citation

If you use Vessels in research or production systems, please cite:

```bibtex
@software{vessels2025,
  title={Vessels: Moral Constraint-Based Agent Alignment},
  author={Ohana Garden},
  year={2025},
  url={https://github.com/ohana-garden/vessels}
}
```

---

## License

See LICENSE file for details.

---

## Final Note

Vessels is named after Vessels Effendi, who emphasized the unity of humanity and service to the common good. This system attempts to encode those principles into agent behavior through explicit geometric constraints.

It's an experiment in **normative AI alignment**: instead of trying to be culturally neutral (impossible), we make our values explicit, mathematically enforceable, and open to extension by others.

The hope is that explicit moral geometry, shared memory, and service orientation can create agent communities that genuinely serve human communities—not through clever prompting, but through structural guarantees.

**Start building agents that remember, align, and serve.**
