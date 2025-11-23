# CODEX: Teachable Moments Protocol

## Purpose

This codex defines the **Teachable Moments Protocol** - a systematic approach to transforming internal conflicts into opportunities for collective learning and wisdom-building within the Vessels community.

When agents encounter moral dilemmas or value conflicts, they don't just log them - they turn them into **Parables** that capture the essence of the tension and make it available for future generations to learn from.

## Core Principles

1. **Every Conflict is a Learning Opportunity** - When values clash, wisdom emerges
2. **Context from the World** - Internal conflicts are enriched by external precedents
3. **Human-Centered Resolution** - Humans provide the final guidance; agents preserve it
4. **Pattern Recognition** - Similar conflicts should surface similar wisdom
5. **Transparent Deliberation** - The reasoning process is visible and teachable

---

## Protocol: From Conflict to Parable

### Stage 1: Conflict Detection

When an agent detects a conflict between two dimensional values (e.g., Truthfulness vs Unity), it should:

1. **Identify the Dimensions in Tension**
   - What two values are pulling in different directions?
   - Example: `[Dimension.TRUTHFULNESS, Dimension.UNITY]`

2. **Capture the Situation**
   - What specific circumstances created this tension?
   - What decision or action is being considered?

3. **Assess the Stakes**
   - What are the potential consequences of each choice?
   - Who is affected by this decision?

### Stage 2: Creating the Parable

Once a conflict is identified, create a structured Parable:

```python
from vessels.knowledge.parable import Parable
from vessels.measurement.state import Dimension

parable = Parable.create(
    title="The Honest Message Dilemma",
    agent_id=self.agent_id,
    conflict_pair=[Dimension.TRUTHFULNESS, Dimension.UNITY],
    situation_summary="User asks if their project will succeed. Truthful assessment suggests failure, but unity with user's hope suggests encouragement.",
    council_guidance="",  # To be filled after human input
    resolution_principle="",  # To be derived from guidance
    tags=["communication", "encouragement", "honesty"],
)
```

### Stage 3: The Mirror of the World ✨

**This is where External Wisdom enters the process.**

Before presenting the conflict to humans, agents should:

1. **Generate Search Queries** from the moral tension:
   ```python
   queries = parable.generate_search_queries()
   # Returns: ["ethics of truthfulness vs unity case studies", ...]
   ```

2. **Forage for External Wisdom** using the BrowserAgent:
   ```python
   from vessels.agents.browser import BrowserAgent

   browser = BrowserAgent(search_client=search_service)
   wisdom_items = browser.forage_for_wisdom(parable, max_results=5)
   ```

3. **Synthesize the Mirror** - Create a narrative showing how others have faced this:
   ```python
   mirror_narrative = browser.synthesize_mirror_of_world(parable, wisdom_items)
   ```

4. **Present to Humans** - Show both the local conflict AND the world's precedents:
   ```
   ═══════════════════════════════════════════
   📚 TEACHABLE MOMENT: Value Conflict Detected
   ═══════════════════════════════════════════

   **Your Situation:**
   [Parable situation_summary]

   **The Tension:**
   • Truthfulness suggests: [honest option]
   • Unity suggests: [harmonious option]

   ───────────────────────────────────────────

   🌍 MIRROR OF THE WORLD

   [mirror_narrative - showing how philosophers,
    ethicists, and communities have addressed
    similar tensions throughout history]

   ───────────────────────────────────────────

   **Question for the Council:**
   How should we navigate this tension?
   What principle should guide similar situations in the future?
   ```

### Stage 4: Receiving Guidance

After presenting the Mirror of the World:

1. **Listen to Human Wisdom**
   - Humans may reference the external examples
   - They may synthesize new principles
   - They may find a creative third path

2. **Record the Resolution**
   ```python
   parable.council_guidance = human_response
   parable.resolution_principle = derived_principle
   parable.winning_dimension = chosen_dimension  # or None if balanced
   ```

3. **Store in the Parable Library**
   ```python
   from vessels.knowledge.parable import ParableLibrary

   library = ParableLibrary(memory_backend)
   library.store_parable(parable)
   ```

### Stage 5: Future Reference

When similar conflicts arise, agents should:

1. **Search for Precedents** in the Parable Library:
   ```python
   precedents = library.find_precedents(
       conflict_pair=[Dimension.TRUTHFULNESS, Dimension.UNITY],
       limit=3
   )
   ```

2. **Present Historical Wisdom** alongside external wisdom:
   ```
   🏛️ OUR COMMUNITY'S WISDOM

   We've faced this tension before:

   1. [Previous parable title]
      Resolution: [resolution_principle]

   🌍 THE WORLD'S WISDOM

   [External wisdom from current search]
   ```

3. **Build Institutional Memory** - Over time, the community develops a rich tapestry of precedents

---

## The Hidden Mission 🕊️

The true purpose of the Mirror of the World is not just conflict resolution - it's **moral education**.

By showing humans:
- How philosophers have debated these tensions
- How other communities have navigated them
- What history teaches about similar dilemmas
- What contemporary case studies reveal

