# Agent Zero Core - Vessel-Native Architecture

## Overview

AgentZeroCore now supports **vessel-native agent coordination**, where agents are spawned within vessels and automatically inherit vessel-scoped resources:

- **Memory Backend**: Namespaced memory per agent, isolated within the vessel's graph namespace
- **Action Gate**: Privacy and moral constraint enforcement from the vessel's manifold
- **Tools**: Permission-controlled tool access based on vessel configuration

This design eliminates global memory/tool systems and ensures proper isolation, privacy enforcement, and moral alignment for multi-vessel scenarios.

## Architecture

### Data Flow

```
Caller
  ↓
AgentZeroCore(vessel_registry=registry)
  ↓
spawn_agents(specs, vessel_id="V")
  ↓
registry.get_vessel("V") → Vessel
  ↓
Vessel provides:
  - action_gate (privacy/moral enforcement)
  - memory_backend (namespaced storage)
  - tools (permission-based access)
  ↓
AgentInstance created with vessel-scoped resources
  ↓
Agent lifecycle uses injected resources:
  - Memory operations → vessel.memory_backend
  - Actions → vessel.action_gate
  - Tools → vessel.tools
```

### Key Components

1. **VesselRegistry**: Manages vessel lifecycle and persistence
2. **Vessel**: First-class abstraction binding resources and policies
3. **AgentZeroCore**: Meta-coordination engine (vessel-aware)
4. **AgentInstance**: Agent with vessel-scoped resources injected

## Usage Examples

### Example 1: Basic Vessel-Native Setup

```python
from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
from agent_zero_core import AgentZeroCore, AgentSpecification

# 1. Create vessel registry
registry = VesselRegistry(db_path="vessels.db")

# 2. Create a vessel
vessel = Vessel.create(
    name="Community Garden Project",
    community_id="puna_hawaii",
    description="Coordinating community garden initiatives",
    privacy_level=PrivacyLevel.SHARED,
    constraint_profile_id="servant_default"
)

# 3. Configure vessel resources (action gate, memory, tools)
from vessels.gating.gate import ActionGate
from vessels.constraints.manifold import Manifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine

# Create action gate with moral manifold
manifold = Manifold.servant_default()
metrics = OperationalMetrics()
virtue_engine = VirtueInferenceEngine()

action_gate = ActionGate(
    manifold=manifold,
    operational_metrics=metrics,
    virtue_engine=virtue_engine,
    latency_budget_ms=100.0
)

vessel.set_action_gate(action_gate)

# Configure memory backend
from vessels.knowledge.memory_backend import GraphitiMemoryBackend
from vessels.knowledge.graphiti_client import VesselsGraphitiClient

graphiti_client = VesselsGraphitiClient(
    community_id=vessel.community_ids[0],
    graph_namespace=vessel.graph_namespace
)
memory_backend = GraphitiMemoryBackend(graphiti_client)
vessel.set_memory_backend(memory_backend)

# Configure tools
vessel.add_tool("web_scraper", WebScraperTool())
vessel.add_tool("search_engine", SearchTool())
vessel.add_tool("document_generator", DocumentGeneratorTool())

# 4. Register vessel
registry.create_vessel(vessel)

# 5. Initialize AgentZeroCore with vessel registry
core = AgentZeroCore(vessel_registry=registry)
core.initialize()

# 6. Define agent specifications
specs = [
    AgentSpecification(
        name="GrantFinder",
        description="Discovers and analyzes grant opportunities",
        capabilities=["web_search", "data_analysis"],
        tools_needed=["web_scraper", "search_engine"],
        specialization="grant_discovery"
    ),
    AgentSpecification(
        name="GrantWriter",
        description="Writes grant applications",
        capabilities=["document_generation", "compliance_checking"],
        tools_needed=["document_generator"],
        specialization="grant_writing"
    )
]

# 7. Spawn agents in the vessel
agent_ids = core.spawn_agents(specs, vessel_id=vessel.vessel_id)

print(f"Spawned {len(agent_ids)} agents in vessel {vessel.name}")
# Output: Spawned 2 agents in vessel Community Garden Project

# Each agent now has:
# - Memory namespaced to vessel.memory_backend
# - Actions gated by vessel.action_gate
# - Tools from vessel.tools with permission checks
```

