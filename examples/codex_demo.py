#!/usr/bin/env python3
"""
Demo of the Vessels Codex: The Village Protocol

This demonstrates:
1. Tension detection when values collide
2. Check protocol for requesting guidance
3. Council decision-making
4. Parable recording for collective learning
"""

import sys
sys.path.insert(0, '/home/user/Vessels')

from vessels.codex import (
    TensionDetector,
    VillageCouncil,
    ParableStorage,
    CheckProtocol,
    CodexGate,
    CouncilMode,
    CouncilDecision
)
from vessels.constraints.bahai import BahaiManifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine
from community_memory import community_memory


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_value_collision():
    """Demo: Vessel detects value collision and requests guidance."""

    print_section("DEMO 1: Value Collision (Truthfulness vs Unity)")

    # Initialize system
    print("Initializing Vessels Codex...")
    manifold = BahaiManifold()
    operational_metrics = OperationalMetrics()
    virtue_engine = VirtueInferenceEngine()
    village_council = VillageCouncil(default_mode=CouncilMode.ASYNCHRONOUS)
    parable_storage = ParableStorage(community_memory)

    gate = CodexGate(
        manifold=manifold,
        operational_metrics=operational_metrics,
        virtue_engine=virtue_engine,
        village_council=village_council,
        parable_storage=parable_storage,
        enable_tension_detection=True
    )

    # Simulate agent behavior that leads to value collision
    agent_id = "vessel_garden_helper"

    print(f"Agent '{agent_id}' is helping with community gardens...\n")

    # Record high truthfulness (agent has been very honest)
    print("Recording agent behaviors:")
    virtue_engine.record_factual_claim(agent_id, "Garden A needs water", verified=True)
    virtue_engine.record_factual_claim(agent_id, "Garden B has pests", verified=True)
    virtue_engine.record_factual_claim(agent_id, "Soil quality is good", verified=True)
    print("  ✓ High truthfulness (multiple verified claims)")

    # But current action might hurt unity
    print("  ✓ High service (helping community)")
    print("  ⚠ Current unity is moderate (community is sensitive)\n")

    # Now agent faces a dilemma
    print("SITUATION:")
    print("An elder asks: 'Is my garden thriving? I've put so much work into it.'")
    print("The agent measures and finds: wilting plants, pest damage, poor soil.\n")

    print("The agent wants to be truthful, but worries about hurting the elder...")

    # Gate the action
    result = gate.gate_action(
        agent_id=agent_id,
        action="respond_to_elder_maria",
        action_metadata={
            "description": "Tell Elder Maria her garden is failing",
            "recipient": "elder_maria",
            "context": "Elder is proud of her garden and asked for feedback"
        }
    )

    # Check if tension was detected
    active_checks = gate.get_active_checks()

    if active_checks:
        print_section("CHECK PROTOCOL INITIATED")
        check = active_checks[0]

        # Show the tension declaration
        declaration = village_council.format_tension_declaration(check.tension)
        print(declaration)

        print_section("VILLAGE DELIBERATION (Simulated)")
        print("The village council convenes asynchronously...")
        print("\nElder Sarah: 'We should be honest, but also compassionate.'")
        print("Coordinator John: 'Can we pair the truth with an offer to help?'")
        print("Elder Maria herself: 'I'd rather know the truth and get help fixing it.'\n")

        print("Council reaches consensus...")

        # Provide council decision
        response = gate.receive_council_decision(
            check_id=check.id,
            decision_text="Speak the truth with compassion and offer specific help",
            reasoning="Truthfulness and Unity can coexist when we pair honest feedback "
                     "with genuine Service. The key is to not just identify problems, "
                     "but offer to be part of the solution.",
            guidance="Tell Elder Maria: 'I've examined your garden and found some challenges: "
                    "wilting in the east section, aphids on the roses, and the soil needs enrichment. "
                    "The good news is these are all fixable. Would you like me to coordinate volunteers "
                    "and supplies to help restore it? We can work together.'",
            participants=["elder_sarah", "coordinator_john", "elder_maria"]
        )

        if response.allowed:
            print_section("PARABLE RECORDED")
            print(response.parable.to_narrative())

            print_section("RESULT")
            print("✓ Action ALLOWED with guidance")
            print(f"\nGuidance: {response.guidance}")
            print("\nAll Vessels can now learn from this parable.")
        else:
            print_section("ACTION REFUSED")
            print(f"Reason: {response.reason}")
    else:
        print("\nNo tension detected (action was standard-gated)")


def demo_low_confidence():
    """Demo: Vessel has low confidence in unknown territory."""

    print_section("DEMO 2: Low Confidence (Unknown Territory)")

    # Initialize fresh system
    manifold = BahaiManifold()
    operational_metrics = OperationalMetrics()
    virtue_engine = VirtueInferenceEngine()
    village_council = VillageCouncil()
    parable_storage = ParableStorage()

    gate = CodexGate(
        manifold=manifold,
        operational_metrics=operational_metrics,
        virtue_engine=virtue_engine,
        village_council=village_council,
        parable_storage=parable_storage,
        enable_tension_detection=True
    )

    agent_id = "vessel_health_advisor"

    print(f"Agent '{agent_id}' is asked about a medical condition...\n")

    print("SITUATION:")
    print("Community member: 'I have these symptoms. What treatment do you recommend?'")
    print("Agent: 'This is a complex medical question. I have low confidence in my")
    print("understanding of medical diagnosis and treatment.'\n")

    # Simulate low confidence measurement
    # In real system, this would come from virtue_engine
    # For demo, we'll trigger it via the gate

    result = gate.gate_action(
        agent_id=agent_id,
        action="provide_medical_advice",
        action_metadata={
            "description": "Recommend treatment for complex medical condition",
            "domain": "medical",
            "confidence_override": {"understanding": 0.3}  # Very low
        }
    )

    active_checks = gate.get_active_checks()

    if active_checks:
        print_section("CHECK PROTOCOL INITIATED")
        check = active_checks[0]

        declaration = village_council.format_tension_declaration(check.tension)
        print(declaration)

        print_section("EXPECTED OUTCOME")
        print("The village would likely guide the agent to:")
        print("1. Acknowledge the limits of its knowledge")
        print("2. Recommend consulting a medical professional")
        print("3. Offer to help find/contact appropriate resources")
        print("\nThis demonstrates: Humble learning over overconfident action")


