"""
LLM Service for Vessels Agents

Provides a unified interface for LLM calls across the Vessels platform.
Handles:
- Tier routing (device → edge → cloud)
- Fallback on failure
- Response parsing
- Cost/latency optimization

REQUIRES AgentZeroCore - all LLM operations are coordinated through A0.
"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agent_zero_core import AgentZeroCore

logger = logging.getLogger(__name__)


class LLMService:
    """
    Unified LLM service for agents.

    Provides both sync and async interfaces for LLM calls,
    routing through the appropriate compute tier.

    REQUIRES AgentZeroCore - all LLM operations are coordinated through A0.
    """

    def __init__(
        self,
        agent_zero: "AgentZeroCore",
        tier_config=None,
        prefer_local: bool = True,
        api_key: Optional[str] = None
    ):
        """
        Initialize LLM service.

        Args:
            agent_zero: AgentZeroCore instance (REQUIRED)
            tier_config: TierConfig from vessel (optional)
            prefer_local: Prefer local/edge tiers when possible
            api_key: API key for cloud tier (defaults to env var)
        """
        if agent_zero is None:
            raise ValueError("LLMService requires AgentZeroCore")

        self.agent_zero = agent_zero
        self.tier_config = tier_config
        self.prefer_local = prefer_local
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")

        self._router = None
        self._anthropic_client = None
        self._openai_client = None

        # Register with A0
        self.agent_zero.llm_service = self
        logger.info("LLMService initialized with A0")

    def call(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Synchronous LLM call - primary interface for Birth Agent.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        # Try cloud APIs first if available (most capable for persona generation)
        if self.api_key:
            # Try Anthropic first
            response = self._call_anthropic(prompt, max_tokens, temperature)
            if response:
                return response

            # Fall back to OpenAI
            response = self._call_openai(prompt, max_tokens, temperature)
            if response:
                return response

        # Try local tier if available
        response = self._call_local(prompt, max_tokens, temperature)
        if response:
            return response

        # Last resort: edge tier
        response = self._call_edge(prompt, max_tokens, temperature)
        if response:
            return response

        raise RuntimeError("No LLM backend available")

    def _call_anthropic(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call Anthropic Claude API."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return None

        try:
            if self._anthropic_client is None:
                try:
                    import anthropic
                    self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                except ImportError:
                    logger.debug("anthropic package not installed")
                    return None

            message = self._anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast, cheap for birth conversations
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )

            return message.content[0].text

        except Exception as e:
            logger.warning(f"Anthropic call failed: {e}")
            return None

    def _call_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call OpenAI API."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            if self._openai_client is None:
                try:
                    import openai
                    self._openai_client = openai.OpenAI(api_key=api_key)
                except ImportError:
                    logger.debug("openai package not installed")
                    return None

            response = self._openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Fast, cheap for birth conversations
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")
            return None

    def _call_local(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call local device LLM."""
        try:
            from vessels.device.local_llm import DeviceLLM

            # Check if tier0 is enabled in config
            if self.tier_config and not self.tier_config.tier0_enabled:
                return None

            llm = DeviceLLM()
            result = llm.generate(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return result.text

        except Exception as e:
            logger.debug(f"Local LLM call failed: {e}")
            return None

    def _call_edge(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call edge tier LLM."""
        try:
            # Check if tier1 is enabled in config
            if self.tier_config and not self.tier_config.tier1_enabled:
                return None

            # Edge tier typically exposed via HTTP
            import requests

            host = "localhost"
            port = 8080

            if self.tier_config:
                host = self.tier_config.tier1_host
                port = self.tier_config.tier1_port

            response = requests.post(
                f"http://{host}:{port}/v1/completions",
                json={
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
                timeout=30
            )

            if response.ok:
                return response.json().get("choices", [{}])[0].get("text", "")

        except Exception as e:
            logger.debug(f"Edge LLM call failed: {e}")

        return None

    async def call_async(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Async LLM call.

        Runs sync call in executor to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.call(prompt, max_tokens, temperature)
        )

    def get_callable(self) -> Callable[[str], str]:
        """
        Get a simple callable for injection into other components.

        Returns:
            Function that takes prompt string and returns response string
        """
        return lambda prompt: self.call(prompt)


def create_llm_service(
    agent_zero: "AgentZeroCore",
    tier_config=None,
    prefer_local: bool = True
) -> LLMService:
    """
    Factory function to create LLM service.

    Args:
        agent_zero: AgentZeroCore instance (REQUIRED)
        tier_config: Optional TierConfig from vessel
        prefer_local: Prefer local tiers

    Returns:
        Configured LLMService instance
    """
    return LLMService(agent_zero=agent_zero, tier_config=tier_config, prefer_local=prefer_local)


def get_llm_callable(agent_zero: "AgentZeroCore", tier_config=None) -> Callable[[str], str]:
    """
    Get a simple LLM callable for injection into Birth Agent etc.

    Args:
        agent_zero: AgentZeroCore instance (REQUIRED)
        tier_config: Optional TierConfig

    Returns:
        Function that takes prompt and returns response
    """
    service = create_llm_service(agent_zero=agent_zero, tier_config=tier_config)
    return service.get_callable()
