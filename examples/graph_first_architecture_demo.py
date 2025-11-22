#!/usr/bin/env python3
"""
Graph-First Architecture Demo

Demonstrates the refactored Agent Zero architecture:
1. Creating durable ServantProjects (not ephemeral agents)
2. Graph-based Run tracking
3. Policy-driven tool execution
4. State persistence across restarts
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dynamic_agent_factory import agent_factory
from vessels.projects.manager import ProjectManager
from vessels.projects.tool_integration import ProjectToolGateway
from vessels.knowledge.schema import ServantType
from agent_zero_core import agent_zero
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_1_create_durable_servants():
    """Demo 1: Create servants as durable projects (not RAM-based agents)"""
    print("\n" + "=" * 80)
    print("DEMO 1: Creating Durable Servant Projects")
    print("=" * 80)

    # Process a natural language request
    request = "I need help finding grants for elder care in Puna"
    print(f"\nUser Request: {request}")

    # This now creates ServantProjects (persistent) instead of AgentInstances (ephemeral)
    result = agent_factory.process_request(request)

    print(f"\nDeployed Servants:")
    for servant in result["deployed_agents"]:
        if servant.get("status") == "deployed":
            print(f"  - {servant['name']} (Project ID: {servant['project_id'][:16]}...)")
            print(f"    Work Dir: {servant['work_dir']}")
            print(f"    Tools: {', '.join(servant['tools'][:3])}...")

    return result["deployed_agents"]


def demo_2_verify_persistence():
    """Demo 2: Verify that projects are persisted to disk"""
    print("\n" + "=" * 80)
    print("DEMO 2: Verifying Project Persistence")
    print("=" * 80)

    project_manager = ProjectManager()
    project_manager.load_all_projects()

    projects = project_manager.list_projects(community_id="puna")

    print(f"\nFound {len(projects)} persistent projects:")
    for project in projects:
        print(f"  - {project.id}")
        print(f"    Type: {project.servant_type.value}")
        print(f"    Status: {project.status.value}")
        print(f"    Config: {project.get_config_file()}")

    return projects


def demo_3_policy_driven_tools():
    """Demo 3: Execute tools with policy enforcement"""
    print("\n" + "=" * 80)
    print("DEMO 3: Policy-Driven Tool Execution")
    print("=" * 80)

    # Get a project
    project_manager = ProjectManager()
    project_manager.load_all_projects()
    projects = project_manager.list_projects(community_id="puna")

    if not projects:
        print("No projects found. Run demo_1 first.")
        return

    project = projects[0]
    print(f"\nUsing project: {project.id}")
    print(f"Servant type: {project.servant_type.value}")

    # Create tool gateway (enforces project policies)
    gateway = ProjectToolGateway(project)

    print(f"\nAllowed tools for {project.servant_type.value}:")
    for tool in gateway.get_allowed_tools():
        print(f"  - {tool}")

    # Try to execute an allowed tool
    print("\n--- Executing allowed tool 'search_web' ---")
    result = gateway.execute_tool(
        "search_web",
        {"query": "elder care grants Hawaii"}
    )
    print(f"Result: {result.get('success')} (Details: {result})")

    # Try to execute a disallowed tool
    print("\n--- Attempting disallowed tool 'nuclear_launch' ---")
    result = gateway.execute_tool(
        "nuclear_launch",
        {"target": "moon"}
    )
    print(f"Result: {result.get('success')} (Reason: {result.get('error')})")


def demo_4_graph_run_tracking():
    """Demo 4: Query Run nodes from Graphiti"""
    print("\n" + "=" * 80)
    print("DEMO 4: Graph-Based Run Tracking")
    print("=" * 80)

    project_manager = ProjectManager()
    project_manager.load_all_projects()
    projects = project_manager.list_projects(community_id="puna")

    if not projects:
        print("No projects found. Run demo_1 first.")
        return

    project = projects[0]
    print(f"\nQuerying Run nodes for project: {project.id}")

    try:
        # Query Run nodes from Graphiti
        runs = project.graphiti.query_nodes(node_type="Run")
        print(f"Found {len(runs)} Run nodes")

        for i, run in enumerate(runs[:5]):  # Show first 5
            print(f"\nRun {i+1}:")
            print(f"  Action: {run.get('action')}")
            print(f"  Timestamp: {run.get('timestamp')}")
            print(f"  Status: {run.get('status', 'N/A')}")

    except Exception as e:
        print(f"Error querying Run nodes: {e}")
        print("(This is expected if Graphiti is in mock mode)")


def demo_5_servant_status():
    """Demo 5: Check status of registered servants"""
    print("\n" + "=" * 80)
    print("DEMO 5: Registered Servant Status")
    print("=" * 80)

    # Get deployment status
    status = agent_factory.get_deployment_status()

    print(f"\nTotal Servants: {status['total_servants']}")

    if status["servants"]:
        print("\nServant Details:")
        for servant in status["servants"]:
            print(f"  - Project ID: {servant['project_id'][:32]}...")
            print(f"    Type: {servant['servant_type']}")
            print(f"    Status: {servant['status']}")
            print(f"    Registration: {servant['registration_status']}")
    else:
        print("No servants registered yet.")

    # Show legacy agent status (if any)
    if status["legacy_agents"]["total_agents"] > 0:
        print(f"\nLegacy Agents (RAM-based): {status['legacy_agents']['total_agents']}")
    else:
        print("\nNo legacy agents (all migrated to graph-first!)")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("GRAPH-FIRST ARCHITECTURE DEMONSTRATION")
    print("Vessels Agent Zero - Post-Refactor")
    print("=" * 80)

    # Initialize Agent Zero Core
    agent_zero.initialize()

    try:
        # Run demos
        demo_1_create_durable_servants()
        demo_2_verify_persistence()
        demo_3_policy_driven_tools()
        demo_4_graph_run_tracking()
        demo_5_servant_status()

        print("\n" + "=" * 80)
        print("✅ All demos completed successfully!")
        print("=" * 80)

    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)

    finally:
        # Cleanup
        agent_zero.shutdown()


if __name__ == "__main__":
    main()
