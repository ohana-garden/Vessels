# Story: Human Governance as Graph Entities

## Metadata
- **Epic**: Governance Entities
- **Priority**: High
- **Status**: Planned
- **Created**: 2025-11-22

## Context

Human governance structures (councils, boards, assemblies) and their decisions must be first-class entities in the knowledge graph, making vessels explicitly accountable to people.

## Requirements

### Functional

1. **Governance Body Nodes**: Councils, boards, assemblies as graph entities
2. **Decision Nodes**: Decisions and policies as graph entities
3. **Approval Links**: Link decisions to vessels and policies
4. **Governance History**: Query governance history for a vessel

### Acceptance Criteria

### AC1: Create governance body
```python
council = graphiti.create_node(
    "GovernanceBody",
    name="Puna Elders Council",
    type="council"
)
assert council.id is not None
```

### AC2: Record decision
```python
decision = graphiti.create_node(
    "Decision",
    description="Approved transport servant",
    approved_at="2025-11-22"
)
graphiti.create_relationship(council.id, "MADE_DECISION", decision.id)
graphiti.create_relationship(decision.id, "APPROVES", vessel.id)
```

### AC3: Query governance history
```python
history = graphiti.get_governance_history(vessel_id)
assert len(history) > 0
```

## Test Cases

1. **test_create_governance_body**: Create council/board
2. **test_create_decision**: Create decision entity
3. **test_link_decision_to_vessel**: Link approval to vessel
4. **test_query_governance_history**: Query history
5. **test_policy_modification_tracking**: Track policy changes over time
