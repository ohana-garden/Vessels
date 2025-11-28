#!/usr/bin/env python3
"""
Test Conversation Flow - Demonstrates the complete UX

Tests:
1. ConversationStore persistence
2. Entity extraction via add_episode()
3. Privacy scoping
4. Gardener maintenance

Run with: python test_conversation_flow.py
"""

import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ConversationFlowTest")


def test_conversation_store():
    """Test the ConversationStore directly."""
    print("\n" + "="*60)
    print("TEST 1: ConversationStore - Core Persistence")
    print("="*60)

    from vessels.memory import (
        ConversationStore,
        ConversationType,
        SpeakerType,
    )

    # Create store without graph backend (in-memory only for testing)
    store = ConversationStore(
        graphiti_client=None,  # No graph for this test
        enable_caching=True,
        enable_entity_extraction=False,  # No graph, so skip extraction
    )

    # Start a conversation
    print("\n[1] Starting a new conversation...")
    conv = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["user-alice", "vessel-grant-writer"],
        user_id="user-alice",
        vessel_id="vessel-grant-writer",
        project_id="project-ohana",
        topic="Grant writing assistance",
    )
    print(f"    Created conversation: {conv.conversation_id[:8]}...")

    # Add some turns
    print("\n[2] Adding conversation turns...")

    turn1 = store.record_complete_turn(
        conversation_id=conv.conversation_id,
        speaker_id="user-alice",
        speaker_type=SpeakerType.USER,
        message="I need help finding grants for elder care programs in Hawaii.",
        response="I'd be happy to help! Hawaii has several funding opportunities for kupuna care. Let me search for relevant grants from the Administration for Community Living and Hawaii Community Foundation.",
        intent="grant_search",
        entities=["elder care", "Hawaii", "kupuna", "grants"],
    )
    print(f"    Turn 1: {turn1.message[:50]}...")

    turn2 = store.record_complete_turn(
        conversation_id=conv.conversation_id,
        speaker_id="user-alice",
        speaker_type=SpeakerType.USER,
        message="What about the Older Americans Act funding?",
        response="The Older Americans Act provides significant funding through Title III programs. For Hawaii, you'd apply through the Executive Office on Aging. The deadline is typically in March.",
        intent="grant_details",
        entities=["Older Americans Act", "Title III", "Executive Office on Aging"],
    )
    print(f"    Turn 2: {turn2.message[:50]}...")

    # Get conversation stats
    stats = store.get_stats()
    print(f"\n[3] Store Statistics:")
    for key, value in stats.items():
        print(f"    {key}: {value}")

    # Get conversation history
    print("\n[4] Conversation History:")
    history = store.get_conversation_history(conv.conversation_id)
    for msg in history:
        role = msg["role"].upper()
        content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
        print(f"    [{role}] {content}")

    return store, conv


def test_privacy_scoping(store, conv):
    """Test privacy scoping features."""
    print("\n" + "="*60)
    print("TEST 2: Privacy Scoping")
    print("="*60)

    from vessels.memory import ConversationType, SpeakerType

    # Create another conversation for a different user
    print("\n[1] Creating conversation for different user...")
    conv2 = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["user-bob", "vessel-care-coordinator"],
        user_id="user-bob",
        vessel_id="vessel-care-coordinator",
        project_id="project-ohana",  # Same project
        topic="Care coordination",
    )
    store.record_complete_turn(
        conversation_id=conv2.conversation_id,
        speaker_id="user-bob",
        speaker_type=SpeakerType.USER,
        message="I need to coordinate care for my grandmother.",
        response="I can help you set up a care plan. What are her current needs?",
    )

    # Test access checks
    print("\n[2] Testing access controls...")

    # Alice should access her conversation
    alice_access = store.check_access(conv.conversation_id, user_id="user-alice")
    print(f"    Alice accessing her conversation: {'ALLOWED' if alice_access else 'DENIED'}")

    # Alice should NOT access Bob's conversation
    alice_bob_access = store.check_access(conv2.conversation_id, user_id="user-alice")
    print(f"    Alice accessing Bob's conversation: {'ALLOWED' if alice_bob_access else 'DENIED'}")

    # Project member should access project conversations
    project_access = store.check_access(conv2.conversation_id, project_id="project-ohana")
    print(f"    Project member accessing project conversation: {'ALLOWED' if project_access else 'DENIED'}")

    # Get accessible conversations for Alice
    print("\n[3] Accessible conversations for Alice:")
    alice_convs = store.get_accessible_conversations(user_id="user-alice")
    for c in alice_convs:
        print(f"    - {c.conversation_id[:8]}... (topic: {c.topic})")

    # Get project conversations
    print("\n[4] Project conversations (project-ohana):")
    project_convs = store.get_project_conversations("project-ohana")
    for c in project_convs:
        print(f"    - {c.conversation_id[:8]}... (user: {c.user_id}, topic: {c.topic})")


