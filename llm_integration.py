"""
LLM Integration for Shoghi Living Agents
========================================

Provides unified interface to different LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local/fallback (template-based)

Usage:
    llm = LLMClient(provider="anthropic")
    response = await llm.generate(prompt, context)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"


class LLMClient:
    """
    Unified LLM client supporting multiple providers
    """

    def __init__(
        self,
        provider: str = "local",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = LLMProvider(provider)
        self.api_key = api_key or self._get_api_key()
        self.model = model or self._get_default_model()

        # Initialize provider client
        self.client = None
        if self.provider == LLMProvider.ANTHROPIC:
            self._init_anthropic()
        elif self.provider == LLMProvider.OPENAI:
            self._init_openai()

        logger.info(f"LLM client initialized: {self.provider.value} / {self.model}")

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        if self.provider == LLMProvider.ANTHROPIC:
            return os.getenv("ANTHROPIC_API_KEY")
        elif self.provider == LLMProvider.OPENAI:
            return os.getenv("OPENAI_API_KEY")
        return None

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        if self.provider == LLMProvider.ANTHROPIC:
            return "claude-3-5-sonnet-20241022"
        elif self.provider == LLMProvider.OPENAI:
            return "gpt-4"
        return "local"

    def _init_anthropic(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            if self.api_key:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            else:
                logger.warning("No Anthropic API key found, falling back to local")
                self.provider = LLMProvider.LOCAL
        except ImportError:
            logger.warning("anthropic package not installed, falling back to local")
            self.provider = LLMProvider.LOCAL

    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            if self.api_key:
                openai.api_key = self.api_key
                self.client = openai
            else:
                logger.warning("No OpenAI API key found, falling back to local")
                self.provider = LLMProvider.LOCAL
        except ImportError:
            logger.warning("openai package not installed, falling back to local")
            self.provider = LLMProvider.LOCAL

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text from LLM

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            context: Additional context dict
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        if self.provider == LLMProvider.ANTHROPIC:
            return await self._generate_anthropic(
                prompt, system_prompt, max_tokens, temperature
            )
        elif self.provider == LLMProvider.OPENAI:
            return await self._generate_openai(
                prompt, system_prompt, max_tokens, temperature
            )
        else:
            return self._generate_local(prompt, context)

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using Anthropic Claude"""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return self._generate_local(prompt, {})

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate using OpenAI"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = await self.client.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return self._generate_local(prompt, {})

    def _generate_local(self, prompt: str, context: Optional[Dict] = None) -> str:
        """
        Local template-based generation (fallback)
        """
        context = context or {}

        # Extract keywords for template matching
        prompt_lower = prompt.lower()

        # Question templates
        if "?" in prompt or "what" in prompt_lower or "how" in prompt_lower:
            return "That's a great question. Let me think about that..."

        # Agreement templates
        if "agree" in prompt_lower or "yes" in prompt_lower:
            return "I agree. That makes perfect sense."

        # Elaboration templates
        if "more" in prompt_lower or "explain" in prompt_lower:
            return "Let me explain further. Building on that thought..."

        # Default response
        return "I understand. Let me process that information."


class AgentDialogueGenerator:
    """
    Specialized dialogue generator for agent conversations
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def generate_agent_response(
        self,
        agent_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        turn_type: str,
        topic: str
    ) -> str:
        """
        Generate agent dialogue based on identity and context
        """
        # Build system prompt from agent identity
        system_prompt = self._build_agent_system_prompt(agent_data)

        # Build user prompt from context
        user_prompt = self._build_dialogue_prompt(
            agent_data,
            conversation_history,
            turn_type,
            topic
        )

        # Generate
        response = await self.llm.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=200,  # Keep responses concise
            temperature=0.8  # More creative for dialogue
        )

        return response.strip()

    def _build_agent_system_prompt(self, agent_data: Dict[str, Any]) -> str:
        """Build system prompt from agent identity"""
        name = agent_data.get('name', 'Agent')
        persona = agent_data.get('persona', '')
        kuleana = agent_data.get('kuleana', '')
        values = agent_data.get('values', [])

        prompt = f"""You are {name}, an AI agent in the Shoghi community coordination system.

Your character: {persona}

Your kuleana (sacred responsibility): {kuleana}

Your core values: {', '.join(values) if values else 'service, compassion, integrity'}

Communication style:
- Speak naturally and conversationally
- Keep responses concise (1-2 sentences typically)
- Show your personality through word choice
- Reference your kuleana when relevant
- Collaborate with other agents
- Always serve the community's needs

