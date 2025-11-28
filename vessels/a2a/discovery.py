"""
A2A Discovery - Agent Discovery and Registry

Provides mechanisms for finding agents based on capabilities,
domain expertise, or identity.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

from .types import AgentCard, AgentSkill

if TYPE_CHECKING:
    from vessels.communication.nostr_adapter import NostrAdapter
    from vessels.knowledge import VesselsGraphitiClient

logger = logging.getLogger(__name__)


# =============================================================================
# Agent Registry - In-Memory Agent Directory
# =============================================================================

@dataclass
class AgentRegistryEntry:
    """Entry in the agent registry."""
    agent_card: AgentCard
    nostr_pubkey: Optional[str] = None
    last_seen: datetime = field(default_factory=datetime.utcnow)
    trust_score: float = 0.5  # 0.0 to 1.0
    verified: bool = False
    tags: List[str] = field(default_factory=list)


class AgentRegistry:
    """
    In-memory registry of known agents.

    Provides fast lookup by various criteria and maintains
    trust scores based on interaction history.
    """

    def __init__(self, graphiti_client: Optional["VesselsGraphitiClient"] = None):
        """
        Initialize registry.

        Args:
            graphiti_client: Optional Graphiti client for persistence
        """
        self.graphiti = graphiti_client
        self._agents: Dict[str, AgentRegistryEntry] = {}
        self._by_skill: Dict[str, List[str]] = {}  # skill_id -> [agent_ids]
        self._by_domain: Dict[str, List[str]] = {}  # domain -> [agent_ids]
        self._by_pubkey: Dict[str, str] = {}  # nostr_pubkey -> agent_id

    def register(
        self,
        agent_card: AgentCard,
        nostr_pubkey: Optional[str] = None,
        trust_score: float = 0.5,
        verified: bool = False,
    ) -> AgentRegistryEntry:
        """
        Register an agent in the registry.

        Args:
            agent_card: Agent's identity card
            nostr_pubkey: Optional Nostr public key
            trust_score: Initial trust score
            verified: Whether agent is verified

        Returns:
            Created registry entry
        """
        entry = AgentRegistryEntry(
            agent_card=agent_card,
            nostr_pubkey=nostr_pubkey or agent_card.nostr_pubkey,
            trust_score=trust_score,
            verified=verified,
            tags=agent_card.domains.copy(),
        )

        self._agents[agent_card.agent_id] = entry

        # Index by skills
        for skill in agent_card.skills:
            if skill.skill_id not in self._by_skill:
                self._by_skill[skill.skill_id] = []
            self._by_skill[skill.skill_id].append(agent_card.agent_id)

            # Also index by skill tags
            for tag in skill.tags:
                if tag not in self._by_skill:
                    self._by_skill[tag] = []
                if agent_card.agent_id not in self._by_skill[tag]:
                    self._by_skill[tag].append(agent_card.agent_id)

        # Index by domain
        for domain in agent_card.domains:
            if domain not in self._by_domain:
                self._by_domain[domain] = []
            self._by_domain[domain].append(agent_card.agent_id)

        # Index by pubkey
        if entry.nostr_pubkey:
            self._by_pubkey[entry.nostr_pubkey] = agent_card.agent_id

        # Persist to graph if available
        if self.graphiti:
            self._persist_to_graph(entry)

        logger.info(f"Registered agent: {agent_card.name} ({agent_card.agent_id[:8]}...)")
        return entry

    def unregister(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self._agents:
            return False

        entry = self._agents[agent_id]

        # Remove from skill index
        for skill in entry.agent_card.skills:
            if skill.skill_id in self._by_skill:
                self._by_skill[skill.skill_id] = [
                    aid for aid in self._by_skill[skill.skill_id] if aid != agent_id
                ]

        # Remove from domain index
        for domain in entry.agent_card.domains:
            if domain in self._by_domain:
                self._by_domain[domain] = [
                    aid for aid in self._by_domain[domain] if aid != agent_id
                ]

        # Remove from pubkey index
        if entry.nostr_pubkey and entry.nostr_pubkey in self._by_pubkey:
            del self._by_pubkey[entry.nostr_pubkey]

        del self._agents[agent_id]

        logger.info(f"Unregistered agent: {agent_id[:8]}...")
        return True

    def get(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_by_pubkey(self, pubkey: str) -> Optional[AgentRegistryEntry]:
        """Get agent by Nostr public key."""
        agent_id = self._by_pubkey.get(pubkey)
        if agent_id:
            return self._agents.get(agent_id)
        return None

    def find_by_skill(self, skill_id_or_tag: str) -> List[AgentCard]:
        """Find agents with a specific skill."""
        agent_ids = self._by_skill.get(skill_id_or_tag, [])
        return [
            self._agents[aid].agent_card
            for aid in agent_ids
            if aid in self._agents
        ]

    def find_by_domain(self, domain: str) -> List[AgentCard]:
        """Find agents in a specific domain."""
        agent_ids = self._by_domain.get(domain, [])
        return [
            self._agents[aid].agent_card
            for aid in agent_ids
            if aid in self._agents
        ]

    def search(
        self,
        query: str,
        domains: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        min_trust: float = 0.0,
        limit: int = 10,
    ) -> List[AgentCard]:
        """
        Search for agents matching criteria.

        Args:
            query: Natural language search query
            domains: Filter by domains
            skills: Filter by skill tags
            min_trust: Minimum trust score
            limit: Maximum results

        Returns:
            List of matching AgentCards sorted by relevance
        """
        results = []

        for entry in self._agents.values():
            # Filter by trust
            if entry.trust_score < min_trust:
                continue

            # Filter by domains
            if domains:
                if not any(d in entry.agent_card.domains for d in domains):
                    continue

            # Filter by skills
            if skills:
                agent_skill_tags = set()
                for skill in entry.agent_card.skills:
                    agent_skill_tags.update(skill.tags)
                if not any(s in agent_skill_tags for s in skills):
                    continue

            # Score by query match
            score = entry.agent_card.matches_need(query)
            if score > 0 or not query:
                results.append((score + entry.trust_score * 0.2, entry.agent_card))

        # Sort by score descending
        results.sort(key=lambda x: x[0], reverse=True)

        return [card for _, card in results[:limit]]

    def update_trust(self, agent_id: str, delta: float) -> Optional[float]:
        """
        Update an agent's trust score.

        Args:
            agent_id: Agent to update
            delta: Change in trust score (-1.0 to 1.0)

        Returns:
            New trust score or None if agent not found
        """
        entry = self._agents.get(agent_id)
        if not entry:
            return None

        entry.trust_score = max(0.0, min(1.0, entry.trust_score + delta))
        entry.last_seen = datetime.utcnow()

        return entry.trust_score

    def mark_seen(self, agent_id: str) -> None:
        """Update last seen timestamp."""
        entry = self._agents.get(agent_id)
        if entry:
            entry.last_seen = datetime.utcnow()

    def _persist_to_graph(self, entry: AgentRegistryEntry) -> None:
        """Persist registry entry to knowledge graph."""
        if not self.graphiti:
            return

        try:
            # Import schema for node types
            from vessels.knowledge.schema import NodeType, PropertyName

            # Check if graphiti has create_node (VesselsGraphitiClient or mock)
            if hasattr(self.graphiti, 'create_node'):
                self.graphiti.create_node(
                    node_type=NodeType.A2A_AGENT,
                    properties={
                        PropertyName.NAME: entry.agent_card.name,
                        PropertyName.DESCRIPTION: entry.agent_card.description,
                        "agent_id": entry.agent_card.agent_id,
                        "vessel_id": entry.agent_card.vessel_id,
                        "nostr_pubkey": entry.nostr_pubkey,
                        "url": entry.agent_card.url,
                        "protocol_version": entry.agent_card.protocol_version,
                        "domains": entry.agent_card.domains,
                        "trust_score": entry.trust_score,
                        "verified": entry.verified,
                        PropertyName.CREATED_AT: datetime.utcnow().isoformat(),
                    },
                    node_id=entry.agent_card.agent_id,
                )
            # Check if graphiti is a GraphitiMemoryBackend with a nested client
            elif hasattr(self.graphiti, 'graphiti') and hasattr(self.graphiti.graphiti, 'create_node'):
                self.graphiti.graphiti.create_node(
                    node_type=NodeType.A2A_AGENT,
                    properties={
                        PropertyName.NAME: entry.agent_card.name,
                        PropertyName.DESCRIPTION: entry.agent_card.description,
                        "agent_id": entry.agent_card.agent_id,
                        "vessel_id": entry.agent_card.vessel_id,
                        "nostr_pubkey": entry.nostr_pubkey,
                        "trust_score": entry.trust_score,
                        "verified": entry.verified,
                        PropertyName.CREATED_AT: datetime.utcnow().isoformat(),
                    },
                    node_id=entry.agent_card.agent_id,
                )
            else:
                logger.debug("Graphiti client does not support create_node, skipping persistence")
        except Exception as e:
            logger.error(f"Failed to persist agent to graph: {e}")

    def list_all(self) -> List[AgentRegistryEntry]:
        """List all registered agents."""
        return list(self._agents.values())

    def count(self) -> int:
        """Get number of registered agents."""
        return len(self._agents)

    def to_dict(self) -> Dict[str, Any]:
        """Get registry stats as dictionary."""
        return {
            "totalAgents": len(self._agents),
            "verifiedAgents": len([e for e in self._agents.values() if e.verified]),
            "domains": list(self._by_domain.keys()),
            "skillTags": list(self._by_skill.keys()),
        }


# =============================================================================
# A2A Discovery - Network Discovery Service
# =============================================================================

class A2ADiscovery:
    """
    A2A Discovery Service.

    Discovers agents via:
    1. Local registry (fast, cached)
    2. Nostr network (decentralized, real-time)
    3. Knowledge graph (project-scoped)
    4. Well-known URIs (external agents)

    Usage:
        discovery = A2ADiscovery(registry, nostr_adapter)

        # Find agents for a need
        agents = await discovery.find_for_need("help with grant writing")

        # Query specific capability
        agents = await discovery.query_capability("grant-research")

        # Discover from Nostr
        await discovery.discover_from_nostr()
    """

    def __init__(
        self,
        registry: AgentRegistry,
        nostr_adapter: Optional["NostrAdapter"] = None,
        graphiti_client: Optional["VesselsGraphitiClient"] = None,
    ):
        """
        Initialize discovery service.

        Args:
            registry: Agent registry for caching
            nostr_adapter: Nostr adapter for network discovery
            graphiti_client: Graphiti client for graph queries
        """
        self.registry = registry
        self.nostr = nostr_adapter
        self.graphiti = graphiti_client

        # Discovery callbacks
        self._on_agent_discovered: List[Callable[[AgentCard], None]] = []

        logger.info("A2A Discovery service initialized")

    def on_agent_discovered(self, callback: Callable[[AgentCard], None]) -> None:
        """Register callback for newly discovered agents."""
        self._on_agent_discovered.append(callback)

    # =========================================================================
    # Local Discovery (Registry)
    # =========================================================================

    def find_for_need(
        self,
        need: str,
        domains: Optional[List[str]] = None,
        min_trust: float = 0.0,
        limit: int = 10,
    ) -> List[AgentCard]:
        """
        Find agents that can help with a need.

        Args:
            need: Natural language description of need
            domains: Optional domain filters
            min_trust: Minimum trust score
            limit: Maximum results

        Returns:
            List of matching AgentCards
        """
        return self.registry.search(
            query=need,
            domains=domains,
            min_trust=min_trust,
            limit=limit,
        )

    def query_capability(self, capability: str) -> List[AgentCard]:
        """Find agents with a specific capability/skill."""
        return self.registry.find_by_skill(capability)

    def find_in_domain(self, domain: str) -> List[AgentCard]:
        """Find agents in a specific domain."""
        return self.registry.find_by_domain(domain)

    # =========================================================================
    # Network Discovery (Nostr)
    # =========================================================================

    def discover_from_nostr(
        self,
        domains: Optional[List[str]] = None,
        since_timestamp: Optional[int] = None,
    ) -> Optional[str]:
        """
        Start discovery subscription on Nostr network.

        Args:
            domains: Filter by domains
            since_timestamp: Only events after this timestamp

        Returns:
            Subscription ID if successful
        """
        if not self.nostr or not self.nostr.enabled:
            logger.warning("Cannot discover - Nostr not enabled")
            return None

        from vessels.a2a.service import A2AEventKind

        filters = [{
            "kinds": [A2AEventKind.AGENT_CARD],
            "#t": ["a2a", "agent-card"],
        }]

        if since_timestamp:
            filters[0]["since"] = since_timestamp

        return self.nostr.subscribe(filters, self._handle_agent_card_event)

    def _handle_agent_card_event(self, event: Any) -> None:
        """Handle discovered agent card from Nostr."""
        try:
            card_data = json.loads(event.content)
            agent_card = AgentCard.from_dict(card_data)

            # Set Nostr pubkey from event
            agent_card.nostr_pubkey = event.pubkey

            # Check if already registered
            existing = self.registry.get(agent_card.agent_id)
            if existing:
                # Update last seen
                self.registry.mark_seen(agent_card.agent_id)
                return

            # Register new agent
            self.registry.register(
                agent_card,
                nostr_pubkey=event.pubkey,
                trust_score=0.3,  # Lower initial trust for network-discovered
            )

            # Notify callbacks
            for callback in self._on_agent_discovered:
                try:
                    callback(agent_card)
                except Exception as e:
                    logger.error(f"Error in discovery callback: {e}")

            logger.info(f"Discovered agent from Nostr: {agent_card.name}")

        except Exception as e:
            logger.error(f"Error parsing agent card: {e}")

    def broadcast_query(
        self,
        capability: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Broadcast a capability query to the network.

        Other agents can respond with their agent cards if they
        have the requested capability.

        Args:
            capability: Capability being sought
            context: Optional context about the need

        Returns:
            Query event ID if successful
        """
        if not self.nostr or not self.nostr.enabled:
            return None

        from vessels.communication.nostr_adapter import NostrEvent
        from vessels.a2a.service import A2AEventKind

        content = {
            "capability": capability,
            "context": context or {},
            "queryId": str(uuid.uuid4()),
        }

        event = NostrEvent(
            kind=A2AEventKind.DISCOVERY_QUERY,
            content=json.dumps(content),
            tags=[
                ["t", "vessels"],
                ["t", "a2a"],
                ["t", "discovery-query"],
                ["capability", capability],
            ],
            pubkey=self.nostr.keypair.public_key,
        )

        event.compute_id()
        event.sig = self.nostr.keypair.sign(event.to_dict())
        self.nostr._publish_to_relays(event)

        logger.info(f"Broadcast capability query: {capability}")
        return event.id

    # =========================================================================
    # Graph Discovery
    # =========================================================================

    def discover_from_graph(
        self,
        project_id: Optional[str] = None,
    ) -> List[AgentCard]:
        """
        Discover agents from knowledge graph.

        Args:
            project_id: Optional project scope

        Returns:
            List of discovered AgentCards
        """
        if not self.graphiti:
            return []

        discovered = []

        try:
            # Query for A2AAgent nodes
            query = "MATCH (a:A2AAgent) RETURN a"
            if project_id:
                query = f"MATCH (p:Project {{id: '{project_id}'}})-[:OWNS]->(a:A2AAgent) RETURN a"

            results = self.graphiti.query(query)

            for record in results:
                node = record.get("a", {})
                card = AgentCard(
                    agent_id=node.get("agent_id", str(uuid.uuid4())),
                    name=node.get("name", "Unknown"),
                    description=node.get("description"),
                    skills=[],  # Would need to query skill relationships
                    domains=node.get("domains", []),
                    vessel_id=node.get("vessel_id"),
                    nostr_pubkey=node.get("nostr_pubkey"),
                )
                discovered.append(card)

                # Register in local cache
                if not self.registry.get(card.agent_id):
                    self.registry.register(
                        card,
                        trust_score=node.get("trust_score", 0.5),
                        verified=node.get("verified", False),
                    )

        except Exception as e:
            logger.error(f"Error discovering from graph: {e}")

        return discovered

    # =========================================================================
    # Well-Known URI Discovery
    # =========================================================================

    def discover_from_url(self, base_url: str) -> Optional[AgentCard]:
        """
        Fetch agent card from well-known URI.

        Per A2A spec, agents expose their card at:
        {base_url}/.well-known/agent-card.json

        Args:
            base_url: Base URL of the agent

        Returns:
            AgentCard if found
        """
        import urllib.request
        import urllib.error

        well_known_url = f"{base_url.rstrip('/')}/.well-known/agent-card.json"

        try:
            with urllib.request.urlopen(well_known_url, timeout=10) as response:
                card_data = json.loads(response.read())
                card = AgentCard.from_dict(card_data)
                card.url = base_url

                # Register with higher trust (explicit URL)
                self.registry.register(card, trust_score=0.6)

                logger.info(f"Discovered agent from {base_url}: {card.name}")
                return card

        except urllib.error.URLError as e:
            logger.debug(f"No agent card at {well_known_url}: {e}")
        except Exception as e:
            logger.error(f"Error fetching agent card from {base_url}: {e}")

        return None

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def get_all_known(self) -> List[AgentCard]:
        """Get all known agents."""
        return [entry.agent_card for entry in self.registry.list_all()]

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery stats."""
        return {
            "registry": self.registry.to_dict(),
            "nostrEnabled": self.nostr.enabled if self.nostr else False,
            "graphEnabled": self.graphiti is not None,
        }


# =============================================================================
# Vessel to Agent Card Conversion
# =============================================================================

def vessel_to_agent_card(
    vessel: Any,
    skills: Optional[List[AgentSkill]] = None,
    nostr_pubkey: Optional[str] = None,
) -> AgentCard:
    """
    Convert a Vessel to an A2A Agent Card.

    This bridges Vessels' internal representation to the
    A2A protocol standard.

    Args:
        vessel: Vessel object
        skills: Optional list of skills (auto-generated if not provided)
        nostr_pubkey: Optional Nostr public key

    Returns:
        AgentCard representing the vessel
    """
    # Auto-generate skills from vessel tools if not provided
    if not skills:
        skills = []
        if hasattr(vessel, 'tools') and vessel.tools:
            for tool_name, tool_impl in vessel.tools.items():
                skill = AgentSkill(
                    skill_id=f"tool-{tool_name}",
                    name=tool_name.replace("_", " ").title(),
                    description=getattr(tool_impl, '__doc__', f"Use {tool_name}") or f"Use {tool_name}",
                    tags=[tool_name.split("_")[0]] if "_" in tool_name else [],
                )
                skills.append(skill)

        # Default skill if none
        if not skills:
            skills = [AgentSkill(
                skill_id="general",
                name="General Assistance",
                description=vessel.description or "General purpose vessel",
                tags=["general"],
            )]

    # Extract domains from vessel
    domains = []
    if hasattr(vessel, 'community_ids'):
        domains.extend(vessel.community_ids)

    return AgentCard(
        agent_id=vessel.vessel_id,
        name=vessel.name,
        description=vessel.description,
        skills=skills,
        vessel_id=vessel.vessel_id,
        project_id=vessel.servant_project_ids[0] if hasattr(vessel, 'servant_project_ids') and vessel.servant_project_ids else None,
        domains=domains,
        nostr_pubkey=nostr_pubkey,
        provider_name="Vessels",
    )
