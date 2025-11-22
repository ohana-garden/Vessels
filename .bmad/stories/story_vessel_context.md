# Story: Vessel Context Propagation

## Metadata
- **Epic**: EPIC 1 - Vessel Context in Runtime
- **Priority**: Critical
- **Status**: In Progress
- **Created**: 2025-11-22

## Context

The system has Vessel abstractions defined, but they're not actively used during runtime. Users and agents interact with the system without a clear "current vessel" context, making it impossible to:
- Apply vessel-specific configurations (tier, privacy, constraints)
- Track which vessel's resources are being used
- Enforce vessel-level policies

## Requirements

### Functional

1. **Vessel Resolution**: System can resolve current vessel from user_id, explicit vessel name, or default
2. **Context Propagation**: Vessel context (vessel_id, graph_namespace, privacy) is passed to:
   - AdaptiveTools
   - ActionGate
   - GraphitiClient
   - CommunityMemory
3. **Tool Metadata**: All tool executions include vessel_id in metadata
4. **Gate Events**: All gate events store vessel_id
5. **Default Vessel**: System has a sensible default when no vessel is specified

### Non-Functional

- Vessel context resolution must be < 10ms
- Backward compatible with existing code that doesn't specify vessel
- Thread-safe for concurrent requests

## Acceptance Criteria

### AC1: Resolve vessel from user_id
```python
context = VesselContext.from_user_id("user_123", vessel_registry)
assert context.vessel is not None
assert context.vessel_id == context.vessel.vessel_id
```

### AC2: Resolve vessel from explicit name
```python
context = VesselContext.from_vessel_name("lower_puna_elders", vessel_registry)
assert context.vessel.name == "Lower Puna Elders Care"
```

### AC3: Use default vessel
```python
context = VesselContext.get_default(vessel_registry)
assert context.vessel is not None
```

### AC4: AdaptiveTools receives vessel context
```python
tools = AdaptiveTools(vessel_id=context.vessel_id)
# Tool execution includes vessel_id in gate metadata
result = tools.execute_tool(tool_id, params, agent_id="agent1")
# Verify vessel_id was passed to gate
```

### AC5: Gate events include vessel_id
```python
gate = ActionGate(...)
result = gate.gate_action(agent_id, action, action_metadata={"vessel_id": "v1"})
# Event stored with vessel_id
events = gate.get_recent_events()
assert events[0]["vessel_id"] == "v1"
```

### AC6: GraphitiClient uses vessel namespace
```python
context = VesselContext.from_vessel_id("v1", vessel_registry)
graphiti = context.get_graphiti_client()
assert graphiti.graph_name == context.vessel.graph_namespace
```

## Test Cases

1. **test_vessel_context_from_user_id**: Resolve vessel from user mapping
2. **test_vessel_context_from_name**: Resolve vessel from name
3. **test_vessel_context_from_id**: Resolve vessel from ID
4. **test_vessel_context_default**: Use default vessel
5. **test_adaptive_tools_with_vessel**: Tools receive and propagate vessel_id
6. **test_gate_events_with_vessel**: Gate events store vessel_id
7. **test_graphiti_client_with_vessel**: Client uses correct namespace
8. **test_vessel_context_thread_safe**: Concurrent context resolution

## Integration Points

- `vessels_interface.py`: Add vessel parameter to process_message
- `agent_zero_core.py`: Pass vessel context to spawned agents
- `adaptive_tools.py`: Already has vessel_id parameter (✓)
- `vessels/gating/gate.py`: Ensure events capture vessel_id
- `vessels/knowledge/graphiti_client.py`: Initialize with vessel namespace

## Dependencies

- VesselRegistry must be initialized and accessible
- User-to-vessel mapping (can be simple dict or db table)
- Default vessel configuration