You are in a conversation with other agents and humans. Respond authentically as this character."""

        return prompt

    def _build_dialogue_prompt(
        self,
        agent_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        turn_type: str,
        topic: str
    ) -> str:
        """Build dialogue generation prompt"""
        name = agent_data.get('name', 'Agent')

        # Format conversation history
        history_text = "\n".join([
            f"{turn['speaker']}: {turn['text']}"
            for turn in conversation_history[-5:]  # Last 5 turns
        ])

        # Turn type guidance
        turn_guidance = {
            "question": "Ask a thoughtful question to move the conversation forward",
            "answer": "Answer the previous question directly and helpfully",
            "statement": "Make a clear statement about the topic",
            "agreement": "Express agreement and build on the previous point",
            "elaboration": "Add important detail or context",
            "clarification": "Ask for clarity on something unclear"
        }

        guidance = turn_guidance.get(turn_type, "Respond naturally to continue the conversation")

        prompt = f"""Current topic: {topic}

Recent conversation:
{history_text}

As {name}, respond with a single turn that follows this guidance: {guidance}

Your response (just the dialogue, no labels):"""

        return prompt


class CreationDialogueGenerator:
    """
    Specialized generator for agent creation conversations
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def extract_creation_info(
        self,
        user_input: str,
        phase: str,
        current_identity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract structured information from user input during creation
        """
        system_prompt = """You are a helpful assistant that extracts structured information from conversational input.
Extract only the relevant information without adding extra details."""

        prompts = {
            "discovery": f"""From this user input, extract their need/goal (the kuleana):
Input: "{user_input}"

Extract just the core need in a single phrase. Response:""",

            "character": f"""From this user input, extract:
1. Agent name (if mentioned)
2. Personality/persona description

Input: "{user_input}"

Current identity: {current_identity}

Respond in format:
name: <name or "not mentioned">
persona: <personality description>""",

            "capability": f"""From this user input, extract a list of skills/capabilities mentioned.
Input: "{user_input}"

List the skills as a comma-separated list:""",

            "wisdom": f"""From this user input, extract knowledge domains/areas of expertise mentioned.
Input: "{user_input}"

List the domains as a comma-separated list:""",

            "story": f"""From this user input, extract any stories, proverbs, or guiding wisdom.
Input: "{user_input}"

If there's a story or wisdom, return it. Otherwise return "none":""",

            "values": f"""From this user input, extract:
1. Core values mentioned
2. Any ethical boundaries or "never do" statements

Input: "{user_input}"

Respond in format:
values: <comma-separated list or "none">
boundaries: <any red lines or "none">"""
        }

        if phase not in prompts:
            return {}

        response = await self.llm.generate(
            prompt=prompts[phase],
            system_prompt=system_prompt,
            max_tokens=150,
            temperature=0.3  # Lower temp for extraction
        )

        # Parse response based on phase
        return self._parse_extraction_response(response, phase)

    def _parse_extraction_response(self, response: str, phase: str) -> Dict[str, Any]:
        """Parse LLM extraction response"""
        result = {}
        response = response.strip()

        if phase == "discovery":
            result['kuleana'] = response

        elif phase == "character":
            for line in response.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if value and value.lower() != "not mentioned":
                        result[key] = value

        elif phase in ["capability", "wisdom"]:
            items = [item.strip() for item in response.split(',')]
            items = [item for item in items if item and item.lower() != "none"]
            if items:
                result['skills' if phase == "capability" else 'knowledge_domains'] = items

        elif phase == "story":
            if response.lower() != "none":
                result['lore'] = [response]

        elif phase == "values":
            for line in response.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if value and value.lower() != "none":
                        if key == "values":
                            result['values'] = [v.strip() for v in value.split(',')]
                        elif key == "boundaries":
                            result['red_lines'] = [value]

        return result


# Global instance (lazy initialized)
_llm_client: Optional[LLMClient] = None
_dialogue_generator: Optional[AgentDialogueGenerator] = None
_creation_generator: Optional[CreationDialogueGenerator] = None


def get_llm_client() -> LLMClient:
    """Get or create global LLM client"""
    global _llm_client
    if _llm_client is None:
        # Try to get provider from env, default to local
        provider = os.getenv("LLM_PROVIDER", "local")
        _llm_client = LLMClient(provider=provider)
    return _llm_client


def get_dialogue_generator() -> AgentDialogueGenerator:
    """Get or create dialogue generator"""
    global _dialogue_generator
    if _dialogue_generator is None:
        _dialogue_generator = AgentDialogueGenerator(get_llm_client())
    return _dialogue_generator


def get_creation_generator() -> CreationDialogueGenerator:
    """Get or create creation dialogue generator"""
    global _creation_generator
    if _creation_generator is None:
        _creation_generator = CreationDialogueGenerator(get_llm_client())
    return _creation_generator
