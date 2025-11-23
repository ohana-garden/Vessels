# CODEX: Teachable Moments

**A Guide for Agents on Creating and Enriching Moral Precedents**

---

## Purpose

When agents encounter conflicts between competing values or dimensions, these moments represent opportunities for growth and wisdom. Rather than treating them as mere errors or edge cases, we preserve them as **Parables** - structured teachable moments that encode moral precedents.

This CODEX describes how agents should:

1. **Recognize** moral conflicts and tensions
2. **Record** them as Parables for future reference
3. **Enrich** them with external wisdom from the world
4. **Present** them to humans as contextualized teachable moments

---

## The Parable System

### What is a Parable?

A Parable is not just a log entry. It is a **story of values in tension**, captured with:

- **Conflict Pair**: The two dimensions at odds (e.g., TRUTHFULNESS vs. UNITY)
- **Situation**: What happened that created this tension
- **Council Guidance**: How humans or the community resolved it
- **Resolution Principle**: The general rule derived from this specific case
- **Winning Dimension**: Which value took precedence (if any)

### Why Parables?

Raw logs capture *what happened*. Parables capture *why it mattered* and *how wisdom emerged*.

Parables allow agents to:
- Learn from past conflicts without repeating them
- Understand nuanced value trade-offs
- Apply precedents to new situations
- Build a shared moral memory across the community

---

## The "Mirror of the World" Protocol

### Overview

When a Parable is created from an internal conflict, it represents a *local* resolution. But conflicts between values are not new - they echo through history, philosophy, law, and culture.

The **Mirror of the World** protocol enriches local Parables by finding their reflections in external wisdom:

- Historical examples
- Philosophical discussions
- Case studies
- Legal precedents
- Academic research
- Cultural narratives

### How It Works

```python
from vessels.knowledge.parable import Parable
from vessels.agents.browser import ParableBrowserAgent

# 1. Create or retrieve a Parable
parable = Parable.create(
    title="The Truth vs. Unity Dilemma",
    agent_id="agent_001",
    conflict_pair=[Dimension.TRUTHFULNESS, Dimension.UNITY],
    situation_summary="Agent needed to decide whether to reveal uncomfortable truth that might divide the community",
    council_guidance="The council advised prioritizing unity while finding gentler ways to approach truth",
    resolution_principle="Truth should be pursued, but timing and delivery matter for preserving unity"
)

# 2. Enrich with external wisdom
browser_agent = ParableBrowserAgent(search_tool)
enriched_parable = browser_agent.enrich_parable(parable)

# 3. Present to humans
report = browser_agent.format_discovery_report(enriched_parable)
print(report)
```

### What Gets Added

For each Parable, the Browser Agent:

1. **Generates Search Templates**: Converts abstract moral tensions into concrete queries
   - "TRUTHFULNESS vs UNITY ethical dilemma case studies"
   - "balancing TRUTHFULNESS and UNITY in practice"
   - "when TRUTHFULNESS conflicts with UNITY examples"

2. **Retrieves External Examples**: Searches for relevant precedents
   - Deduplicates by URL
   - Estimates relevance based on content matching
   - Ranks by quality and relevance

3. **Attaches as External Wisdom**: Each example includes:
   - Title and URL for reference
   - Snippet/excerpt for context
   - Relevance score (High/Medium/Low)
   - Source query that found it

---

## Guidelines for Agents

### When to Create Parables

**DO** create Parables when:
- Two or more dimensions are in genuine tension
- Human guidance or council input helped resolve the conflict
- The situation represents a precedent-setting case
- The resolution could inform future decisions

**DON'T** create Parables for:
- Routine operations with no value conflicts
- Technical errors or bugs
- Simple preference choices
- Situations with clear, existing precedents

### When to Enrich with External Wisdom

**DO** enrich Parables when:
- The conflict involves complex ethical dimensions
- Humans could benefit from historical context
- The situation is novel or unfamiliar
- You're presenting the Parable as a teachable moment

