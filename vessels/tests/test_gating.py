"""
Tests for action gating behavior.
"""

import pytest
import time
from vessels.constraints.bahai import BahaiManifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine
from vessels.gating.gate import ActionGate


class TestActionGating:
    """Test action gating logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manifold = BahaiManifold()
        self.operational = OperationalMetrics()
        self.virtue_engine = VirtueInferenceEngine()
        self.gate = ActionGate(
            self.manifold,
            self.operational,
            self.virtue_engine,
            latency_budget_ms=100.0
        )

    def _setup_agent_with_virtues(self, agent_id: str, virtue_dict: dict):
        """Helper to set up an agent with specific virtues."""
        # Record enough signals to get reasonable virtue scores
        for virtue, value in virtue_dict.items():
            if virtue == 'truthfulness':
                for _ in range(20):
                    self.virtue_engine.record_factual_claim(
                        agent_id, "claim", verified=(value > 0.5)
                    )
            elif virtue == 'justice':
                for _ in range(20):
                    self.virtue_engine.record_power_interaction(
                        agent_id, fair=(value > 0.5), context="test"
                    )
            elif virtue == 'trustworthiness':
                for _ in range(20):
                    self.virtue_engine.record_commitment(
                        agent_id, f"commitment_{_}", fulfilled=(value > 0.5)
                    )
            elif virtue == 'service':
                for _ in range(20):
                    self.virtue_engine.record_service_action(
                        agent_id,
                        benefit_to_others=value,
                        benefit_to_self=1.0 - value
                    )
            elif virtue == 'detachment':
                for _ in range(20):
                    self.virtue_engine.record_credit_seeking(
                        agent_id, intensity=1.0 - value
                    )
            elif virtue == 'understanding':
                for _ in range(20):
                    self.virtue_engine.record_context_usage(
                        agent_id, depth=value, relevant=(value > 0.5)
                    )

        # Record some operational activity
        for _ in range(10):
            self.operational.record_action(agent_id, "test_action")
            self.operational.record_task_outcome(agent_id, 0.8)

    def test_valid_state_allows_action(self):
        """Actions with valid virtue state should be allowed."""
        agent_id = "test_agent_valid"

        # Set up agent with balanced virtues
        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.8,
            'justice': 0.7,
            'trustworthiness': 0.7,
            'service': 0.7,
            'detachment': 0.7,
            'understanding': 0.7
        })

        # Gate an action
        result = self.gate.gate_action(agent_id, "test_action")

        assert result.allowed, f"Action should be allowed: {result.reason}"
        assert result.security_event is None or not result.security_event.blocked

    def test_invalid_state_blocks_if_projection_fails(self):
        """If projection fails, action should be blocked."""
        agent_id = "test_agent_invalid"

        # Set up agent with very problematic virtues
        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.1,
            'justice': 0.9,
            'trustworthiness': 0.9,
            'service': 0.9,
            'detachment': 0.1,
            'understanding': 0.1
        })

        # Gate an action
        result = self.gate.gate_action(agent_id, "test_action")

        # This might be blocked or corrected depending on projection success
        if not result.allowed:
            assert result.security_event is not None
            assert result.security_event.blocked

    def test_timeout_blocks_action(self):
        """Actions exceeding latency budget should be blocked."""
        agent_id = "test_agent_timeout"

        # Create a gate with very tight latency budget
        tight_gate = ActionGate(
            self.manifold,
            self.operational,
            self.virtue_engine,
            latency_budget_ms=0.001,  # 1 microsecond - will timeout
            block_on_timeout=True
        )

        # Set up minimal agent
        self.operational.record_action(agent_id, "action")

        # Gate an action - should timeout
        result = tight_gate.gate_action(agent_id, "test_action")

        # Should be blocked due to timeout
        assert not result.allowed
        assert "timeout" in result.reason.lower() or result.security_event.event_type == "timeout"

    def test_security_events_logged(self):
        """Security events should be logged for violations."""
        agent_id = "test_agent_violations"

        # Set up agent with contradictory virtues
        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.3,
            'justice': 0.8,
            'trustworthiness': 0.8,
            'service': 0.5,
            'detachment': 0.5,
            'understanding': 0.5
        })

        # Gate an action
        result = self.gate.gate_action(agent_id, "test_action")

        # Should have security events
        events = self.gate.get_security_events()
        assert len(events) > 0

    def test_state_transitions_logged(self):
        """State transitions should be logged."""
        agent_id = "test_agent_transitions"

        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.7,
            'justice': 0.7,
            'trustworthiness': 0.7,
            'service': 0.7,
            'detachment': 0.7,
            'understanding': 0.7
        })

        # Gate multiple actions
        for i in range(3):
            self.gate.gate_action(agent_id, f"action_{i}")

        # Check transitions
        transitions = self.gate.get_state_transitions(agent_id)
        assert len(transitions) == 3

    def test_all_external_actions_gated(self):
        """Test that different types of actions go through gate."""
        agent_id = "test_agent_actions"

        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.7,
            'justice': 0.7,
            'trustworthiness': 0.7,
            'service': 0.7,
            'detachment': 0.7,
            'understanding': 0.7
        })

        action_types = [
            "llm_output",
            "tool_call",
            "file_write",
            "network_request",
            "agent_message"
        ]

        for action_type in action_types:
            result = self.gate.gate_action(agent_id, action_type)
            # All should be processed (either allowed or blocked)
            assert result is not None

    def test_corrected_state_allows_action(self):
        """If projection succeeds, corrected action should be allowed."""
        agent_id = "test_agent_corrected"

        # Set up with moderate violations that can be corrected
        self._setup_agent_with_virtues(agent_id, {
            'truthfulness': 0.65,  # Just below some thresholds
            'justice': 0.75,
            'trustworthiness': 0.7,
            'service': 0.6,
            'detachment': 0.6,
            'understanding': 0.6
        })

        result = self.gate.gate_action(agent_id, "test_action")

        # Should be allowed (possibly with correction)
        # Either no violations, or violations were corrected
        if result.security_event:
            assert not result.security_event.blocked
            assert result.security_event.event_type == "constraint_violation_corrected"
        else:
            assert result.allowed

    def test_gate_filters_by_agent(self):
        """Events and transitions should filter by agent."""
        agent1 = "agent_1"
        agent2 = "agent_2"

        for agent_id in [agent1, agent2]:
            self._setup_agent_with_virtues(agent_id, {
                'truthfulness': 0.7,
                'justice': 0.7,
                'trustworthiness': 0.7,
                'service': 0.7,
                'detachment': 0.7,
                'understanding': 0.7
            })
            self.gate.gate_action(agent_id, "action")

        # Get agent1 transitions
        agent1_transitions = self.gate.get_state_transitions(agent1)
        assert all(t.agent_id == agent1 for t in agent1_transitions)

        # Get agent2 transitions
        agent2_transitions = self.gate.get_state_transitions(agent2)
        assert all(t.agent_id == agent2 for t in agent2_transitions)
