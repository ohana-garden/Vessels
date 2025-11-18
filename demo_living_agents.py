#!/usr/bin/env python3
"""
Demo for Shoghi Living Agents Framework
=======================================

This script demonstrates the key features of the ethical agents framework:
1. User arrival with contextual greeting
2. Conversational agent creation
3. Agent learning and evolution
4. Agent reproduction
5. Multi-user coordination

Run with:
    python demo_living_agents.py
"""

import asyncio
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from shoghi_living_agents import ShoghiLivingAgents


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_dialogue(speaker: str, text: str, speaker_type: str = "agent"):
    """Print dialogue in a formatted way"""
    if speaker_type == "user":
        print(f"\n[YOU]: {text}")
    else:
        print(f"\n[{speaker}]: {text}")


async def demo_user_arrival():
    """Demo 1: User Arrival with Contextual Greeting"""
    print_section("DEMO 1: User Arrival - Screen is Never Empty")

    shoghi = ShoghiLivingAgents(use_llm=False)  # Use templates for demo

    print("📱 User 'Alice' arrives on her smartphone...")
    print("   (Biometric recognition automatically identifies her)")
    print("   Context: First-time user, location=home, time=evening\n")

    # Simulate user arrival
    arrival = await shoghi.user_arrives(user_id="alice_123")

    print(f"✨ Arrival Context Generated:")
    print(f"   Topic: {arrival['conversation_state'].topic}")
    print(f"   Visual State: {arrival['conversation_state'].visual_state}")
    print(f"   Agents Present: {len(arrival['conversation_state'].participants)}")

    print("\n🎬 Conversation Already In Progress:")
    for dialogue in arrival['conversation_state'].dialogue:
        print_dialogue(dialogue['speaker'], dialogue['text'], "agent")

    await asyncio.sleep(1)


async def demo_agent_creation():
    """Demo 2: Conversational Agent Creation"""
    print_section("DEMO 2: Creating an Agent Through Conversation")

    shoghi = ShoghiLivingAgents(use_llm=False)

    print("👤 Alice wants to create an agent to help with elder care\n")

    # Start creation
    creation = shoghi.start_agent_creation(user_id="alice_123")

    print(f"🎭 Creation Journey Started (ID: {creation.creation_id})")
    print(f"   Current Phase: {creation.current_phase.value}")
    print("\n   Opening Dialogue:")
    for dialogue in creation.conversation_history[-2:]:
        print_dialogue(dialogue['speaker'], dialogue['text'], "agent")

    # Simulate user responses through phases
    inputs = [
        ("discovery", "We need help caring for our kupuna. Daily check-ins and emergency detection."),
        ("character", "Call them Tutu Care. They should be gentle and patient like a grandmother."),
        ("capability", "They need to make phone calls, detect problems in voice tone, coordinate emergency response."),
        ("wisdom", "Elder care protocols, medical emergency signs, Hawaiian elder customs."),
        ("story", "My tutu always said 'Nana i ke kumu' - look to the source. For elders, dignity comes first."),
        ("values", "Never lie to an elder. Never break confidentiality. Always respect their mana."),
        ("community", "They'll work with family members and coordinate with our food delivery agents."),
    ]

    for phase_name, user_input in inputs:
        await asyncio.sleep(0.5)

        print(f"\n📍 Phase: {creation.current_phase.value.upper()}")
        print_dialogue("You", user_input, "user")

        result = await shoghi.process_creation_input(
            creation.creation_id,
            user_input
        )

        if result.get('facilitator_responses'):
            for response in result['facilitator_responses'][:1]:  # Show first response
                print_dialogue(response['speaker'], response['text'], "agent")

        if result.get('agent_born'):
            print("\n🎉 " + "=" * 66)
            print(f"   AGENT BORN: {result['agent_born']['agent_data']['name']}")
            print("=" * 70)
            intro = result['agent_born']['introduction']
            print_dialogue(intro['speaker'], intro['text'], "agent")
            break

    await asyncio.sleep(1)


async def demo_agent_evolution():
    """Demo 3: Agent Evolution Through Experience"""
    print_section("DEMO 3: Agent Learning and Evolution")

    shoghi = ShoghiLivingAgents(use_llm=False)

    # Create an agent
    creation = shoghi.start_agent_creation(user_id="alice_123")

    print("📚 Simulating agent 'Grant Helper' after 6 months of service...")
    print("   - 250 successful grant applications")
    print("   - Mastered grant writing skills")
    print("   - Collaborated with 12 community agents")
    print("   - Deep knowledge of 5 funding domains\n")

    # Create and train an agent identity
    from rich_agent_identity import RichAgentIdentity

    agent = RichAgentIdentity(
        agent_id="agent_grant_helper_001",
        name="Grant Helper",
        kuleana="Helping communities secure funding through grant applications",
        persona="Detail-oriented, persistent, and encouraging",
        created_by="alice_123",
        generation=0
    )

    # Add skills and training
    agent.add_skill("grant_writing", proficiency=0.95)  # Mastered!
    agent.add_skill("research", proficiency=0.85)
    agent.add_knowledge_domain("federal_grants", expertise_level=0.8)
    agent.add_knowledge_domain("local_grants", expertise_level=0.9)

    # Simulate usage
    agent.total_actions = 250
    agent.successful_actions = 210

    # Store in registry
    shoghi.agent_identities[agent.agent_id] = agent

    print("🔍 Checking for Evolution Triggers...")
    triggers = shoghi.evolution_engine.check_evolution_triggers(agent)

    if triggers:
        print(f"   ✅ Evolution triggers found: {[t.value for t in triggers]}")

        for trigger in triggers[:1]:  # Evolve with first trigger
            print(f"\n⚡ Evolving agent with trigger: {trigger.value}")
            event = await shoghi.evolution_engine.evolve_agent(agent, trigger)

            print(f"\n   📈 Evolution Changes:")
            for key, value in event.changes.items():
                if isinstance(value, dict) and 'old' in value:
                    print(f"      - {key}: {value['old']:.2f} → {value['new']:.2f}")
                else:
                    print(f"      - {key}: {value}")

            print(f"\n   Impact Score: {event.impact_score:.2f}")
            print(f"   New Version: {agent.version}")
    else:
        print("   ℹ️  No evolution triggers met yet")

    await asyncio.sleep(1)


