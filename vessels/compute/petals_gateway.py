"""
Petals Gateway for Distributed Large Model Inference

Provides access to very large open models (70B-405B params) via decentralized
volunteer GPU network. Optional and disabled by default.

IMPORTANT PRIVACY NOTES:
- Only use for NON-SENSITIVE, sanitized content
- All prompts are automatically sanitized before transmission
- Data goes to distributed compute nodes (not your hardware)
- Latency: 2-10 seconds typical
- Use only when edge nodes insufficient
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PetalsResult:
    """Result from Petals inference"""
    text: str
    tokens: int
    latency_ms: int
    model: str
    sanitized: bool
    error: Optional[str] = None


class PetalsGateway:
    """
    Gateway to Petals distributed inference network

    Petals allows running large open models across volunteer GPUs:
    - Llama 3.1 (70B, 405B)
    - Mixtral 8x7B
    - Falcon 180B
    - BLOOM 176B
    """

    SUPPORTED_MODELS = {
        "meta-llama/Llama-3.1-70b-hf": {
            "params": "70B",
            "context": 8192,
            "speed": "medium",
            "quality": "excellent"
        },
        "meta-llama/Llama-3.1-405b-hf": {
            "params": "405B",
            "context": 8192,
            "speed": "slow",
            "quality": "best"
        },
        "mistralai/Mixtral-8x7B-v0.1": {
            "params": "47B",
            "context": 32768,
            "speed": "fast",
            "quality": "excellent"
        },
        "tiiuae/falcon-180B": {
            "params": "180B",
            "context": 2048,
            "speed": "slow",
            "quality": "excellent"
        }
    }

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Petals gateway

        Args:
            config: {
                "enabled": bool,
                "allowed_models": List[str],
                "max_tokens": int,
                "timeout_seconds": int,
                "sanitize_data": bool
            }
        """
        self.enabled = config.get("enabled", False)
        self.allowed_models = config.get("allowed_models", [])
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout_seconds", 30)
        self.sanitize = config.get("sanitize_data", True)

        self.client = None
        self.stats = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "sanitized_prompts": 0
        }

        if self.enabled:
            self._initialize_client()
            logger.info(f"Petals gateway ENABLED with models: {self.allowed_models}")
        else:
            logger.info("Petals gateway DISABLED (privacy-first default)")

    def _initialize_client(self):
        """Initialize Petals client"""
        try:
            from petals import AutoDistributedModelForCausalLM

            self.client_class = AutoDistributedModelForCausalLM
            self.backend = "petals"
            logger.info("Petals client initialized")

        except ImportError:
            logger.warning(
                "Petals library not installed. "
                "Install with: pip install petals"
            )
            self.client_class = None
            self.backend = None

    def generate(
        self,
        prompt: str,
        model_name: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None
    ) -> PetalsResult:
        """
        Generate text using Petals network

        Args:
            prompt: Input prompt (will be sanitized)
            model_name: Model identifier
            max_tokens: Max tokens to generate
            temperature: Sampling temperature
            stop_sequences: Stop generation on these strings

        Returns:
            PetalsResult with generated text and metadata
        """
        self.stats["total_requests"] += 1

        # Check if enabled
        if not self.enabled:
            return PetalsResult(
                text="",
                tokens=0,
                latency_ms=0,
                model=model_name,
                sanitized=False,
                error="Petals gateway is disabled"
            )

        # Check if model is allowed
        if model_name not in self.allowed_models:
            logger.warning(f"Model {model_name} not in allowed list")
            return PetalsResult(
                text="",
                tokens=0,
                latency_ms=0,
                model=model_name,
                sanitized=False,
                error=f"Model {model_name} not allowed"
            )

        # Check if client available
        if not self.client_class:
            return PetalsResult(
                text="",
                tokens=0,
                latency_ms=0,
                model=model_name,
                sanitized=False,
                error="Petals client not available"
            )

        # Sanitize prompt
        sanitized_prompt = prompt
        was_sanitized = False

        if self.sanitize:
            from ..communication.sanitizer import DataSanitizer
            sanitizer = DataSanitizer()
            sanitized_prompt = sanitizer.sanitize_for_petals(prompt)
            was_sanitized = (sanitized_prompt != prompt)

            if was_sanitized:
                self.stats["sanitized_prompts"] += 1
                logger.debug("Prompt sanitized before sending to Petals")

        # Generate
        start_time = time.time()

        try:
            # Load model (cached after first use)
            model = self.client_class.from_pretrained(model_name)

            # Tokenize
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            inputs = tokenizer(sanitized_prompt, return_tensors="pt")

            # Generate
            max_new_tokens = min(
                max_tokens or 512,
                self.max_tokens
            )

            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                timeout=self.timeout
            )

            # Decode
            generated = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove prompt from output
            if generated.startswith(sanitized_prompt):
                generated = generated[len(sanitized_prompt):].strip()

            latency_ms = int((time.time() - start_time) * 1000)

            self.stats["successful"] += 1

            return PetalsResult(
                text=generated,
                tokens=len(outputs[0]) - len(inputs["input_ids"][0]),
                latency_ms=latency_ms,
                model=model_name,
                sanitized=was_sanitized,
                error=None
            )

        except TimeoutError:
            logger.error("Petals request timed out")
            self.stats["failed"] += 1

            return PetalsResult(
                text="",
                tokens=0,
                latency_ms=int((time.time() - start_time) * 1000),
                model=model_name,
                sanitized=was_sanitized,
                error="Request timed out"
            )

        except Exception as e:
            logger.error(f"Petals generation failed: {e}")
            self.stats["failed"] += 1

            return PetalsResult(
                text="",
                tokens=0,
                latency_ms=int((time.time() - start_time) * 1000),
                model=model_name,
                sanitized=was_sanitized,
                error=str(e)
            )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> PetalsResult:
        """
        Chat-style generation (formats messages as prompt)

        Args:
            messages: [{"role": "user"/"assistant", "content": str}]
            model_name: Model identifier
            max_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            PetalsResult with response
        """
        # Format messages as prompt
        prompt = self._format_chat_prompt(messages)

        # Generate
        return self.generate(
            prompt=prompt,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature
        )

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format chat messages as prompt"""
        prompt_parts = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                prompt_parts.append(f"System: {content}\n")
            elif role == "user":
                prompt_parts.append(f"User: {content}\n")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}\n")

        prompt_parts.append("Assistant:")

        return "\n".join(prompt_parts)

    def should_use_petals(self, task: Dict[str, Any]) -> bool:
        """
        Decide if task should go to Petals

        Args:
            task: {
                "sensitive": bool,
                "context_length": int,
                "latency_requirement_ms": int,
                "quality_requirement": float
            }

        Returns:
            True if Petals is appropriate
        """
        if not self.enabled:
            return False

        # Must be non-sensitive
        if task.get("sensitive", True):
            logger.debug("Task marked sensitive, not using Petals")
            return False

        # Must benefit from large context
        if task.get("context_length", 0) < 8192:
            logger.debug("Context too small for Petals, use edge node")
            return False

        # Must not be real-time
        if task.get("latency_requirement_ms", 0) < 2000:
            logger.debug("Latency requirement too strict for Petals")
            return False

        # Must need high quality (large model)
        if task.get("quality_requirement", 0) < 0.8:
            logger.debug("Quality requirement not high enough for Petals overhead")
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get Petals gateway statistics"""
        stats = self.stats.copy()

        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful"] / stats["total_requests"]
            stats["sanitization_rate"] = stats["sanitized_prompts"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["sanitization_rate"] = 0.0

        return stats

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a model"""
        return self.SUPPORTED_MODELS.get(model_name)

    def list_available_models(self) -> List[str]:
        """List all available Petals models"""
        return list(self.SUPPORTED_MODELS.keys())


def create_petals_gateway(config: Dict[str, Any]) -> PetalsGateway:
    """
    Factory function to create Petals gateway from config

    Args:
        config: {
            "enabled": bool (default False),
            "allowed_models": List[str],
            "max_tokens": int (default 4096),
            "timeout_seconds": int (default 30),
            "sanitize_data": bool (default True)
        }

    Returns:
        Configured PetalsGateway instance
    """
    return PetalsGateway(config)


def example_usage():
    """Example usage of PetalsGateway"""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Configure Petals (disabled by default)
    config = {
        "enabled": True,
        "allowed_models": [
            "meta-llama/Llama-3.1-70b-hf",
            "mistralai/Mixtral-8x7B-v0.1"
        ],
        "max_tokens": 4096,
        "timeout_seconds": 30,
        "sanitize_data": True
    }

    gateway = create_petals_gateway(config)

    # Example 1: Should we use Petals for this task?
    task = {
        "sensitive": False,
        "context_length": 10000,
        "latency_requirement_ms": 5000,
        "quality_requirement": 0.9
    }

    if gateway.should_use_petals(task):
        print("Using Petals for this task")

        # Generate text
        result = gateway.generate(
            prompt="Analyze the following policy document and summarize the key points...",
            model_name="meta-llama/Llama-3.1-70b-hf",
            max_tokens=500
        )

        if result.error:
            print(f"Error: {result.error}")
        else:
            print(f"Generated {result.tokens} tokens in {result.latency_ms}ms")
            print(f"Sanitized: {result.sanitized}")
            print(f"Response: {result.text[:200]}...")

    # Get stats
    stats = gateway.get_stats()
    print(f"\nStats: {stats}")


if __name__ == "__main__":
    example_usage()
