"""
Emotional Intelligence Layer

Tracks and responds to user emotional state for adaptive interaction.
Runs entirely on-device for privacy.

NO DIAGNOSIS. NO LONG-TERM PROFILING (unless explicitly enabled).
Used only for real-time interaction adaptation.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EmotionalState:
    """User's current emotional state"""
    valence: float  # -1 (negative) to 1 (positive)
    arousal: float  # 0 (calm) to 1 (excited)
    tags: List[str]  # e.g., ["content", "focused", "overwhelmed"]
    confidence: float  # 0-1
    timestamp: float
    source: str  # "text", "prosody", "combined"


class EmotionalIntelligence:
    """
    Track and respond to user emotional state

    Privacy guarantees:
    - Emotional state NEVER leaves device
    - No long-term profiling by default (history only kept for session)
    - Can be disabled entirely
    - No diagnostic claims
    """

    # Emotion vocabulary (simplified, non-clinical)
    EMOTION_TAGS = {
        # Positive, high arousal
        "excited", "enthusiastic", "energized", "eager",
        # Positive, low arousal
        "content", "calm", "peaceful", "satisfied",
        # Negative, high arousal
        "stressed", "frustrated", "anxious", "overwhelmed",
        # Negative, low arousal
        "tired", "sad", "disappointed", "bored"
    }

    def __init__(
        self,
        enabled: bool = True,
        history_length: int = 10,
        model_path: Optional[str] = None
    ):
        """
        Initialize emotional intelligence layer

        Args:
            enabled: Whether emotion tracking is enabled
            history_length: Number of recent states to keep
            model_path: Path to emotion classifier model (optional)
        """
        self.enabled = enabled
        self.history = deque(maxlen=history_length)
        self.model = None

        if enabled:
            self._load_model(model_path)
            logger.info("Emotional intelligence layer enabled")
        else:
            logger.info("Emotional intelligence layer DISABLED")

    def _load_model(self, model_path: Optional[str]):
        """
        Load emotion classification model

        Tries multiple backends in order of preference
        """
        # Try to load a small emotion classifier
        try:
            # Option 1: Use a tiny fine-tuned model (e.g., on GoEmotions)
            from transformers import pipeline

            self.model = pipeline(
                "text-classification",
                model="bhadresh-savani/distilbert-base-uncased-emotion",
                device=-1,  # CPU
                top_k=3
            )
            self.backend = "transformers"
            logger.info("Loaded emotion model with transformers")
            return
        except ImportError:
            logger.debug("transformers not available")

        # Option 2: Use rule-based heuristics (fast, no ML)
        logger.info("Using rule-based emotion detection (no ML model)")
        self.model = None
        self.backend = "rules"

    def analyze(
        self,
        text: str,
        prosody: Optional[Dict[str, float]] = None,
        use_llm: bool = False
    ) -> EmotionalState:
        """
        Infer emotional state from text + optional prosody

        Args:
            text: User's text input
            prosody: Optional prosody features {
                "pitch_mean": float,
                "pitch_std": float,
                "energy_mean": float,
                "tempo": float  # words per second
            }
            use_llm: Whether to use on-device LLM for inference

        Returns:
            EmotionalState with valence, arousal, tags
        """
        if not self.enabled:
            return self._neutral_state()

        if not text:
            return self._neutral_state()

        # Combine text and prosody analysis
        if self.backend == "transformers":
            state = self._analyze_with_model(text, prosody)
        elif use_llm:
            state = self._analyze_with_llm(text)
        else:
            state = self._analyze_with_rules(text, prosody)

        # Store in history
        self.history.append(state)

        return state

    def _analyze_with_model(
        self,
        text: str,
        prosody: Optional[Dict[str, float]]
    ) -> EmotionalState:
        """Analyze with ML model (transformers)"""
        # Get emotion predictions
        predictions = self.model(text)[0]

        # Map predictions to valence/arousal space
        emotion_map = {
            "joy": (0.8, 0.7),
            "love": (0.9, 0.5),
            "surprise": (0.5, 0.9),
            "anger": (-0.7, 0.9),
            "sadness": (-0.8, 0.3),
            "fear": (-0.7, 0.8)
        }

        # Weighted average based on scores
        valence = 0.0
        arousal = 0.5
        total_score = 0.0

        for pred in predictions[:3]:  # Top 3
            emotion = pred["label"]
            score = pred["score"]

            if emotion in emotion_map:
                v, a = emotion_map[emotion]
                valence += v * score
                arousal += a * score
                total_score += score

        if total_score > 0:
            valence /= total_score
            arousal /= total_score

        # Adjust with prosody if available
        if prosody:
            arousal = self._adjust_arousal_with_prosody(arousal, prosody)

        # Get tags
        tags = [pred["label"] for pred in predictions[:2]]

        return EmotionalState(
            valence=valence,
            arousal=arousal,
            tags=tags,
            confidence=predictions[0]["score"],
            timestamp=time.time(),
            source="combined" if prosody else "text"
        )

    def _analyze_with_llm(self, text: str) -> EmotionalState:
        """Analyze with on-device LLM"""
        try:
            from .local_llm import DeviceLLM

            llm = DeviceLLM()
            result = llm.classify_emotion(text)

            return EmotionalState(
                valence=result["valence"],
                arousal=result["arousal"],
                tags=result.get("tags", []),
                confidence=result.get("confidence", 0.7),
                timestamp=time.time(),
                source="llm"
            )
        except Exception as e:
            logger.warning(f"LLM emotion analysis failed: {e}")
            return self._analyze_with_rules(text, None)

    def _analyze_with_rules(
        self,
        text: str,
        prosody: Optional[Dict[str, float]]
    ) -> EmotionalState:
        """
        Analyze with rule-based heuristics (fast, no ML)

        Simple pattern matching on keywords
        """
        text_lower = text.lower()

        # Positive keywords
        positive = sum([
            text_lower.count(word) for word in
            ["happy", "great", "good", "love", "awesome", "excellent", "wonderful", "excited"]
        ])

        # Negative keywords
        negative = sum([
            text_lower.count(word) for word in
            ["sad", "bad", "hate", "awful", "terrible", "frustrated", "angry", "stressed"]
        ])

        # High arousal keywords
        high_arousal = sum([
            text_lower.count(word) for word in
            ["excited", "stressed", "angry", "overwhelmed", "urgent", "rushed", "!"]
        ])

        # Compute valence
        if positive + negative > 0:
            valence = (positive - negative) / (positive + negative + 1)
        else:
            valence = 0.0

        # Compute arousal (baseline 0.5)
        arousal = 0.5
        if high_arousal > 0:
            arousal = min(1.0, 0.5 + high_arousal * 0.2)

        # Adjust with prosody
        if prosody:
            arousal = self._adjust_arousal_with_prosody(arousal, prosody)

        # Infer tags
        tags = []
        if valence > 0.3 and arousal > 0.6:
            tags.append("excited")
        elif valence > 0.3 and arousal < 0.4:
            tags.append("content")
        elif valence < -0.3 and arousal > 0.6:
            tags.append("stressed")
        elif valence < -0.3 and arousal < 0.4:
            tags.append("tired")

        return EmotionalState(
            valence=valence,
            arousal=arousal,
            tags=tags,
            confidence=0.6,  # Lower confidence for rules
            timestamp=time.time(),
            source="rules"
        )

    def _adjust_arousal_with_prosody(
        self,
        base_arousal: float,
        prosody: Dict[str, float]
    ) -> float:
        """Adjust arousal based on prosody features"""
        # High pitch variation + high energy = high arousal
        pitch_std = prosody.get("pitch_std", 0)
        energy = prosody.get("energy_mean", 0.5)
        tempo = prosody.get("tempo", 3.0)  # words per second

        prosody_arousal = (pitch_std + energy + (tempo / 5.0)) / 3.0
        prosody_arousal = np.clip(prosody_arousal, 0, 1)

        # Weighted average (60% text, 40% prosody)
        return 0.6 * base_arousal + 0.4 * prosody_arousal

    def _neutral_state(self) -> EmotionalState:
        """Return neutral emotional state"""
        return EmotionalState(
            valence=0.0,
            arousal=0.5,
            tags=["neutral"],
            confidence=1.0,
            timestamp=time.time(),
            source="default"
        )

    def adapt_response(
        self,
        response: str,
        state: Optional[EmotionalState] = None
    ) -> Dict[str, Any]:
        """
        Adapt response style based on emotional state

        Args:
            response: Original response text
            state: Emotional state (uses latest if None)

        Returns:
            {
                "text": str,  # Adapted text
                "tts_style": Dict,  # TTS parameters
                "verbosity": str  # "low", "medium", "high"
            }
        """
        if not self.enabled:
            return {
                "text": response,
                "tts_style": {"speed": 1.0, "emotion": "neutral"},
                "verbosity": "medium"
            }

        state = state or self.get_current_state()

        # User overwhelmed (high arousal, low valence)?
        # → Simplify, slow down, be calming
        if state.arousal > 0.7 and state.valence < 0.3:
            return {
                "text": self._simplify_language(response),
                "tts_style": {
                    "speed": 0.85,
                    "pitch": 0.95,
                    "energy": 0.7,
                    "emotion": "calm"
                },
                "verbosity": "low"
            }

        # User engaged and positive (high arousal, high valence)?
        # → Provide richer detail, match energy
        elif state.arousal > 0.5 and state.valence > 0.5:
            return {
                "text": self._expand_detail(response),
                "tts_style": {
                    "speed": 1.05,
                    "pitch": 1.0,
                    "energy": 1.1,
                    "emotion": "warm"
                },
                "verbosity": "high"
            }

        # User tired or sad (low arousal, low valence)?
        # → Be gentle, slower pace
        elif state.arousal < 0.3 and state.valence < 0.3:
            return {
                "text": response,
                "tts_style": {
                    "speed": 0.9,
                    "pitch": 0.95,
                    "energy": 0.8,
                    "emotion": "gentle"
                },
                "verbosity": "medium"
            }

        # Default: neutral
        else:
            return {
                "text": response,
                "tts_style": {
                    "speed": 1.0,
                    "pitch": 1.0,
                    "energy": 1.0,
                    "emotion": "neutral"
                },
                "verbosity": "medium"
            }

    def _simplify_language(self, text: str) -> str:
        """Simplify language for overwhelmed users"""
        # Split into sentences
        sentences = text.split(". ")

        # Keep only first 1-2 sentences
        simplified = ". ".join(sentences[:2])

        # Remove complex phrases
        simplified = simplified.replace("furthermore", "also")
        simplified = simplified.replace("additionally", "also")
        simplified = simplified.replace("nevertheless", "but")

        return simplified

    def _expand_detail(self, text: str) -> str:
        """Add more detail for engaged users"""
        # In production, this could:
        # - Add examples
        # - Include related information
        # - Provide context

        # For now, just return as-is
        return text

    def get_current_state(self) -> EmotionalState:
        """Get most recent emotional state"""
        if not self.history:
            return self._neutral_state()
        return self.history[-1]

    def get_trend(self) -> Dict[str, Any]:
        """
        Analyze emotional trend over recent history

        Returns:
            {
                "valence_trend": str ("improving", "stable", "declining"),
                "arousal_trend": str ("increasing", "stable", "decreasing"),
                "overall": str ("getting_better", "stable", "getting_worse")
            }
        """
        if len(self.history) < 3:
            return {
                "valence_trend": "stable",
                "arousal_trend": "stable",
                "overall": "stable"
            }

        recent = list(self.history)[-5:]

        # Compute trends
        valences = [s.valence for s in recent]
        arousals = [s.arousal for s in recent]

        valence_trend = np.mean(np.diff(valences))
        arousal_trend = np.mean(np.diff(arousals))

        return {
            "valence_trend": (
                "improving" if valence_trend > 0.1 else
                "declining" if valence_trend < -0.1 else
                "stable"
            ),
            "arousal_trend": (
                "increasing" if arousal_trend > 0.1 else
                "decreasing" if arousal_trend < -0.1 else
                "stable"
            ),
            "overall": (
                "getting_better" if valence_trend > 0.1 else
                "getting_worse" if valence_trend < -0.1 else
                "stable"
            )
        }

    def clear_history(self):
        """Clear emotional state history"""
        self.history.clear()
        logger.info("Emotional state history cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about emotion tracking"""
        if not self.history:
            return {"count": 0}

        recent = list(self.history)

        return {
            "count": len(recent),
            "avg_valence": np.mean([s.valence for s in recent]),
            "avg_arousal": np.mean([s.arousal for s in recent]),
            "most_common_tags": self._most_common_tags(recent),
            "trend": self.get_trend()
        }

    def _most_common_tags(self, states: List[EmotionalState]) -> List[str]:
        """Get most common emotion tags"""
        from collections import Counter

        all_tags = []
        for state in states:
            all_tags.extend(state.tags)

        if not all_tags:
            return []

        counter = Counter(all_tags)
        return [tag for tag, _ in counter.most_common(3)]


def example_usage():
    """Example usage of EmotionalIntelligence"""

    # Initialize
    ei = EmotionalIntelligence(enabled=True)

    # Analyze text
    state = ei.analyze("I'm so frustrated with this! Nothing is working!")
    print(f"State: valence={state.valence:.2f}, arousal={state.arousal:.2f}")
    print(f"Tags: {state.tags}")

    # Adapt response
    response = "Here's how to fix that issue. First, check the configuration..."
    adapted = ei.adapt_response(response, state)
    print(f"Adapted verbosity: {adapted['verbosity']}")
    print(f"TTS style: {adapted['tts_style']}")

    # Analyze positive state
    state2 = ei.analyze("This is amazing! I love how this works!")
    adapted2 = ei.adapt_response(response, state2)
    print(f"\nPositive state - verbosity: {adapted2['verbosity']}")

    # Get trend
    trend = ei.get_trend()
    print(f"\nTrend: {trend}")

    # Get stats
    stats = ei.get_stats()
    print(f"\nStats: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