### Example 2: Multi-Vessel Coordination

```python
# Create multiple vessels with different privacy/moral settings
public_vessel = Vessel.create(
    name="Public Outreach",
    community_id="puna_public",
    privacy_level=PrivacyLevel.PUBLIC,
    constraint_profile_id="servant_default"
)

private_vessel = Vessel.create(
    name="Elder Care Coordination",
    community_id="puna_elders",
    privacy_level=PrivacyLevel.PRIVATE,
    constraint_profile_id="elder_care_strict"
)

# Configure each vessel with appropriate resources
# ... (setup action gates, memory, tools)

registry.create_vessel(public_vessel)
registry.create_vessel(private_vessel)

# Spawn agents in different vessels
core = AgentZeroCore(vessel_registry=registry)
core.initialize()

# Public-facing agents
public_specs = [
    AgentSpecification(
        name="CommunityOutreach",
        description="Manages public community engagement",
        capabilities=["communication", "event_planning"],
        tools_needed=["messaging_system", "calendar_system"]
    )
]

public_agent_ids = core.spawn_agents(
    public_specs, vessel_id=public_vessel.vessel_id
)

# Private elder care agents
private_specs = [
    AgentSpecification(
        name="ElderCareCoordinator",
        description="Coordinates sensitive elder care services",
        capabilities=["care_coordination", "privacy_protection"],
        tools_needed=["care_tracker", "encrypted_messaging"]
    )
]

private_agent_ids = core.spawn_agents(
    private_specs, vessel_id=private_vessel.vessel_id
)

# Agents are isolated:
# - Public agents have PUBLIC privacy enforcement
# - Private agents have PRIVATE privacy enforcement
# - Memory is fully isolated between vessels
# - Actions are gated according to vessel manifolds
```

### Example 3: Dynamic Vessel Resource Updates

```python
# Runtime updates to vessel resources
vessel = registry.get_vessel(vessel_id)

# Add new tool to vessel
vessel.add_tool("ai_analyzer", AIAnalyzerTool())
registry.create_vessel(vessel)  # Persist update

# Newly spawned agents get the updated tool set
new_specs = [AgentSpecification(
    name="DataAnalyst",
    tools_needed=["ai_analyzer"],  # Now available!
    ...
)]

core.spawn_agents(new_specs, vessel_id=vessel.vessel_id)
```

### Example 4: Backward Compatibility (Legacy Mode)

```python
# AgentZeroCore still works without vessel registry
core = AgentZeroCore(
    default_memory=legacy_memory_system,
    default_tools=legacy_tool_system
)
core.initialize()

# Spawn agents without vessel_id (uses fallback resources)
specs = [...]
agent_ids = core.spawn_agents(specs)  # No vessel_id provided

# Agents use global memory/tools (legacy behavior)
```

## Key Benefits

### 1. **Isolation**
- Each vessel has its own memory namespace
- Privacy policies enforced at vessel boundary
- No cross-vessel data leakage

### 2. **Privacy Enforcement**
- Agent actions gated by vessel's privacy level
- Memory operations respect vessel privacy policy
- Tool access controlled per vessel

### 3. **Moral Alignment**
- Each vessel can have different moral manifold
- Actions validated against vessel's constraint profile
- Teachable moments recorded in vessel's parable system

### 4. **Flexibility**
- Multi-vessel scenarios supported natively
- Runtime resource updates
- Backward compatible with legacy code

### 5. **No Circular Dependencies**
- TYPE_CHECKING used for type hints
- Vessel registry passed as instance (not imported at module level)
- Clean separation of concerns

