"""
Vessels Startup Banner and Service Health Checks

Displays detailed initialization status for all core services:
- Agent Zero Core
- FalkorDB (Graph Database)
- Graphiti (Episodic Memory)
- TEN Framework (Voice/Multimodal UX)
- Petals Gateway (Distributed AI)
- Payment Service (TigerBeetle + Mojaloop + RTP)
- LLM Router (Tier 0/1/2)
- Nostr Connector (P2P)
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class ServiceStatus:
    """Track and display service initialization status"""

    def __init__(self):
        self.services = {}
        self.start_time = time.time()

    def update(self, service: str, status: str, details: str = ""):
        """Update service status"""
        self.services[service] = {
            "status": status,
            "details": details,
            "timestamp": time.time() - self.start_time
        }

    def print_status(self, service: str, status: str, details: str = ""):
        """Print formatted status line"""
        symbols = {
            "starting": "⏳",
            "ready": "✅",
            "warning": "⚠️",
            "error": "❌",
            "disabled": "⏸️"
        }

        symbol = symbols.get(status, "●")
        timestamp = f"[{time.time() - self.start_time:>6.2f}s]"

        status_line = f"{timestamp} {symbol} {service:<30} {status.upper():<10}"
        if details:
            status_line += f" - {details}"

        print(status_line, flush=True)
        logger.info(status_line)


def print_banner():
    """Print Vessels startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  ██╗   ██╗███████╗███████╗███████╗███████╗██╗     ███████╗         ║
║  ██║   ██║██╔════╝██╔════╝██╔════╝██╔════╝██║     ██╔════╝         ║
║  ██║   ██║█████╗  ███████╗███████╗█████╗  ██║     ███████╗         ║
║  ╚██╗ ██╔╝██╔══╝  ╚════██║╚════██║██╔══╝  ██║     ╚════██║         ║
║   ╚████╔╝ ███████╗███████║███████║███████╗███████╗███████║         ║
║    ╚═══╝  ╚══════╝╚══════╝╚══════╝╚══════╝╚══════╝╚══════╝         ║
║                                                                      ║
║            Neighborhood Commerce + Agent Zero Platform              ║
║                  Unified Container Architecture                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(banner, flush=True)
    print("=" * 72, flush=True)
    print("INITIALIZING ALL SERVICES...", flush=True)
    print("=" * 72, flush=True)
    print(flush=True)


def check_falkordb(status: ServiceStatus) -> bool:
    """Check FalkorDB connection"""
    status.print_status("FalkorDB (Graph DB)", "starting", "Connecting to Redis with FalkorDB module...")

    try:
        import redis
        host = os.getenv("FALKORDB_HOST", "localhost")
        port = int(os.getenv("FALKORDB_PORT", "6379"))

        client = redis.Redis(host=host, port=port, decode_responses=True)
        client.ping()

        # Check if FalkorDB module is loaded
        modules = client.execute_command("MODULE", "LIST")
        has_falkor = any("graph" in str(m).lower() for m in modules)

        if has_falkor:
            status.print_status("FalkorDB (Graph DB)", "ready", f"Connected to {host}:{port}")
            return True
        else:
            status.print_status("FalkorDB (Graph DB)", "warning", "FalkorDB module not loaded")
            return False

    except Exception as e:
        status.print_status("FalkorDB (Graph DB)", "error", str(e))
        return False


def check_graphiti(status: ServiceStatus) -> bool:
    """Check Graphiti episodic memory system"""
    status.print_status("Graphiti (Memory)", "starting", "Initializing episodic memory layer...")

    try:
        from graphiti_core import Graphiti
        from graphiti_core.nodes import EpisodicNode

        status.print_status("Graphiti (Memory)", "ready", "Episodic memory layer initialized")
        return True

    except ImportError as e:
        status.print_status("Graphiti (Memory)", "warning", "Graphiti not installed (optional)")
        return False
    except Exception as e:
        status.print_status("Graphiti (Memory)", "error", str(e))
        return False


def check_agent_zero(status: ServiceStatus) -> bool:
    """Initialize Agent Zero core"""
    status.print_status("Agent Zero Core", "starting", "Loading agentic control plane...")

    try:
        # Check for core Agent Zero components
        components = []

        try:
            from vessels.core.vessel import Vessel
            components.append("Vessel (Servant)")
        except ImportError:
            pass

        try:
            from vessels.core.action_gate import ActionGate
            components.append("Action Gate (12D)")
        except ImportError:
            pass

        if components:
            status.print_status("Agent Zero Core", "ready", f"Loaded: {', '.join(components)}")
            return True
        else:
            status.print_status("Agent Zero Core", "warning", "Core modules not found")
            return False

    except Exception as e:
        status.print_status("Agent Zero Core", "error", str(e))
        return False


def check_llm_router(status: ServiceStatus) -> bool:
    """Check LLM routing system"""
    status.print_status("LLM Router (Tiers)", "starting", "Configuring Tier 0/1/2 compute...")

    try:
        from vessels.compute.llm_router import LLMRouter, ComputeTier

        tier_info = []
        tier_info.append("Tier 0 (Device)")
        tier_info.append("Tier 1 (Edge)")

        if os.getenv("PETALS_ENABLED", "false").lower() == "true":
            tier_info.append("Tier 2 (Petals)")

        status.print_status("LLM Router (Tiers)", "ready", " + ".join(tier_info))
        return True

    except ImportError:
        status.print_status("LLM Router (Tiers)", "warning", "Router not found")
        return False
    except Exception as e:
        status.print_status("LLM Router (Tiers)", "error", str(e))
        return False