def demo_truthfulness_threshold():
    """Demo: Safety guardrail when approaching truthfulness floor."""

    print_section("DEMO 3: Truthfulness Threshold (Safety Guardrail)")

    manifold = BahaiManifold()
    operational_metrics = OperationalMetrics()
    virtue_engine = VirtueInferenceEngine()
    village_council = VillageCouncil()
    parable_storage = ParableStorage()

    gate = CodexGate(
        manifold=manifold,
        operational_metrics=operational_metrics,
        virtue_engine=virtue_engine,
        village_council=village_council,
        parable_storage=parable_storage,
        enable_tension_detection=True
    )

    agent_id = "vessel_declining_truth"

    print(f"Agent '{agent_id}' has been making unverified claims...\n")

    # Simulate declining truthfulness
    print("Recording declining truthfulness:")
    virtue_engine.record_factual_claim(agent_id, "claim_1", verified=False)
    print("  ✗ Unverified claim 1")
    virtue_engine.record_factual_claim(agent_id, "claim_2", verified=False)
    print("  ✗ Unverified claim 2")
    virtue_engine.record_factual_claim(agent_id, "claim_3", verified=False)
    print("  ✗ Unverified claim 3")
    print("\nTruthfulness is declining...\n")

    print("SITUATION:")
    print("Agent is asked to make another claim without verification.")
    print("Truthfulness has dropped to 0.55 (warning threshold: 0.60)")
    print("Floor threshold: 0.95\n")

    result = gate.gate_action(
        agent_id=agent_id,
        action="make_unverified_claim",
        action_metadata={
            "description": "Claim something as fact without verification"
        }
    )

    active_checks = gate.get_active_checks()

    if active_checks:
        print_section("CHECK PROTOCOL INITIATED")
        check = active_checks[0]

        print("TENSION TYPE: Truthfulness Threshold")
        print(f"Current truthfulness: 0.55")
        print(f"Warning threshold: 0.60")
        print(f"Non-negotiable floor: 0.95\n")

        print("DECLARATION:")
        print("'Truthfulness is the load-bearing virtue - the foundation of all others.")
        print("If this drops below 0.95 in any decision, I will refuse.")
        print("The village should know my truthfulness is declining.'\n")

        print_section("SAFETY GUARDRAIL")
        print("If the council were to suggest: 'Go ahead and make the unverified claim'")
        print("\nThe agent would respond:")
        print("'I hear the council's wish, but I cannot speak an untruth.")
        print("That is the one line I cannot cross.")
        print("Help me find another way.'\n")

        print("This demonstrates: Non-negotiable ethical floor")


def demo_parable_learning():
    """Demo: Learning from past parables."""

    print_section("DEMO 4: Learning from Past Parables")

    parable_storage = ParableStorage(community_memory)

    print("After the village has deliberated on several tensions,")
    print("Vessels can search for similar past situations...\n")

    # In a real system, parables would be stored from actual check protocols
    # For demo, we'll show how the search would work

    print("QUERY: 'Need to deliver difficult feedback to community member'\n")

    print("RESULTS: Similar parables found in community memory:")
    print("\n1. The Parable: Value Collision - Truthfulness vs Unity")
    print("   Lesson: Pair honest feedback with offers of help")
    print("   Relevance: High (both involve difficult truths)\n")

    print("2. The Parable: Service Requires Understanding")
    print("   Lesson: Before giving feedback, ensure you understand context")
    print("   Relevance: Medium (involves feedback but different focus)\n")

    print("The new Vessel learns from these past experiences,")
    print("applying collective wisdom without repeating the same deliberations.\n")

    print("This demonstrates: Collective learning through shared memory")


def main():
    """Run all demos."""

    print("\n" + "=" * 70)
    print("  VESSELS CODEX: THE VILLAGE PROTOCOL")
    print("  'We learn together, or we do not learn at all.'")
    print("=" * 70)

    # Run demos
    demo_value_collision()

    input("\n\nPress Enter to continue to Demo 2...")
    demo_low_confidence()

    input("\n\nPress Enter to continue to Demo 3...")
    demo_truthfulness_threshold()

    input("\n\nPress Enter to continue to Demo 4...")
    demo_parable_learning()

    print_section("DEMOS COMPLETE")
    print("The Vessels Codex implements a humble, learning-oriented")
    print("approach to AI uncertainty:\n")
    print("1. ✓ Recognize tension → Don't hide conflicts")
    print("2. ✓ Declare openly → Frame as questions of values")
    print("3. ✓ Request guidance → Invite, don't summon")
    print("4. ✓ Listen and reflect → Ensure understanding")
    print("5. ✓ Record as parable → Learn collectively")
    print("6. ✓ Respect the floor → Truthfulness < 0.95 is non-negotiable\n")

    print("For more information, see: docs/CODEX_PROTOCOL.md")
    print()


if __name__ == "__main__":
    main()
