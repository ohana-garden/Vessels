"""
Speech-to-Text via whisper.cpp

On-device speech recognition with no cloud dependencies.
Supports multiple languages and model sizes for different latency/accuracy tradeoffs.

Dependencies:
- whisper.cpp (compiled binary or Python bindings)
- pyaudio (for microphone input)
"""

import time
import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription"""
    text: str
    confidence: float
    language: str
    latency_ms: int
    model: str
    streaming: bool


class WhisperSTT:
    """
    On-device speech recognition via whisper.cpp

    Provides both streaming (real-time) and batch (file) transcription.
    """

    MODELS = {
        "tiny.en": {"params": "39M", "size_mb": 75, "speed_factor": 10, "accuracy": "good"},
        "base.en": {"params": "74M", "size_mb": 140, "speed_factor": 6, "accuracy": "better"},
        "small.en": {"params": "244M", "size_mb": 460, "speed_factor": 3, "accuracy": "excellent"},
        "medium.en": {"params": "769M", "size_mb": 1500, "speed_factor": 1.5, "accuracy": "near-perfect"},
    }

    def __init__(
        self,
        model_name: str = "small.en",
        model_path: Optional[str] = None,
        language: str = "en",
        device: str = "cpu"
    ):
        """
        Initialize Whisper STT

        Args:
            model_name: Model size (tiny.en, base.en, small.en, medium.en)
            model_path: Path to model file (auto-downloaded if None)
            language: Language code (en, es, fr, etc.)
            device: Device to run on (cpu, cuda, metal)
        """
        self.model_name = model_name
        self.language = language
        self.device = device

        # Find or download model
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self._get_model_path(model_name)

        # Initialize model
        self.model = None
        self._load_model()

        logger.info(f"WhisperSTT initialized: {model_name} on {device}")

    def _get_model_path(self, model_name: str) -> Path:
        """
        Get path to Whisper model, downloading if necessary

        Models stored in: ~/.cache/vessels/whisper/
        """
        cache_dir = Path.home() / ".cache" / "vessels" / "whisper"
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_file = cache_dir / f"ggml-{model_name}.bin"

        if not model_file.exists():
            logger.info(f"Model {model_name} not found, downloading...")
            self._download_model(model_name, model_file)

        return model_file

    def _download_model(self, model_name: str, output_path: Path):
        """
        Download Whisper model from Hugging Face

        Models available at: https://huggingface.co/ggerganov/whisper.cpp
        """
        try:
            import urllib.request

            base_url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"
            url = f"{base_url}/ggml-{model_name}.bin"

            logger.info(f"Downloading from {url}...")

            # Show progress
            def report_progress(block_num, block_size, total_size):
                downloaded = block_num * block_size
                percent = min(100, downloaded * 100 / total_size)
                if block_num % 100 == 0:
                    logger.info(f"Download progress: {percent:.1f}%")

            urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
            logger.info(f"Model downloaded to {output_path}")

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            raise RuntimeError(f"Could not download Whisper model: {e}")

    def _load_model(self):
        """
        Load Whisper model

        Try multiple backends in order:
        1. faster-whisper (most efficient)
        2. whisper.cpp Python bindings
        3. openai-whisper (fallback)
        """
        # Try faster-whisper first
        try:
            from faster_whisper import WhisperModel

            self.model = WhisperModel(
                str(self.model_path).replace("ggml-", "").replace(".bin", ""),
                device=self.device,
                compute_type="int8" if self.device == "cpu" else "float16"
            )
            self.backend = "faster-whisper"
            logger.info("Loaded model with faster-whisper backend")
            return
        except ImportError:
            logger.debug("faster-whisper not available")

        # Try whisper.cpp bindings
        try:
            from whispercpp import Whisper

            self.model = Whisper(str(self.model_path))
            self.backend = "whispercpp"
            logger.info("Loaded model with whisper.cpp backend")
            return
        except ImportError:
            logger.debug("whisper.cpp bindings not available")

        # Fallback to openai-whisper
        try:
            import whisper

            self.model = whisper.load_model(
                self.model_name.replace(".en", ""),
                device=self.device
            )
            self.backend = "openai-whisper"
            logger.info("Loaded model with openai-whisper backend")
            return
        except ImportError:
            logger.error("No Whisper backend available")

        raise RuntimeError(
            "No Whisper backend found. Install one of: "
            "faster-whisper, whisper.cpp, openai-whisper"
        )

    def transcribe(
        self,
        audio: Any,
        streaming: bool = False,
        temperature: float = 0.0,
        beam_size: int = 5
    ) -> TranscriptionResult:
        """
        Transcribe audio to text

        Args:
            audio: Audio data (file path, bytes, or numpy array)
            streaming: True for real-time (faster, less accurate)
            temperature: Sampling temperature (0 = deterministic)
            beam_size: Beam search width (1 = greedy, 5 = better quality)

        Returns:
            TranscriptionResult with text and metadata
        """
        if self.model is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        try:
            if self.backend == "faster-whisper":
                result = self._transcribe_faster_whisper(audio, streaming, beam_size)
            elif self.backend == "whispercpp":
                result = self._transcribe_whispercpp(audio)
            elif self.backend == "openai-whisper":
                result = self._transcribe_openai_whisper(audio, temperature)
            else:
                raise RuntimeError(f"Unknown backend: {self.backend}")

            latency_ms = int((time.time() - start_time) * 1000)

            return TranscriptionResult(
                text=result["text"].strip(),
                confidence=result.get("confidence", 0.9),
                language=result.get("language", self.language),
                latency_ms=latency_ms,
                model=self.model_name,
                streaming=streaming
            )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _transcribe_faster_whisper(self, audio, streaming: bool, beam_size: int) -> Dict:
        """Transcribe with faster-whisper backend"""
        segments, info = self.model.transcribe(
            audio,
            language=self.language,
            beam_size=beam_size if not streaming else 1,
            vad_filter=True,  # Voice activity detection
            vad_parameters={"threshold": 0.5}
        )

        text = " ".join([seg.text for seg in segments])

        return {
            "text": text,
            "language": info.language,
            "confidence": info.language_probability
        }

    def _transcribe_whispercpp(self, audio) -> Dict:
        """Transcribe with whisper.cpp backend"""
        result = self.model.transcribe(audio)

        return {
            "text": result["text"],
            "language": self.language,
            "confidence": 0.9  # whispercpp doesn't provide confidence
        }

    def _transcribe_openai_whisper(self, audio, temperature: float) -> Dict:
        """Transcribe with OpenAI Whisper backend"""
        result = self.model.transcribe(
            audio,
            language=self.language,
            temperature=temperature,
            fp16=(self.device != "cpu")
        )

        return {
            "text": result["text"],
            "language": result.get("language", self.language),
            "confidence": 0.9  # Estimate
        }

    def transcribe_file(self, file_path: str) -> TranscriptionResult:
        """
        Transcribe audio file

        Supports: wav, mp3, m4a, flac, ogg
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        logger.info(f"Transcribing file: {file_path}")
        return self.transcribe(file_path, streaming=False, beam_size=5)

    def transcribe_stream(self, audio_chunks: List[bytes]) -> List[str]:
        """
        Transcribe streaming audio in real-time

        Args:
            audio_chunks: List of audio chunks (16kHz, mono, PCM)

        Returns:
            List of transcribed text segments
        """
        results = []

        for chunk in audio_chunks:
            result = self.transcribe(chunk, streaming=True, beam_size=1)
            if result.text:
                results.append(result.text)

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about loaded model"""
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "language": self.language,
            "device": self.device,
            "backend": self.backend,
            "specs": self.MODELS.get(self.model_name, {})
        }


def example_usage():
    """Example usage of WhisperSTT"""

    # Initialize with small model (recommended for most use cases)
    stt = WhisperSTT(model_name="small.en", device="cpu")

    # Transcribe audio file
    result = stt.transcribe_file("test_audio.wav")
    print(f"Transcription: {result.text}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Latency: {result.latency_ms}ms")

    # Get model info
    info = stt.get_model_info()
    print(f"Model: {info['model_name']} ({info['specs']['params']} params)")
    print(f"Backend: {info['backend']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