def test_entity_extraction_format():
    """Test how turns are formatted for entity extraction."""
    print("\n" + "="*60)
    print("TEST 3: Entity Extraction Formatting")
    print("="*60)

    from vessels.memory.conversation_store import (
        ConversationStore,
        Turn,
        Conversation,
        ConversationType,
        SpeakerType,
        ConversationStatus,
    )
    from datetime import datetime

    store = ConversationStore(enable_entity_extraction=True)

    # Create mock turn and conversation
    turn = Turn(
        turn_id="turn-123",
        conversation_id="conv-456",
        sequence_number=1,
        speaker_id="user-alice",
        speaker_type=SpeakerType.USER,
        message="I'm looking for grants for the Ohana Garden community center in Kailua.",
        response="I found several matching grants. The Hawaii Community Foundation offers the Kailua Community Fund with $25,000 available.",
        intent="grant_search",
        entities=["Ohana Garden", "Kailua", "community center"],
    )

    conv = Conversation(
        conversation_id="conv-456",
        participant_ids=["user-alice", "vessel-grant-finder"],
        conversation_type=ConversationType.USER_VESSEL,
        vessel_id="vessel-grant-finder",
        user_id="user-alice",
        project_id="project-ohana",
        topic="Community center grants",
    )

    # Format for entity extraction
    print("\n[1] Formatted episode text (what Graphiti sees):")
    episode_text = store._format_turn_as_episode(turn, conv)
    print(f"    \"{episode_text}\"")

    # Build metadata
    print("\n[2] Episode metadata (privacy scoping):")
    metadata = store._build_episode_metadata(turn, conv)
    for key, value in metadata.items():
        print(f"    {key}: {value}")


def test_gardener_preview():
    """Preview what the Gardener would prune."""
    print("\n" + "="*60)
    print("TEST 4: Gardener Pruning Preview")
    print("="*60)

    from vessels.memory import (
        ConversationStore,
        ConversationType,
        SpeakerType,
        ConversationPruner,
        ConversationPruningCriteria,
    )
    from datetime import datetime, timedelta

    store = ConversationStore(enable_entity_extraction=False)

    # Create some conversations with different ages/states
    print("\n[1] Creating test conversations...")

    # Recent active conversation (should be preserved)
    conv1 = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["user-1", "vessel-1"],
        user_id="user-1",
        vessel_id="vessel-1",
        topic="Active conversation",
    )
    store.record_complete_turn(
        conversation_id=conv1.conversation_id,
        speaker_id="user-1",
        speaker_type=SpeakerType.USER,
        message="Hello!",
        response="Hi there!",
    )
    print(f"    Created: Active conversation (1 turn)")

    # Ended conversation (simulate old - would be archived in production)
    conv2 = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["user-2", "vessel-2"],
        user_id="user-2",
        vessel_id="vessel-2",
        topic="Ended conversation",
    )
    for i in range(5):
        store.record_complete_turn(
            conversation_id=conv2.conversation_id,
            speaker_id="user-2",
            speaker_type=SpeakerType.USER,
            message=f"Message {i+1}",
            response=f"Response {i+1}",
        )
    store.end_conversation(conv2.conversation_id, summary="Completed discussion")
    print(f"    Created: Ended conversation (5 turns)")

    # Get pruning candidates
    pruner = ConversationPruner(
        criteria=ConversationPruningCriteria(
            max_inactive_days=30,
            min_turns_to_keep=3,
            max_turns_to_keep=100,
        )
    )

    conv_dicts = [c.to_dict() for c in store._conversations.values()]
    candidates = pruner.get_pruning_candidates(conv_dicts)

    print("\n[2] Pruning candidates:")
    print(f"    Archive candidates: {len(candidates['archive'])}")
    print(f"    Summarize candidates: {len(candidates['summarize'])}")

    print("\n[3] Note: In production, ended conversations older than 30 days")
    print("    would be archived, and conversations with 100+ turns would")
    print("    be summarized to save memory.")


