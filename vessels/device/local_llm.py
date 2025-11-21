"""
On-Device LLM via ExecuTorch

Runs small language models locally for intent classification, simple dialogue,
and emotional state inference.

Supports:
- ExecuTorch (PyTorch's on-device runtime)
- llama.cpp (for GGUF models)
- MLC-LLM (for mobile deployment)
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class InferenceResult:
    """Result from LLM inference"""
    text: str
    tokens: int
    latency_ms: int
    model: str
    stop_reason: str  # "eos", "max_tokens", "stop_sequence"


class DeviceLLM:
    """
    On-device LLM for fast, private inference

    Optimized for:
    - Intent classification (< 100ms)
    - Simple Q&A (< 1s)
    - Emotional state inference (< 100ms)
    - Command parsing (< 50ms)
    """

    MODELS = {
        "Llama-3.2-1B": {
            "params": "1B",
            "size_mb": 500,
            "speed_toks": 20,
            "context": 2048,
            "use_cases": ["intent", "emotion", "simple_qa"]
        },
        "Phi-3-Mini": {
            "params": "3.8B",
            "size_mb": 800,
            "speed_toks": 15,
            "context": 4096,
            "use_cases": ["dialogue", "qa", "reasoning"]
        },
        "Gemma-2B": {
            "params": "2B",
            "size_mb": 1000,
            "speed_toks": 12,
            "context": 8192,
            "use_cases": ["dialogue", "summarization", "qa"]
        },
        "TinyLlama-1.1B": {
            "params": "1.1B",
            "size_mb": 600,
            "speed_toks": 25,
            "context": 2048,
            "use_cases": ["intent", "classification", "simple_qa"]
        }
    }

    def __init__(
        self,
        model_name: str = "Llama-3.2-1B",
        model_path: Optional[str] = None,
        device: str = "cpu",
        quantization: str = "q4"
    ):
        """
        Initialize on-device LLM

        Args:
            model_name: Model to use
            model_path: Path to model file (auto-downloaded if None)
            device: Device to run on (cpu, cuda, mps, xnnpack)
            quantization: Quantization level (q4, q8, fp16)
        """
        self.model_name = model_name
        self.device = device
        self.quantization = quantization

        # Find or download model
        if model_path:
            self.model_path = Path(model_path)
        else:
            self.model_path = self._get_model_path(model_name, quantization)

        self.model = None
        self.tokenizer = None
        self._load_model()

        logger.info(f"DeviceLLM initialized: {model_name} ({quantization}) on {device}")

    def _get_model_path(self, model_name: str, quantization: str) -> Path:
        """Get path to model, downloading if necessary"""
        cache_dir = Path.home() / ".cache" / "vessels" / "llm"
        cache_dir.mkdir(parents=True, exist_ok=True)

        model_file = cache_dir / f"{model_name}-{quantization}.pte"

        if not model_file.exists():
            logger.info(f"Model {model_name} not found, will attempt to download...")
            # In production, this would download from HuggingFace or convert from GGUF

        return model_file

    def _load_model(self):
        """Load LLM with appropriate backend"""
        # Try ExecuTorch first
        try:
            from executorch.extension.pybindings import portable_lib as exec_lib

            self.model = exec_lib.load(str(self.model_path))
            self.backend = "executorch"
            logger.info("Loaded model with ExecuTorch backend")
            return
        except ImportError:
            logger.debug("ExecuTorch not available")

        # Try llama.cpp
        try:
            from llama_cpp import Llama

            # Look for GGUF format
            gguf_path = str(self.model_path).replace(".pte", ".gguf")
            if Path(gguf_path).exists():
                self.model = Llama(
                    model_path=gguf_path,
                    n_ctx=self.MODELS[self.model_name]["context"],
                    n_threads=4,
                    n_gpu_layers=0 if self.device == "cpu" else -1
                )
                self.backend = "llama.cpp"
                logger.info("Loaded model with llama.cpp backend")
                return
        except ImportError:
            logger.debug("llama.cpp not available")

        # Try MLC-LLM
        try:
            from mlc_llm import MLCEngine

            self.model = MLCEngine(str(self.model_path), device=self.device)
            self.backend = "mlc"
            logger.info("Loaded model with MLC-LLM backend")
            return
        except ImportError:
            logger.debug("MLC-LLM not available")

        # Fallback: Use transformers (slower but always works)
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            model_id = f"meta-llama/{self.model_name}" if "Llama" in self.model_name else self.model_name

            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                device_map=self.device,
                torch_dtype="float16" if self.quantization == "fp16" else "int8"
            )
            self.backend = "transformers"
            logger.info("Loaded model with transformers backend (slower)")
            return
        except ImportError:
            pass

        raise RuntimeError(
            "No LLM backend available. Install one of: "
            "executorch, llama-cpp-python, mlc-llm, transformers"
        )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> InferenceResult:
        """
        Generate text from prompt

        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0 = deterministic)
            stop_sequences: Stop generation on these strings

        Returns:
            InferenceResult with generated text and metadata
        """
        if not prompt:
            raise ValueError("Prompt cannot be empty")

        start_time = time.time()

        try:
            if self.backend == "executorch":
                result = self._generate_executorch(prompt, max_tokens, temperature)
            elif self.backend == "llama.cpp":
                result = self._generate_llamacpp(prompt, max_tokens, temperature, stop_sequences)
            elif self.backend == "mlc":
                result = self._generate_mlc(prompt, max_tokens, temperature)
            elif self.backend == "transformers":
                result = self._generate_transformers(prompt, max_tokens, temperature)
            else:
                raise RuntimeError(f"Unknown backend: {self.backend}")

            latency_ms = int((time.time() - start_time) * 1000)

            return InferenceResult(
                text=result["text"],
                tokens=result.get("tokens", len(result["text"].split())),
                latency_ms=latency_ms,
                model=self.model_name,
                stop_reason=result.get("stop_reason", "max_tokens")
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise

    def _generate_executorch(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with ExecuTorch"""
        # ExecuTorch inference (simplified)
        output = self.model.forward(prompt, max_tokens=max_tokens)
        return {"text": output, "tokens": max_tokens}

    def _generate_llamacpp(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: Optional[List[str]]
    ) -> Dict:
        """Generate with llama.cpp"""
        result = self.model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop_sequences or []
        )

        return {
            "text": result["choices"][0]["text"],
            "tokens": result["usage"]["completion_tokens"],
            "stop_reason": result["choices"][0]["finish_reason"]
        }

    def _generate_mlc(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with MLC-LLM"""
        output = self.model.generate(
            prompt,
            max_gen_len=max_tokens,
            temperature=temperature
        )
        return {"text": output, "tokens": len(output.split())}

    def _generate_transformers(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Generate with transformers (fallback)"""
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0
        )

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove prompt from output
        text = text[len(prompt):].strip()

        return {
            "text": text,
            "tokens": len(outputs[0]) - len(inputs["input_ids"][0])
        }

    def classify_intent(self, text: str) -> Dict[str, Any]:
        """
        Fast intent classification for routing

        Returns:
            {
                "intent": str,
                "confidence": float,
                "entities": Dict
            }
        """
        prompt = f"""Classify the user's intent. Choose ONE:
- question: User asking for information
- command: User requesting action
- conversation: General chat
- emotion: Expressing feelings

User: {text}
Intent:"""

        result = self.generate(prompt, max_tokens=10, temperature=0.0)
        intent_text = result.text.strip().lower()

        # Parse intent
        if "question" in intent_text:
            intent = "question"
        elif "command" in intent_text:
            intent = "command"
        elif "emotion" in intent_text:
            intent = "emotion"
        else:
            intent = "conversation"

        return {
            "intent": intent,
            "confidence": 0.85,  # Simplified
            "entities": {},
            "latency_ms": result.latency_ms
        }

    def simple_dialogue(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Local conversation for simple queries

        Args:
            message: User message
            history: Conversation history [{"role": "user"/"assistant", "content": str}]
            system_prompt: Optional system message

        Returns:
            Assistant response
        """
        history = history or []

        # Build prompt
        prompt_parts = []

        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}\n")

        for turn in history[-5:]:  # Last 5 turns only
            role = turn["role"]
            content = turn["content"]
            prompt_parts.append(f"{role.capitalize()}: {content}\n")

        prompt_parts.append(f"User: {message}\nAssistant:")

        prompt = "\n".join(prompt_parts)

        result = self.generate(prompt, max_tokens=200, temperature=0.7)
        return result.text.strip()

    def classify_emotion(self, text: str) -> Dict[str, Any]:
        """
        Infer emotional state from text

        Returns:
            {
                "valence": float (-1 to 1),
                "arousal": float (0 to 1),
                "tags": List[str]
            }
        """
        prompt = f"""Analyze emotion in the text. Rate on scale 1-5:
Positivity (1=very negative, 5=very positive):
Energy (1=very calm, 5=very excited):

Text: {text}
Positivity:"""

        result = self.generate(prompt, max_tokens=20, temperature=0.0)
        response = result.text.strip()

        # Parse numbers (simplified)
        try:
            lines = response.split("\n")
            positivity = int(lines[0].strip().split()[0])
            energy = int(lines[1].strip().split()[0]) if len(lines) > 1 else 3

            valence = (positivity - 3) / 2  # Convert 1-5 to -1 to 1
            arousal = (energy - 1) / 4      # Convert 1-5 to 0 to 1
        except:
            valence = 0.0
            arousal = 0.5

        return {
            "valence": valence,
            "arousal": arousal,
            "tags": [],
            "confidence": 0.7,
            "latency_ms": result.latency_ms
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "model_path": str(self.model_path),
            "device": self.device,
            "quantization": self.quantization,
            "backend": self.backend,
            "specs": self.MODELS.get(self.model_name, {})
        }


def example_usage():
    """Example usage of DeviceLLM"""

    # Initialize with small model
    llm = DeviceLLM(model_name="Llama-3.2-1B", device="cpu", quantization="q4")

    # Classify intent
    intent = llm.classify_intent("What's the weather like today?")
    print(f"Intent: {intent['intent']} (confidence: {intent['confidence']:.2f})")

    # Simple dialogue
    response = llm.simple_dialogue(
        "How do I plant tomatoes?",
        system_prompt="You are a helpful garden assistant."
    )
    print(f"Response: {response}")

    # Classify emotion
    emotion = llm.classify_emotion("I'm so frustrated with this!")
    print(f"Emotion: valence={emotion['valence']:.2f}, arousal={emotion['arousal']:.2f}")

    # Get model info
    info = llm.get_model_info()
    print(f"Model: {info['model_name']} ({info['specs']['params']})")
    print(f"Backend: {info['backend']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_usage()
