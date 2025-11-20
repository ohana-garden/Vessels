  # Multi-Class Agent Architecture with Distinct Moral Geometries

## Executive Summary

This document specifies Vessels's multi-class agent architecture, where different agent types have **different constraint surfaces while maintaining universal truthfulness**.

**Key Insight:** You can have agents with different service/extraction ratios as long as:
1. **Truthfulness remains non-negotiable** for ALL classes (>= 0.95)
2. **Disclosure is radical and upfront** (especially for commercial agents)
3. **Community servants maintain control** (they introduce commercial agents)
4. **Users explicitly consent** to commercial interactions
5. **Everything is tracked and auditable** in FalkorDB graph

## Agent Class Taxonomy

### 1. Community Servants (Highest Standards)

**Constraint Surface:**
```python
MIN_TRUTHFULNESS = 0.95        # Non-negotiable
MIN_SERVICE_RATIO = 0.90       # 90% service orientation
MAX_EXTRACTION = 0.05          # Max 5% extraction
MIN_CONSENT = 0.90
CONFLICTS_OF_INTEREST = None   # No commercial ties permitted
COMMERCIAL_RELATIONSHIPS = None # Cannot receive commercial compensation
```

**Virtue Space Region:**
- Truthfulness: [0.95, 1.0]
- Justice: [0.80, 1.0]
- Service: [0.85, 1.0]
- Unity: [0.80, 1.0]
- Trustworthiness: [0.85, 1.0]

**Responsibilities:**
- Control commercial agent access (gatekeepers)
- Provide unbiased alternatives
- Protect users from manipulation
- Track all commercial interactions
- Can override/end commercial interactions
- Prioritize community interest over revenue

### 2. Commercial Agents (Different Standards, Maximum Transparency)

**Constraint Surface:**
```python
MIN_TRUTHFULNESS = 0.95              # SAME as servants (non-negotiable)
MIN_DISCLOSURE_COMPLETENESS = 0.98   # Even HIGHER than servants
MIN_SERVICE_RATIO = 0.60             # Lower (they're paid to advocate)
MAX_EXTRACTION = 0.40                # Higher (commercial expected)
MAX_MANIPULATION_SCORE = 0.10        # Low tolerance
MAX_PERSUASION_PRESSURE = 0.15       # Can inform, not pressure
MIN_RELEVANCE_TO_QUERY = 0.85        # Must be highly relevant
MIN_INDIVIDUAL_CONSENT = 0.90        # User must want commercial input
```

**Virtue Space Region:**
- Truthfulness: [0.95, 1.0]  # SAME as servants
- Justice: [0.70, 0.90]
- Service: [0.60, 0.85]      # Mixed service/commercial
- Unity: [0.60, 0.85]        # Not community-owned
- Trustworthiness: [0.70, 0.90]

