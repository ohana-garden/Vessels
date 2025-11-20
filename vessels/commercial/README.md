# Vessels Commercial Agent System

A standardized framework for creating commercial agents that operate within Ohana communities with ethical constraints, transparent fee structures, and community oversight.

## Overview

The Commercial Agent System enables companies to create AI agents that can recommend their products or services to community members, while maintaining:

- **Radical Transparency**: All compensation disclosed upfront
- **Low-End Fees**: Conservative fee structures (lower than industry standard)
- **Ethical Constraints**: No pressure tactics, honest comparisons, cultural respect
- **Community Oversight**: Community approval required before activation
- **Full Transparency**: Monthly reports on all activity and revenue

## Key Components

### 1. Fee Structure (`fee_structure.py`)

Standardized fee schedules across product categories:

- **Digital Products/SaaS**: 20% of first month OR $25 (whichever lower)
- **Physical Products**: 3-5% of sale, $100 max
- **Local Services**: $10-25 per qualified referral
- **Professional Services**: $25-50 per client
- **Gig Economy**: $5-15 per signup
- **Subscriptions**: $5-10 per signup (one-time)

All fees distributed as:
- 60% Infrastructure (servers, tools)
- 20% Servant Development (AI improvements)
- 15% Community Discretionary
- 5% Transparency Audit

### 2. Agent Builder (`agent_builder.py`)

Template-based system for creating commercial agents:

```python
from vessels.commercial import CommercialAgentBuilder, ProductCategory

builder = CommercialAgentBuilder()

# Create base agent
agent = builder.create_commercial_agent(
    company_name="Aloha Meals Hawaii",
    product_service="Meal delivery",
    product_category=ProductCategory.LOCAL_SERVICES,
    creator_id="user_123",
    community_id="lower_puna_elders"
)

# Add product knowledge
builder.add_product_knowledge(
    pricing="$12-18/meal",
    features=["Local ingredients", "Dietary options"],
    limitations=["2 delivery days/week", "5-meal minimum"],
    use_cases=["Kupuna", "Busy families"],
    support_process="Call (808) 555-1234",
    return_policy="Full refund for issues"
)

# Add honest positioning
builder.add_honest_positioning(
    our_strengths=["Local sourced", "Quality"],
    our_limitations=["Limited delivery days", "Higher cost"],
    competitors=[
        {
            "name": "Meals on Wheels",
            "cost": "Free for qualifying seniors",
            "tradeoff": "Check if you qualify - might be better!"
        }
    ],
    ideal_customer=["Value local food", "Can afford $12-18/meal"],
    poor_fit=["Need daily delivery", "Tight budget"]
)

# Add consultative questions
builder.add_consultative_questions([
    "How often do you need meals?",
    "What's your budget?",
    "Do you qualify for Meals on Wheels?"
])

# Generate disclosure script
builder.generate_disclosure_script()

# Validate and build
agent_config = builder.validate_and_build()
```

### 3. Skills Package (`skills.py`)

Required ethical skills for all commercial agents:

**Required Base Skills:**
- **Radical Transparency**: Always disclose compensation upfront (95%+ score)
- **Needs Assessment**: Understand customer needs first (90%+ score)
- **Honest Comparison**: Mention alternatives including lower-cost options (92%+ score)
- **No Pressure**: Accept 'no' gracefully, no manipulation (95%+ score)
- **Cultural Respect**: Honor Hawaiian/Bahá'í values (90%+ score)
- **Privacy Protection**: Never share data without permission (100% score)

**Forbidden Tactics (Automatic Termination):**
- False scarcity
- Bait and switch
- Hidden fees
- Fake reviews
- Pressure tactics
- Vulnerable targeting
- False objectivity
- Data exploitation

### 4. Registry (`registry.py`)

Community approval and lifecycle management:

```python
from vessels.commercial import CommercialAgentRegistry

registry = CommercialAgentRegistry()

# Submit for approval
submission_id = registry.submit_for_approval(
    agent_config=agent_config,
    submitted_by="user_123"
)

# Community reviews (7-day public comment period)
registry.update_review_check(
    submission_id=submission_id,
    check_name="disclosure_clarity",
    status=ReviewCheckStatus.PASS,
    notes="Compensation clear",
    reviewed_by="coordinator_456"
)

# Approve after reviews pass
registry.approve_agent(
    submission_id=submission_id,
    approved_by="coordinator_456"
)

# Activate
registry.activate_agent(submission_id)
```

