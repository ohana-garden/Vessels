# Story: Vessel Manifest and CLI

## Metadata
- **Epic**: Developer Ergonomics
- **Priority**: Medium
- **Status**: Planned
- **Created**: 2025-11-22

## Context

Developers need an easy way to define vessels via manifest files and interact with them via CLI without modifying excluded files.

## Requirements

### Functional

1. **Manifest File**: YAML/JSON file defines vessels, projects, policies, connectors
2. **Manifest Validation**: CLI validates manifest before loading
3. **Vessel Start**: CLI command starts a vessel from manifest
4. **Vessel List**: CLI lists available vessels

### Acceptance Criteria

### AC1: Load manifest
```python
vessels = load_manifest("vessels_manifest.yaml")
assert len(vessels) > 0
```

### AC2: Validate manifest
```python
errors = validate_manifest("invalid_manifest.yaml")
assert len(errors) > 0
```

### AC3: CLI start vessel
```bash
vessels-cli start --vessel=my_vessel
# Vessel starts successfully
```

## Test Cases

1. **test_load_valid_manifest**: Load valid manifest
2. **test_load_invalid_manifest**: Handle invalid manifest
3. **test_validate_manifest**: Validation catches errors
4. **test_cli_list_vessels**: CLI lists vessels
5. **test_cli_start_vessel**: CLI starts vessel
