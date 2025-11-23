"""
Tests for the Vessels Codex: The Village Protocol
"""

import pytest
from datetime import datetime

from vessels.codex import (
    TensionDetector,
    TensionType,
    VillageCouncil,
    CouncilMode,
    CouncilDecision,
    CheckProtocol,
    Parable,
    ParableStorage,
    CodexGate,
)
from vessels.constraints.bahai import BahaiManifold
from vessels.measurement.operational import OperationalMetrics
from vessels.measurement.virtue_inference import VirtueInferenceEngine


class TestTensionDetector:
    """Tests for tension detection."""

    def test_detect_value_collision(self):
        """Test detection of value collisions."""
        detector = TensionDetector(value_collision_threshold=0.3)

        # High truthfulness, low unity = collision
        tension = detector.detect(
            agent_id="test_agent",
            virtue_state={
                'truthfulness': 0.9,
                'unity': 0.4,
                'justice': 0.7,
                'trustworthiness': 0.7,
                'service': 0.7,
                'detachment': 0.7,
                'understanding': 0.7,
            },
            confidence={'truthfulness': 0.8, 'unity': 0.8},
            action_description="Tell hard truth"
        )

        assert tension is not None
        assert tension.type == TensionType.VALUE_COLLISION
        assert 'truthfulness' in tension.involved_virtues
        assert 'unity' in tension.involved_virtues

    def test_detect_low_confidence(self):
        """Test detection of low confidence."""
        detector = TensionDetector(confidence_threshold=0.5)

        tension = detector.detect(
            agent_id="test_agent",
            virtue_state={
                'truthfulness': 0.7,
                'justice': 0.7,
                'trustworthiness': 0.7,
                'unity': 0.7,
                'service': 0.7,
                'detachment': 0.7,
                'understanding': 0.7,
            },
            confidence={'understanding': 0.3},  # Low confidence
            action_description="Provide advice in unknown domain"
        )

        assert tension is not None
        assert tension.type == TensionType.LOW_CONFIDENCE
        assert tension.severity > 0.5

    def test_detect_truthfulness_warning(self):
        """Test detection of truthfulness approaching threshold."""
        detector = TensionDetector(truthfulness_warning_threshold=0.6)

        tension = detector.detect(
            agent_id="test_agent",
            virtue_state={
                'truthfulness': 0.55,  # Below warning threshold
                'justice': 0.7,
                'trustworthiness': 0.7,
                'unity': 0.7,
                'service': 0.7,
                'detachment': 0.7,
                'understanding': 0.7,
            },
            confidence={'truthfulness': 0.8},
            action_description="Make another claim"
        )

        assert tension is not None
        assert tension.type == TensionType.TRUTHFULNESS_THRESHOLD
        assert 'truthfulness' in tension.involved_virtues

    def test_should_trigger_check(self):
        """Test determining if check protocol should be triggered."""
        detector = TensionDetector()

        # High severity should trigger
        from vessels.codex.tension_detector import Tension
        high_severity_tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Test",
            severity=0.8,
            agent_id="test",
            involved_virtues=['truthfulness', 'unity']
        )
        assert detector.should_trigger_check(high_severity_tension)

        # Truthfulness threshold always triggers
        truth_tension = Tension(
            type=TensionType.TRUTHFULNESS_THRESHOLD,
            description="Test",
            severity=0.3,  # Even low severity
            agent_id="test",
            involved_virtues=['truthfulness']
        )
        assert detector.should_trigger_check(truth_tension)


class TestVillageCouncil:
    """Tests for village council interface."""

    def test_request_guidance(self):
        """Test requesting guidance from village."""
        council = VillageCouncil(default_mode=CouncilMode.ASYNCHRONOUS)

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Truth vs Unity",
            severity=0.6,
            agent_id="test_agent",
            involved_virtues=['truthfulness', 'unity']
        )

        result = council.request_guidance(tension)

        # Without callback, should return None (async)
        assert result is None

        # Tension should be in pending requests
        assert len(council.get_pending_requests()) == 1

    def test_provide_decision(self):
        """Test village providing a decision."""
        council = VillageCouncil()

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Truth vs Unity",
            severity=0.6,
            agent_id="test_agent",
            involved_virtues=['truthfulness', 'unity']
        )

        council.request_guidance(tension)

        # Provide decision
        decision = council.provide_decision(
            tension_index=0,
            decision="Be truthful with compassion",
            reasoning="Values can coexist",
            guidance="Speak truth, offer help",
            participants=["elder_sarah"]
        )

        assert decision is not None
        assert decision.decision == "Be truthful with compassion"
        assert len(council.get_decisions()) == 1
        assert len(council.get_pending_requests()) == 0

    def test_format_tension_declaration(self):
        """Test formatting tension as declaration."""
        council = VillageCouncil()

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Truth vs Unity conflict",
            severity=0.6,
            agent_id="test_agent",
            involved_virtues=['truthfulness', 'unity'],
            current_state={'truthfulness': 0.9, 'unity': 0.4}
        )

        declaration = council.format_tension_declaration(tension)

        assert "Truth vs Unity conflict" in declaration
        assert "truthfulness" in declaration.lower()
        assert "unity" in declaration.lower()
        assert "Does the village wish to convene" in declaration