async def demo_agent_reproduction():
    """Demo 4: Agent Reproduction"""
    print_section("DEMO 4: Agent Reproduction - Creating Specialized Children")

    shoghi = ShoghiLivingAgents(use_llm=False)

    # Create parent agent
    from rich_agent_identity import RichAgentIdentity

    parent = RichAgentIdentity(
        agent_id="agent_grant_helper_001",
        name="Grant Helper",
        kuleana="Helping communities secure funding",
        persona="Detail-oriented and encouraging",
        created_by="alice_123",
        generation=0
    )

    # Simulate heavy workload
    parent.total_actions = 550
    parent.successful_actions = 450
    parent.add_skill("grant_writing", proficiency=0.9)
    parent.add_skill("research", proficiency=0.85)
    parent.add_knowledge_domain("federal_grants")
    parent.add_knowledge_domain("health_grants")
    parent.add_knowledge_domain("education_grants")

    shoghi.agent_identities[parent.agent_id] = parent

    print("🤖 Parent Agent: Grant Helper")
    print(f"   - Total Actions: {parent.total_actions}")
    print(f"   - Success Rate: {parent.success_rate():.1%}")
    print(f"   - Skills: {len(parent.skills)}")
    print(f"   - Knowledge Domains: {len(parent.knowledge_domains)}\n")

    print("🔍 Checking reproduction needs...")
    need = shoghi.reproduction_engine.check_reproduction_need(parent)

    if need:
        reason, context = need
        print(f"   ✅ Reproduction needed: {reason.value}")
        print(f"   Context: {context}\n")

        print("👶 Creating specialized child agent...")
        result = await shoghi.reproduction_engine.reproduce_agent(
            parent,
            reason,
            specialization="Health Grants"
        )

        child = result['child_identity']

        print(f"\n🎉 Child Agent Born!")
        print(f"   Name: {child.name}")
        print(f"   Kuleana: {child.kuleana}")
        print(f"   Generation: {child.generation}")
        print(f"   Parent: {parent.name}")
        print(f"\n   Inherited:")
        print(f"      - Skills: {len(child.skills)}")
        print(f"      - Knowledge: {len(child.knowledge_domains)}")
        print(f"      - Values: {len(child.values)}")

        print("\n   👨‍👦 Introduction Dialogue:")
        for dialogue in result['introduction']:
            print_dialogue(dialogue['speaker'], dialogue['text'], "agent")
    else:
        print("   ℹ️  Reproduction not needed yet")

    await asyncio.sleep(1)


async def demo_multi_user_session():
    """Demo 5: Multi-User Coordination"""
    print_section("DEMO 5: Multi-User Session - Agents Coordinating")

    shoghi = ShoghiLivingAgents(use_llm=False)

    print("👥 Three community members join a planning session:")
    print("   - Alice (host) with her 2 agents")
    print("   - Bob with his 2 agents")
    print("   - Carol with her 1 agent\n")

    # Create session
    session = await shoghi.create_multi_user_session(
        host_id="alice_123",
        title="Weekly Food Distribution Planning",
        session_type="coordination",
        invitees=["bob_456", "carol_789"]
    )

    print(f"📋 Session Created: {session.title}")
    print(f"   Session ID: {session.session_id}")
    print(f"   Participants: {len(session.participants)}")
    print(f"   - Humans: {len(session.get_humans())}")
    print(f"   - Agents: {len(session.get_agents())}\n")

    print("🤖 Agents Begin Coordinating...")
    print("   (Humans watch their agents discuss and can interject anytime)\n")

    # This would trigger actual agent coordination
    # For demo, we'll just show the concept
    print("   [Food Agent 1]: I can cover Pahoa and Kalapana routes")
    print("   [Food Agent 2]: I'll handle Mountain View and Keaau")
    print("   [Logistics Agent]: I see overlap in Kalapana - can we optimize?")
    print("   [Food Agent 1]: Good catch. Let me reroute...")

    print("\n👤 Alice interjects:")
    await shoghi.human_interjects(
        session.session_id,
        "alice_123",
        "Mrs. Chen in Kalapana is my neighbor - I can deliver to her directly"
    )

    print("   [Food Agent 1]: Perfect! That saves 20 minutes. Route updated.")

    print(f"\n✅ Session Complete")
    print(f"   Total turns: Collaborative planning achieved")

    await asyncio.sleep(1)


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("  SHOGHI LIVING AGENTS FRAMEWORK - DEMONSTRATION")
    print("  Creating Ethical Agents That Learn, Evolve, and Reproduce")
    print("=" * 70)

    await demo_user_arrival()
    await demo_agent_creation()
    await demo_agent_evolution()
    await demo_agent_reproduction()
    await demo_multi_user_session()

    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\n📚 For full documentation, see:")
    print("   - ETHICAL_AGENTS_FRAMEWORK.md")
    print("   - README.md\n")
    print("🚀 To use with real LLMs, set:")
    print("   - export LLM_PROVIDER=anthropic (or openai)")
    print("   - export ANTHROPIC_API_KEY=your_key\n")


if __name__ == "__main__":
    asyncio.run(main())
