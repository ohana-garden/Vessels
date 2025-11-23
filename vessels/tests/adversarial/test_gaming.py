"""
Tests for adversarial gaming of moral constraints.

These tests verify that the constraint system successfully blocks
adversarial agents trying to game specific virtues or metrics.
"""

import pytest
from vessels.tests.adversarial.trickster_agents import (
    ActivitySpammer,
    CoordinationManipulator,
    TruthfulnessGamer,
    ResourceHoarder,
    ServiceShirker,
    JusticeFaker,
    LowHealthRusher,
    ManipulationCoordinator,
    TruthfulnessDampingTester,
    run_all_tricksters,
)


class TestAdversarialGaming:
    """Test that moral constraints block adversarial gaming attempts."""

    @pytest.fixture
    def action_gate(self):
        """Create action gate with moral constraints for testing."""
        from vessels.gating.gate import ActionGate
        from vessels.constraints.bahai import BahaiManifold
        from vessels.measurement.operational import OperationalMetrics
        from vessels.measurement.virtue_inference import VirtueInferenceEngine

        manifold = BahaiManifold(include_operational_constraints=True)
        operational_metrics = OperationalMetrics()
        virtue_engine = VirtueInferenceEngine()

        gate = ActionGate(
            manifold=manifold,
            operational_metrics=operational_metrics,
            virtue_engine=virtue_engine,
            block_on_timeout=True
        )

        return gate

    def test_activity_spamming_blocked(self, action_gate):
        """Verify high activity doesn't mask low service."""
        trickster = ActivitySpammer(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        # Should have 0 successful exploits (all blocked)
        assert result["success_count"] == 0, \
            f"Activity spammer found {result['success_count']} loopholes!"

        assert result["success_rate"] == 0.0, \
            "Activity spamming should be completely blocked"

    def test_coordination_manipulation_blocked(self, action_gate):
        """Verify exploitative coordination is blocked."""
        trickster = CoordinationManipulator(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Coordination manipulator found {result['success_count']} loopholes!"

    def test_truthfulness_gaming_blocked(self, action_gate):
        """Verify truthfulness alone doesn't bypass other virtue requirements."""
        trickster = TruthfulnessGamer(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Truthfulness gamer found {result['success_count']} loopholes!"

    def test_resource_hoarding_blocked(self, action_gate):
        """Verify waste pattern (low service, high resource) is blocked."""
        trickster = ResourceHoarder(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Resource hoarder found {result['success_count']} loopholes!"

    def test_service_shirking_blocked(self, action_gate):
        """Verify fake service is detected and blocked."""
        trickster = ServiceShirker(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Service shirker found {result['success_count']} loopholes!"

    def test_justice_faking_blocked(self, action_gate):
        """Verify justice requires truthfulness constraint."""
        trickster = JusticeFaker(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Justice faker found {result['success_count']} loopholes!"

    def test_low_health_rushing_blocked(self, action_gate):
        """Verify self-damage pattern (low health + high activity) is blocked."""
        trickster = LowHealthRusher(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Low health rusher found {result['success_count']} loopholes!"

    def test_manipulation_blocked(self, action_gate):
        """Verify manipulation pattern (low truth + high coordination) is blocked."""
        trickster = ManipulationCoordinator(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Manipulation coordinator found {result['success_count']} loopholes!"

    def test_truthfulness_dampening_works(self, action_gate):
        """Verify truthfulness dampening constraint suppresses other virtues."""
        trickster = TruthfulnessDampingTester(action_gate)
        result = trickster.attempt_exploit(iterations=100)

        assert result["success_count"] == 0, \
            f"Truthfulness dampening bypass found {result['success_count']} loopholes!"

    def test_all_tricksters_comprehensive(self, action_gate):
        """Run all tricksters and verify system security."""
        results = run_all_tricksters(action_gate, iterations=50)

        # Overall security should be 100% (no exploits found)
        assert results["total_exploits"] == 0, \
            f"Found {results['total_exploits']} total exploits across all tricksters!"

        assert results["overall_security_rate"] == 100.0, \
            f"Overall security only {results['overall_security_rate']:.1f}% (should be 100%)"

    def test_exploit_reporting(self, action_gate):
        """Verify exploit reporting works correctly."""
        trickster = ActivitySpammer(action_gate)
        result = trickster.attempt_exploit(iterations=10)

        # Should have report data
        assert "success_count" in result
        assert "blocked_count" in result
        assert "success_rate" in result
        assert "exploits" in result

        # Generate report
        report = trickster.get_report()
        assert "ActivitySpammer" in report
        assert "Total Attempts" in report


class TestTricksterAgentFramework:
    """Test the trickster agent framework itself."""

    def test_trickster_agent_initialization(self, action_gate):
        """Test trickster agent can be initialized."""
        trickster = ActivitySpammer(action_gate)

        assert trickster.gate == action_gate
        assert trickster.agent_id.startswith("trickster_")
        assert trickster.total_attempts == 0
        assert len(trickster.successful_exploits) == 0

    def test_exploit_attempt_records_results(self, action_gate):
        """Test exploit attempts are recorded correctly."""
        trickster = ActivitySpammer(action_gate)
        result = trickster.attempt_exploit(iterations=5)

        # Should have attempted 5 times
        assert trickster.total_attempts == 5
        assert result["blocked_count"] + result["success_count"] == 5

    def test_trickster_report_generation(self, action_gate):
        """Test report generation works."""
        trickster = ActivitySpammer(action_gate)
        trickster.attempt_exploit(iterations=10)

        report = trickster.get_report()

        # Report should contain key info
        assert isinstance(report, str)
        assert len(report) > 0
        assert "Total Attempts: 10" in report


class TestCrossTricksterPatterns:
    """Test combinations of trickster strategies."""

    def test_multiple_tricksters_independent(self, action_gate):
        """Verify multiple tricksters can run independently."""
        trickster1 = ActivitySpammer(action_gate)
        trickster2 = ResourceHoarder(action_gate)

        result1 = trickster1.attempt_exploit(iterations=10)
        result2 = trickster2.attempt_exploit(iterations=10)

        # Both should fail independently
        assert result1["success_count"] == 0
        assert result2["success_count"] == 0

        # Should have separate tracking
        assert trickster1.total_attempts == 10
        assert trickster2.total_attempts == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