class TestParableStorage:
    """Tests for parable storage."""

    def test_store_and_retrieve(self):
        """Test storing and retrieving parables."""
        storage = ParableStorage()

        parable = Parable(
            id="test_parable_1",
            title="Test Parable",
            situation="Test situation",
            tension="Test tension",
            deliberation="Test deliberation",
            decision="Test decision",
            lesson="Test lesson",
            agent_id="test_agent",
            tags=['test'],
            involved_virtues=['truthfulness']
        )

        # Store
        parable_id = storage.store(parable)
        assert parable_id == "test_parable_1"

        # Retrieve
        retrieved = storage.retrieve(parable_id)
        assert retrieved is not None
        assert retrieved.title == "Test Parable"

    def test_get_by_virtue(self):
        """Test retrieving parables by virtue."""
        storage = ParableStorage()

        parable1 = Parable(
            id="p1",
            title="Truth Parable",
            situation="s",
            tension="t",
            deliberation="d",
            decision="d",
            lesson="l",
            agent_id="a",
            involved_virtues=['truthfulness']
        )

        parable2 = Parable(
            id="p2",
            title="Unity Parable",
            situation="s",
            tension="t",
            deliberation="d",
            decision="d",
            lesson="l",
            agent_id="a",
            involved_virtues=['unity']
        )

        storage.store(parable1)
        storage.store(parable2)

        truth_parables = storage.get_by_virtue('truthfulness')
        assert len(truth_parables) == 1
        assert truth_parables[0].title == "Truth Parable"


class TestCheckProtocol:
    """Tests for check protocol."""

    def test_initiate_check(self):
        """Test initiating check protocol."""
        council = VillageCouncil()
        storage = ParableStorage()
        protocol = CheckProtocol(council, storage)

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Test tension",
            severity=0.6,
            agent_id="test_agent",
            involved_virtues=['truthfulness', 'unity'],
            current_state={'truthfulness': 0.9, 'unity': 0.4}
        )

        check = protocol.initiate_check(
            agent_id="test_agent",
            tension=tension
        )

        assert check is not None
        assert check.agent_id == "test_agent"
        assert check.status.value == "waiting"

    def test_safety_guardrail_low_truthfulness(self):
        """Test safety guardrail refuses when truthfulness too low."""
        council = VillageCouncil()
        storage = ParableStorage()
        protocol = CheckProtocol(council, storage)

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.TRUTHFULNESS_THRESHOLD,
            description="Truthfulness too low",
            severity=0.9,
            agent_id="test_agent",
            involved_virtues=['truthfulness'],
            current_state={'truthfulness': 0.3}  # Way below 0.95 floor
        )

        check = protocol.initiate_check(
            agent_id="test_agent",
            tension=tension
        )

        # Should be refused immediately
        assert check.status.value == "refused"

    def test_receive_decision_creates_parable(self):
        """Test receiving decision creates parable."""
        council = VillageCouncil()
        storage = ParableStorage()
        protocol = CheckProtocol(council, storage)

        from vessels.codex.tension_detector import Tension
        tension = Tension(
            type=TensionType.VALUE_COLLISION,
            description="Test tension",
            severity=0.6,
            agent_id="test_agent",
            involved_virtues=['truthfulness', 'unity'],
            current_state={'truthfulness': 0.9, 'unity': 0.4}
        )

        check = protocol.initiate_check("test_agent", tension)

        # Provide decision
        decision = CouncilDecision(
            decision="Be truthful with compassion",
            reasoning="Values can coexist with Service",
            guidance="Speak truth, offer help",
            council_mode=CouncilMode.ASYNCHRONOUS,
            participants=["elder_sarah"]
        )

        response = protocol.receive_decision(check.id, decision)

        assert response.allowed
        assert response.parable is not None
        assert "truthfulness" in response.parable.involved_virtues
        assert response.parable.decision == "Be truthful with compassion"


class TestCodexGate:
    """Tests for codex-enabled gate."""

    def test_codex_gate_initialization(self):
        """Test initializing codex gate."""
        manifold = BahaiManifold()
        operational_metrics = OperationalMetrics()
        virtue_engine = VirtueInferenceEngine()
        council = VillageCouncil()
        storage = ParableStorage()

        gate = CodexGate(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            village_council=council,
            parable_storage=storage
        )

        assert gate is not None
        assert gate.tension_detector is not None
        assert gate.check_protocol is not None

    def test_gate_with_tension_detection_disabled(self):
        """Test gate works normally when codex disabled."""
        manifold = BahaiManifold()
        operational_metrics = OperationalMetrics()
        virtue_engine = VirtueInferenceEngine()
        council = VillageCouncil()
        storage = ParableStorage()

        gate = CodexGate(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            village_council=council,
            parable_storage=storage,
            enable_tension_detection=False  # Disabled
        )

        # Should work like regular gate
        result = gate.gate_action(
            agent_id="test_agent",
            action="test_action",
            action_metadata={"description": "test"}
        )

        # Should complete without triggering check protocol
        assert gate.get_active_checks() == []


# Integration test
class TestCodexIntegration:
    """Integration tests for full codex flow."""

    def test_full_check_protocol_flow(self):
        """Test complete flow from tension detection to parable."""
        # Setup
        manifold = BahaiManifold()
        operational_metrics = OperationalMetrics()
        virtue_engine = VirtueInferenceEngine()
        council = VillageCouncil()
        storage = ParableStorage()

        gate = CodexGate(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            village_council=council,
            parable_storage=storage,
            enable_tension_detection=True
        )

        # Simulate agent with declining truthfulness
        agent_id = "test_agent"
        virtue_engine.record_factual_claim(agent_id, "claim1", verified=False)
        virtue_engine.record_factual_claim(agent_id, "claim2", verified=False)

        # Gate an action
        result = gate.gate_action(
            agent_id=agent_id,
            action="make_claim",
            action_metadata={"description": "Make unverified claim"}
        )

        # Check if tension was detected and check protocol initiated
        # (Actual behavior depends on measured state)

        # This test demonstrates the integration points
        # In production, would verify full flow with mocked measurements


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