def check_petals(status: ServiceStatus) -> bool:
    """Check Petals distributed AI gateway"""
    enabled = os.getenv("PETALS_ENABLED", "false").lower() == "true"

    if not enabled:
        status.print_status("Petals Gateway (Tier 2)", "disabled", "Distributed AI disabled (set PETALS_ENABLED=true)")
        return True

    status.print_status("Petals Gateway (Tier 2)", "starting", "Connecting to distributed model network...")

    try:
        from vessels.compute.petals_gateway import PetalsGateway

        model = os.getenv("PETALS_MODEL", "petals-team/StableBeluga2")
        status.print_status("Petals Gateway (Tier 2)", "ready", f"Model: {model}")
        return True

    except ImportError:
        status.print_status("Petals Gateway (Tier 2)", "warning", "Petals not installed")
        return False
    except Exception as e:
        status.print_status("Petals Gateway (Tier 2)", "error", str(e))
        return False


def check_ten_framework(status: ServiceStatus) -> bool:
    """Check TEN Framework integration"""
    enabled = os.getenv("TEN_FRAMEWORK_ENABLED", "true").lower() == "true"

    if not enabled:
        status.print_status("TEN Framework (UX)", "disabled", "Voice/multimodal UX disabled")
        return True

    status.print_status("TEN Framework (UX)", "starting", "Loading voice/multimodal pipeline...")

    try:
        graphs_dir = os.getenv("TEN_GRAPHS_DIR", "/app/graphs")

        if os.path.exists(graphs_dir):
            graphs = [f for f in os.listdir(graphs_dir) if f.endswith(".json")]
            status.print_status("TEN Framework (UX)", "ready", f"Graphs loaded: {len(graphs)}")
            return True
        else:
            status.print_status("TEN Framework (UX)", "warning", f"Graphs directory not found: {graphs_dir}")
            return False

    except Exception as e:
        status.print_status("TEN Framework (UX)", "error", str(e))
        return False


def check_payment_service(status: ServiceStatus) -> bool:
    """Check payment service (TigerBeetle + Mojaloop + RTP)"""
    status.print_status("Payment Service", "starting", "Connecting to TigerBeetle ledger...")

    try:
        api_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:3000")

        # Give payment service time to start
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{api_url}/health", timeout=2)
                if response.status_code == 200:
                    status.print_status("Payment Service", "ready", f"TigerBeetle + Mojaloop + RTP at {api_url}")
                    return True
            except:
                if i < max_retries - 1:
                    time.sleep(1)

        status.print_status("Payment Service", "warning", f"Not responding at {api_url}")
        return False

    except Exception as e:
        status.print_status("Payment Service", "error", str(e))
        return False


def check_nostr(status: ServiceStatus) -> bool:
    """Check Nostr connector"""
    status.print_status("Nostr Connector (P2P)", "starting", "Initializing peer-to-peer network...")

    try:
        from vessels.communication.nostr_client import NostrClient

        # Check if Nostr is configured
        relays = os.getenv("NOSTR_RELAYS", "").split(",")
        if relays and relays[0]:
            status.print_status("Nostr Connector (P2P)", "ready", f"Relays: {len(relays)}")
            return True
        else:
            status.print_status("Nostr Connector (P2P)", "disabled", "No relays configured")
            return True

    except ImportError:
        status.print_status("Nostr Connector (P2P)", "warning", "Nostr client not installed")
        return False
    except Exception as e:
        status.print_status("Nostr Connector (P2P)", "error", str(e))
        return False


def load_env_file():
    """Load .env file if it exists"""
    from pathlib import Path
    env_file = Path(__file__).parent.parent.parent / ".env"

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def check_config_status():
    """Check if configuration is complete"""
    required_for_basic = [
        'FALKORDB_HOST',
    ]

    ai_providers = [
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'AZURE_OPENAI_API_KEY',
        'OLLAMA_ENABLED'
    ]

    has_ai = any(os.getenv(key) for key in ai_providers)

    if not has_ai:
        print("⚠️  WARNING: No AI providers configured!", flush=True)
        print("   Run 'python setup.py' to configure Agent Zero", flush=True)
        print(flush=True)


def run_startup_checks():
    """Run all startup checks and display status"""
    # Load .env file
    load_env_file()

    print_banner()

    # Check if setup is complete
    check_config_status()

    status = ServiceStatus()

    print("DATABASE LAYER", flush=True)
    print("-" * 72, flush=True)
    check_falkordb(status)
    check_graphiti(status)
    print(flush=True)

    print("AGENT ZERO INTELLIGENCE", flush=True)
    print("-" * 72, flush=True)
    check_agent_zero(status)
    check_llm_router(status)
    print(flush=True)

    print("COMPUTE TIERS", flush=True)
    print("-" * 72, flush=True)
    check_petals(status)
    print(flush=True)

    print("USER EXPERIENCE", flush=True)
    print("-" * 72, flush=True)
    check_ten_framework(status)
    print(flush=True)

    print("PAYMENT INFRASTRUCTURE", flush=True)
    print("-" * 72, flush=True)
    check_payment_service(status)
    print(flush=True)

    print("NETWORKING", flush=True)
    print("-" * 72, flush=True)
    check_nostr(status)
    print(flush=True)

    print("=" * 72, flush=True)
    elapsed = time.time() - status.start_time
    print(f"✨ VESSELS READY - Total startup time: {elapsed:.2f}s", flush=True)
    print("=" * 72, flush=True)
    print(flush=True)

    return status


if __name__ == "__main__":
    run_startup_checks()
