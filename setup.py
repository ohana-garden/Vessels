#!/usr/bin/env python3
"""
Vessels Interactive Setup

Collects API keys and configuration, writes to .env file.
Automatically configures Agent Zero and all payment frameworks.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple


class VesselsSetup:
    """Interactive setup for Vessels platform"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        self.config = {}

    def print_banner(self):
        """Print setup banner"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    VESSELS INTERACTIVE SETUP                         ║
║                                                                      ║
║  This will configure API keys for:                                  ║
║  • Agent Zero (OpenAI, Anthropic, etc.)                             ║
║  • Payment Services (TigerBeetle, Mojaloop, RTP)                    ║
║  • TEN Framework (Voice/STT/TTS)                                    ║
║  • Petals (Distributed AI)                                          ║
║  • Nostr (P2P Network)                                              ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    def ask_question(
        self,
        key: str,
        description: str,
        required: bool = False,
        default: Optional[str] = None,
        secret: bool = False
    ) -> str:
        """Ask user for configuration value"""

        prompt = f"\n{description}"
        if default:
            prompt += f" [{default}]"
        if required:
            prompt += " (required)"
        prompt += ": "

        while True:
            if secret:
                import getpass
                value = getpass.getpass(prompt)
            else:
                value = input(prompt).strip()

            # Use default if provided and no input
            if not value and default:
                value = default

            # Check if required
            if required and not value:
                print("⚠️  This field is required. Please enter a value.")
                continue

            return value

    def ask_yes_no(self, question: str, default: bool = False) -> bool:
        """Ask yes/no question"""
        default_text = "Y/n" if default else "y/N"
        while True:
            response = input(f"{question} [{default_text}]: ").strip().lower()

            if not response:
                return default

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")

    def collect_agent_zero_config(self):
        """Collect Agent Zero API keys"""
        print("\n" + "="*72)
        print("AGENT ZERO - AI MODEL CONFIGURATION")
        print("="*72)
        print("\nAgent Zero can use multiple AI providers.")
        print("Configure at least one to get started.")

        # OpenAI
        print("\n--- OpenAI ---")
        if self.ask_yes_no("Configure OpenAI?", default=True):
            self.config['OPENAI_API_KEY'] = self.ask_question(
                'OPENAI_API_KEY',
                'OpenAI API Key (sk-...)',
                required=False,
                secret=True
            )
            if self.config['OPENAI_API_KEY']:
                self.config['OPENAI_MODEL'] = self.ask_question(
                    'OPENAI_MODEL',
                    'OpenAI Model',
                    default='gpt-4-turbo-preview'
                )

        # Anthropic
        print("\n--- Anthropic (Claude) ---")
        if self.ask_yes_no("Configure Anthropic?", default=False):
            self.config['ANTHROPIC_API_KEY'] = self.ask_question(
                'ANTHROPIC_API_KEY',
                'Anthropic API Key',
                required=False,
                secret=True
            )
            if self.config['ANTHROPIC_API_KEY']:
                self.config['ANTHROPIC_MODEL'] = self.ask_question(
                    'ANTHROPIC_MODEL',
                    'Anthropic Model',
                    default='claude-3-opus-20240229'
                )

        # Azure OpenAI
        print("\n--- Azure OpenAI ---")
        if self.ask_yes_no("Configure Azure OpenAI?", default=False):
            self.config['AZURE_OPENAI_API_KEY'] = self.ask_question(
                'AZURE_OPENAI_API_KEY',
                'Azure OpenAI API Key',
                secret=True
            )
            if self.config['AZURE_OPENAI_API_KEY']:
                self.config['AZURE_OPENAI_ENDPOINT'] = self.ask_question(
                    'AZURE_OPENAI_ENDPOINT',
                    'Azure OpenAI Endpoint',
                    required=True
                )
                self.config['AZURE_OPENAI_DEPLOYMENT'] = self.ask_question(
                    'AZURE_OPENAI_DEPLOYMENT',
                    'Azure OpenAI Deployment Name',
                    required=True
                )

        # Local LLMs
        print("\n--- Local LLMs (Ollama) ---")
        if self.ask_yes_no("Use local LLMs via Ollama?", default=True):
            self.config['OLLAMA_ENABLED'] = 'true'
            self.config['OLLAMA_BASE_URL'] = self.ask_question(
                'OLLAMA_BASE_URL',
                'Ollama Base URL',
                default='http://localhost:11434'
            )
            self.config['OLLAMA_MODEL'] = self.ask_question(
                'OLLAMA_MODEL',
                'Ollama Model',
                default='llama3.2:3b'
            )

    def collect_payment_config(self):
        """Collect payment service configuration"""
        print("\n" + "="*72)
        print("PAYMENT SERVICES - TigerBeetle, Mojaloop, RTP")
        print("="*72)

        # TigerBeetle (required for payments)
        print("\nTigerBeetle runs automatically (no keys needed)")
        self.config['TIGERBEETLE_CLUSTER_ID'] = '0'
        self.config['TIGERBEETLE_REPLICA_ADDRESSES'] = 'localhost:3001'

        # JWT for payment API
        print("\n--- Payment API Security ---")
        import secrets
        jwt_secret = secrets.token_urlsafe(32)
        self.config['JWT_SECRET'] = jwt_secret
        print(f"✅ Generated JWT secret: {jwt_secret[:16]}...")

        # Mojaloop
        print("\n--- Mojaloop (Instant Payments) ---")
        if self.ask_yes_no("Configure Mojaloop?", default=False):
            self.config['MOJALOOP_ENABLED'] = 'true'
            self.config['MOJALOOP_SWITCH_URL'] = self.ask_question(
                'MOJALOOP_SWITCH_URL',
                'Mojaloop Switch URL',
                default='https://mojaloop.hawaii.gov'
            )
            self.config['MOJALOOP_PARTICIPANT_ID'] = self.ask_question(
                'MOJALOOP_PARTICIPANT_ID',
                'Mojaloop Participant ID (DFSP ID)',
                default='vessels-dfsp'
            )
            self.config['MOJALOOP_API_KEY'] = self.ask_question(
                'MOJALOOP_API_KEY',
                'Mojaloop API Key',
                secret=True
            )
            self.config['MOJALOOP_CALLBACK_URL'] = self.ask_question(
                'MOJALOOP_CALLBACK_URL',
                'Mojaloop Callback URL',
                default='https://api.vessels.ohana/webhooks/mojaloop'
            )
        else:
            self.config['MOJALOOP_ENABLED'] = 'false'

        # RTP/FedNow
        print("\n--- RTP/FedNow (Real-Time Payments) ---")
        if self.ask_yes_no("Configure RTP/FedNow?", default=False):
            self.config['RTP_PROVIDER'] = self.ask_question(
                'RTP_PROVIDER',
                'RTP Provider',
                default='modern_treasury'
            )
            self.config['RTP_API_URL'] = self.ask_question(
                'RTP_API_URL',
                'RTP API URL',
                default='https://api.moderntreasury.com'
            )
            self.config['RTP_API_KEY'] = self.ask_question(
                'RTP_API_KEY',
                'RTP API Key',
                secret=True
            )

        # Modern Treasury (ACH + RTP)
        print("\n--- Modern Treasury (ACH + RTP) ---")
        if self.ask_yes_no("Configure Modern Treasury?", default=False):
            self.config['MODERN_TREASURY_API_KEY'] = self.ask_question(
                'MODERN_TREASURY_API_KEY',
                'Modern Treasury API Key',
                secret=True
            )
            self.config['MODERN_TREASURY_ORG_ID'] = self.ask_question(
                'MODERN_TREASURY_ORG_ID',
                'Modern Treasury Organization ID'
            )

    def collect_ten_framework_config(self):
        """Collect TEN Framework configuration"""
        print("\n" + "="*72)
        print("TEN FRAMEWORK - Voice/Multimodal UX")
        print("="*72)

        if self.ask_yes_no("Enable TEN Framework?", default=True):
            self.config['TEN_FRAMEWORK_ENABLED'] = 'true'
            self.config['TEN_GRAPHS_DIR'] = '/app/graphs'

            # OpenAI Realtime API (for TEN voice)
            print("\n--- OpenAI Realtime API (Voice) ---")
            if self.ask_yes_no("Use OpenAI Realtime API for voice?", default=False):
                # Reuse OpenAI key if already set
                if 'OPENAI_API_KEY' not in self.config:
                    self.config['OPENAI_API_KEY'] = self.ask_question(
                        'OPENAI_API_KEY',
                        'OpenAI API Key',
                        secret=True
                    )
        else:
            self.config['TEN_FRAMEWORK_ENABLED'] = 'false'

    def collect_petals_config(self):
        """Collect Petals distributed AI configuration"""
        print("\n" + "="*72)
        print("PETALS - Distributed AI (Tier 2)")
        print("="*72)

        if self.ask_yes_no("Enable Petals distributed AI?", default=False):
            self.config['PETALS_ENABLED'] = 'true'
            self.config['PETALS_MODEL'] = self.ask_question(
                'PETALS_MODEL',
                'Petals Model',
                default='petals-team/StableBeluga2'
            )
        else:
            self.config['PETALS_ENABLED'] = 'false'

    def collect_nostr_config(self):
        """Collect Nostr P2P configuration"""
        print("\n" + "="*72)
        print("NOSTR - Peer-to-Peer Network")
        print("="*72)

        if self.ask_yes_no("Configure Nostr relays?", default=False):
            relays = self.ask_question(
                'NOSTR_RELAYS',
                'Nostr Relays (comma-separated)',
                default='wss://relay.damus.io,wss://nos.lol'
            )
            self.config['NOSTR_RELAYS'] = relays

            # Generate Nostr keys if needed
            if self.ask_yes_no("Generate new Nostr keys?", default=True):
                import secrets
                private_key = secrets.token_hex(32)
                self.config['NOSTR_PRIVATE_KEY'] = private_key
                print(f"✅ Generated Nostr private key")

    def write_env_file(self):
        """Write configuration to .env file"""
        print("\n" + "="*72)
        print("WRITING CONFIGURATION")
        print("="*72)

        # Check if .env exists
        if self.env_file.exists():
            if not self.ask_yes_no(f"\n⚠️  {self.env_file} already exists. Overwrite?", default=False):
                backup = self.env_file.with_suffix('.env.backup')
                self.env_file.rename(backup)
                print(f"✅ Backed up existing .env to {backup}")

        # Write new .env
        with open(self.env_file, 'w') as f:
            f.write("# Vessels Configuration - Generated by setup.py\n")
            f.write("# " + "="*68 + "\n\n")

            # Group by category
            categories = {
                'Agent Zero': ['OPENAI_', 'ANTHROPIC_', 'AZURE_', 'OLLAMA_'],
                'Payment Services': ['TIGERBEETLE_', 'JWT_', 'MOJALOOP_', 'RTP_', 'MODERN_TREASURY_'],
                'TEN Framework': ['TEN_'],
                'Petals': ['PETALS_'],
                'Nostr': ['NOSTR_'],
                'Database': ['DATABASE_', 'POSTGRES_'],
                'General': []
            }

            for category, prefixes in categories.items():
                category_keys = [k for k in self.config.keys()
                               if any(k.startswith(p) for p in prefixes)] if prefixes else []

                if category == 'General':
                    # Catch all remaining keys
                    all_categorized = set()
                    for cat_prefixes in categories.values():
                        for k in self.config.keys():
                            if any(k.startswith(p) for p in cat_prefixes):
                                all_categorized.add(k)
                    category_keys = [k for k in self.config.keys() if k not in all_categorized]

                if category_keys:
                    f.write(f"# {category}\n")
                    for key in sorted(category_keys):
                        value = self.config[key]
                        f.write(f"{key}={value}\n")
                    f.write("\n")

        print(f"✅ Configuration written to {self.env_file}")

    def create_agent_zero_config(self):
        """Create Agent Zero configuration to skip setup screen"""
        print("\n" + "="*72)
        print("CONFIGURING AGENT ZERO")
        print("="*72)

        # Create Agent Zero config directory
        a0_config_dir = self.project_root / "agent_zero_config"
        a0_config_dir.mkdir(exist_ok=True)

        # Write Agent Zero config JSON
        import json
        a0_config = {
            "api_keys_configured": True,
            "skip_setup": True,
            "providers": []
        }

        # Add configured providers
        if self.config.get('OPENAI_API_KEY'):
            a0_config['providers'].append({
                "type": "openai",
                "api_key": self.config['OPENAI_API_KEY'],
                "model": self.config.get('OPENAI_MODEL', 'gpt-4-turbo-preview')
            })

        if self.config.get('ANTHROPIC_API_KEY'):
            a0_config['providers'].append({
                "type": "anthropic",
                "api_key": self.config['ANTHROPIC_API_KEY'],
                "model": self.config.get('ANTHROPIC_MODEL', 'claude-3-opus-20240229')
            })

        if self.config.get('OLLAMA_ENABLED') == 'true':
            a0_config['providers'].append({
                "type": "ollama",
                "base_url": self.config.get('OLLAMA_BASE_URL', 'http://localhost:11434'),
                "model": self.config.get('OLLAMA_MODEL', 'llama3.2:3b')
            })

        config_file = a0_config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(a0_config, f, indent=2)

        print(f"✅ Agent Zero config written to {config_file}")
        print("   Agent Zero will skip setup screen on startup")

    def run(self):
        """Run interactive setup"""
        self.print_banner()

        print("\nThis setup will guide you through configuring Vessels.")
        print("You can skip optional components by answering 'n'.")
        print("\nPress Enter to continue...")
        input()

        # Collect all configuration
        self.collect_agent_zero_config()
        self.collect_payment_config()
        self.collect_ten_framework_config()
        self.collect_petals_config()
        self.collect_nostr_config()

        # Write configuration
        self.write_env_file()
        self.create_agent_zero_config()

        # Final summary
        print("\n" + "="*72)
        print("✨ SETUP COMPLETE!")
        print("="*72)
        print(f"\nConfiguration saved to: {self.env_file}")
        print("\nTo start Vessels:")
        print("  docker-compose up --build")
        print("\nOr run locally:")
        print("  python vessels.py")
        print("\n" + "="*72 + "\n")


def main():
    """Main entry point"""
    setup = VesselsSetup()
    try:
        setup.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
