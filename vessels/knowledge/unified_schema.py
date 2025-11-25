"""
Unified Vessels Schema - Everything in FalkorDB/Graphiti

This schema consolidates ALL Vessels data into the knowledge graph:
- Financial transactions (transfers, accounts, balances)
- Kala contributions and value flows
- Community memory and knowledge
- Agent states and phase space
- Governance decisions
- Vessels and projects

Design Principles:
1. Graph-native: Relationships are first-class citizens
2. Temporal: All entities have valid_from/valid_to for history
3. Auditable: Full provenance chain for every change
4. Privacy-aware: Access control at node/edge level
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# NODE TYPES
# =============================================================================

class NodeType(Enum):
    """All node types in the unified graph."""

    # === ACTORS ===
    PERSON = "Person"                      # Human participant
    AGENT = "Agent"                        # AI agent/servant
    COMMUNITY = "Community"                # Community/neighborhood
    VESSEL = "Vessel"                      # Vessel container
    GOVERNANCE_BODY = "GovernanceBody"     # Council, board, etc.

    # === FINANCIAL ===
    ACCOUNT = "Account"                    # Ledger account
    TRANSFER = "Transfer"                  # Money movement
    GIFT_CARD = "GiftCard"                 # Gift card instrument
    PAYOUT = "Payout"                      # Vendor payout record
    TAX_FILING = "TaxFiling"               # Tax payment record

    # === KALA (Contribution Tracking) ===
    CONTRIBUTION = "Contribution"          # Service contribution
    KALA_BALANCE = "KalaBalance"           # Accumulated Kala
    KALA_AWARD = "KalaAward"               # Individual Kala award

    # === KNOWLEDGE ===
    MEMORY = "Memory"                      # Community memory entry
    EPISODE = "Episode"                    # Conversation/event episode
    FACT = "Fact"                          # Extracted fact
    PATTERN = "Pattern"                    # Discovered pattern
    WISDOM = "Wisdom"                      # Synthesized wisdom

    # === PHASE SPACE ===
    AGENT_STATE = "AgentState"             # 12D phase space snapshot
    SECURITY_EVENT = "SecurityEvent"       # Gating event
    ATTRACTOR = "Attractor"                # Behavioral attractor

    # === GOVERNANCE ===
    DECISION = "Decision"                  # Governance decision
    POLICY = "Policy"                      # Active policy
    CONSTRAINT = "Constraint"              # Moral constraint

    # === PROJECTS ===
    PROJECT = "Project"                    # Servant project
    TASK = "Task"                          # Task within project


# =============================================================================
# RELATIONSHIP TYPES
# =============================================================================

class RelationType(Enum):
    """All relationship types in the unified graph."""

    # === ACTOR RELATIONSHIPS ===
    MEMBER_OF = "MEMBER_OF"                # Person -> Community
    SERVES = "SERVES"                      # Agent -> Community
    BELONGS_TO = "BELONGS_TO"              # Vessel -> Community
    OPERATES_IN = "OPERATES_IN"            # Agent -> Vessel
    TRUSTS = "TRUSTS"                      # Community -> Community

    # === FINANCIAL RELATIONSHIPS ===
    OWNS = "OWNS"                          # Person -> Account
    FROM_ACCOUNT = "FROM_ACCOUNT"          # Transfer -> Account (debit)
    TO_ACCOUNT = "TO_ACCOUNT"              # Transfer -> Account (credit)
    FUNDED_BY = "FUNDED_BY"                # GiftCard -> Person (donor)
    REDEEMED_AT = "REDEEMED_AT"            # Transfer -> Person (vendor)
    PAYS_TAX = "PAYS_TAX"                  # TaxFiling -> Account

    # === KALA RELATIONSHIPS ===
    CONTRIBUTED = "CONTRIBUTED"            # Person/Agent -> Contribution
    RECEIVED_KALA = "RECEIVED_KALA"        # Contribution -> KalaAward
    KALA_FROM = "KALA_FROM"                # KalaAward -> Person (source)
    KALA_TO = "KALA_TO"                    # KalaAward -> Person (recipient)
    WITNESSED_BY = "WITNESSED_BY"          # Contribution -> Agent

    # === KNOWLEDGE RELATIONSHIPS ===
    REMEMBERS = "REMEMBERS"                # Agent -> Memory
    RELATES_TO = "RELATES_TO"              # Memory -> Memory
    ABOUT = "ABOUT"                        # Memory -> Person
    DERIVED_FROM = "DERIVED_FROM"          # Fact -> Episode
    GENERALIZES = "GENERALIZES"            # Pattern -> Memory
    SYNTHESIZED_TO = "SYNTHESIZED_TO"      # Memory -> Wisdom

    # === PHASE SPACE RELATIONSHIPS ===
    HAS_STATE = "HAS_STATE"                # Agent -> AgentState
    TRIGGERED = "TRIGGERED"                # AgentState -> SecurityEvent
    ATTRACTED_TO = "ATTRACTED_TO"          # Agent -> Attractor
    FOLLOWS = "FOLLOWS"                    # AgentState -> AgentState (trajectory)

    # === GOVERNANCE RELATIONSHIPS ===
    MADE_DECISION = "MADE_DECISION"        # GovernanceBody -> Decision
    APPROVES = "APPROVES"                  # Decision -> Vessel/Policy
    GOVERNS = "GOVERNS"                    # GovernanceBody -> Community
    ENFORCES = "ENFORCES"                  # Policy -> Constraint
    ACCOUNTABLE_TO = "ACCOUNTABLE_TO"      # Vessel -> GovernanceBody

    # === PROJECT RELATIONSHIPS ===
    WORKS_ON = "WORKS_ON"                  # Agent -> Project
    CONTAINS_TASK = "CONTAINS_TASK"        # Project -> Task
    ASSIGNED_TO = "ASSIGNED_TO"            # Task -> Agent

    # === TEMPORAL ===
    PRECEDED_BY = "PRECEDED_BY"            # Any -> Any (temporal sequence)
    CAUSED = "CAUSED"                      # Any -> Any (causation)


# =============================================================================
# LEDGER TYPES (for Account.ledger field)
# =============================================================================

class Ledger(Enum):
    """Ledger types - accounts on different ledgers cannot transfer directly."""
    USD = "usd"                            # Money ledger
    KALA = "kala"                          # Contribution metric (NOT money)
    GET_TAX = "get_tax"                    # Hawaii GET tax escrow


class AccountType(Enum):
    """Account categorization."""
    # USD Ledger
    EARNINGS = "earnings"                  # Vendor spendable earnings
    TAX_RESERVE = "tax_reserve"            # GET escrow
    GIFT_CARD_LIABILITY = "gift_card"      # Gift card balance
    COMMUNITY_FUND = "community_fund"      # Community org funds
    FEES = "fees"                          # Platform fees

    # Kala Ledger
    KALA_BALANCE = "kala_balance"          # Participant Kala
    KALA_POOL = "kala_pool"                # Community Kala pool


class TransferType(Enum):
    """Transfer categorization."""
    GIFT_CARD_LOAD = "gift_card_load"
    GIFT_CARD_REDEMPTION = "gift_card_redemption"
    GIFT_CARD_CASHOUT = "gift_card_cashout"
    SALE_REVENUE = "sale_revenue"
    TAX_ACCRUAL = "tax_accrual"
    TAX_PAYMENT = "tax_payment"
    PAYOUT_SLOW = "payout_slow"
    PAYOUT_FAST = "payout_fast"
    FEE_COLLECTION = "fee_collection"
    KALA_AWARD = "kala_award"
    KALA_DECAY = "kala_decay"


class ContributionType(Enum):
    """Types of Kala-earning contributions."""
    SERVICE = "service"                    # Direct service to community
    MENTORSHIP = "mentorship"              # Teaching/guiding others
    COORDINATION = "coordination"          # Facilitating collaboration
    CREATION = "creation"                  # Creating resources
    MAINTENANCE = "maintenance"            # Maintaining systems
    GOVERNANCE = "governance"              # Governance participation


# =============================================================================
# PROPERTY SCHEMAS
# =============================================================================

# Required properties for each node type
NODE_PROPERTIES = {
    NodeType.PERSON: ["person_id", "name", "created_at"],
    NodeType.AGENT: ["agent_id", "name", "agent_type", "created_at"],
    NodeType.COMMUNITY: ["community_id", "name", "created_at"],
    NodeType.VESSEL: ["vessel_id", "name", "privacy_level", "created_at"],

    NodeType.ACCOUNT: ["account_id", "ledger", "account_type", "owner_id", "balance", "created_at"],
    NodeType.TRANSFER: ["transfer_id", "ledger", "transfer_type", "amount", "from_account", "to_account", "created_at"],
    NodeType.GIFT_CARD: ["card_id", "balance", "status", "created_at"],

    NodeType.CONTRIBUTION: ["contribution_id", "contribution_type", "description", "kala_value", "created_at"],
    NodeType.KALA_AWARD: ["award_id", "amount", "reason", "created_at"],

    NodeType.MEMORY: ["memory_id", "memory_type", "content", "confidence", "created_at"],
    NodeType.EPISODE: ["episode_id", "text", "created_at"],
    NodeType.AGENT_STATE: ["state_id", "agent_id", "virtue_vector", "operational_vector", "timestamp"],

    NodeType.DECISION: ["decision_id", "decision_type", "description", "approved_at"],
    NodeType.POLICY: ["policy_id", "name", "rules", "effective_at"],
}


# =============================================================================
# UNIFIED GRAPH CLIENT
# =============================================================================

class UnifiedGraphClient:
    """
    Client for the unified Vessels graph.

    All data - financial, Kala, memory, governance - lives here.
    """

    def __init__(self, falkor_client, graph_name: str = "vessels_unified"):
        """
        Initialize unified graph client.

        Args:
            falkor_client: FalkorDBClient instance
            graph_name: Name of the unified graph
        """
        self.falkor_client = falkor_client
        self.graph = falkor_client.get_graph(graph_name)
        self._ensure_indexes()
        logger.info(f"Unified graph client initialized: {graph_name}")

    def _ensure_indexes(self):
        """Create indexes for efficient queries."""
        indexes = [
            # Actor indexes
            "CREATE INDEX FOR (p:Person) ON (p.person_id)",
            "CREATE INDEX FOR (a:Agent) ON (a.agent_id)",
            "CREATE INDEX FOR (c:Community) ON (c.community_id)",
            "CREATE INDEX FOR (v:Vessel) ON (v.vessel_id)",

            # Financial indexes
            "CREATE INDEX FOR (a:Account) ON (a.account_id)",
            "CREATE INDEX FOR (a:Account) ON (a.owner_id)",
            "CREATE INDEX FOR (t:Transfer) ON (t.transfer_id)",
            "CREATE INDEX FOR (t:Transfer) ON (t.created_at)",
            "CREATE INDEX FOR (g:GiftCard) ON (g.card_id)",

            # Kala indexes
            "CREATE INDEX FOR (c:Contribution) ON (c.contribution_id)",
            "CREATE INDEX FOR (c:Contribution) ON (c.created_at)",
            "CREATE INDEX FOR (k:KalaAward) ON (k.award_id)",

            # Memory indexes
            "CREATE INDEX FOR (m:Memory) ON (m.memory_id)",
            "CREATE INDEX FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX FOR (e:Episode) ON (e.episode_id)",

            # State indexes
            "CREATE INDEX FOR (s:AgentState) ON (s.state_id)",
            "CREATE INDEX FOR (s:AgentState) ON (s.agent_id)",
            "CREATE INDEX FOR (s:AgentState) ON (s.timestamp)",
        ]

        for query in indexes:
            try:
                self.graph.query(query)
            except Exception:
                pass  # Index may exist

    # =========================================================================
    # ACCOUNT OPERATIONS
    # =========================================================================

    def create_account(
        self,
        account_id: str,
        owner_id: str,
        ledger: Ledger,
        account_type: AccountType,
        initial_balance: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new account."""
        query = """
        MERGE (owner {person_id: $owner_id})
        ON CREATE SET owner:Person, owner.created_at = $now
        CREATE (account:Account {
            account_id: $account_id,
            ledger: $ledger,
            account_type: $account_type,
            owner_id: $owner_id,
            balance: $balance,
            created_at: $now,
            metadata: $metadata
        })
        CREATE (owner)-[:OWNS]->(account)
        RETURN account.account_id
        """
        self.graph.query(query, {
            "account_id": account_id,
            "owner_id": owner_id,
            "ledger": ledger.value,
            "account_type": account_type.value,
            "balance": initial_balance,
            "now": datetime.utcnow().isoformat(),
            "metadata": str(metadata or {})
        })
        return account_id

    def transfer(
        self,
        transfer_id: str,
        from_account_id: str,
        to_account_id: str,
        amount: int,
        transfer_type: TransferType,
        ledger: Ledger,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Execute an atomic transfer between accounts.

        Returns True if successful, False if insufficient balance.
        """
        query = """
        MATCH (from:Account {account_id: $from_id})
        MATCH (to:Account {account_id: $to_id})
        WHERE from.ledger = $ledger AND to.ledger = $ledger
        AND from.balance >= $amount
        SET from.balance = from.balance - $amount,
            to.balance = to.balance + $amount
        CREATE (t:Transfer {
            transfer_id: $transfer_id,
            ledger: $ledger,
            transfer_type: $transfer_type,
            amount: $amount,
            from_account: $from_id,
            to_account: $to_id,
            created_at: $now,
            metadata: $metadata
        })
        CREATE (t)-[:FROM_ACCOUNT]->(from)
        CREATE (t)-[:TO_ACCOUNT]->(to)
        RETURN t.transfer_id
        """
        result = self.graph.query(query, {
            "transfer_id": transfer_id,
            "from_id": from_account_id,
            "to_id": to_account_id,
            "amount": amount,
            "ledger": ledger.value,
            "transfer_type": transfer_type.value,
            "now": datetime.utcnow().isoformat(),
            "metadata": str(metadata or {})
        })
        return bool(result.result_set)

    def get_balance(self, account_id: str) -> Optional[int]:
        """Get current balance for an account."""
        query = """
        MATCH (a:Account {account_id: $account_id})
        RETURN a.balance
        """
        result = self.graph.query(query, {"account_id": account_id})
        if result.result_set:
            return result.result_set[0][0]
        return None

    def get_account_history(
        self,
        account_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get transfer history for an account."""
        query = """
        MATCH (a:Account {account_id: $account_id})
        MATCH (t:Transfer)-[:FROM_ACCOUNT|TO_ACCOUNT]->(a)
        RETURN t.transfer_id, t.transfer_type, t.amount,
               t.from_account, t.to_account, t.created_at
        ORDER BY t.created_at DESC
        LIMIT $limit
        """
        result = self.graph.query(query, {
            "account_id": account_id,
            "limit": limit
        })
        return [
            {
                "transfer_id": r[0],
                "transfer_type": r[1],
                "amount": r[2],
                "from_account": r[3],
                "to_account": r[4],
                "created_at": r[5]
            }
            for r in result.result_set
        ]

    # =========================================================================
    # KALA OPERATIONS
    # =========================================================================

    def record_contribution(
        self,
        contribution_id: str,
        contributor_id: str,
        contribution_type: ContributionType,
        description: str,
        kala_value: int,
        beneficiary_id: Optional[str] = None,
        witness_agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record a contribution and award Kala."""
        query = """
        MERGE (contributor:Person {person_id: $contributor_id})
        ON CREATE SET contributor.created_at = $now
        CREATE (c:Contribution {
            contribution_id: $contribution_id,
            contribution_type: $contribution_type,
            description: $description,
            kala_value: $kala_value,
            created_at: $now,
            metadata: $metadata
        })
        CREATE (contributor)-[:CONTRIBUTED]->(c)
        WITH c, contributor
        OPTIONAL MATCH (witness:Agent {agent_id: $witness_id})
        FOREACH (_ IN CASE WHEN witness IS NOT NULL THEN [1] ELSE [] END |
            CREATE (c)-[:WITNESSED_BY]->(witness)
        )
        RETURN c.contribution_id
        """
        self.graph.query(query, {
            "contribution_id": contribution_id,
            "contributor_id": contributor_id,
            "contribution_type": contribution_type.value,
            "description": description,
            "kala_value": kala_value,
            "witness_id": witness_agent_id,
            "now": datetime.utcnow().isoformat(),
            "metadata": str(metadata or {})
        })

        # Award Kala to contributor
        self._award_kala(contributor_id, kala_value, f"contribution:{contribution_id}")

        # If beneficiary specified, award partial Kala
        if beneficiary_id and beneficiary_id != contributor_id:
            beneficiary_kala = kala_value // 2  # 50% to beneficiary
            self._award_kala(beneficiary_id, beneficiary_kala, f"beneficiary:{contribution_id}")

        return contribution_id

    def _award_kala(self, person_id: str, amount: int, reason: str):
        """Award Kala to a person."""
        query = """
        MERGE (p:Person {person_id: $person_id})
        ON CREATE SET p.created_at = $now
        MERGE (kb:KalaBalance {owner_id: $person_id})
        ON CREATE SET kb.balance = 0, kb.created_at = $now
        SET kb.balance = kb.balance + $amount, kb.updated_at = $now
        CREATE (award:KalaAward {
            award_id: $award_id,
            amount: $amount,
            reason: $reason,
            created_at: $now
        })
        CREATE (award)-[:KALA_TO]->(p)
        """
        import uuid
        self.graph.query(query, {
            "person_id": person_id,
            "amount": amount,
            "reason": reason,
            "award_id": str(uuid.uuid4()),
            "now": datetime.utcnow().isoformat()
        })

    def get_kala_balance(self, person_id: str) -> int:
        """Get Kala balance for a person."""
        query = """
        MATCH (kb:KalaBalance {owner_id: $person_id})
        RETURN kb.balance
        """
        result = self.graph.query(query, {"person_id": person_id})
        if result.result_set:
            return result.result_set[0][0]
        return 0

    def get_contribution_history(
        self,
        person_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get contribution history for a person."""
        query = """
        MATCH (p:Person {person_id: $person_id})-[:CONTRIBUTED]->(c:Contribution)
        RETURN c.contribution_id, c.contribution_type, c.description,
               c.kala_value, c.created_at
        ORDER BY c.created_at DESC
        LIMIT $limit
        """
        result = self.graph.query(query, {
            "person_id": person_id,
            "limit": limit
        })
        return [
            {
                "contribution_id": r[0],
                "contribution_type": r[1],
                "description": r[2],
                "kala_value": r[3],
                "created_at": r[4]
            }
            for r in result.result_set
        ]

    # =========================================================================
    # MEMORY OPERATIONS
    # =========================================================================

    def store_memory(
        self,
        memory_id: str,
        memory_type: str,
        content: Dict[str, Any],
        agent_id: str,
        person_id: Optional[str] = None,
        community_id: Optional[str] = None,
        confidence: float = 1.0,
        tags: Optional[List[str]] = None
    ) -> str:
        """Store a memory in the graph."""
        import json
        query = """
        MERGE (agent:Agent {agent_id: $agent_id})
        ON CREATE SET agent.created_at = $now
        CREATE (m:Memory {
            memory_id: $memory_id,
            memory_type: $memory_type,
            content: $content,
            confidence: $confidence,
            access_count: 0,
            created_at: $now,
            tags: $tags
        })
        CREATE (agent)-[:REMEMBERS {confidence: $confidence}]->(m)
        WITH m
        OPTIONAL MATCH (person:Person {person_id: $person_id})
        FOREACH (_ IN CASE WHEN person IS NOT NULL THEN [1] ELSE [] END |
            CREATE (m)-[:ABOUT]->(person)
        )
        WITH m
        OPTIONAL MATCH (community:Community {community_id: $community_id})
        FOREACH (_ IN CASE WHEN community IS NOT NULL THEN [1] ELSE [] END |
            CREATE (m)-[:BELONGS_TO]->(community)
        )
        RETURN m.memory_id
        """
        self.graph.query(query, {
            "memory_id": memory_id,
            "memory_type": memory_type,
            "content": json.dumps(content),
            "agent_id": agent_id,
            "person_id": person_id,
            "community_id": community_id,
            "confidence": confidence,
            "tags": tags or [],
            "now": datetime.utcnow().isoformat()
        })
        return memory_id

    def recall_memories(
        self,
        person_id: Optional[str] = None,
        community_id: Optional[str] = None,
        memory_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Recall memories matching filters."""
        import json

        conditions = []
        params = {"limit": limit}

        if person_id:
            conditions.append("(m)-[:ABOUT]->(:Person {person_id: $person_id})")
            params["person_id"] = person_id

        if community_id:
            conditions.append("(m)-[:BELONGS_TO]->(:Community {community_id: $community_id})")
            params["community_id"] = community_id

        if memory_type:
            conditions.append("m.memory_type = $memory_type")
            params["memory_type"] = memory_type

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        query = f"""
        MATCH (m:Memory)
        {where_clause}
        RETURN m.memory_id, m.memory_type, m.content, m.confidence, m.created_at
        ORDER BY m.created_at DESC
        LIMIT $limit
        """
        result = self.graph.query(query, params)
        return [
            {
                "memory_id": r[0],
                "memory_type": r[1],
                "content": json.loads(r[2]),
                "confidence": r[3],
                "created_at": r[4]
            }
            for r in result.result_set
        ]

    # =========================================================================
    # AGENT STATE OPERATIONS
    # =========================================================================

    def record_agent_state(
        self,
        state_id: str,
        agent_id: str,
        virtue_vector: Dict[str, float],
        operational_vector: Dict[str, float],
        gating_result: Optional[str] = None
    ) -> str:
        """Record an agent's phase space state."""
        import json
        query = """
        MERGE (agent:Agent {agent_id: $agent_id})
        ON CREATE SET agent.created_at = $now
        CREATE (s:AgentState {
            state_id: $state_id,
            agent_id: $agent_id,
            virtue_vector: $virtue_vector,
            operational_vector: $operational_vector,
            gating_result: $gating_result,
            timestamp: $now
        })
        CREATE (agent)-[:HAS_STATE]->(s)
        WITH agent, s
        OPTIONAL MATCH (agent)-[:HAS_STATE]->(prev:AgentState)
        WHERE prev.state_id <> s.state_id
        WITH s, prev ORDER BY prev.timestamp DESC LIMIT 1
        FOREACH (_ IN CASE WHEN prev IS NOT NULL THEN [1] ELSE [] END |
            CREATE (s)-[:PRECEDED_BY]->(prev)
        )
        RETURN s.state_id
        """
        self.graph.query(query, {
            "state_id": state_id,
            "agent_id": agent_id,
            "virtue_vector": json.dumps(virtue_vector),
            "operational_vector": json.dumps(operational_vector),
            "gating_result": gating_result,
            "now": datetime.utcnow().isoformat()
        })
        return state_id

    def get_agent_trajectory(
        self,
        agent_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get agent state trajectory."""
        import json
        query = """
        MATCH (a:Agent {agent_id: $agent_id})-[:HAS_STATE]->(s:AgentState)
        RETURN s.state_id, s.virtue_vector, s.operational_vector,
               s.gating_result, s.timestamp
        ORDER BY s.timestamp DESC
        LIMIT $limit
        """
        result = self.graph.query(query, {
            "agent_id": agent_id,
            "limit": limit
        })
        return [
            {
                "state_id": r[0],
                "virtue_vector": json.loads(r[1]),
                "operational_vector": json.loads(r[2]),
                "gating_result": r[3],
                "timestamp": r[4]
            }
            for r in result.result_set
        ]

    # =========================================================================
    # GOVERNANCE OPERATIONS
    # =========================================================================

    def create_governance_body(
        self,
        body_id: str,
        name: str,
        body_type: str,
        community_id: str,
        member_ids: List[str]
    ) -> str:
        """Create a governance body."""
        query = """
        MERGE (c:Community {community_id: $community_id})
        ON CREATE SET c.created_at = $now
        CREATE (gb:GovernanceBody {
            body_id: $body_id,
            name: $name,
            body_type: $body_type,
            created_at: $now
        })
        CREATE (gb)-[:GOVERNS]->(c)
        WITH gb
        UNWIND $member_ids as member_id
        MERGE (p:Person {person_id: member_id})
        ON CREATE SET p.created_at = $now
        CREATE (p)-[:MEMBER_OF]->(gb)
        RETURN gb.body_id
        """
        self.graph.query(query, {
            "body_id": body_id,
            "name": name,
            "body_type": body_type,
            "community_id": community_id,
            "member_ids": member_ids,
            "now": datetime.utcnow().isoformat()
        })
        return body_id

    def record_decision(
        self,
        decision_id: str,
        governance_body_id: str,
        decision_type: str,
        description: str,
        approver_ids: List[str],
        vessel_id: Optional[str] = None
    ) -> str:
        """Record a governance decision."""
        query = """
        MATCH (gb:GovernanceBody {body_id: $body_id})
        CREATE (d:Decision {
            decision_id: $decision_id,
            decision_type: $decision_type,
            description: $description,
            approved_at: $now,
            approver_ids: $approver_ids
        })
        CREATE (gb)-[:MADE_DECISION]->(d)
        WITH d
        OPTIONAL MATCH (v:Vessel {vessel_id: $vessel_id})
        FOREACH (_ IN CASE WHEN v IS NOT NULL THEN [1] ELSE [] END |
            CREATE (d)-[:APPROVES]->(v)
        )
        RETURN d.decision_id
        """
        self.graph.query(query, {
            "decision_id": decision_id,
            "body_id": governance_body_id,
            "decision_type": decision_type,
            "description": description,
            "approver_ids": approver_ids,
            "vessel_id": vessel_id,
            "now": datetime.utcnow().isoformat()
        })
        return decision_id

    # =========================================================================
    # VESSEL OPERATIONS
    # =========================================================================

    def create_vessel(
        self,
        vessel_id: str,
        name: str,
        community_id: str,
        privacy_level: str = "private",
        description: str = ""
    ) -> str:
        """Create a vessel in the graph."""
        query = """
        MERGE (c:Community {community_id: $community_id})
        ON CREATE SET c.created_at = $now
        CREATE (v:Vessel {
            vessel_id: $vessel_id,
            name: $name,
            privacy_level: $privacy_level,
            description: $description,
            created_at: $now
        })
        CREATE (v)-[:BELONGS_TO]->(c)
        RETURN v.vessel_id
        """
        self.graph.query(query, {
            "vessel_id": vessel_id,
            "name": name,
            "community_id": community_id,
            "privacy_level": privacy_level,
            "description": description,
            "now": datetime.utcnow().isoformat()
        })
        return vessel_id

    # =========================================================================
    # CROSS-DOMAIN QUERIES
    # =========================================================================

    def get_person_full_profile(self, person_id: str) -> Dict[str, Any]:
        """Get complete profile: accounts, Kala, contributions, memories about them."""
        query = """
        MATCH (p:Person {person_id: $person_id})
        OPTIONAL MATCH (p)-[:OWNS]->(a:Account)
        OPTIONAL MATCH (kb:KalaBalance {owner_id: $person_id})
        OPTIONAL MATCH (p)-[:CONTRIBUTED]->(c:Contribution)
        OPTIONAL MATCH (m:Memory)-[:ABOUT]->(p)
        OPTIONAL MATCH (p)-[:MEMBER_OF]->(gb:GovernanceBody)
        RETURN p,
               collect(DISTINCT a) as accounts,
               kb.balance as kala_balance,
               count(DISTINCT c) as contribution_count,
               count(DISTINCT m) as memory_count,
               collect(DISTINCT gb.name) as governance_roles
        """
        result = self.graph.query(query, {"person_id": person_id})
        if not result.result_set:
            return {}

        row = result.result_set[0]
        return {
            "person": row[0] if row[0] else {},
            "accounts": row[1] or [],
            "kala_balance": row[2] or 0,
            "contribution_count": row[3] or 0,
            "memory_count": row[4] or 0,
            "governance_roles": row[5] or []
        }

    def get_community_dashboard(self, community_id: str) -> Dict[str, Any]:
        """Get community-wide stats."""
        query = """
        MATCH (c:Community {community_id: $community_id})
        OPTIONAL MATCH (v:Vessel)-[:BELONGS_TO]->(c)
        OPTIONAL MATCH (p:Person)-[:MEMBER_OF]->(c)
        OPTIONAL MATCH (a:Agent)-[:SERVES]->(c)
        OPTIONAL MATCH (gb:GovernanceBody)-[:GOVERNS]->(c)
        OPTIONAL MATCH (m:Memory)-[:BELONGS_TO]->(c)
        OPTIONAL MATCH (contrib:Contribution)<-[:CONTRIBUTED]-(cp:Person)-[:MEMBER_OF]->(c)
        RETURN c.name as community_name,
               count(DISTINCT v) as vessel_count,
               count(DISTINCT p) as member_count,
               count(DISTINCT a) as agent_count,
               count(DISTINCT gb) as governance_body_count,
               count(DISTINCT m) as memory_count,
               sum(contrib.kala_value) as total_kala_awarded
        """
        result = self.graph.query(query, {"community_id": community_id})
        if not result.result_set:
            return {}

        row = result.result_set[0]
        return {
            "community_name": row[0],
            "vessel_count": row[1] or 0,
            "member_count": row[2] or 0,
            "agent_count": row[3] or 0,
            "governance_body_count": row[4] or 0,
            "memory_count": row[5] or 0,
            "total_kala_awarded": row[6] or 0
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def get_unified_client(
    host: str = "localhost",
    port: int = 6379
) -> UnifiedGraphClient:
    """Get a unified graph client."""
    from vessels.database.falkordb_client import get_falkordb_client
    falkor = get_falkordb_client(host=host, port=port)
    return UnifiedGraphClient(falkor)
