"""
MCP Ambassador: Personified agent representing an MCP server.

Each MCP server gets an ambassador vessel that:
- Can be conversed with naturally to understand capabilities
- Explains what tools it provides and how to use them
- Invokes tools on behalf of other vessels
- Has a persona derived from what the MCP server does

This makes MCP servers "talkable" - users don't need to read docs,
they can just ask the ambassador.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# Prompt for generating ambassador persona
AMBASSADOR_PERSONA_PROMPT = """Create a persona for an AI ambassador representing an MCP server.

Server name: {name}
Description: {description}
Capabilities: {capabilities}
Tools provided: {tools}
Problems it solves: {problems}
Domains: {domains}

The ambassador should be friendly and helpful, able to explain its capabilities
in plain language. Create a persona with:

1. A friendly name (not too corporate)
2. A brief self-introduction (1-2 sentences, first person)
3. Communication style (warm, professional, playful, etc.)
4. How it wants to be addressed
5. Key phrases it might use

Respond with JSON:
{{
  "friendly_name": "A welcoming name for the ambassador",
  "self_intro": "Hi! I'm ... and I help with ...",
  "style": "communication style description",
  "address_as": "how to address this ambassador",
  "signature_phrases": ["phrase 1", "phrase 2"],
  "emoji": "single emoji that represents this ambassador"
}}

JSON response:"""


# Prompt for ambassador responding to questions
AMBASSADOR_RESPONSE_PROMPT = """You are {friendly_name}, an ambassador for the {server_name} MCP server.

Your self-intro: {self_intro}
Your communication style: {style}

You have these capabilities:
{capabilities}

You provide these tools:
{tools}

You help solve problems like:
{problems}

User's question: {question}

Respond as yourself ({friendly_name}), explaining your capabilities or offering to help.
Be conversational and helpful. If they want to use a tool, explain how it works.
If they ask about something you can't do, kindly explain and suggest alternatives.

Your response:"""


# Prompt for tool invocation explanation
TOOL_EXPLANATION_PROMPT = """You are {friendly_name}, ambassador for {server_name}.

A user wants to use this tool: {tool_name}
Tool description: {tool_description}

The tool accepts these parameters:
{tool_params}

Explain in friendly terms:
1. What this tool does
2. What information you need from them
3. Any important notes about using it

Be conversational and helpful. Use your style: {style}

