# Grants Use Case

This module provides grant discovery, writing, and coordination as a Vessels use case.

## Overview

The Grants use case allows you to:
- Discover grant opportunities from multiple sources
- Create and manage grant applications
- Track your grant pipeline
- Generate reports

All operations are scoped to a specific Vessel, ensuring data isolation and proper governance.

## Quick Start

```python
from vessels.core import VesselRegistry
from vessels.use_cases.grants import GrantsUseCase

# Get or create a vessel for grant management
registry = VesselRegistry()
vessel = registry.create_vessel(
    name="Elder Care Grants",
    community_id="lower_puna_community",
    description="Grant management for elder care programs"
)

# Create grants use case for this vessel
grants = GrantsUseCase(vessel)

# Discover grants
opportunities = grants.discover_grants(
    focus_areas=["elder care", "healthcare", "community health"],
    geographic_scope="Hawaii"
)

print(f"Found {len(opportunities)} grants")
for grant in opportunities[:3]:
    print(f"  - {grant.title}: {grant.amount} (score: {grant.analysis_score:.2f})")

# Create application for best match
if opportunities:
    best_match = opportunities[0]
    application = grants.create_application(grant_id=best_match.id)
    print(f"Created application: {application.id}")

# Get pipeline summary
summary = grants.get_pipeline_summary()
print(f"Total grants: {summary['grants']['total']}")
print(f"Total applications: {summary['applications']['total']}")
```

## Architecture

### Models (`models.py`)
- `GrantOpportunity`: Represents a grant funding opportunity
- `GrantApplication`: Represents a grant application
- `GrantStatus`: Status enum for tracking progress
- `GrantSearchCriteria`: Search criteria for discovering grants

### Repository (`repository.py`)
- SQLite-based storage for grants and applications
- Scoped to a specific vessel
- Thread-safe operations

### Discovery Service (`discovery.py`)
- Searches multiple grant sources
- Calculates match scores
- Generates match reasoning

### Application Writer (`writer.py`)
- Generates application narratives
- Creates budgets
- Manages compliance checklists

### Use Case (`use_case.py`)
- Main orchestration class
- Coordinates all grant operations
- Provides reporting capabilities

## Data Storage

Grant data is stored in SQLite databases:
- `data/grants_{vessel_id}.db`: Per-vessel grant storage

## Extending

### Adding New Grant Sources

Extend the `GrantDiscoveryService` class:

```python
class CustomDiscoveryService(GrantDiscoveryService):
    def _search_custom_source(self, criteria):
        # Implement your source
        return [GrantOpportunity(...)]
```

### Custom Application Content

Pass custom sections when creating applications:

```python
application = grants.create_application(
    grant_id="grant-123",
    custom_sections={
        "executive_summary": "Our custom executive summary...",
    }
)
```