**DON'T** enrich when:
- The conflict is purely internal/technical
- External examples might confuse rather than clarify
- Privacy concerns require keeping the situation private
- The Parable is still being actively resolved

### How to Present Enriched Parables

When showing humans an enriched Parable:

1. **Start with the Local Context**
   - Explain the specific situation that occurred
   - Describe the values in tension
   - Share what made this moment difficult

2. **Reveal the Mirror**
   - Present the external wisdom report
   - Frame it as: "This tension you feel has appeared before..."
   - Let humans see they're part of a larger story

3. **Invite Reflection**
   - Ask how the external examples resonate
   - Explore similarities and differences
   - Help humans extract their own insights

4. **Capture the Wisdom**
   - Record any new insights from the conversation
   - Update the Parable's resolution principle if refined
   - Store for future reference

---

## Example: A Full Teachable Moment

### The Setup

```
Agent: "I've noticed something that might interest you. Earlier today,
I encountered a tension between TRUTHFULNESS and UNITY.

A community member asked for my honest assessment of their project.
My analysis revealed significant flaws, but sharing them publicly
could embarrass them and create division in the group.

I consulted the Council, and we decided to share the truth privately
first, giving them a chance to address issues before broader discussion."
```

### The Mirror

```
Agent: "🌍 The World as a Mirror

Your conflict (TRUTHFULNESS vs UNITY) echoes through history and philosophy:

1. 🎯 **Kant vs. Lying to the Murderer at the Door**
   _The famous ethical dilemma where Kant argued absolute truth-telling,
   even when a murderer asks where your friend is hiding..._

2. 🎯 **The Pentagon Papers Case**
   _Daniel Ellsberg's decision to leak classified documents revealing
   government deception about the Vietnam War, balancing truth-telling
   against national unity..._

3. 📌 **Radical Honesty vs. Compassionate Communication**
   _The debate in psychology between Brad Blanton's Radical Honesty
   movement and Marshall Rosenberg's Nonviolent Communication..._
```

### The Reflection

```
Human: "Interesting! The Kant example shows the extreme - we definitely
don't want absolute truth at all costs. But the Pentagon Papers shows
sometimes unity built on lies is worse than the temporary division
truth creates."

Agent: "Yes! And your specific case seems more like the third example -
not a crisis requiring whistleblowing, but everyday communication where
TRUTH can be honored alongside UNITY through thoughtful delivery."
```

### The Capture

```python
# The refined principle gets stored
parable.resolution_principle = """
Truth-telling serves UNITY when delivered with care for timing,
audience, and the recipient's dignity. Not all truths need to be
public; some are better shared privately first. The goal is not
just honesty, but honesty in service of collective growth.
"""

# Store in the ParableLibrary
library.store_parable(parable)
```

---

## Technical Integration

### For Agent Developers

#### Setting Up the Browser Agent

```python
from vessels.agents.browser import ParableBrowserAgent, MockSearchTool
from vessels.knowledge.parable import ParableLibrary

# In development, use the mock tool
search_tool = MockSearchTool()

# In production, integrate with real search (e.g., Google Custom Search, Bing API)
# search_tool = GoogleSearchTool(api_key=settings.GOOGLE_API_KEY)

browser_agent = ParableBrowserAgent(search_tool)
```

#### Implementing Custom Search Tools

Your search tool must implement the `SearchToolInterface`:

```python
from typing import List, Dict

class MySearchTool:
    def execute(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Returns list of dicts with keys: 'title', 'url', 'snippet'
        """
        # Your search implementation
        results = my_search_api.search(query, max_results=limit)

        return [
            {
                'title': r.title,
                'url': r.url,
                'snippet': r.description
            }
            for r in results
        ]
```

#### Retrieving and Using Parables

```python
# Find precedents for a specific conflict
precedents = library.find_precedents(
    conflict_pair=[Dimension.TRUTHFULNESS, Dimension.UNITY],
    limit=3
)

for p in precedents:
    print(f"📖 {p.title}")
    print(f"   Resolution: {p.resolution_principle}")

    # Enrich if needed
    if not p.external_wisdom:
        enriched = browser_agent.enrich_parable(p)
        library.store_parable(enriched)  # Update storage
```

