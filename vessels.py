#!/usr/bin/env python3
"""
VESSELS CLI - Command Line Interface
Connects directly to the Clean Architecture (VesselsSystem)
"""

import sys
import argparse
import logging
from typing import Dict, Any

# Import the NEW System
from vessels.system import VesselsSystem

# Import startup banner for detailed service status
from vessels.core.startup_banner import run_startup_checks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VesselsCLI")

class VesselsCLI:
    def __init__(self, show_startup_banner=True):
        # Show detailed startup status for all services
        if show_startup_banner:
            run_startup_checks()

        try:
            self.system = VesselsSystem()
            logger.info("✅ Connected to Vessels System")
        except Exception as e:
            logger.error(f"❌ Failed to connect to system: {e}")
            sys.exit(1)

    def interactive_mode(self):
        print("\n" + "="*60)
        print("🌺 VESSELS INTERACTIVE CLI (Clean Architecture)")
        print("="*60)
        print("Type 'exit' to quit.")

        # Mock session for CLI
        session_id = "cli_user"
        context = {'history': []}

        while True:
            try:
                user_input = input("\n🗣️  You: ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("👋 Mahalo!")
                    break

                if not user_input:
                    continue

                # Process via the REAL system
                result = self.system.process_request(user_input, session_id, context)

                # Display Response
                agent = result.get('agent', 'System')

                # Handle different content types
                if result.get('content_type') == 'chat':
                    message = result['data'].get('message', '')
                    print(f"\n🤖 {agent}: {message}")

                elif result.get('content_type') == 'grant_cards':
                    print(f"\n🤖 {agent}: Found Grants:")
                    for grant in result['data']:
                        print(f"   - {grant['title']} ({grant['amount']})")

                elif result.get('content_type') == 'care_protocol':
                    print(f"\n🤖 {agent}: Generated Protocol:")
                    print(f"   Title: {result['data'].get('title')}")
                    for step in result['data'].get('steps', []):
                        print(f"   - {step}")

            except KeyboardInterrupt:
                print("\n👋 Mahalo!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")

    def run_command(self, command: str):
        """Run a single command and exit"""
        session_id = "cli_single"
        result = self.system.process_request(command, session_id, {})
        print(result)

def main():
    parser = argparse.ArgumentParser(description='Vessels CLI')
    parser.add_argument('--command', '-c', help='Execute a single command')
    parser.add_argument('--status', '-s', action='store_true', help='Check system status')

    args = parser.parse_args()

    cli = VesselsCLI()

    if args.status:
        print(cli.system.get_status())
    elif args.command:
        cli.run_command(args.command)
    else:
        cli.interactive_mode()

if __name__ == "__main__":
    main()
