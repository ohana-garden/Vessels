# Kala: Valuing Community Contributions

## What Is Kala?

Kala is **not a currency**.

It's a value measurement unit that enables communities to track and recognize non-monetary contributions. Think of it like measuring distance in miles or weight in pounds - kala measures social value.

## The Dollar Peg

Kala is loosely pegged to the US dollar at a 1:1 ratio:

**1 kala ≈ $1 USD**

This peg serves as a reference point. It helps communities:

1. **Estimate value consistently** - Whether you're in Puna or Portland, you can understand what "50 kala" represents
2. **Record in-kind contributions** - Translate volunteer time, donated goods, and services into trackable units
3. **Recognize small acts** - Value the neighbor who drives kupuna to appointments or shares breadfruit
4. **Report to funders** - Show grantmakers the real community value being created

## Why Not Just Use Dollars?

Because kala measures **social value**, not financial transactions.

When Maria spends 3 hours helping Uncle Joe with his garden, that has real value to the community. But no money changed hands. No one needs a W-2 form. No one pays taxes.

Kala lets us say: "Maria contributed ~$45 worth of value" (3 hours × $15/hour) without creating a financial transaction.

## What Gets Valued in Kala?

Everything that contributes to community wellbeing:

### Time & Service
- Volunteer hours
- Elder care visits
- Meal preparation and delivery
- Transportation services
- Coordination and organizing

### Skills & Knowledge
- Teaching and mentoring
- Professional services (nursing, accounting, legal)
- Trades (plumbing, carpentry, electrical)
- Cultural knowledge sharing

### Resources
- Food donations
- Material goods
- Tool lending
- Facility access

### Creative & Cultural
- Music and art
- Storytelling
- Cultural practices
- Community celebrations

## Valuation Guidelines

The dollar peg provides rough equivalents:

### Time-Based Contributions

| Skill Level | Kala per Hour | Examples |
|-------------|---------------|----------|
| General volunteer | 15 kala | Meal delivery, basic yardwork, event help |
| Skilled service | 35 kala | Nursing, teaching, carpentry, organizing |
| Professional | 75 kala | Specialized consulting, complex coordination |
| Expert | 150 kala | High-level expertise, rare specialized knowledge |

### Resource-Based Contributions

Use market value as reference:
- 50 lbs breadfruit = ~30 kala (market value ~$30)
- Meal for 10 people = ~120 kala (food + prep time)
- Round-trip transport, 20 miles = ~15 kala (IRS mileage rate)

### Cultural & Social Contributions

Harder to quantify, but equally valuable:
- Leading a protocol = 50-100 kala (2-3 hours professional time)
- Organizing community gathering = 100-200 kala (coordination + execution)
- Teaching cultural practice = 35 kala/hour (skilled instruction)

## How Communities Use Kala

### Recording Contributions

When someone contributes, record:
1. Who contributed
2. What they contributed
3. Estimated kala value
4. When it happened

Example:
```
Maria delivered meals to 3 kupuna
- Time: 2 hours driving and visiting (2 × 35 = 70 kala)
- Transportation: 30 miles (30 × 0.67 = 20 kala)
- Total: 90 kala contribution
```

### Verification

Kala contributions can be:
- **Self-reported** - "I spent 5 hours organizing the hui"
- **Community-verified** - Others confirm the contribution
- **Coordinator-verified** - Program coordinator approves value

Verification builds trust and accuracy.

### Reporting

Generate reports showing:
- Total community value created: "Our community created 50,000 kala of value this quarter (≈$50,000)"
- Individual contributions: "Maria has contributed 450 kala this month"
- Program impact: "Elder care program generated 12,000 kala of care services"

These reports help with:
- Grant applications
- Impact measurement
- Community recognition
- Program evaluation

## What Kala Is NOT

### It's Not Money

You cannot:
- Pay bills with kala
- Exchange kala for cash
- Owe kala debt
- Charge interest on kala
- Create financial obligations with kala

### It's Not a Time Bank

Time banks track hours 1:1 (your hour = my hour).

Kala recognizes that different contributions have different value. An hour of expert consultation has more market value than an hour of yard work. The dollar peg helps reflect this reality.

### It's Not Cryptocurrency

No blockchain. No tokens. No speculation. No "to the moon."

Kala is just a measurement unit, like pounds or meters.

## The Philosophy

Kala acknowledges a simple truth: **Communities run on more than money**.

They run on:
- People showing up
- Skills being shared
- Resources being pooled
- Elders being cared for
- Knowledge being passed down
- Neighbors helping neighbors

Money measures some of this. But not all of it.

Kala measures what matters to communities, using the dollar as a familiar reference point.

## Implementation in Vessels

Vessels tracks kala through the `kala.py` module, which:

1. **Records contributions** with type, value, and metadata
2. **Manages accounts** for community members and organizations
3. **Generates reports** for grants and impact measurement
4. **Integrates with memory** so agents learn from contribution patterns
5. **Provides helpers** for common valuations (elder care, meals, transport)

See `kala.py` for the full implementation.

## Getting Started

```python
from kala import kala_system, ContributionType

# Record a volunteer contribution
kala_system.record_contribution(
    contributor_id="maria@ohana.org",
    contribution_type=ContributionType.CARE,
    description="Elder care visit - wellness check and medication reminder",
    kala_value=kala_system.value_time_contribution(
        hours=2.0,
        skill_level="skilled"  # Nursing skills
    ),
    tags=["elder_care", "kupuna", "wellness"]
)

# Record a food contribution
kala_system.record_contribution(
    contributor_id="ana@garden.org",
    contribution_type=ContributionType.FOOD,
    description="50 lbs fresh breadfruit from garden",
    kala_value=kala_system.value_resource_contribution(
        resource_description="50 lbs breadfruit",
        market_value_usd=30.0
    ),
    tags=["food", "produce", "local"]
)

# Get community total
report = kala_system.get_community_total()
print(f"Community value created: {report['total_kala']} kala")
print(f"USD equivalent: ${report['total_usd_equivalent']}")
```

## Questions & Answers

**Q: Why not just track hours?**
A: Because an hour of professional nursing is more valuable than an hour of weeding. The dollar peg helps recognize this.

**Q: Isn't this just capitalism?**
A: No. We're measuring value without creating financial transactions. No money changes hands. No one gets taxed. No one goes into debt.

**Q: Who decides the value?**
A: Communities do. The valuation guidelines are starting points. Local communities can adjust based on their context.

**Q: What if someone inflates their contributions?**
A: Use verification. Build trust. Remember - kala isn't money. There's no financial incentive to cheat.

**Q: Can organizations use kala?**
A: Yes. Schools, nonprofits, and community groups can track both contributions they receive and contributions they make.

**Q: Does this replace grants?**
A: No. Grants provide actual money for actual expenses. Kala helps show grantmakers the additional value communities create beyond just spending grant dollars.

---

*Kala: Measuring what matters to communities.*

*Pegged to dollars for clarity. Valued for community.*
