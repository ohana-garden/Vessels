#!/usr/bin/env python3
"""
VESSELS CLI - Command Line Interface
Uses AgentZeroCore as THE main core for all operations.
"""

import argparse
import logging

from agent_zero_core import agent_zero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("VesselsCLI")


class VesselsCLI:
    def __init__(self, show_startup_banner=True):
        if show_startup_banner:
            self._show_startup_banner()

        # Initialize Agent Zero
        try:
            agent_zero.initialize()
            logger.info("Connected to Agent Zero Core")
        except Exception as e:
            logger.error(f"Failed to initialize Agent Zero: {e}")
            # Continue anyway - A0 may work in degraded mode

    def _show_startup_banner(self):
        """Display startup banner with system status."""
        print("\n" + "=" * 60)
        print("   VESSELS PLATFORM")
        print("   Powered by Agent Zero Core")
        print("=" * 60)
        print(f"   Agents: {len(agent_zero.agents)}")
        print(f"   Status: {'Running' if agent_zero.running else 'Idle'}")
        print("=" * 60)

    def interactive_mode(self):
        print("\n" + "=" * 60)
        print("VESSELS INTERACTIVE CLI")
        print("=" * 60)
        print("Type 'exit' to quit, 'status' for system status.")

        user_id = "cli_user"

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                if user_input.lower() == 'status':
                    self._show_status()
                    continue

                # Process via Agent Zero Core
                result = agent_zero.process_request(user_input, user_id=user_id)

                # Display response
                message = result.get('message', str(result))
                print(f"\nVessels: {message}")

                # Show agent info if any were spawned
                if result.get('agents'):
                    print(f"   [Spawned {len(result['agents'])} agents]")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {e}")

    def _show_status(self):
        """Display system status."""
        print("\n--- System Status ---")
        print(f"Agents active: {len(agent_zero.agents)}")
        print(f"Running: {agent_zero.running}")

        if agent_zero.agents:
            print("\nActive agents:")
            for agent_id, agent in list(agent_zero.agents.items())[:5]:
                print(f"  - {agent.specification.name}: {agent.status.value}")

    def run_command(self, command: str):
        """Run a single command and exit."""
        result = agent_zero.process_request(command, user_id="cli_single")
        print(result)


def main():
    parser = argparse.ArgumentParser(description='Vessels CLI')
    parser.add_argument('--command', '-c', help='Execute a single command')
    parser.add_argument('--status', '-s', action='store_true', help='Check system status')

    args = parser.parse_args()

    cli = VesselsCLI()

    if args.status:
        cli._show_status()
    elif args.command:
        cli.run_command(args.command)
    else:
        cli.interactive_mode()


if __name__ == "__main__":
    main()
