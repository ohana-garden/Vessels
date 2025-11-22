# Story: Data Governance and Privacy

## Metadata
- **Epic**: Data Governance
- **Priority**: Critical
- **Status**: Planned
- **Created**: 2025-11-22

## Context

Cross-community and cross-vessel data access must be governed by clear policies that respect privacy levels and control which agent classes can read/write to which namespaces.

## Requirements

### Functional

1. **Privacy Policy per Vessel**: Each vessel defines what can be shared
2. **Cross-Vessel Access Control**: Queries across vessels checked against policy
3. **Agent Class Restrictions**: Commercial agents cannot write to community graphs
4. **Node/Edge Type Filtering**: Policy specifies which types can be exported

### Acceptance Criteria

### AC1: Cross-vessel query allowed
```python
# Vessel A trusts Vessel B
result = policy.check_read_access(
    vessel_id="vessel_b",
    agent_id="agent_from_vessel_a",
    resource="community_graph"
)
assert result == True
```

### AC2: Cross-vessel query denied
```python
# Vessel A does not trust Vessel C
result = policy.check_read_access(
    vessel_id="vessel_c",
    agent_id="agent_from_vessel_a",
    resource="community_graph"
)
assert result == False
```

### AC3: Commercial agent write blocked
```python
result = policy.check_write_access(
    vessel_id="vessel_a",
    agent_identity=commercial_agent,
    resource="community_graph"
)
assert result == False
```

## Test Cases

1. **test_read_access_allowed**: Allowed cross-vessel read
2. **test_read_access_denied**: Denied cross-vessel read
3. **test_write_access_servant_allowed**: Servant can write
4. **test_write_access_commercial_denied**: Commercial agent cannot write
5. **test_node_type_filtering**: Only allowed node types exported
