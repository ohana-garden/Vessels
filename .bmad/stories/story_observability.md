# Story: Observability and Ethical HUD

## Metadata
- **Epic**: Observability Layer
- **Priority**: High
- **Status**: Planned
- **Created**: 2025-11-22

## Context

Operators need visibility into gating decisions, phase space trajectories, and cross-vessel interactions to understand system behavior and ensure ethical operation.

## Requirements

### Functional

1. **Query Gating Events**: List recent gating events by vessel and agent class
2. **Inspect Attractors**: View good/bad attractors from phase space
3. **Vessel Metrics**: Aggregate virtue/operational metrics per vessel
4. **Cross-Vessel Tracking**: See interactions across vessel boundaries

### Non-Functional

- Queries must complete in <500ms
- Handle empty databases gracefully
- Support filtering by vessel, agent, time range

## Acceptance Criteria

### AC1: List gating events
```python
events = observability.list_gating_events(vessel_id="vessel1", limit=10)
assert len(events) <= 10
assert all(e.vessel_id == "vessel1" for e in events)
```

### AC2: List attractors
```python
attractors = observability.list_attractors(vessel_id="vessel1")
assert len(attractors) >= 0
```

### AC3: Get vessel metrics
```python
metrics = observability.get_vessel_metrics("vessel1")
assert "avg_truthfulness" in metrics
assert "total_actions" in metrics
```

## Test Cases

1. **test_list_gating_events**: Query recent gating events
2. **test_list_gating_events_empty**: Handle empty event log
3. **test_list_attractors**: Query attractors
4. **test_get_vessel_metrics**: Aggregate metrics for vessel
5. **test_filter_by_agent_class**: Filter events by agent class

## Dependencies

- `TrajectoryTracker` for events and states
- Attractor discovery from `vessels/phase_space/attractors.py`
# Story: Observability for gating and attractors

## Summary
Operators need a simple way to view recent gating events, attractors, and per-vessel metrics for auditing ethical behavior.

## Acceptance Criteria
- Observability service can list recent gating events filtered by vessel and agent.
- Observability service can list attractors including metadata if present.
- Observability service provides per-vessel metrics summarizing total and blocked events.