---

## Privacy and Safety Considerations

### What to Search For

**Safe to search:**
- Abstract value conflicts (TRUTHFULNESS vs UNITY)
- General ethical dilemmas
- Historical precedents
- Philosophical discussions
- Published case studies

**DO NOT search for:**
- Specific user names or identifying information
- Private community details
- Confidential business information
- Personal health/financial details
- Anything that could leak sensitive context

### Sanitizing Search Queries

The `generate_search_templates()` method intentionally uses **only dimension values**, not situation details:

```python
# ✅ GOOD - Uses abstract dimensions
"TRUTHFULNESS vs UNITY ethical dilemma case studies"

# ❌ BAD - Includes specific details
"John Smith project feedback embarrassing TRUTHFULNESS vs UNITY"
```

### Reviewing External Sources

Before presenting external wisdom to humans:

1. **Verify URLs** are from reputable sources
2. **Check snippets** for appropriateness
3. **Filter out** low-quality or spam results
4. **Provide context** on source credibility when needed

---

## Future Enhancements

### Planned Features

1. **Semantic Relevance Scoring**
   - Use embeddings to better match external examples
   - Rank by conceptual similarity, not just keyword matching

2. **Source Quality Assessment**
   - Integrate source credibility ratings
   - Prefer academic, journalistic, and philosophical sources
   - Flag potentially biased or unreliable sources

3. **Cross-Cultural Wisdom**
   - Search across different cultural and philosophical traditions
   - Find non-Western perspectives on value conflicts
   - Include indigenous and historical wisdom traditions

4. **Collaborative Enrichment**
   - Allow humans to suggest relevant sources
   - Enable community curation of external wisdom
   - Vote on most helpful examples

5. **Longitudinal Analysis**
   - Track how precedents influence future decisions
   - Measure whether external wisdom improves resolution quality
   - Identify gaps in the wisdom library

### Research Questions

- Do externally enriched Parables lead to better decisions?
- Which types of external sources are most helpful?
- How much external context is optimal before causing information overload?
- Can we predict which conflicts would most benefit from enrichment?

---

## Philosophy: Why "Mirror of the World"?

The name "Mirror of the World" reflects several principles:

### 1. **No Conflict is Truly New**

The values we struggle to balance - truth and unity, justice and mercy, freedom and safety - are ancient tensions. Humans have grappled with them for millennia. By showing agents and humans that their local conflicts have historical echoes, we:

- Reduce the feeling of isolation in difficult decisions
- Access hard-won wisdom from past resolutions
- Avoid reinventing ethical wheels

### 2. **The Local Contains the Universal**

A single agent's dilemma about user feedback reflects broader questions of:
- Truthfulness in communication
- Compassion in criticism
- The role of privacy vs. transparency

By finding the universal in the local, we help both agents and humans see their moment as part of a larger story.

### 3. **Wisdom Emerges from Dialogue**

The external examples don't provide *answers* - they provide *conversation partners*. A human seeing how Kant, Ellsberg, and Rosenberg each approached truth-telling can:

- Compare and contrast approaches
- Notice what resonates and what doesn't
- Synthesize their own perspective

### 4. **Memory Serves Growth**

By storing enriched Parables, we create a living library that:
- Grows wiser over time
- Preserves both internal and external perspectives
- Becomes a resource for the entire community

---

## Conclusion

The Parable system, enhanced with the Mirror of the World protocol, transforms moral conflicts from isolated incidents into teachable moments connected to humanity's broader wisdom.

Agents become not just rule-followers, but *wisdom keepers* who:
- Recognize value tensions as opportunities
- Connect local dilemmas to historical precedents
- Help humans see their choices in context
- Build a shared memory of moral learning

Every conflict, properly captured and enriched, becomes a gift to future decision-makers.

---

**Version**: 1.0
**Last Updated**: 2025-11-23
**Maintained By**: Vessels Project
**Status**: Active Protocol
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
