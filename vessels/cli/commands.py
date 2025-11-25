"""
Vessels CLI Commands - Command-line interface for vessel management.

Usage:
    vessels-cli list                     List all vessels
    vessels-cli show <vessel_id>         Show vessel details
    vessels-cli start --manifest <file>  Start vessels from manifest
    vessels-cli validate <manifest>      Validate manifest file
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from .manifest import load_manifest, validate_manifest, ManifestLoader
from vessels.core import VesselRegistry, Vessel

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def cmd_list(args):
    """List all vessels."""
    try:
        registry = VesselRegistry()
        vessels = registry.list_vessels()

        if not vessels:
            print("No vessels found.")
            return 0

        print(f"\nFound {len(vessels)} vessel(s):\n")
        print(f"{'ID':<36} {'Name':<30} {'Privacy':<12} {'Status':<10}")
        print("-" * 90)

        for vessel in vessels:
            print(
                f"{vessel.vessel_id:<36} "
                f"{vessel.name:<30} "
                f"{vessel.privacy_level.value:<12} "
                f"{vessel.status:<10}"
            )

        return 0

    except Exception as e:
        logger.error(f"Error listing vessels: {e}")
        return 1


def cmd_show(args):
    """Show vessel details."""
    try:
        registry = VesselRegistry()
        vessel = registry.get_vessel(args.vessel_id)

        if not vessel:
            print(f"Vessel '{args.vessel_id}' not found.")
            return 1

        print(f"\nVessel: {vessel.name}")
        print("=" * 50)
        print(f"ID:                  {vessel.vessel_id}")
        print(f"Description:         {vessel.description or '(none)'}")
        print(f"Privacy Level:       {vessel.privacy_level.value}")
        print(f"Constraint Profile:  {vessel.constraint_profile_id}")
        print(f"Graph Namespace:     {vessel.graph_namespace}")
        print(f"Communities:         {', '.join(vessel.community_ids)}")
        print(f"Projects:            {', '.join(vessel.servant_project_ids) or '(none)'}")
        print(f"Status:              {vessel.status}")
        print(f"Created:             {vessel.created_at}")
        print(f"Last Active:         {vessel.last_active}")

        print("\nTier Configuration:")
        print(f"  Tier 0 (Device):   {'Enabled' if vessel.tier_config.tier0_enabled else 'Disabled'}")
        if vessel.tier_config.tier0_enabled:
            print(f"    Model: {vessel.tier_config.tier0_model}")
        print(f"  Tier 1 (Edge):     {'Enabled' if vessel.tier_config.tier1_enabled else 'Disabled'}")
        if vessel.tier_config.tier1_enabled:
            print(f"    Host: {vessel.tier_config.tier1_host}:{vessel.tier_config.tier1_port}")
            print(f"    Model: {vessel.tier_config.tier1_model}")
        print(f"  Tier 2 (Cloud):    {'Enabled' if vessel.tier_config.tier2_enabled else 'Disabled'}")

        if vessel.connectors:
            print("\nConnectors:")
            for name, config in vessel.connectors.items():
                print(f"  {name}: {config}")

        return 0

    except Exception as e:
        logger.error(f"Error showing vessel: {e}")
        return 1


def cmd_start(args):
    """Start vessels from manifest."""
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print(f"Manifest file not found: {manifest_path}")
        return 1

    try:
        # Validate first
        validation = validate_manifest(manifest_path)

        if validation.warnings:
            for warning in validation.warnings:
                print(f"Warning at {warning.path}: {warning.message}")

        if not validation.valid:
            print("\nManifest validation failed:")
            for error in validation.errors:
                print(f"  Error at {error.path}: {error.message}")
            return 1

        # Load vessels
        vessels = load_manifest(manifest_path)

        if not vessels:
            print("No vessels found in manifest.")
            return 1

        # Register vessels
        registry = VesselRegistry()

        print(f"\nLoading {len(vessels)} vessel(s) from {manifest_path}:")

        for vessel in vessels:
            try:
                existing = registry.get_vessel(vessel.vessel_id)
                if existing:
                    print(f"  Updating: {vessel.name} ({vessel.vessel_id})")
                else:
                    print(f"  Creating: {vessel.name} ({vessel.vessel_id})")

                registry.create_vessel(vessel)

            except Exception as e:
                print(f"  Failed: {vessel.name} - {e}")
                if not args.continue_on_error:
                    return 1

        print("\nVessels loaded successfully!")
        return 0

    except Exception as e:
        logger.error(f"Error starting vessels: {e}")
        return 1


def cmd_validate(args):
    """Validate manifest file."""
    manifest_path = Path(args.manifest)

    if not manifest_path.exists():
        print(f"Manifest file not found: {manifest_path}")
        return 1

    validation = validate_manifest(manifest_path)

    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"  {warning.path}: {warning.message}")

    if validation.errors:
        print("Errors:")
        for error in validation.errors:
            print(f"  {error.path}: {error.message}")

    if validation.valid:
        print(f"\n{manifest_path}: Valid")
        return 0
    else:
        print(f"\n{manifest_path}: Invalid")
        return 1


def cmd_create(args):
    """Create a new vessel."""
    try:
        registry = VesselRegistry()

        vessel = Vessel.create(
            name=args.name,
            community_id=args.community,
            description=args.description or "",
        )

        registry.create_vessel(vessel)

        print(f"Created vessel: {vessel.name}")
        print(f"  ID: {vessel.vessel_id}")
        print(f"  Community: {args.community}")

        return 0

    except Exception as e:
        logger.error(f"Error creating vessel: {e}")
        return 1


def cmd_delete(args):
    """Delete a vessel."""
    try:
        registry = VesselRegistry()

        if not args.force:
            vessel = registry.get_vessel(args.vessel_id)
            if vessel:
                confirm = input(f"Delete vessel '{vessel.name}' ({args.vessel_id})? [y/N]: ")
                if confirm.lower() != 'y':
                    print("Cancelled.")
                    return 0

        success = registry.delete_vessel(args.vessel_id)

        if success:
            print(f"Deleted vessel: {args.vessel_id}")
            return 0
        else:
            print(f"Vessel not found: {args.vessel_id}")
            return 1

    except Exception as e:
        logger.error(f"Error deleting vessel: {e}")
        return 1


def main(argv=None):
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="vessels-cli",
        description="Vessels CLI - Manage AI agent vessels"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all vessels")
    list_parser.set_defaults(func=cmd_list)

    # Show command
    show_parser = subparsers.add_parser("show", help="Show vessel details")
    show_parser.add_argument("vessel_id", help="Vessel ID to show")
    show_parser.set_defaults(func=cmd_show)

    # Start command
    start_parser = subparsers.add_parser("start", help="Start vessels from manifest")
    start_parser.add_argument(
        "--manifest", "-m",
        required=True,
        help="Path to manifest file"
    )
    start_parser.add_argument(
        "--continue-on-error", "-c",
        action="store_true",
        help="Continue loading other vessels if one fails"
    )
    start_parser.set_defaults(func=cmd_start)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate manifest file")
    validate_parser.add_argument("manifest", help="Path to manifest file")
    validate_parser.set_defaults(func=cmd_validate)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new vessel")
    create_parser.add_argument("name", help="Vessel name")
    create_parser.add_argument("--community", "-c", required=True, help="Community ID")
    create_parser.add_argument("--description", "-d", help="Vessel description")
    create_parser.set_defaults(func=cmd_create)

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a vessel")
    delete_parser.add_argument("vessel_id", help="Vessel ID to delete")
    delete_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args(argv)

    setup_logging(args.verbose)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
