# Story: First-Class Vessel Abstraction

## Metadata
- **Epic**: Vessel as First-Class Object
- **Priority**: Critical
- **Status**: In Progress
- **Created**: 2025-11-22

## Context

Currently, the Vessels platform manages servant projects, communities, and various configurations, but lacks a cohesive "Vessel" abstraction that binds these elements together. A Vessel should represent a complete, isolated environment for coordinating community work.

## Requirements

### Functional

1. **Vessel Creation**: System can create a new Vessel with a unique ID, name, and configuration
2. **Vessel Listing**: System can list all available Vessels
3. **Vessel Loading**: System can load a Vessel's complete state from storage
4. **Vessel Deletion**: System can archive/delete a Vessel safely
5. **Project Association**: Each Vessel knows its associated servant projects
6. **Community Binding**: Each Vessel is bound to one or more community graph namespaces
7. **Constraint Profile**: Each Vessel has an associated constraint manifold/profile
8. **Privacy Configuration**: Each Vessel has a clear privacy level and data sharing rules
9. **Tier Configuration**: Each Vessel knows its device/edge/cloud tier setup
10. **Connector Management**: Each Vessel manages its Nostr/Petals/other connectors

### Non-Functional

- Vessel metadata must load in <100ms
- Vessel creation must be idempotent
- Vessel configuration must be persisted to disk and recoverable after restart

## Acceptance Criteria

### AC1: Create Vessel
```python
vessel = registry.create_vessel(
    name="Lower Puna Elders Care",
    community_id="lower_puna_elders",
    privacy_level=PrivacyLevel.PRIVATE,
    constraint_profile_id="servant_default"
)
assert vessel.vessel_id is not None
assert vessel.name == "Lower Puna Elders Care"
```

### AC2: List Vessels
```python
vessels = registry.list_vessels()
assert len(vessels) > 0
assert all(isinstance(v, Vessel) for v in vessels)
```

### AC3: Load Vessel
```python
vessel = registry.get_vessel(vessel_id)
assert vessel is not None
assert vessel.community_ids == ["lower_puna_elders"]
```

### AC4: Attach Project
```python
registry.attach_project_to_vessel(vessel_id, project_id)
vessel = registry.get_vessel(vessel_id)
assert project_id in vessel.servant_project_ids
```

### AC5: Set Privacy
```python
registry.set_vessel_privacy(vessel_id, PrivacyLevel.SHARED)
vessel = registry.get_vessel(vessel_id)
assert vessel.privacy_level == PrivacyLevel.SHARED
```

### AC6: Persist and Reload
```python
# After restart
vessel_reloaded = registry.get_vessel(vessel_id)
assert vessel_reloaded.name == vessel.name
assert vessel_reloaded.config == vessel.config
```

## Test Cases

1. **test_create_vessel**: Create vessel with minimal config
2. **test_create_vessel_full**: Create vessel with all optional fields
3. **test_list_vessels_empty**: List vessels when none exist
4. **test_list_vessels**: List vessels after creating several
5. **test_get_vessel_not_found**: Attempt to get non-existent vessel
6. **test_attach_project**: Attach project to vessel
7. **test_attach_project_idempotent**: Attach same project twice
8. **test_set_privacy**: Change vessel privacy level
9. **test_persistence**: Verify vessel survives restart
10. **test_delete_vessel**: Archive a vessel

## Tools & APIs

- `vessels/core/vessel.py`: Vessel model
- `vessels/core/registry.py`: Vessel registry and management
- `vessels/tests/test_vessel_core.py`: Test suite

## Dependencies

- Existing `ServantProject` model
- Privacy enums from knowledge layer
- Tier configuration from `config/vessels.yaml`
