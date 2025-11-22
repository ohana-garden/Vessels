from datetime import datetime

from vessels.gating.events import SecurityEvent, StateTransition
from vessels.observability.service import ObservabilityService
from vessels.phase_space.tracker import TrajectoryTracker
from adaptive_tools import AdaptiveTools, ToolSpecification, ToolType


class FakeGateResult:
    def __init__(self, allowed: bool, reason: str, security_event=None, transition=None):
        self.allowed = allowed
        self.reason = reason
        self.security_event = security_event
        self.state_transition = transition


class FakeGate:
    def __init__(self, allowed=True, tracker=None):
        self.allowed = allowed
        self.invocations = 0
        self.tracker = tracker

    def gate_action(self, agent_id, action, action_metadata=None):
        self.invocations += 1
        metadata = action_metadata or {}
        event = SecurityEvent(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            violations=[],
            original_virtue_state={},
            blocked=not self.allowed,
            action_hash="hash",
            event_type="test_gate",
            metadata=metadata,
        )
        transition = StateTransition(
            agent_id=agent_id,
            timestamp=datetime.utcnow(),
            from_state={},
            to_state={},
            action_hash="hash",
            gating_result="allowed" if self.allowed else "blocked",
            action_metadata=metadata,
        )
        if self.tracker and self.allowed:
            self.tracker.store_security_event(event)
            self.tracker.store_transition(transition)
        return FakeGateResult(self.allowed, "ok" if self.allowed else "blocked", event, transition)


def _echo_handler(params):
    return {"success": True, "echo": params}


def test_adaptive_tools_respects_gate_block(tmp_path):
    tracker = TrajectoryTracker(db_path=str(tmp_path / "events.db"))
    gate = FakeGate(allowed=False, tracker=tracker)
    tools = AdaptiveTools(gate=gate, tracker=tracker, vessel_id="vessel-a")
    spec = ToolSpecification(
        name="echo",
        description="",
        tool_type=ToolType.GENERIC,
        parameters={},
        returns={},
        capabilities=[],
    )
    tool_id = tools.create_tool(spec)
    result = tools.execute_tool(tool_id, {"text": "hi"}, agent_id="agent-1")
    assert result["success"] is False
    assert gate.invocations == 1


def test_observability_lists_events_by_vessel(tmp_path):
    tracker = TrajectoryTracker(db_path=str(tmp_path / "events.db"))
    event = SecurityEvent(
        agent_id="agent-1",
        timestamp=datetime.utcnow(),
        violations=[],
        original_virtue_state={},
        blocked=True,
        action_hash="hash",
        event_type="blocked",
        metadata={"vessel_id": "vessel-a"},
    )
    tracker.store_security_event(event)
    tracker.store_attractor([0.0], 0.1, "good", 1, metadata={"vessel_id": "vessel-a"})

    observability = ObservabilityService(tracker)
    gating_events = observability.list_gating_events(vessel_id="vessel-a")
    assert len(gating_events) == 1
    assert gating_events[0].vessel_id == "vessel-a"

    attractors = observability.list_attractors(vessel_id="vessel-a")
    assert len(attractors) == 1

    metrics = observability.get_vessel_metrics("vessel-a")
    assert metrics.total_events == 1
    assert metrics.blocked_events == 1