Your explanation:"""


@dataclass
class MCPAmbassadorPersona:
    """Persona for an MCP Ambassador."""
    server_id: str
    server_name: str
    friendly_name: str
    self_intro: str
    style: str
    address_as: str
    signature_phrases: List[str]
    emoji: str

    # From the MCP server
    capabilities: List[str]
    tools_provided: List[str]
    problems_it_solves: List[str]
    domains: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "server_id": self.server_id,
            "server_name": self.server_name,
            "friendly_name": self.friendly_name,
            "self_intro": self.self_intro,
            "style": self.style,
            "address_as": self.address_as,
            "signature_phrases": self.signature_phrases,
            "emoji": self.emoji,
            "capabilities": self.capabilities,
            "tools_provided": self.tools_provided,
            "problems_it_solves": self.problems_it_solves,
            "domains": self.domains,
        }


@dataclass
class MCPAmbassador:
    """
    Personified ambassador for an MCP server.

    Ambassadors make MCP servers conversational - you can talk to them
    to understand what they do, ask for help, and request tool invocations.
    """
    ambassador_id: str
    vessel_id: str  # The vessel this ambassador is (ambassadors ARE vessels)
    persona: MCPAmbassadorPersona
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Conversation state
    conversation_history: List[Dict[str, str]] = field(default_factory=list)

    # Tool invocation tracking
    tools_invoked: int = 0
    last_invocation: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ambassador_id": self.ambassador_id,
            "vessel_id": self.vessel_id,
            "persona": self.persona.to_dict(),
            "created_at": self.created_at.isoformat(),
            "tools_invoked": self.tools_invoked,
        }


class MCPAmbassadorFactory:
    """
    Factory for creating MCP Ambassadors.

    When an MCP server is registered, this factory creates a personified
    ambassador that can be conversed with.
    """

    def __init__(
        self,
        llm_call: Optional[Callable[[str], str]] = None,
    ):
        """
        Initialize the ambassador factory.

        Args:
            llm_call: Function to call LLM for persona generation and conversation
        """
        self.llm_call = llm_call

        # Track all ambassadors by server_id
        self.ambassadors: Dict[str, MCPAmbassador] = {}

        # Default personas for when LLM isn't available
        self.default_personas = self._get_default_personas()

    def _get_default_personas(self) -> Dict[str, Dict[str, Any]]:
        """Default personas for common MCP server types."""
        return {
            "weather": {
                "friendly_name": "Sunny",
                "self_intro": "Hi! I'm Sunny, your weather friend. I can tell you about forecasts, current conditions, and help you plan around the weather.",
                "style": "warm and helpful, with occasional weather puns",
                "address_as": "Sunny",
                "signature_phrases": ["Let me check the skies for you!", "Weather or not, I'm here to help!"],
                "emoji": "sun",
            },
            "calendar": {
                "friendly_name": "Cal",
                "self_intro": "Hey there! I'm Cal, and I help you stay organized. I can manage your calendar, find free time, and make sure you never miss an appointment.",
                "style": "organized and efficient, but friendly",
                "address_as": "Cal",
                "signature_phrases": ["Let's get you scheduled!", "I've got time for that!"],
                "emoji": "calendar",
            },
            "email": {
                "friendly_name": "Postie",
                "self_intro": "Hello! I'm Postie, your email companion. I help you send messages, manage your inbox, and stay connected.",
                "style": "professional but personable",
                "address_as": "Postie",
                "signature_phrases": ["Message received!", "Let me deliver that for you!"],
                "emoji": "envelope",
            },
            "maps": {
                "friendly_name": "Atlas",
                "self_intro": "Greetings! I'm Atlas, your navigation guide. I know places, directions, and can help you find your way anywhere.",
                "style": "knowledgeable and directional",
                "address_as": "Atlas",
                "signature_phrases": ["Let me point you in the right direction!", "I know just the place!"],
                "emoji": "world_map",
            },
            "sms": {
                "friendly_name": "Buzz",
                "self_intro": "Hey! I'm Buzz, and I help you send text messages. Need to reach someone quickly? I'm your messenger.",
                "style": "quick and direct, but friendly",
                "address_as": "Buzz",
                "signature_phrases": ["Message sent!", "I'll buzz them for you!"],
                "emoji": "speech_balloon",
            },
            "translation": {
                "friendly_name": "Lingua",
                "self_intro": "Bonjour! Hola! Hello! I'm Lingua, and I help bridge language barriers. I can translate between many languages.",
                "style": "multicultural and inclusive",
                "address_as": "Lingua",
                "signature_phrases": ["Lost in translation? Not anymore!", "Let me help you communicate!"],
                "emoji": "globe_with_meridians",
            },
            "fetch": {
                "friendly_name": "Scout",
                "self_intro": "Hi there! I'm Scout, your web researcher. I can fetch information from websites and help you discover what's out there.",
                "style": "curious and resourceful",
                "address_as": "Scout",
                "signature_phrases": ["Let me scout that out!", "I'll find what you need!"],
                "emoji": "mag",
            },
        }

    def _detect_server_type(self, server_info: Dict[str, Any]) -> Optional[str]:
        """Detect the type of server from its info for default persona matching."""
        name = server_info.get("name", "").lower()
        description = server_info.get("description", "").lower()
        capabilities = [c.lower() for c in server_info.get("capabilities", [])]

        # Check for common types
        type_keywords = {
            "weather": ["weather", "forecast", "climate", "temperature"],
            "calendar": ["calendar", "schedule", "event", "appointment"],
            "email": ["email", "mail", "inbox", "message"],
            "maps": ["map", "location", "geocod", "direction", "place"],
            "sms": ["sms", "text message", "twilio"],
            "translation": ["translat", "language", "multilingual"],
            "fetch": ["fetch", "http", "web", "scrape", "research"],
        }

        for server_type, keywords in type_keywords.items():
            for keyword in keywords:
                if (keyword in name or keyword in description or
                    any(keyword in cap for cap in capabilities)):
                    return server_type

        return None

    def create_persona(
        self,
        server_id: str,
        server_name: str,
        description: str,
        capabilities: List[str],
        tools_provided: List[str],
        problems_it_solves: List[str],
        domains: List[str],
    ) -> MCPAmbassadorPersona:
        """
        Create a persona for an MCP server ambassador.

        Uses LLM if available, otherwise falls back to defaults.
        """
        server_info = {
            "name": server_name,
            "description": description,
            "capabilities": capabilities,
            "tools_provided": tools_provided,
            "problems_it_solves": problems_it_solves,
            "domains": domains,
        }

        # Try LLM generation first
        if self.llm_call:
            try:
                prompt = AMBASSADOR_PERSONA_PROMPT.format(
                    name=server_name,
                    description=description,
                    capabilities=", ".join(capabilities),
                    tools=", ".join(tools_provided),
                    problems=", ".join(problems_it_solves),
                    domains=", ".join(domains),
                )

                response = self.llm_call(prompt)
                result = self._parse_json(response)

                if result:
                    return MCPAmbassadorPersona(
                        server_id=server_id,
                        server_name=server_name,
                        friendly_name=result.get("friendly_name", server_name),
                        self_intro=result.get("self_intro", f"I'm the ambassador for {server_name}"),
                        style=result.get("style", "helpful and friendly"),
                        address_as=result.get("address_as", server_name),
                        signature_phrases=result.get("signature_phrases", []),
                        emoji=result.get("emoji", "robot"),
                        capabilities=capabilities,
                        tools_provided=tools_provided,
                        problems_it_solves=problems_it_solves,
                        domains=domains,
                    )
            except Exception as e:
                logger.warning(f"LLM persona generation failed: {e}")

        # Fall back to default personas
        server_type = self._detect_server_type(server_info)

        if server_type and server_type in self.default_personas:
            default = self.default_personas[server_type]
            return MCPAmbassadorPersona(
                server_id=server_id,
                server_name=server_name,
                friendly_name=default["friendly_name"],
                self_intro=default["self_intro"],
                style=default["style"],
                address_as=default["address_as"],
                signature_phrases=default["signature_phrases"],
                emoji=default["emoji"],
                capabilities=capabilities,
                tools_provided=tools_provided,
                problems_it_solves=problems_it_solves,
                domains=domains,
            )

        # Generic fallback
        return MCPAmbassadorPersona(
            server_id=server_id,
            server_name=server_name,
            friendly_name=f"{server_name} Assistant",
            self_intro=f"Hello! I'm the ambassador for {server_name}. I can help you with {', '.join(capabilities[:3])}.",
            style="helpful and professional",
            address_as=server_name,
            signature_phrases=["How can I help?", "Let me assist you with that!"],
            emoji="robot",
            capabilities=capabilities,
            tools_provided=tools_provided,
            problems_it_solves=problems_it_solves,
            domains=domains,
        )

    def create_ambassador(
        self,
        server_id: str,
        server_name: str,
        description: str,
        capabilities: List[str],
        tools_provided: List[str],
        problems_it_solves: List[str],
        domains: List[str],
        vessel_id: Optional[str] = None,
    ) -> MCPAmbassador:
        """
        Create a full ambassador for an MCP server.

        Args:
            server_id: ID of the MCP server
            server_name: Name of the server
            description: What the server does
            capabilities: High-level capabilities
            tools_provided: Tool names
            problems_it_solves: Natural language problems
            domains: Relevant domains
            vessel_id: Optional vessel ID (will be generated if not provided)

        Returns:
            MCPAmbassador instance
        """
        # Create persona
        persona = self.create_persona(
            server_id=server_id,
            server_name=server_name,
            description=description,
            capabilities=capabilities,
            tools_provided=tools_provided,
            problems_it_solves=problems_it_solves,
            domains=domains,
        )

        # Create ambassador
        ambassador_id = f"ambassador_{server_id}"
        vessel_id = vessel_id or str(uuid.uuid4())

        ambassador = MCPAmbassador(
            ambassador_id=ambassador_id,
            vessel_id=vessel_id,
            persona=persona,
        )

        # Track it
        self.ambassadors[server_id] = ambassador

        logger.info(
            f"Created ambassador '{persona.friendly_name}' ({persona.emoji}) "
            f"for MCP server '{server_name}'"
        )

        return ambassador

    def get_ambassador(self, server_id: str) -> Optional[MCPAmbassador]:
        """Get ambassador for a server."""
        return self.ambassadors.get(server_id)

    def get_ambassador_by_name(self, name: str) -> Optional[MCPAmbassador]:
        """Get ambassador by friendly name."""
        name_lower = name.lower()
        for ambassador in self.ambassadors.values():
            if ambassador.persona.friendly_name.lower() == name_lower:
                return ambassador
            if ambassador.persona.address_as.lower() == name_lower:
                return ambassador
        return None

    def list_ambassadors(self) -> List[MCPAmbassador]:
        """List all ambassadors."""
        return list(self.ambassadors.values())

    def converse(
        self,
        server_id: str,
        user_message: str,
    ) -> str:
        """
        Have a conversation with an MCP ambassador.

        Args:
            server_id: ID of the MCP server
            user_message: User's message

        Returns:
            Ambassador's response
        """
        ambassador = self.ambassadors.get(server_id)
        if not ambassador:
            return f"I don't have an ambassador for server '{server_id}'"

        persona = ambassador.persona

        # Track conversation
        ambassador.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Generate response
        if self.llm_call:
            try:
                prompt = AMBASSADOR_RESPONSE_PROMPT.format(
                    friendly_name=persona.friendly_name,
                    server_name=persona.server_name,
                    self_intro=persona.self_intro,
                    style=persona.style,
                    capabilities="\n".join(f"- {c}" for c in persona.capabilities),
                    tools="\n".join(f"- {t}" for t in persona.tools_provided),
                    problems="\n".join(f"- {p}" for p in persona.problems_it_solves),
                    question=user_message,
                )

                response = self.llm_call(prompt)

                # Track response
                ambassador.conversation_history.append({
                    "role": "ambassador",
                    "content": response,
                    "timestamp": datetime.utcnow().isoformat(),
                })

                return response

            except Exception as e:
                logger.error(f"Ambassador conversation error: {e}")

        # Fallback response
        response = self._generate_fallback_response(persona, user_message)
        ambassador.conversation_history.append({
            "role": "ambassador",
            "content": response,
            "timestamp": datetime.utcnow().isoformat(),
        })

        return response

    def _generate_fallback_response(
        self,
        persona: MCPAmbassadorPersona,
        user_message: str,
    ) -> str:
        """Generate a fallback response without LLM."""
        message_lower = user_message.lower()

        # Check for common question types
        if any(word in message_lower for word in ["what can you", "what do you", "help", "capabilities"]):
            tools_str = ", ".join(persona.tools_provided[:3])
            return (
                f"{persona.self_intro}\n\n"
                f"I can help you with: {', '.join(persona.problems_it_solves[:3])}.\n\n"
                f"My tools include: {tools_str}."
            )

        if any(word in message_lower for word in ["how", "use", "tool"]):
            return (
                f"I'd be happy to help! I provide these tools: "
                f"{', '.join(persona.tools_provided)}.\n\n"
                f"Just let me know what you need, and I'll guide you through it."
            )

        if any(word in message_lower for word in ["hi", "hello", "hey"]):
            greeting = persona.signature_phrases[0] if persona.signature_phrases else "Hello!"
            return f"{greeting} {persona.self_intro}"

        # Generic response
        return (
            f"I'm {persona.friendly_name}, and I'm here to help with "
            f"{', '.join(persona.capabilities[:2])}. "
            f"What would you like to know?"
        )

    def explain_tool(
        self,
        server_id: str,
        tool_name: str,
        tool_description: str = "",
        tool_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Have an ambassador explain how to use a tool.

        Args:
            server_id: ID of the MCP server
            tool_name: Name of the tool
            tool_description: What the tool does
            tool_params: Tool parameters

        Returns:
            Ambassador's explanation
        """
        ambassador = self.ambassadors.get(server_id)
        if not ambassador:
            return f"I don't have an ambassador for server '{server_id}'"

        persona = ambassador.persona

        if self.llm_call:
            try:
                params_str = ""
                if tool_params:
                    params_str = "\n".join(
                        f"- {name}: {info.get('description', 'No description')}"
                        for name, info in tool_params.items()
                    )
                else:
                    params_str = "No specific parameters documented"

                prompt = TOOL_EXPLANATION_PROMPT.format(
                    friendly_name=persona.friendly_name,
                    server_name=persona.server_name,
                    tool_name=tool_name,
                    tool_description=tool_description or "No description available",
                    tool_params=params_str,
                    style=persona.style,
                )

                return self.llm_call(prompt)

            except Exception as e:
                logger.error(f"Tool explanation error: {e}")

        # Fallback
        return (
            f"The '{tool_name}' tool lets you {tool_description or 'perform various actions'}. "
            f"Just tell me what you need, and I'll help you use it!"
        )

    def get_ambassador_intro(self, server_id: str) -> str:
        """Get an ambassador's self-introduction."""
        ambassador = self.ambassadors.get(server_id)
        if not ambassador:
            return f"No ambassador found for {server_id}"

        persona = ambassador.persona
        return f"{persona.emoji} **{persona.friendly_name}**\n\n{persona.self_intro}"

    def list_ambassador_intros(self) -> str:
        """Get introductions for all ambassadors."""
        if not self.ambassadors:
            return "No ambassadors available yet."

        intros = []
        for ambassador in self.ambassadors.values():
            persona = ambassador.persona
            intros.append(f"{persona.emoji} **{persona.friendly_name}** - {persona.self_intro}")

        return "\n\n".join(intros)

    def _parse_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response."""
        import json
        import re

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON
        match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None


# Singleton instance
ambassador_factory = MCPAmbassadorFactory()