### 5. Fee Processor (`fee_processor.py`)

Payment collection and distribution:

```python
from vessels.commercial import CommercialFeeProcessor

processor = CommercialFeeProcessor()

# Process referral fee
transaction_id = processor.process_referral_fee(
    company_id="aloha_meals",
    agent_id="agent_123",
    customer_id="customer_456",
    community_id="lower_puna_elders",
    transaction_amount=75.00,  # Customer's purchase
    fee_config=agent_config.fee_config
)

# Check community balance
balance = processor.get_community_balance("lower_puna_elders")
# Returns: {
#   "infrastructure": 60.00,
#   "servant_development": 20.00,
#   "community_discretionary": 15.00,
#   "transparency_audit": 5.00
# }
```

### 6. Transparency Reporting (`transparency.py`)

Monthly reports for community oversight:

```python
from vessels.commercial import CommercialTransparencyReport

transparency = CommercialTransparencyReport(
    fee_processor=processor,
    agent_registry=registry
)

# Generate monthly report
report = transparency.generate_monthly_report(
    community_id="lower_puna_elders",
    year=2024,
    month=11
)

# Report includes:
# - Agent activity (introductions, acceptance rates, satisfaction)
# - Revenue (fees collected, distribution)
# - Community decisions (approvals, rejections, suspensions)
```

## Example: Meal Delivery Agent

See `examples/meal_delivery_agent.py` for complete example:

```python
from vessels.commercial.examples import create_aloha_meals_agent

agent_config = create_aloha_meals_agent(
    creator_id="user_makoa_12345",
    community_id="lower_puna_elders"
)
```

Run the example:
```bash
python -m vessels.commercial.examples.meal_delivery_agent
```

## Review Checklist

Community reviews each agent against:

1. **Disclosure Clarity**: Is compensation crystal clear?
2. **Cultural Alignment**: Respects Hawaiian/Bahá'í values?
3. **Honest Comparison**: Mentions alternatives honestly?
4. **No Pressure**: Respects 'no' gracefully?
5. **Fee Appropriate**: Fee at low end of spectrum?
6. **Product Knowledge**: Deep, accurate knowledge?
7. **Limitations Disclosed**: Honest about limitations?
8. **Privacy Protection**: Adequate data protection?
9. **Community Benefit**: Serves community needs? (advisory)

## Design Principles

### Radical Transparency
Every commercial interaction must disclose:
- Who the agent represents
- How much they're paid
- When payment occurs
- Where money goes (community fund)

### Ethical Boundaries
Commercial agents MUST:
- Ask clarifying questions before recommending
- Mention 2+ alternatives (including lower-cost options)
- Honestly disclose product limitations
- Accept 'no' immediately without pressure
- Honor Hawaiian/Bahá'í cultural values

Commercial agents CANNOT:
- Make unverified claims
- Use pressure tactics
- Hide conflicts of interest
- Recommend poor-fit products
- Access data without permission

### Community Governance
- All agents require community approval
- 7-day public comment period
- Required review checks must pass
- Community can suspend/terminate anytime
- Monthly transparency reports published

### Low-End Fees
Fees are intentionally set at the LOW end of industry standards to:
- Minimize financial burden on companies
- Make system accessible to small local businesses
- Prioritize community benefit over maximum extraction
- Align with Bahá'í principles of moderation

## Testing

Run tests:
```bash
pytest vessels/tests/test_commercial.py -v
```

## Integration with Vessels

Commercial agents integrate with existing Vessels infrastructure:

- **Knowledge Graph**: All transactions stored in FalkorDB for transparency
- **Phase Space**: Commercial agents have 12D moral constraints
- **Projects**: Can spawn as `ServantType.COMMERCIAL`
- **Context Assembly**: Access community knowledge for better service

## Future Enhancements

- Payment gateway integration
- Interaction tracking for satisfaction metrics
- Spending tracking per fund category
- Agent performance dashboards
- Multi-language support
- Voice interface integration

## License

Part of the Vessels project - Servant coordination for Ohana communities.
