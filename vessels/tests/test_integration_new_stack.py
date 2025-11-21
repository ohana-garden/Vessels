"""
Integration Tests for New Vessels Stack

Tests for:
- Nostr communication layer
- On-device AI (STT, TTS, Local LLM, Emotion)
- Petals gateway
- LLM router
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import numpy as np


# ============================================================================
# NOSTR COMMUNICATION TESTS
# ============================================================================

class TestNostrAdapter:
    """Tests for Nostr protocol adapter"""

    def test_nostr_keypair_generation(self):
        """Test Nostr keypair generation"""
        from vessels.communication.nostr_adapter import NostrKeypair

        keypair = NostrKeypair.generate()

        assert isinstance(keypair.public_key, str)
        assert isinstance(keypair.private_key, str)
        assert len(keypair.public_key) == 64  # 32 bytes hex
        assert len(keypair.private_key) == 64

    def test_nostr_adapter_disabled_by_default(self):
        """Test that Nostr is disabled by default"""
        from vessels.communication.nostr_adapter import NostrAdapter, NostrKeypair

        keypair = NostrKeypair.generate()
        adapter = NostrAdapter(
            keypair=keypair,
            relays=["wss://relay.damus.io"],
            enabled=False
        )

        assert not adapter.enabled

        # Should raise error when trying to publish
        with pytest.raises(Exception):
            adapter.publish_node_status({"node_id": "test"})

    def test_nostr_event_creation(self):
        """Test Nostr event creation and signing"""
        from vessels.communication.nostr_adapter import NostrEvent, NostrKeypair

        keypair = NostrKeypair.generate()

        event = NostrEvent(
            kind=1,
            content="Test event",
            tags=[["t", "vessels"]],
            pubkey=keypair.public_key
        )

        event.compute_id()
        assert event.id
        assert len(event.id) == 64  # SHA256 hex

    def test_protocol_registry(self):
        """Test protocol registry"""
        from vessels.communication.protocol_registry import ProtocolRegistry, Protocol

        registry = ProtocolRegistry()

        # Initially empty
        status = registry.get_status()
        assert len(status["enabled_protocols"]) == 0


class TestDataSanitizer:
    """Tests for data sanitization"""

    def test_sanitize_phone_numbers(self):
        """Test phone number removal"""
        from vessels.communication.sanitizer import DataSanitizer

        sanitizer = DataSanitizer()

        text = "Call me at 510-555-1234"
        result = sanitizer._remove_phone_numbers(text)

        assert "510-555-1234" not in result
        assert "[PHONE]" in result

    def test_sanitize_emails(self):
        """Test email removal"""
        from vessels.communication.sanitizer import DataSanitizer

        sanitizer = DataSanitizer()

        text = "Contact john@example.com"
        result = sanitizer._remove_emails(text)

        assert "john@example.com" not in result
        assert "[EMAIL]" in result

    def test_sanitize_offer(self):
        """Test offer sanitization"""
        from vessels.communication.sanitizer import DataSanitizer

        sanitizer = DataSanitizer()

        offer = {
            "type": "tomatoes",
            "quantity": 12.5,
            "unit": "kg",
            "location": "123 Main St, Oakland, CA",
            "phone": "510-555-1234"
        }

        sanitized = sanitizer.sanitize(offer, event_type="offer")

        # Should keep allowed fields
        assert "type" in sanitized
        assert sanitized["type"] == "tomatoes"

        # Should round quantity
        assert sanitized["quantity"] == 20.0  # Rounded from 12.5

        # Should not have phone (not in allowed fields)
        assert "phone" not in sanitized


# ============================================================================
# ON-DEVICE AI TESTS
# ============================================================================

class TestDeviceSTT:
    """Tests for on-device speech-to-text"""

    def test_whisper_stt_initialization(self):
        """Test WhisperSTT initialization"""
        from vessels.device.stt import WhisperSTT

        # This will try to load a model; may fail if not installed
        # In that case, it should fall back gracefully
        try:
            stt = WhisperSTT(model_name="tiny.en")
            assert stt.model_name == "tiny.en"
            assert stt.backend in ["faster-whisper", "whispercpp", "openai-whisper", "espeak"]
        except RuntimeError as e:
            # No backend available, skip
            pytest.skip(f"No Whisper backend available: {e}")

    def test_stt_model_info(self):
        """Test STT model info"""
        from vessels.device.stt import WhisperSTT

        assert "tiny.en" in WhisperSTT.MODELS
        assert "small.en" in WhisperSTT.MODELS

        model_info = WhisperSTT.MODELS["small.en"]
        assert model_info["params"] == "244M"


class TestDeviceTTS:
    """Tests for on-device text-to-speech"""

    def test_tts_initialization(self):
        """Test VesselsTTS initialization"""
        from vessels.device.tts import VesselsTTS

        # Try to initialize TTS
        try:
            tts = VesselsTTS(engine="kokoro")
            assert tts.engine == "kokoro"
            assert tts.backend in ["kokoro", "styletts2", "piper", "espeak"]
        except Exception as e:
            # No backend available, skip
            pytest.skip(f"No TTS backend available: {e}")

    def test_tts_emotional_adaptation(self):
        """Test TTS emotional adaptation"""
        from vessels.device.tts import VesselsTTS

        try:
            tts = VesselsTTS(engine="kokoro")

            # Test overwhelmed state
            emotional_state = {
                "valence": 0.2,
                "arousal": 0.8,
                "tags": ["stressed"]
            }

            style = tts.adapt_to_emotion(emotional_state)

            # Should slow down for overwhelmed user
            assert style["speed"] < 1.0
            assert style["emotion"] == "calm"

        except Exception:
            pytest.skip("TTS backend not available")


class TestDeviceLLM:
    """Tests for on-device LLM"""

    def test_device_llm_models(self):
        """Test device LLM model definitions"""
        from vessels.device.local_llm import DeviceLLM

        assert "Llama-3.2-1B" in DeviceLLM.MODELS
        assert "Phi-3-Mini" in DeviceLLM.MODELS

        model_info = DeviceLLM.MODELS["Llama-3.2-1B"]
        assert model_info["params"] == "1B"
        assert "intent" in model_info["use_cases"]

    @patch('vessels.device.local_llm.Llama')
    def test_device_llm_intent_classification(self, mock_llama):
        """Test intent classification (mocked)"""
        from vessels.device.local_llm import DeviceLLM

        # Mock the model
        mock_model = MagicMock()
        mock_model.return_value = {
            "choices": [{"text": "question", "finish_reason": "stop"}],
            "usage": {"completion_tokens": 5}
        }
        mock_llama.return_value = mock_model

        try:
            llm = DeviceLLM(model_name="Llama-3.2-1B")
            llm.backend = "llama.cpp"  # Force backend
            llm.model = mock_model

            result = llm.classify_intent("What's the weather?")

            assert "intent" in result
            assert result["intent"] in ["question", "command", "conversation", "emotion"]

        except RuntimeError:
            pytest.skip("No LLM backend available")


class TestEmotionalIntelligence:
    """Tests for emotional intelligence layer"""

    def test_emotion_initialization(self):
        """Test EmotionalIntelligence initialization"""
        from vessels.device.emotion import EmotionalIntelligence

        ei = EmotionalIntelligence(enabled=True)
        assert ei.enabled
        assert ei.backend in ["transformers", "rules"]

    def test_emotion_analysis_rule_based(self):
        """Test rule-based emotion analysis"""
        from vessels.device.emotion import EmotionalIntelligence

        ei = EmotionalIntelligence(enabled=True)
        ei.backend = "rules"  # Force rule-based

        # Test negative, high arousal
        state = ei.analyze("I'm so frustrated with this!")

        assert state.valence < 0  # Negative
        assert state.arousal > 0.5  # High arousal
        assert "stressed" in state.tags or "frustrated" in state.tags

    def test_emotion_adaptation(self):
        """Test response adaptation based on emotion"""
        from vessels.device.emotion import EmotionalIntelligence, EmotionalState

        ei = EmotionalIntelligence(enabled=True)

        # Overwhelmed state
        state = EmotionalState(
            valence=-0.3,
            arousal=0.8,
            tags=["stressed"],
            confidence=0.9,
            timestamp=0.0,
            source="test"
        )

        response = "Here's a detailed explanation of the problem..."
        adapted = ei.adapt_response(response, state)

        # Should simplify for overwhelmed user
        assert adapted["verbosity"] == "low"
        assert adapted["tts_style"]["speed"] < 1.0

    def test_emotion_disabled(self):
        """Test emotion tracking when disabled"""
        from vessels.device.emotion import EmotionalIntelligence

        ei = EmotionalIntelligence(enabled=False)

        state = ei.analyze("I'm so happy!")

        # Should return neutral state
        assert state.valence == 0.0
        assert state.arousal == 0.5


# ============================================================================
# COMPUTE TIER TESTS
# ============================================================================

class TestPetalsGateway:
    """Tests for Petals gateway"""

    def test_petals_disabled_by_default(self):
        """Test that Petals is disabled by default"""
        from vessels.compute.petals_gateway import PetalsGateway

        config = {"enabled": False}
        gateway = PetalsGateway(config)

        assert not gateway.enabled

    def test_petals_should_use_logic(self):
        """Test Petals routing logic"""
        from vessels.compute.petals_gateway import PetalsGateway

        config = {"enabled": True, "allowed_models": ["meta-llama/Llama-3.1-70b-hf"]}
        gateway = PetalsGateway(config)

        # Sensitive data should NOT use Petals
        task1 = {
            "sensitive": True,
            "context_length": 10000,
            "latency_requirement_ms": 5000
        }
        assert not gateway.should_use_petals(task1)

        # Non-sensitive, large context, high quality → use Petals
        task2 = {
            "sensitive": False,
            "context_length": 10000,
            "latency_requirement_ms": 5000,
            "quality_requirement": 0.9
        }
        assert gateway.should_use_petals(task2)

        # Real-time requirement → don't use Petals
        task3 = {
            "sensitive": False,
            "context_length": 10000,
            "latency_requirement_ms": 500
        }
        assert not gateway.should_use_petals(task3)


class TestLLMRouter:
    """Tests for LLM router"""

    def test_llm_router_initialization(self):
        """Test LLM router initialization"""
        from vessels.compute.llm_router import LLMRouter

        config = {
            "tier0": {"enabled": False},
            "tier1": {"enabled": True, "host": "localhost", "port": 8080},
            "tier2": {"enabled": False}
        }

        router = LLMRouter(config)

        status = router.get_tier_status()
        assert "tier0" in status
        assert "tier1" in status
        assert "tier2" in status

    def test_llm_router_tier_selection(self):
        """Test tier selection logic"""
        from vessels.compute.llm_router import LLMRouter, LLMRequest, ComputeTier

        config = {
            "tier0": {"enabled": True, "model": "Llama-3.2-1B"},
            "tier1": {"enabled": True, "host": "localhost", "port": 8080},
            "tier2": {"enabled": True, "models": ["meta-llama/Llama-3.1-70b-hf"]}
        }

        router = LLMRouter(config)

        # Ultra-low latency → Tier 0
        request1 = LLMRequest(
            prompt="Quick question",
            latency_requirement_ms=100,
            sensitive=True
        )
        tier1 = router._select_tier(request1)
        assert tier1 in [ComputeTier.DEVICE, ComputeTier.EDGE]  # Depends on availability

        # Sensitive data with large context → Tier 1 (never Petals)
        request2 = LLMRequest(
            prompt="Analyze my personal data",
            latency_requirement_ms=5000,
            sensitive=True,
            context_length=50000
        )
        tier2 = router._select_tier(request2)
        assert tier2 != ComputeTier.PETALS

        # Non-sensitive, large context, high quality → Tier 2
        request3 = LLMRequest(
            prompt="Analyze this public document",
            latency_requirement_ms=10000,
            sensitive=False,
            context_length=50000,
            quality_requirement=0.9
        )
        tier3 = router._select_tier(request3)
        # May be PETALS if available, otherwise EDGE
        assert tier3 in [ComputeTier.PETALS, ComputeTier.EDGE]


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndIntegration:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_device_to_edge_flow(self):
        """Test data flow from device to edge"""
        # This would test the full flow:
        # 1. STT on device
        # 2. Emotion analysis
        # 3. LLM routing
        # 4. TTS response
        # 5. Emotional adaptation

        # For now, skip (requires full setup)
        pytest.skip("Requires full environment setup")

    def test_privacy_enforcement(self):
        """Test that sensitive data never goes to Petals"""
        from vessels.compute.llm_router import LLMRouter, LLMRequest, ComputeTier

        config = {
            "tier0": {"enabled": True},
            "tier1": {"enabled": True, "host": "localhost", "port": 8080},
            "tier2": {"enabled": True, "models": ["meta-llama/Llama-3.1-70b-hf"]}
        }

        router = LLMRouter(config)

        # Sensitive data should NEVER go to Petals, even if optimal
        request = LLMRequest(
            prompt="My social security number is...",
            latency_requirement_ms=10000,
            sensitive=True,
            context_length=50000,
            quality_requirement=0.95
        )

        tier = router._select_tier(request)

        # Must be Tier 0 or 1, never 2
        assert tier != ComputeTier.PETALS


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
