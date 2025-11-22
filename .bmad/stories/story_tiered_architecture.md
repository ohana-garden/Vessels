# Story: Tier 0/1/2 Architecture

## Metadata
- **Epic**: Tiered Architecture
- **Priority**: Medium
- **Status**: Planned
- **Created**: 2025-11-22

## Context

The three-tier architecture (Tier 0=device, Tier 1=edge, Tier 2=cloud) needs to be reflected in runtime code paths with clear configuration and routing.

## Requirements

### Functional

1. **Tier Configuration**: Vessel specifies which tiers are available
2. **Routing Logic**: System routes requests to appropriate tier
3. **Tier Preferences**: Local operations prefer Tier 0/1 when available

### Acceptance Criteria

### AC1: Load tier config
```python
vessel = load_vessel(vessel_id)
assert vessel.tier_config.tier0_enabled == True
assert vessel.tier_config.tier0_model == "Llama-3.2-1B"
```

### AC2: Route to appropriate tier
```python
tier = tier_router.select_tier(request_type="simple_qa", vessel=vessel)
assert tier == TierLevel.TIER0  # Local device
```

## Test Cases

1. **test_tier_config_loaded**: Tier config loads from vessel
2. **test_route_to_tier0**: Simple requests go to device
3. **test_route_to_tier1**: Medium requests go to edge
4. **test_route_to_tier2**: Heavy requests go to cloud
5. **test_tier_fallback**: Fallback when tier unavailable