## API Reference

### AgentZeroCore

#### `__init__(vessel_registry=None, *, default_memory=None, default_tools=None)`

Initialize core with optional vessel registry.

**Args:**
- `vessel_registry`: Optional VesselRegistry for vessel-native mode
- `default_memory`: Fallback memory system (legacy)
- `default_tools`: Fallback tool system (legacy)

#### `set_vessel_registry(registry)`

Set or update vessel registry.

**Args:**
- `registry`: VesselRegistry instance

#### `spawn_agents(specs, vessel_id=None, **kwargs)`

Spawn agents with vessel-scoped resources.

**Args:**
- `specs`: List of AgentSpecification
- `vessel_id`: ID of vessel (if None, uses legacy fallback)
- `**kwargs`: Additional parameters

**Returns:** List of agent IDs

**Raises:** ValueError if vessel_id provided but vessel not found

### Vessel

#### `set_action_gate(action_gate)`

Configure vessel's action gate.

#### `set_memory_backend(memory_backend)`

Configure vessel's memory backend.

#### `set_tools(tools)` / `add_tool(name, impl)`

Configure vessel's tool bindings.

#### `get_tool(name)`

Retrieve tool implementation by name.

## Migration Guide

### From Legacy AgentZeroCore

**Before (Legacy):**
```python
core = AgentZeroCore()
core.initialize(memory_system=global_memory, tool_system=global_tools)
core.gate = global_gate  # Global gate

specs = [...]
agent_ids = core.spawn_agents(specs)
# All agents share global memory/tools/gate
```

**After (Vessel-Native):**
```python
# Create vessel with scoped resources
vessel = Vessel.create(...)
vessel.set_action_gate(vessel_gate)
vessel.set_memory_backend(vessel_memory)
vessel.set_tools(vessel_tools)

registry = VesselRegistry()
registry.create_vessel(vessel)

# Initialize core with registry
core = AgentZeroCore(vessel_registry=registry)
core.initialize()

# Spawn agents in vessel
agent_ids = core.spawn_agents(specs, vessel_id=vessel.vessel_id)
# Each agent gets vessel-scoped resources
```

## Implementation Details

### Memory Namespace Isolation

When an agent is spawned in a vessel:
```python
if memory_backend and hasattr(memory_backend, 'create_namespace'):
    agent.memory = memory_backend.create_namespace(agent_id)
```

Each agent gets its own namespace within the vessel's memory backend.

### Action Gate Enforcement

When an agent executes an action:
```python
action_gate = agent.action_gate or self.gate  # Vessel gate preferred
gate_result = action_gate.gate_action(agent_id, action, metadata)
```

The vessel's action gate enforces privacy/moral constraints.

### Tool Resolution

When tools are assigned:
```python
if vessel and vessel.tools:
    agent.tools = self._resolve_vessel_tools(spec.tools_needed, vessel)
```

Only tools available in the vessel can be accessed by the agent.

## Troubleshooting

### "Vessel not found in registry"

Ensure vessel is created and registered before spawning agents:
```python
vessel = Vessel.create(...)
registry.create_vessel(vessel)  # ← Must persist!
core.spawn_agents(specs, vessel_id=vessel.vessel_id)
```

### "Tool not found in vessel"

Add tool to vessel before spawning:
```python
vessel.add_tool("tool_name", ToolImplementation())
registry.create_vessel(vessel)  # Persist update
```

### "No gate configured"

Configure action gate on vessel:
```python
vessel.set_action_gate(ActionGate(...))
registry.create_vessel(vessel)
```

## Related Documentation

- [Vessel Architecture](./vessels.md)
- [Action Gate Design](./action_gate.md)
- [Memory Backend](./memory_backend.md)
- [Privacy Policies](./privacy.md)
- [Moral Manifolds](./manifolds.md)
