#!/usr/bin/env python3
"""
Vessels Main Entry Point

Starts the Vessels platform with full service initialization and monitoring.
This is the primary entry point when running in Docker container.
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VesselsMain")


def main():
    """
    Main entry point for Vessels platform.

    Initializes all services and starts the CLI/web interface.
    """
    try:
        # Import and run the CLI
        from vessels_cli import VesselsCLI

        # Create CLI instance (this will run startup checks)
        cli = VesselsCLI(show_startup_banner=True)

        # Check if running in web mode
        if os.getenv("VESSELS_MODE", "cli").lower() == "web":
            logger.info("Starting web interface on port 5000...")
            # TODO: Import and start web server
            # For now, just run interactive mode
            cli.interactive_mode()
        else:
            # Run interactive CLI
            cli.interactive_mode()

    except KeyboardInterrupt:
        logger.info("\n👋 Vessels shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error starting Vessels: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
