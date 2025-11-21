import uuid

from community_memory import CommunityMemory
from vessels.hive_mind import HiveMind


def test_hive_mind_collects_all_agents():
    memory = CommunityMemory(db_path=":memory:")
    hive = HiveMind(memory=memory)

    hive.store_experience("agent_a", {"message": "hello hive", "tags": ["intro"]})
    hive.store_experience("agent_b", {"message": "another note", "tags": ["intro", "note"]})

    insights = hive.collective_insights()
    assert insights["total_memories"] == 2
    assert insights["agent_contributions"]["agent_a"] == 1
    assert insights["agent_contributions"]["agent_b"] == 1

    results = hive.search("hello")
    assert len(results) == 1
    assert results[0].content["message"] == "hello hive"


def test_hive_mind_events_are_shared():
    memory = CommunityMemory(db_path=":memory:")
    hive = HiveMind(memory=memory)

    event_id = str(uuid.uuid4())
    recorded = hive.record_event(
        "coordination",
        {"id": event_id, "detail": "sync"},
        source_agent="agent_a",
        target_agents=["agent_b", "agent_c"],
    )

    events = hive.recent_events()
    assert any(event["id"] == recorded["id"] for event in events)
    assert events[-1]["type"] == "coordination"
