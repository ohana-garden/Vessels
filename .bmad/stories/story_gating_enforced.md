# Story: Gating and Virtue Constraints on Hot Path

## Metadata
- **Epic**: Gating Enforcement
- **Priority**: Critical
- **Status**: Planned
- **Created**: 2025-11-22

## Context

The Action Gate exists but is not integrated into tool execution paths. All external actions (tool calls, message sends, graph writes, commercial introductions) must go through the Gate to ensure moral constraints are respected.

## Requirements

### Functional

1. **Tool Gating**: All tool invocations via AdaptiveTools pass through Gate
2. **Commercial Gating**: Commercial agent introductions log gating events
3. **Graph Write Gating**: Graph writes are gated by agent class and policy
4. **Event Logging**: All gating decisions logged to phase space tracker
5. **Constraint Outcomes**: Gating results include constraint violations and corrections

### Non-Functional

- Gating latency must stay under 100ms (configurable budget)
- Gating failures must default to BLOCK (safe by default)

## Acceptance Criteria

### AC1: Tool execution passes through gate
```python
result = adaptive_tools.execute_tool(tool_id, params)
# Gate was consulted
assert gate.get_state_transitions(agent_id) contains transition
```

### AC2: Blocked actions are prevented
```python
# Simulate constraint violation
result = adaptive_tools.execute_tool(tool_id, params)
assert result["success"] == False
assert "blocked by gate" in result["error"]
```

### AC3: Gating events are logged
```python
events = tracker.get_security_events(agent_id)
assert len(events) > 0
```

## Test Cases

1. **test_tool_gating_allowed**: Tool execution allowed by gate
2. **test_tool_gating_blocked**: Tool execution blocked by gate
3. **test_commercial_introduction_logged**: Commercial intro creates gating event
4. **test_gate_latency_budget**: Gating respects latency budget
5. **test_gate_timeout_blocks**: Timeout results in BLOCK

## Dependencies

- Existing `ActionGate` from `vessels/gating/gate.py`
- `AdaptiveTools` from `adaptive_tools.py`
- `TrajectoryTracker` from `vessels/phase_space/tracker.py`
