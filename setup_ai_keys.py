#!/usr/bin/env python3
"""
SECURE API KEY SETUP HELPER
Helps users securely configure their API keys for AI content generation
"""

import os
import sys
import getpass
from pathlib import Path


def print_header():
    """Print setup header"""
    print("\n" + "=" * 70)
    print("  🔒 SHOGHI AI CONTENT GENERATOR - SECURE SETUP")
    print("=" * 70)
    print()


def print_security_warning():
    """Print security warning"""
    print("⚠️  SECURITY REMINDERS:")
    print("  • Never share API keys in plain text")
    print("  • Never commit .env files to git")
    print("  • Revoke any keys that have been exposed")
    print("  • Use separate keys for development and production")
    print()


def check_existing_env():
    """Check if .env file already exists"""
    env_path = Path(".env")
    if env_path.exists():
        print("ℹ️  Existing .env file found")
        response = input("  Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("  Setup cancelled. Existing .env file preserved.")
            return False
        print()
    return True


def get_api_key(provider_name: str, provider_url: str) -> str:
    """Securely get API key from user"""
    print(f"\n{provider_name} Setup")
    print(f"  Get your key from: {provider_url}")

    has_key = input(f"  Do you have a {provider_name} API key? (y/N): ").strip().lower()

    if has_key == 'y':
        # Use getpass to hide input (more secure)
        api_key = getpass.getpass(f"  Enter {provider_name} API key (hidden): ").strip()

        if api_key:
            # Basic validation
            if provider_name == "OpenAI" and not api_key.startswith("sk-"):
                print("  ⚠️  Warning: OpenAI keys typically start with 'sk-'")
                confirm = input("  Continue anyway? (y/N): ").strip().lower()
                if confirm != 'y':
                    return ""

            elif provider_name == "Anthropic" and not api_key.startswith("sk-ant-"):
                print("  ⚠️  Warning: Anthropic keys typically start with 'sk-ant-'")
                confirm = input("  Continue anyway? (y/N): ").strip().lower()
                if confirm != 'y':
                    return ""

            print(f"  ✓ {provider_name} key received")
            return api_key
        else:
            print(f"  ℹ️  No {provider_name} key provided")
            return ""
    else:
        print(f"  ℹ️  Skipping {provider_name} setup")
        return ""


def create_env_file(openai_key: str, anthropic_key: str):
    """Create .env file with API keys"""

    if not openai_key and not anthropic_key:
        print("\n⚠️  No API keys provided!")
        print("  The system will fall back to template-based generation.")
        print("  You can run this setup again later to add keys.")
        create_anyway = input("\nCreate .env file anyway? (y/N): ").strip().lower()
        if create_anyway != 'y':
            return False

    # Determine provider preference
    if openai_key and anthropic_key:
        print("\n  Both API keys provided!")
        print("  Which provider should be preferred?")
        print("    1. Auto (try Anthropic first, then OpenAI)")
        print("    2. OpenAI (GPT-4)")
        print("    3. Anthropic (Claude)")
        choice = input("  Choice (1-3) [1]: ").strip() or "1"

        provider_map = {"1": "auto", "2": "openai", "3": "anthropic"}
        ai_provider = provider_map.get(choice, "auto")
    elif openai_key:
        ai_provider = "openai"
    elif anthropic_key:
        ai_provider = "anthropic"
    else:
        ai_provider = "auto"

    # Create .env content
    env_content = f"""# SHOGHI AI CONTENT GENERATION - API KEYS
# Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# DO NOT COMMIT THIS FILE TO GIT!

# OpenAI API Key (for GPT-4)
{"OPENAI_API_KEY=" + openai_key if openai_key else "# OPENAI_API_KEY=your_key_here"}

# Anthropic API Key (for Claude)
{"ANTHROPIC_API_KEY=" + anthropic_key if anthropic_key else "# ANTHROPIC_API_KEY=your_key_here"}

# Content Generation Settings
AI_PROVIDER={ai_provider}
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=2000

# Quality Assurance Settings
MIN_QUALITY_SCORE=0.7
ENABLE_MORAL_CHECKS=true

# Logging
LOG_LEVEL=INFO
"""

    # Write .env file
    try:
        with open(".env", "w") as f:
            f.write(env_content)

        # Set restrictive permissions (Unix-like systems only)
        try:
            os.chmod(".env", 0o600)  # Read/write for owner only
        except:
            pass  # Windows doesn't support chmod

        print("\n✓ .env file created successfully!")
        return True

    except Exception as e:
        print(f"\n✗ Error creating .env file: {e}")
        return False


def check_gitignore():
    """Ensure .env is in .gitignore"""
    gitignore_path = Path(".gitignore")

    try:
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                content = f.read()

            if ".env" not in content:
                print("\n⚠️  .env is not in .gitignore")
                add_to_gitignore = input("  Add .env to .gitignore? (Y/n): ").strip().lower()

                if add_to_gitignore != 'n':
                    with open(gitignore_path, "a") as f:
                        f.write("\n# Environment variables (API keys)\n.env\n")
                    print("  ✓ Added .env to .gitignore")
            else:
                print("\n✓ .env is already in .gitignore")
        else:
            print("\n⚠️  No .gitignore file found")
            create_gitignore = input("  Create .gitignore with .env entry? (Y/n): ").strip().lower()

            if create_gitignore != 'n':
                with open(gitignore_path, "w") as f:
                    f.write("# Environment variables (API keys)\n.env\n")
                print("  ✓ Created .gitignore with .env entry")

    except Exception as e:
        print(f"\n⚠️  Could not update .gitignore: {e}")


def test_setup():
    """Test the setup"""
    print("\n" + "-" * 70)
    print("  Testing Setup...")
    print("-" * 70)

    try:
        # Try to load .env
        from dotenv import load_dotenv
        load_dotenv()

        openai_key = os.environ.get("OPENAI_API_KEY")
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")

        print(f"\n  OpenAI API Key: {'✓ Loaded' if openai_key else '✗ Not found'}")
        print(f"  Anthropic API Key: {'✓ Loaded' if anthropic_key else '✗ Not found'}")

        if openai_key or anthropic_key:
            print("\n  ✓ Setup successful! You can now use AI content generation.")
            print("\n  Quick test:")
            print("    python test_ai_content_generation.py --quick")
        else:
            print("\n  ⚠️  No API keys loaded. Will use template-based generation.")

    except ImportError:
        print("\n  ℹ️  python-dotenv not installed")
        print("    Install with: pip install python-dotenv")
    except Exception as e:
        print(f"\n  ⚠️  Test failed: {e}")


def main():
    """Main setup flow"""
    print_header()
    print_security_warning()

    # Check if overwriting existing .env
    if not check_existing_env():
        return

    # Get API keys
    print("\nℹ️  You need at least one API key (OpenAI OR Anthropic)")
    print("   Both providers work well, choose based on preference/cost")
    print()

    openai_key = get_api_key(
        "OpenAI",
        "https://platform.openai.com/api-keys"
    )

    anthropic_key = get_api_key(
        "Anthropic",
        "https://console.anthropic.com/"
    )

    # Create .env file
    if create_env_file(openai_key, anthropic_key):
        # Check gitignore
        check_gitignore()

        # Test setup
        test_setup()

        print("\n" + "=" * 70)
        print("  Setup complete! 🎉")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run: python test_ai_content_generation.py --quick")
        print("  2. Review: AI_CONTENT_GENERATOR_README.md")
        print("  3. Start generating content!")
        print()
    else:
        print("\n✗ Setup incomplete")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
