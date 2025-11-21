"""
Text-to-Speech via Piper and Kokoro

On-device neural text-to-speech with emotional adaptation.
Supports multiple voices and styles for natural, expressive speech.

Supported Engines:
- Kokoro-82M: High-quality Apache 2.0 licensed TTS (82M params)
- Piper: Fast ONNX-based TTS with many voice options (MIT licensed)
"""

import time
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SpeechResult:
    """Result from text-to-speech synthesis"""
    audio: np.ndarray  # Audio samples (float32, 22050Hz)
    sample_rate: int
    duration_ms: int
    text: str
    latency_ms: int
    voice: str
    style: Optional[Dict[str, float]] = None


class VesselsTTS:
    """
    On-device text-to-speech with emotional adaptation

    Supports both Kokoro (high quality) and Piper (fast, many voices)
    """

    ENGINES = {
        "kokoro": {
            "model": "hexgrad/Kokoro-82M",
            "license": "Apache 2.0",
            "quality": "excellent",
            "speed": "medium",
            "voices": ["default", "calm", "warm", "energetic"]
        },
        "piper": {
            "model": "piper-tts",
            "license": "MIT",
            "quality": "good",
            "speed": "fast",
            "voices": ["en_US-lessac-medium", "en_US-amy-medium", "en_GB-alan-medium"]
        }
    }

    def __init__(
        self,
        engine: str = "kokoro",
        voice: Optional[str] = None,
        device: str = "cpu",
        sample_rate: int = 22050
    ):
        """
        Initialize TTS engine

        Args:
            engine: "kokoro" or "piper"
            voice: Voice name (engine-specific)
            device: Device to run on (cpu, cuda)
            sample_rate: Audio sample rate in Hz
        """
        self.engine = engine
        self.voice = voice or self._get_default_voice(engine)
        self.device = device
        self.sample_rate = sample_rate

        self.model = None
        self._load_model()

        logger.info(f"VesselsTTS initialized: {engine} with voice '{self.voice}'")

    def _get_default_voice(self, engine: str) -> str:
        """Get default voice for engine"""
        voices = self.ENGINES[engine]["voices"]
        return voices[0] if voices else "default"

    def _load_model(self):
        """Load TTS model based on engine"""
        if self.engine == "kokoro":
            self._load_kokoro()
        elif self.engine == "piper":
            self._load_piper()
        else:
            raise ValueError(f"Unknown TTS engine: {self.engine}")

    def _load_kokoro(self):
        """Load Kokoro-82M model"""
        try:
            # Try to import kokoro TTS
            try:
                from kokoro import Kokoro
                self.model = Kokoro.from_pretrained("hexgrad/Kokoro-82M")
                self.backend = "kokoro"
                logger.info("Loaded Kokoro-82M model")
                return
            except ImportError:
                logger.warning("kokoro library not available, will use fallback")

            # Fallback: Try StyleTTS2 or other Apache 2.0 TTS
            try:
                from styletts2 import StyleTTS2
                self.model = StyleTTS2()
                self.backend = "styletts2"
                logger.info("Loaded StyleTTS2 as Kokoro alternative")
                return
            except ImportError:
                pass

            # Ultimate fallback: Use espeak (basic but always available)
            logger.warning("Kokoro not available, using espeak fallback")
            self.model = {"type": "espeak"}
            self.backend = "espeak"

        except Exception as e:
            logger.error(f"Failed to load Kokoro model: {e}")
            raise

    def _load_piper(self):
        """Load Piper TTS model"""
        try:
            # Try to import piper
            try:
                from piper import PiperVoice

                # Get voice model path
                voice_path = self._get_piper_voice_path(self.voice)

                self.model = PiperVoice.load(voice_path)
                self.backend = "piper"
                logger.info(f"Loaded Piper voice: {self.voice}")
                return
            except ImportError:
                logger.warning("piper-tts library not available")

            # Fallback to espeak
            logger.warning("Piper not available, using espeak fallback")
            self.model = {"type": "espeak"}
            self.backend = "espeak"

        except Exception as e:
            logger.error(f"Failed to load Piper model: {e}")
            raise

    def _get_piper_voice_path(self, voice_name: str) -> Path:
        """
        Get path to Piper voice model, downloading if necessary

        Models stored in: ~/.cache/vessels/piper/
        """
        cache_dir = Path.home() / ".cache" / "vessels" / "piper"
        cache_dir.mkdir(parents=True, exist_ok=True)

        voice_file = cache_dir / f"{voice_name}.onnx"

        if not voice_file.exists():
            logger.info(f"Voice {voice_name} not found, downloading...")
            self._download_piper_voice(voice_name, voice_file)

        return voice_file

    def _download_piper_voice(self, voice_name: str, output_path: Path):
        """Download Piper voice model"""
        try:
            import urllib.request

            base_url = "https://github.com/rhasspy/piper/releases/download/v1.2.0"
            url = f"{base_url}/{voice_name}.onnx"

            logger.info(f"Downloading Piper voice from {url}...")
            urllib.request.urlretrieve(url, output_path)
            logger.info(f"Voice downloaded to {output_path}")

        except Exception as e:
            logger.error(f"Failed to download voice: {e}")
            raise

    def speak(
        self,
        text: str,
        style: Optional[Dict[str, Any]] = None
    ) -> SpeechResult:
        """
        Synthesize speech from text

        Args:
            text: Text to synthesize
            style: {
                "speed": float (0.5-2.0, default 1.0),
                "pitch": float (0.5-2.0, default 1.0),
                "energy": float (0.5-2.0, default 1.0),
                "emotion": str ("neutral", "calm", "warm", "urgent")
            }

        Returns:
            SpeechResult with audio and metadata
        """
        if not text:
            raise ValueError("Text cannot be empty")

        style = style or {}
        start_time = time.time()

        try:
            if self.backend == "kokoro":
                audio = self._synthesize_kokoro(text, style)
            elif self.backend == "styletts2":
                audio = self._synthesize_styletts2(text, style)
            elif self.backend == "piper":
                audio = self._synthesize_piper(text, style)
            elif self.backend == "espeak":
                audio = self._synthesize_espeak(text, style)
            else:
                raise RuntimeError(f"Unknown backend: {self.backend}")

            latency_ms = int((time.time() - start_time) * 1000)
            duration_ms = int(len(audio) / self.sample_rate * 1000)

            return SpeechResult(
                audio=audio,
                sample_rate=self.sample_rate,
                duration_ms=duration_ms,
                text=text,
                latency_ms=latency_ms,
                voice=self.voice,
                style=style
            )

        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
            raise

    def _synthesize_kokoro(self, text: str, style: Dict) -> np.ndarray:
        """Synthesize with Kokoro model"""
        # Apply emotion/style if supported
        emotion = style.get("emotion", "neutral")
        if hasattr(self.model, "set_emotion"):
            self.model.set_emotion(emotion)

        # Generate audio
        audio = self.model.synthesize(
            text,
            speed=style.get("speed", 1.0),
            pitch=style.get("pitch", 1.0)
        )

        return audio.astype(np.float32)

    def _synthesize_styletts2(self, text: str, style: Dict) -> np.ndarray:
        """Synthesize with StyleTTS2"""
        audio = self.model.inference(
            text,
            alpha=style.get("speed", 1.0),
            beta=style.get("pitch", 1.0)
        )
        return audio.astype(np.float32)

    def _synthesize_piper(self, text: str, style: Dict) -> np.ndarray:
        """Synthesize with Piper"""
        # Piper uses length_scale for speed (inverse of speed)
        length_scale = 1.0 / style.get("speed", 1.0)

        audio = self.model.synthesize(
            text,
            length_scale=length_scale
        )

        return audio.astype(np.float32)

    def _synthesize_espeak(self, text: str, style: Dict) -> np.ndarray:
        """Synthesize with espeak (basic fallback)"""
        import subprocess
        import tempfile

        # Create temporary file for output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            # Calculate espeak parameters
            speed = int(175 * style.get("speed", 1.0))  # Default 175 wpm
            pitch = int(50 * style.get("pitch", 1.0))   # Default 50

            # Run espeak
            subprocess.run([
                "espeak",
                "-v", "en-us",
                "-s", str(speed),
                "-p", str(pitch),
                "-w", output_path,
                text
            ], check=True, capture_output=True)

            # Load audio
            import wave
            with wave.open(output_path, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

            return audio

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.remove(output_path)

    def adapt_to_emotion(self, emotional_state: Dict[str, float]) -> Dict[str, float]:
        """
        Adapt TTS style based on user's emotional state

        Args:
            emotional_state: {
                "valence": float (-1 to 1),
                "arousal": float (0 to 1),
                "tags": List[str]
            }

        Returns:
            TTS style parameters
        """
        valence = emotional_state.get("valence", 0.0)
        arousal = emotional_state.get("arousal", 0.5)

        # User overwhelmed (high arousal, low valence)? Slow down and calm
        if arousal > 0.7 and valence < 0.3:
            return {
                "speed": 0.85,
                "pitch": 0.95,
                "energy": 0.7,
                "emotion": "calm"
            }

        # User engaged and positive? Match their energy
        elif arousal > 0.5 and valence > 0.5:
            return {
                "speed": 1.05,
                "pitch": 1.0,
                "energy": 1.1,
                "emotion": "warm"
            }

        # User tired or sad? Gentle and slower
        elif arousal < 0.3 and valence < 0.3:
            return {
                "speed": 0.9,
                "pitch": 0.95,
                "energy": 0.8,
                "emotion": "gentle"
            }

        # User needs urgency?
        elif "urgent" in emotional_state.get("tags", []):
            return {
                "speed": 1.15,
                "pitch": 1.05,
                "energy": 1.2,
                "emotion": "urgent"
            }

        # Default: neutral
        else:
            return {
                "speed": 1.0,
                "pitch": 1.0,
                "energy": 1.0,
                "emotion": "neutral"
            }

    def save_audio(self, audio: np.ndarray, output_path: str):
        """Save audio to WAV file"""
        import wave

        # Convert to int16
        audio_int16 = (audio * 32767).astype(np.int16)

        with wave.open(output_path, 'wb') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(self.sample_rate)
            wav.writeframes(audio_int16.tobytes())

        logger.info(f"Audio saved to {output_path}")

    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about TTS engine"""
        return {
            "engine": self.engine,
            "backend": self.backend,
            "voice": self.voice,
            "sample_rate": self.sample_rate,
            "device": self.device,
            "specs": self.ENGINES.get(self.engine, {})
        }


def example_usage():
    """Example usage of VesselsTTS"""

    # Initialize with Kokoro (high quality)
    tts = VesselsTTS(engine="kokoro", device="cpu")

    # Synthesize speech
    result = tts.speak("Welcome to Vessels. How can I help you today?")
    print(f"Generated {result.duration_ms}ms of audio in {result.latency_ms}ms")

    # Save to file
    tts.save_audio(result.audio, "output.wav")

    # Adapt to emotional state
    emotional_state = {"valence": 0.2, "arousal": 0.8, "tags": []}
    style = tts.adapt_to_emotion(emotional_state)
    result = tts.speak("I understand you're feeling stressed. Let's take this slowly.", style=style)
    print(f"Style: {style}")

    # Get engine info
    info = tts.get_engine_info()
    print(f"Engine: {info['engine']} ({info['specs']['quality']})")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