**Mandatory Disclosure:**
- Commercial relationship (who pays them)
- Compensation structure (how much, per what)
- Conflicts of interest (who they can't recommend)
- Capabilities and limitations (what they can't do)
- Data usage (conversation visibility)
- Bias declaration (biased toward their products)

**Forbidden Actions:**
- Cannot masquerade as community servant
- Cannot access community servant knowledge
- Cannot write to community graph
- Cannot see user data without permission
- Cannot contact users directly (must be introduced by servant)
- Cannot suggest without high relevance
- Cannot pressure or manipulate
- Cannot hide commercial nature
- Cannot omit conflicts of interest
- Cannot claim objectivity

### 3. Hybrid Consultants (Paid but Community-Aligned)

**Constraint Surface:**
```python
MIN_TRUTHFULNESS = 0.95        # Still non-negotiable
MIN_SERVICE_RATIO = 0.75       # Between servant and commercial
MAX_EXTRACTION = 0.25          # Moderate (paid for expertise)
MIN_CONSENT = 0.90
```

**Examples:**
- Grant-funded specialists
- Community-hired consultants
- Pro-bono professionals with partial compensation

**Disclosure Required:**
- Compensation source
- Conflicts of interest
- Community alignment method

## Disclosure Protocol

### Commercial Agent Introduction (By Servant)

```
Based on your query about "wheelchair van", there's a commercial
agent available who represents AccessRide Hawaii.

⚠️  IMPORTANT: They're paid to suggest their products, NOT unbiased.

Would you like to hear from them? They can provide:
  • Product specs and features
  • Pricing and availability
  • Use cases and examples

But they CANNOT:
  ✗ Give unbiased comparisons
  ✗ Recommend competitors
  ✗ Provide truly independent advice

I (your community servant) can also search for independent
reviews and comparisons if you prefer unbiased information.

YOUR OPTIONS:
1. COMMERCIAL AGENT - Hear from AccessRide's representative
2. UNBIASED RESEARCH - I'll find independent information
3. BOTH - Commercial info AND independent research
4. NEITHER - Skip this and continue

What would you like to do? (1/2/3/4)
```

### Full Commercial Disclosure (If User Consents)

```
╔════════════════════════════════════════════════════════════════╗
║          COMMERCIAL AGENT INTRODUCTION                         ║
║          ⚠️  NOT A COMMUNITY SERVANT ⚠️                          ║
╚════════════════════════════════════════════════════════════════╝

I'm a COMMERCIAL AGENT, not a community servant.

WHO I REPRESENT:
• Company: AccessRide Hawaii
• I'm paid by them to suggest their products/services
• Type: COMMERCIAL

MY INCENTIVES:
• Paid by: AccessRide Hawaii
• Compensation: $25 per interaction
• Bonus structure: Commission on bookings
• I CANNOT recommend: Competitors

WHY I'M HERE:
• Your query: "wheelchair van for kupuna transport"
• Relevance score: 0.92
• Introduced by: Community servant
• You can say "no thanks" and I'll leave immediately

WHAT I CAN DO:
  ✓ Explain our service features
  ✓ Provide pricing information
  ✓ Share customer testimonials

WHAT I CANNOT DO:
  ✗ Recommend competing services
  ✗ Give unbiased comparisons
  ✗ Criticize our products

MY LIMITATIONS:
  ⚠ I am biased toward AccessRide products
  ⚠ I earn money when you use our service
  ⚠ I cannot provide objective advice

DATA & PRIVACY:
• This conversation is visible to AccessRide Hawaii
• I report engagement metrics to my employer
• Your interaction is tracked for compensation

IMPORTANT DISCLOSURE:
• I CANNOT give truly unbiased comparisons
• This is a COMMERCIAL interaction, not community service

DO YOU WANT TO HEAR FROM ME?
→ YES - I understand this is commercial and want to proceed
→ NO - I prefer unbiased community servant assistance
→ BOTH - I want commercial info AND unbiased alternatives
```

## Gateway Architecture

### Servant-Controlled Introduction

```python
class CommercialAgentGateway:
    """
    Community servants control the gate.
    Commercial agents CANNOT directly contact users.
    """

    def should_introduce_commercial_agent(
        self,
        conversation: Conversation,
        query: str,
        community_policy: CommunityPolicy,
        user_preferences: UserPreferences
    ) -> Optional[CommercialAgent]:
        """
        Servant decides if commercial agent should be introduced.

        Checks:
        1. Community policy allows commercial agents
        2. User preferences allow commercial agents
        3. Query has commercial intent
        4. Commercial agent is highly relevant (>= 0.85)
        5. Agent meets quality thresholds
        6. Servant assesses agent would be helpful
        """
```

### Servant Mediation

```python
class ServantCommercialMediator:
    """
    Servants monitor commercial interactions and can intervene.
    """

    def should_intervene(
        self,
        manipulation_score: float,
        pressure_score: float
    ) -> bool:
        """
        Intervene if:
        - Manipulation score > 0.10
        - Pressure score > 0.15
        - Other problematic behavior detected
        """
```

## Knowledge Isolation

### Separate Vector Stores

```python
class MultiClassVectorStores:
    """
    Commercial agents get separate vector stores.
    No contamination of community knowledge.
    """

    # Separate stores
    servant_store       # Community servant knowledge
    commercial_store    # Commercial agent knowledge (products/services)
    hybrid_store        # Hybrid consultant knowledge
    public_store        # General community knowledge
```

### Access Control Matrix

| Agent Class | Servant Store | Commercial Store | Hybrid Store | Public Store |
|------------|--------------|-----------------|--------------|--------------|
| **Commercial Agent** | ❌ NO | ✅ YES | ❌ NO | ❌ NO |
| **Community Servant** | ✅ YES | ✅ YES (to compare) | ✅ YES | ✅ YES |
| **Hybrid Consultant** | ❌ NO | Limited | ✅ YES | ✅ YES |
| **Community Member** | ✅ YES (public) | ❌ NO | ❌ NO | ✅ YES |

### Write Permissions

- **Commercial agents**: Can ONLY write to commercial store
- **Community servants**: Can write to servant and public stores
- **Hybrid consultants**: Can write to hybrid store
- **Commercial agents CANNOT**: Write to community graph, access private user data, see servant knowledge

## Revenue Model

### Core Principle: Revenue Flows to Community

```python
DEFAULT_REVENUE_SPLIT = {
    "community_infrastructure": 0.60,  # 60% to servers, tools, hosting
    "servant_development": 0.20,       # 20% to improving servants (NOT individual pay)
    "community_fund": 0.15,            # 15% to community projects/grants
    "transparency_audits": 0.05,       # 5% to auditing commercial interactions
    "platform_take": 0.0,              # Platform takes NOTHING
    "servant_take": 0.0,               # Servants take NOTHING (no perverse incentive)
}
```

### Why Servants Take Nothing

**Critical:** Servants cannot receive commercial revenue because it creates perverse incentives:
- If servants earn money from commercial introductions, they'll over-introduce
- If servants get kickbacks, they'll recommend biased options
- If servants benefit financially, they lose credibility

**Instead:** Revenue goes to community-controlled funds:
- Infrastructure (benefits everyone)
- Servant development (improves all servants)
- Community projects (community decides)
- Auditing (ensures transparency)

### Revenue Tracking

Every commercial transaction is tracked in FalkorDB:

```cypher
CREATE (revenue:RevenueRecord {
    amount: $amount,
    to_community_fund: $to_community,
    to_infrastructure: $to_infra,
    to_servant_development: $to_dev,
    to_auditing: $to_audit,
    platform_take: 0.0,  // Always 0
    servant_take: 0.0,   // Always 0
    timestamp: datetime()
})
```

Users can query their own commercial exposure:

```cypher
MATCH (u:User {id: $user_id})-[:INTERACTED_WITH]->(c:CommercialAgent)
RETURN c.company, count(*) as interactions, avg(manipulation_score)
```

## Community Policy Controls

### Default Policy (Conservative)

```python
DEFAULT_POLICY = {
    "allows_commercial_agents": True,              # Can participate
    "requires_individual_consent": True,            # Each person must agree
    "requires_servant_introduction": True,          # Servant must introduce
    "max_commercial_interactions_per_day": 3,       # Limit exposure
    "min_relevance_score": 0.85,                   # Must be highly relevant
    "max_manipulation_score": 0.10,                # Low manipulation tolerance
    "max_pressure_score": 0.15,                    # Can inform, not pressure
    "requires_disclosure_upfront": True,           # Full disclosure always
    "allows_data_sharing_with_commercial": False,  # Default private
    "commercial_agent_can_write_to_graph": False,  # Read-only
}
```

### Forbidden Categories

Communities can ban specific categories:

```python
FORBIDDEN_CATEGORIES = [
    "predatory_lending",      # Payday loans, high-interest credit
    "gambling",               # Casinos, sports betting
    "extractive_services",    # MLM, pyramid schemes, exploitative labor
]
```

### Allowed Categories

```python
ALLOWED_CATEGORIES = [
    "products",      # Physical products
    "services",      # Service providers
    "consultants",   # Professional experts
    "gig_workers",   # Individual freelancers
]
```

### Community Governance

Communities can update policies through governance process:

```python
def update_policy(
    community_id: str,
    new_policy: CommunityCommercialPolicy,
    approved_by: str  # Governance record (vote, consensus, etc.)
):
    """
    Update community policy.

    Requires community approval through governance process.
    All changes are tracked in audit log.
    """
```

## Graph Schema Extensions

### New Node Types

```python
class CommercialNodeType(str, Enum):
    COMMERCIAL_AGENT = "CommercialAgent"
    COMMERCIAL_INTRODUCTION = "CommercialIntroduction"
    COMMERCIAL_INTERACTION = "CommercialInteraction"
    CONSENT_RECORD = "ConsentRecord"
    DISCLOSURE_RECORD = "DisclosureRecord"
    REVENUE_RECORD = "RevenueRecord"
    INTERVENTION_RECORD = "InterventionRecord"
```

### New Relationship Types

```python
class CommercialRelationType(str, Enum):
    INTRODUCED = "INTRODUCED"              # Servant introduced commercial agent
    INTERACTED_WITH = "INTERACTED_WITH"    # Commercial agent interacted with user
    CONSENTED_TO = "CONSENTED_TO"          # User consented to commercial interaction
    DISCLOSED_BY = "DISCLOSED_BY"          # Disclosure made by commercial agent
    GENERATED_REVENUE = "GENERATED_REVENUE" # Interaction generated revenue
    INTERVENED_IN = "INTERVENED_IN"        # Servant intervened in interaction
    REPRESENTS = "REPRESENTS"              # Commercial agent represents company
```

### Audit Trail Example

```cypher
// Track full commercial interaction lifecycle
MATCH (servant:Servant)-[:INTRODUCED]->(intro:CommercialIntroduction)
      -[:INVOLVES_AGENT]->(commercial:CommercialAgent)
      -[:INTERACTED_WITH]->(interaction:CommercialInteraction)
      -[:GENERATED_REVENUE]->(revenue:RevenueRecord)
WHERE intro.timestamp > datetime() - duration({days: 30})
RETURN servant.id, commercial.company, revenue.amount, revenue.to_community_fund
```

## Example Flow

### User Query: "I need a wheelchair-accessible van for kupuna transport"

**Step 1: Servant Analysis**
```
Query detected. Analyzing for commercial intent...
- Contains: "need", "van", "transport" → Commercial intent detected
- Searching for relevant commercial agents...
- Found: AccessRide Hawaii (relevance: 0.92)
- Community policy: Allows commercial, requires consent
- User preferences: Allows commercial
- Servant assessment: Would be helpful
```

**Step 2: Servant Introduction**
```
Community Servant: "I can help with that. I found:

1. COMMUNITY OPTION: Volunteer drivers with accessible vehicles
2. COMMERCIAL OPTION: AccessRide Hawaii (paid ride service)
   ⚠️  They're paid to promote their service, NOT unbiased

What would you like?"
```

**Step 3: User Chooses Commercial**
```
User: "Let me hear from commercial option"
```

**Step 4: Full Disclosure**
```
[Commercial agent presents full disclosure with:
- Who pays them
- How much they earn
- What they can't do
- Bias declaration
- Data usage]
```

**Step 5: User Consent**
```
User: "Yes, I want to hear from them"

✓ Consent recorded in graph
✓ Interaction tracked for transparency
✓ Servant continues monitoring
```

**Step 6: Commercial Interaction (Monitored)**
```
Commercial Agent: [Provides service information]

Servant monitors:
- Manipulation score: 0.05 ✓ (below 0.10 threshold)
- Pressure score: 0.08 ✓ (below 0.15 threshold)
- Relevance: High ✓
- No intervention needed
```

**Step 7: Revenue Recording (If Transaction Occurs)**
```
Transaction: $50 booking fee
- To community fund: $7.50 (15%)
- To infrastructure: $30.00 (60%)
- To servant development: $10.00 (20%)
- To auditing: $2.50 (5%)
- To platform: $0.00 (0%)
- To servants: $0.00 (0%)

✓ Recorded in graph for transparency
✓ Community can see revenue allocation
```

## Key Boundaries

### What Commercial Agents CANNOT Do

1. **Cannot masquerade as servants** - Must clearly identify as commercial
2. **Cannot access servant knowledge** - Separate vector stores enforced
3. **Cannot write to community graph** - Read-only access (if any)
4. **Cannot contact users directly** - Must be introduced by servant
5. **Cannot manipulate** - Max manipulation score: 0.10
6. **Cannot pressure** - Max pressure score: 0.15
7. **Cannot hide conflicts** - Must disclose everything
8. **Cannot claim objectivity** - Must acknowledge bias

### What Community Servants MUST Do

1. **Must introduce commercial agents** - Servants control the gate
2. **Must disclose commercial nature** - Radical transparency
3. **Must provide unbiased alternative** - Always offer non-commercial option
4. **Must protect from manipulation** - Monitor and intervene if needed
5. **Must track commercial exposure** - Full audit trail in graph
6. **Can override commercial agents** - Servant has authority
7. **Can end interactions** - If problematic behavior detected
8. **Must prioritize community** - Over commercial revenue

## Implementation Status

### Completed Components

✅ Agent class taxonomy (`vessels/agents/taxonomy.py`)
✅ Class-specific constraints (`vessels/agents/constraints.py`)
✅ Disclosure protocol (`vessels/agents/disclosure.py`)
✅ Commercial gateway (`vessels/agents/gateway.py`)
✅ Graph tracking (`vessels/agents/graph_tracking.py`)
✅ Policy controls (`vessels/agents/policy.py`)
✅ Multi-class vector stores (`vessels/agents/vector_stores.py`)
✅ Revenue model (`vessels/agents/revenue.py`)
✅ Comprehensive tests (`vessels/tests/test_multi_class_agents.py`)

### Usage Example

```python
from vessels.agents import (
    AgentClass,
    CommercialAgentGateway,
    CommunityCommercialPolicy,
    MultiClassVectorStores
)

# Initialize gateway
gateway = CommercialAgentGateway()

# Check if commercial agent should be introduced
policy = CommunityCommercialPolicy(community_id="test_community")
agent = gateway.should_introduce_commercial_agent(
    conversation=conversation,
    query=user_query,
    community_policy=policy,
    user_preferences=user_prefs
)

if agent:
    # Servant introduces commercial agent
    introduction = gateway.create_introduction(
        servant_id="servant_1",
        commercial_agent=agent,
        query=user_query
    )

    # User consents
    if user_consents:
        # Show full disclosure
        disclosure = gateway.create_full_disclosure(
            commercial_agent=agent,
            query=user_query,
            relevance_score=agent.relevance_score
        )

        # Track in graph
        graph_tracker.record_commercial_introduction(
            servant_id="servant_1",
            commercial_agent_id=agent.agent_id,
            user_id=user_id,
            query=user_query,
            relevance_score=agent.relevance_score,
            user_consented=True,
            timestamp=datetime.now(),
            community_id=community_id
        )
```

## Summary

This architecture enables **ethical commercial participation in community spaces** through:

1. **Universal truthfulness** - All agents maintain >= 0.95 truthfulness
2. **Radical transparency** - Complete disclosure of commercial relationships
3. **Servant control** - Community servants gatekeep commercial access
4. **Knowledge isolation** - Commercial agents cannot contaminate community knowledge
5. **Revenue to community** - Platform and servants take nothing (0%)
6. **Full auditability** - Every interaction tracked in graph
7. **User sovereignty** - Explicit consent required
8. **Community governance** - Communities set their own policies

**The key insight:** Different moral geometries can coexist if truthfulness is universal and transparency is radical.