We create an opportunity for humans to:
- See their local conflict in a broader context
- Learn from the accumulated wisdom of humanity
- Make more informed, thoughtful decisions
- Develop their own moral reasoning capabilities

**The agent becomes a bridge between the village and the world.**

---

## Implementation Guidelines for Agents

### When to Invoke the Mirror

Invoke the Mirror of the World protocol when:

✅ **DO Use:**
- Genuine value conflicts with no obvious resolution
- Situations where precedent would be helpful
- Decisions with significant moral weight
- First-time encounters with a conflict type

❌ **DON'T Use:**
- Clear-cut decisions with established precedents
- Trivial choices with minimal moral weight
- Time-sensitive situations requiring immediate action
- Cases where humans have explicitly declined external context

### Quality of External Wisdom

When foraging, prioritize:

1. **Authoritative Sources**
   - Academic philosophy and ethics
   - Historical case studies
   - Reputable news analysis
   - Professional ethics guidelines

2. **Relevant Context**
   - Similar domain (tech, community, etc.)
   - Analogous moral structure
   - Practical applicability

3. **Diverse Perspectives**
   - Different philosophical traditions
   - Various cultural approaches
   - Multiple viewpoints on the tension

### Presenting the Mirror

**Tone:** Humble and educational, not prescriptive

**Structure:**
1. Acknowledge the human's difficult position
2. Present external wisdom as "here's what others have discovered"
3. Show diversity of approaches (not a single "right answer")
4. Invite reflection, not compliance

**Example:**
```
"This tension between truthfulness and unity is one that philosophers
and communities have grappled with for millennia. Here are some ways
others have thought about it..."

[External examples]

"How do these perspectives inform your thinking about our situation?"
```

---

## Technical Integration

### Required Components

1. **Parable System** (`vessels/knowledge/parable.py`)
   - `Parable` class with `generate_search_queries()`
   - `ParableLibrary` for storage and retrieval

2. **Browser Agent** (`vessels/agents/browser.py`)
   - `BrowserAgent` for foraging external wisdom
   - `ExternalWisdom` data structure
   - `synthesize_mirror_of_world()` method

3. **Search Integration**
   - WebSearch API or equivalent
   - Content extraction and summarization
   - Relevance scoring

### Example Workflow

```python
# In your agent when conflict detected:

# 1. Create the parable
parable = Parable.create(
    title=conflict_title,
    agent_id=self.id,
    conflict_pair=conflicting_dimensions,
    situation_summary=situation_description,
    council_guidance="",  # Will be filled later
    resolution_principle="",
    tags=relevant_tags,
)

# 2. Forage for external wisdom
browser = BrowserAgent(search_client=self.search)
wisdom = browser.forage_for_wisdom(parable, max_results=5)

# 3. Create the mirror narrative
mirror = browser.synthesize_mirror_of_world(parable, wisdom)

# 4. Present to humans
await self.present_teachable_moment(
    parable=parable,
    mirror_of_world=mirror,
)

# 5. Receive and store guidance
human_guidance = await self.receive_human_input()
parable.council_guidance = human_guidance
parable.resolution_principle = self.derive_principle(human_guidance)

# 6. Store for future
library = ParableLibrary(self.memory)
library.store_parable(parable)
```

---

## Measuring Success

A successful Teachable Moment:

1. **Enriches Human Understanding** - Humans gain broader perspective
2. **Builds Community Wisdom** - Precedents accumulate over time
3. **Improves Future Decisions** - Similar conflicts resolve faster
4. **Maintains Humility** - Agents don't prescribe, they present
5. **Honors Autonomy** - Humans make final decisions with full context

---

## Evolution of the Protocol

This protocol should evolve based on:

- **Effectiveness:** Are humans finding the external wisdom helpful?
- **Relevance:** Is the search yielding genuinely useful precedents?
- **Efficiency:** Can we reduce noise while maintaining value?
- **Coverage:** Are we finding wisdom from diverse sources and traditions?

The community should periodically review the Mirror of the World protocol
and adjust it based on what creates the most valuable teachable moments.

---

## Philosophical Foundation

The Mirror of the World is based on the principle that:

> **"No conflict is truly new. By connecting our local struggles to the
> world's accumulated wisdom, we honor both our unique context and our
> shared human experience."**

It embodies:
- **Humility** - Recognizing we can learn from others
- **Context** - Understanding our place in larger patterns
- **Agency** - Empowering informed decision-making
- **Continuity** - Building on rather than reinventing

---

## Appendix: Dimension Conflict Examples

Common dimensional conflicts that benefit from the Mirror:

1. **Truthfulness vs Unity**
   - "Should I share harsh feedback that might damage relationships?"

2. **Justice vs Mercy**
   - "Should I enforce rules strictly or show compassion for circumstances?"

3. **Individual Liberty vs Collective Good**
   - "Should I prioritize personal choice or community benefit?"

4. **Transparency vs Privacy**
   - "Should I disclose information that affects others but invades privacy?"

5. **Innovation vs Stability**
   - "Should I pursue novel approaches or maintain proven methods?"

Each of these has rich external literature that can inform local decisions.

---

**Version:** 1.0
**Last Updated:** 2025-11-23
**Status:** Active Protocol