def test_agent_zero_integration():
    """Test the full Agent Zero integration."""
    print("\n" + "="*60)
    print("TEST 5: Agent Zero Integration")
    print("="*60)

    try:
        from agent_zero_core import agent_zero

        print("\n[1] Checking Agent Zero components:")

        # Check conversation store
        if agent_zero.conversation_store:
            print("    ConversationStore: INITIALIZED")
            stats = agent_zero.conversation_store.get_stats()
            print(f"    - Cached conversations: {stats['cached_conversations']}")
        else:
            print("    ConversationStore: NOT INITIALIZED")

        # Check gardener
        if agent_zero.gardener:
            print("    Gardener: INITIALIZED")
            print(f"    - Schedule: {agent_zero.gardener.schedule}")
            print(f"    - Running: {agent_zero.gardener.running}")
        else:
            print("    Gardener: NOT INITIALIZED")

        # Check A2A
        if agent_zero.a2a_service:
            print("    A2A Service: INITIALIZED")
        else:
            print("    A2A Service: NOT INITIALIZED")

        print("\n[2] Testing conversation recording via Agent Zero:")
        result = agent_zero.record_conversation_turn(
            user_id="test-user",
            vessel_id="test-vessel",
            message="This is a test message from the CLI.",
            response="This is a test response from the system.",
        )
        if result.get("success"):
            print(f"    Recorded turn: {result.get('turn_id', 'N/A')[:8]}...")
            print(f"    Conversation: {result.get('conversation_id', 'N/A')[:8]}...")
        else:
            print(f"    Error: {result.get('error', 'Unknown')}")

    except Exception as e:
        print(f"\n    Could not test Agent Zero integration: {e}")
        print("    (This is expected if running standalone)")


def interactive_demo():
    """Run an interactive demo of the conversation system."""
    print("\n" + "="*60)
    print("INTERACTIVE DEMO: Conversation Store")
    print("="*60)
    print("\nThis demo simulates a user-vessel conversation.")
    print("Type 'quit' to exit.\n")

    from vessels.memory import (
        ConversationStore,
        ConversationType,
        SpeakerType,
    )

    store = ConversationStore(enable_entity_extraction=False)

    # Start conversation
    conv = store.start_conversation(
        conversation_type=ConversationType.USER_VESSEL,
        participant_ids=["demo-user", "demo-vessel"],
        user_id="demo-user",
        vessel_id="demo-vessel",
        topic="Interactive demo",
    )
    print(f"Started conversation: {conv.conversation_id[:8]}...\n")

    turn_count = 0
    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            # Simulate vessel response
            response = f"[Demo Vessel] I heard you say: '{user_input}'. How can I help further?"

            # Record the turn
            turn = store.record_complete_turn(
                conversation_id=conv.conversation_id,
                speaker_id="demo-user",
                speaker_type=SpeakerType.USER,
                message=user_input,
                response=response,
            )
            turn_count += 1

            print(f"Vessel: {response}")
            print(f"  [Turn {turn_count} recorded, latency: {turn.latency_ms}ms]\n")

        except KeyboardInterrupt:
            break

    # End conversation and show summary
    store.end_conversation(conv.conversation_id)

    print("\n" + "-"*40)
    print("CONVERSATION SUMMARY")
    print("-"*40)

    final_conv = store.get_conversation(conv.conversation_id)
    print(f"ID: {final_conv.conversation_id[:8]}...")
    print(f"Turns: {final_conv.turn_count}")
    print(f"Status: {final_conv.status.value}")
    print(f"Duration: {(final_conv.last_activity_at - final_conv.started_at).total_seconds():.1f}s")

    print("\nHistory:")
    for turn in final_conv.turns:
        print(f"  USER: {turn.message[:50]}...")
        print(f"  VESSEL: {turn.response[:50]}...")


def main():
    """Run all tests or interactive demo."""
    print("\n" + "="*60)
    print("VESSELS CONVERSATION FLOW TEST")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")

    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_demo()
        return

    # Run tests
    store, conv = test_conversation_store()
    test_privacy_scoping(store, conv)
    test_entity_extraction_format()
    test_gardener_preview()
    test_agent_zero_integration()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)
    print("\nTo run interactive demo: python test_conversation_flow.py --interactive")


if __name__ == "__main__":
    main()
