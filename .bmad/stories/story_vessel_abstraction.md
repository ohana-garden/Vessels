# Story: Vessel abstraction and registry

## Summary
Operators need to define vessels with clear metadata so that projects, constraints, and privacy settings are tied to a first-class object that can be created, listed, loaded, and deleted.

## Acceptance Criteria
- A vessel can be instantiated from configuration data with id, name, description, communities, graph namespace, privacy level, constraint profile, and tier/connectors metadata.
- Vessels can be persisted, listed, loaded by id, and deleted through a registry.
- Projects can be attached to and detached from a vessel and are persisted.
- Privacy level updates on a vessel are persisted and retrievable.
