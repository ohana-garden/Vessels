#!/usr/bin/env python3
"""
Vessels CLI - Command-line interface for vessel management.

Provides commands for:
- Listing vessels
- Creating vessels from manifest
- Viewing vessel status
"""

import argparse
import sys
import json
from pathlib import Path

from vessels.core import VesselRegistry, PrivacyLevel
from vessels.core.manifest import load_manifest, validate_manifest


def list_vessels(args):
    """List all vessels."""
    registry = VesselRegistry(registry_dir=args.registry_dir)
    vessels = registry.list_vessels()

    if not vessels:
        print("No vessels found.")
        return

    print(f"\nFound {len(vessels)} vessel(s):\n")
    for vessel in vessels:
        print(f"  {vessel.name}")
        print(f"    ID: {vessel.vessel_id}")
        print(f"    Community: {', '.join(vessel.community_ids)}")
        print(f"    Privacy: {vessel.config.privacy_level.value}")
        print(f"    Projects: {len(vessel.servant_project_ids)}")
        print(f"    Status: {vessel.status}")
        print()


def create_vessel(args):
    """Create a new vessel."""
    registry = VesselRegistry(registry_dir=args.registry_dir)

    privacy_level = PrivacyLevel(args.privacy_level)

    vessel = registry.create_vessel(
        name=args.name,
        community_id=args.community_id,
        description=args.description or "",
        privacy_level=privacy_level
    )

    print(f"Created vessel: {vessel.name}")
    print(f"  ID: {vessel.vessel_id}")
    print(f"  Community: {vessel.community_ids[0]}")
    print(f"  Privacy: {vessel.config.privacy_level.value}")


def load_from_manifest(args):
    """Load vessels from manifest file."""
    # Validate first
    errors = validate_manifest(args.manifest)
    if errors:
        print("Manifest validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    # Load vessels
    vessels = load_manifest(args.manifest)

    # Create in registry
    registry = VesselRegistry(registry_dir=args.registry_dir)

    for vessel in vessels:
        # Save to registry
        registry.vessels[vessel.vessel_id] = vessel
        registry._save_vessel(vessel)
        print(f"Loaded vessel: {vessel.name} ({vessel.vessel_id})")

    print(f"\nSuccessfully loaded {len(vessels)} vessel(s) from manifest.")


def show_vessel(args):
    """Show detailed vessel information."""
    registry = VesselRegistry(registry_dir=args.registry_dir)
    vessel = registry.get_vessel(args.vessel_id)

    if vessel is None:
        print(f"Vessel not found: {args.vessel_id}")
        sys.exit(1)

    print(f"\nVessel: {vessel.name}")
    print(f"  ID: {vessel.vessel_id}")
    print(f"  Description: {vessel.description}")
    print(f"  Community IDs: {', '.join(vessel.community_ids)}")
    print(f"  Graph Namespace: {vessel.graph_namespace}")
    print(f"  Privacy Level: {vessel.config.privacy_level.value}")
    print(f"  Constraint Profile: {vessel.config.constraint_profile_id}")
    print(f"  Status: {vessel.status}")
    print(f"  Created: {vessel.created_at.isoformat()}")
    print(f"  Last Active: {vessel.last_active.isoformat()}")
    print(f"\n  Projects ({len(vessel.servant_project_ids)}):")
    for project_id in vessel.servant_project_ids:
        print(f"    - {project_id}")

    print(f"\n  Trusted Communities ({len(vessel.config.trusted_communities)}):")
    for community_id in vessel.config.trusted_communities:
        print(f"    - {community_id}")

    print(f"\n  Tier Configuration:")
    print(f"    Tier 0 (Device): {'Enabled' if vessel.config.tier_config.tier0_enabled else 'Disabled'}")
    if vessel.config.tier_config.tier0_enabled:
        print(f"      Model: {vessel.config.tier_config.tier0_model}")
    print(f"    Tier 1 (Edge): {'Enabled' if vessel.config.tier_config.tier1_enabled else 'Disabled'}")
    if vessel.config.tier_config.tier1_enabled:
        print(f"      Host: {vessel.config.tier_config.tier1_host}")
    print(f"    Tier 2 (Cloud): {'Enabled' if vessel.config.tier_config.tier2_enabled else 'Disabled'}")

    print(f"\n  Connectors:")
    print(f"    Nostr: {'Enabled' if vessel.config.connector_config.nostr_enabled else 'Disabled'}")
    print(f"    Petals: {'Enabled' if vessel.config.connector_config.petals_enabled else 'Disabled'}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vessels CLI - Manage vessels and configurations"
    )
    parser.add_argument(
        "--registry-dir",
        default="work_dir/vessels",
        help="Vessel registry directory"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List all vessels")
    list_parser.set_defaults(func=list_vessels)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new vessel")
    create_parser.add_argument("--name", required=True, help="Vessel name")
    create_parser.add_argument("--community-id", required=True, help="Community ID")
    create_parser.add_argument("--description", help="Vessel description")
    create_parser.add_argument(
        "--privacy-level",
        choices=["private", "shared", "public", "federated"],
        default="private",
        help="Privacy level"
    )
    create_parser.set_defaults(func=create_vessel)

    # Load manifest command
    load_parser = subparsers.add_parser("load", help="Load vessels from manifest")
    load_parser.add_argument("manifest", help="Path to manifest YAML file")
    load_parser.set_defaults(func=load_from_manifest)

    # Show command
    show_parser = subparsers.add_parser("show", help="Show vessel details")
    show_parser.add_argument("vessel_id", help="Vessel ID")
    show_parser.set_defaults(func=show_vessel)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
