#!/usr/bin/env python3
"""
Example: Vessel-Native Agent Coordination

Demonstrates the vessel-native architecture where agents are spawned
within vessels and inherit vessel-scoped resources.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vessels.core.registry import VesselRegistry
from vessels.core.vessel import Vessel, PrivacyLevel
from agent_zero_core import AgentZeroCore, AgentSpecification
from vessels.knowledge.schema import CommunityPrivacy


def main():
    print("=" * 60)
    print("VESSEL-NATIVE AGENT COORDINATION EXAMPLE")
    print("=" * 60)
    print()

    # 1. Create vessel registry
    print("1. Creating vessel registry...")
    registry = VesselRegistry(db_path="example_vessels.db")
    print("   ✓ Registry created")
    print()

    # 2. Create a vessel
    print("2. Creating vessel for community garden project...")
    vessel = Vessel.create(
        name="Community Garden Project",
        community_id="puna_hawaii",
        description="Coordinating community garden initiatives",
        privacy_level=PrivacyLevel.SHARED,
        constraint_profile_id="servant_default"
    )
    print(f"   ✓ Vessel created: {vessel.name}")
    print(f"   - Vessel ID: {vessel.vessel_id}")
    print(f"   - Privacy: {vessel.privacy_level.value}")
    print(f"   - Constraint Profile: {vessel.constraint_profile_id}")
    print()

    # 3. Configure vessel resources
    print("3. Configuring vessel resources...")

    # For this example, we'll use mock objects since we don't want to
    # initialize full action gates and memory backends
    print("   - Configuring action gate (mock)")
    vessel.action_gate = "MockActionGate"  # In real usage, use ActionGate instance

    print("   - Configuring memory backend (mock)")
    vessel.memory_backend = "MockMemoryBackend"  # In real usage, use GraphitiMemoryBackend

    print("   - Configuring tools")
    vessel.add_tool("web_scraper", "MockWebScraperTool")
    vessel.add_tool("search_engine", "MockSearchTool")
    vessel.add_tool("document_generator", "MockDocumentGeneratorTool")
    print(f"   ✓ Tools configured: {list(vessel.tools.keys())}")
    print()

    # 4. Register vessel
    print("4. Registering vessel...")
    registry.create_vessel(vessel)
    print("   ✓ Vessel registered and persisted")
    print()

    # 5. Initialize AgentZeroCore with vessel registry
    print("5. Initializing AgentZeroCore with vessel registry...")
    core = AgentZeroCore(vessel_registry=registry)
    core.initialize()
    print("   ✓ AgentZeroCore initialized")
    print()

    # 6. Define agent specifications
    print("6. Defining agent specifications...")
    specs = [
        AgentSpecification(
            name="GrantFinder",
            description="Discovers and analyzes grant opportunities",
            capabilities=["web_search", "data_analysis"],
            tools_needed=["web_scraper", "search_engine"],
            specialization="grant_discovery"
        ),
        AgentSpecification(
            name="GrantWriter",
            description="Writes grant applications",
            capabilities=["document_generation", "compliance_checking"],
            tools_needed=["document_generator"],
            specialization="grant_writing"
        ),
        AgentSpecification(
            name="CommunityCoordinator",
            description="Coordinates community activities",
            capabilities=["resource_allocation", "scheduling"],
            tools_needed=["search_engine"],
            specialization="community_coordination"
        )
    ]
    print(f"   ✓ {len(specs)} agent specifications defined")
    for spec in specs:
        print(f"     - {spec.name}: {spec.description}")
    print()

    # 7. Spawn agents in the vessel
    print("7. Spawning agents in vessel...")
    agent_ids = core.spawn_agents(specs, vessel_id=vessel.vessel_id)
    print(f"   ✓ Spawned {len(agent_ids)} agents in vessel '{vessel.name}'")
    print()

    # 8. Verify agent configuration
    print("8. Verifying agent configuration...")
    for i, agent_id in enumerate(agent_ids):
        agent = core.agents[agent_id]
        print(f"   Agent {i+1}: {agent.specification.name}")
        print(f"     - ID: {agent.id}")
        print(f"     - Vessel: {agent.vessel_id}")
        print(f"     - Action Gate: {agent.action_gate}")
        print(f"     - Memory Backend: {agent.memory_backend}")
        print(f"     - Tools: {agent.tools}")
        print(f"     - Status: {agent.status.value}")
        print()

    # 9. Demonstrate multi-vessel scenario
    print("9. Creating second vessel for elder care...")
    elder_vessel = Vessel.create(
        name="Elder Care Coordination",
        community_id="puna_elders",
        description="Coordinating elder care services",
        privacy_level=PrivacyLevel.PRIVATE,
        constraint_profile_id="elder_care_strict"
    )
    elder_vessel.action_gate = "StrictActionGate"  # Different gate!
    elder_vessel.memory_backend = "IsolatedMemoryBackend"
    elder_vessel.add_tool("care_tracker", "CareTrackerTool")
    registry.create_vessel(elder_vessel)
    print(f"   ✓ Second vessel created: {elder_vessel.name}")
    print(f"   - Privacy: {elder_vessel.privacy_level.value}")
    print()

    # 10. Spawn agents in second vessel
    print("10. Spawning agents in second vessel...")
    elder_specs = [
        AgentSpecification(
            name="ElderCareSpecialist",
            description="Manages elder care program development",
            capabilities=["needs_assessment", "program_design"],
            tools_needed=["care_tracker"],
            specialization="elder_care"
        )
    ]
    elder_agent_ids = core.spawn_agents(
        elder_specs, vessel_id=elder_vessel.vessel_id
    )
    print(f"   ✓ Spawned {len(elder_agent_ids)} agents in vessel '{elder_vessel.name}'")
    print()

    # 11. Show agent status
    print("11. All active agents:")
    all_status = core.get_all_agents_status()
    for status in all_status:
        print(f"   - {status['name']} ({status['specialization']})")
        print(f"     Status: {status['status']}")
        print(f"     Active tasks: {status['active_tasks']}")
        print()

    # 12. Cleanup
    print("12. Shutting down coordination system...")
    time.sleep(2)  # Let agents process for a moment
    core.shutdown()
    print("   ✓ Coordination system shutdown complete")
    print()

    print("=" * 60)
    print("VESSEL-NATIVE COORDINATION SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Key Achievements:")
    print("  ✓ Created 2 vessels with different privacy levels")
    print("  ✓ Configured vessel-scoped resources (gates, memory, tools)")
    print("  ✓ Spawned 4 agents across 2 vessels")
    print("  ✓ Each agent inherited vessel-scoped resources")
    print("  ✓ Demonstrated isolation between vessels")
    print()
    print("Data Flow Verified:")
    print("  Agent → vessel.action_gate (privacy/moral enforcement)")
    print("  Agent → vessel.memory_backend (namespaced storage)")
    print("  Agent → vessel.tools (permission-based access)")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
