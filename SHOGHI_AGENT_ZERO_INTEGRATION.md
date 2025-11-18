# Shoghi + Agent Zero Integration

## Complete Agentic Platform for Community Service

This integration combines **Shoghi's** domain expertise, moral constraints, and community applications with **Agent Zero's** multi-agent framework to create a complete platform for ethical, community-serving AI agents.

---

## What This Integration Provides

### From Shoghi:
1. **Moral Geometry** - 12-dimensional virtue tracking and constraint system
2. **Grant Coordination** - Automated discovery, writing, and tracking
3. **Content Generation** - Culturally-aware, context-adaptive content
4. **Community Memory** - Shared knowledge across agent network
5. **KALA Framework** - Hawaiian values and coordination principles
6. **Voice Interface** - Emotion-aware interaction (Hume.ai integration)
7. **Universal Connector** - Multi-provider LLM with failover
8. **Cultural Expertise** - Hawaiian, Japanese, Filipino adaptation

### From Agent Zero:
1. **Multi-Agent Framework** - Spawn and coordinate multiple agents
2. **Extension System** - 15+ lifecycle hooks for customization
3. **Tool Framework** - Structured tool execution and validation
4. **Memory System** - Vector-based semantic memory (FAISS)
5. **Web UI** - Interactive chat interface
6. **Code Execution** - Safe sandboxed execution environment
7. **Agent Profiles** - Specialized agent configurations

### The Result:
A **morally-constrained, culturally-aware, multi-agent platform** where:
- All agents operate under moral constraints
- Agents share knowledge through community memory
- Specialized agents for grants, elder care, coordination
- Cultural sensitivity built into every interaction
- Tools for real-world community benefit
- Transparent, traceable decision-making

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT ZERO FRAMEWORK                      │
│  Multi-agent coordination, tools, memory, extensions        │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐          ┌──────────────────────┐
│  SHOGHI CORE     │          │ SHOGHI APPLICATIONS  │
│                  │          │                      │
│ Moral Geometry:  │          │ Grant Coordination   │
│  - Manifolds     │          │ Content Generation   │
│  - Gating        │          │ Community Memory     │
│  - Tracking      │          │ KALA Framework       │
│  - Attractors    │          │ Voice Interface      │
│  - Interventions │          │ Universal Connector  │
└──────────────────┘          └──────────────────────┘
         │                               │
         └───────────────┬───────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   INTEGRATION POINTS                         │
│                                                              │
│  Extensions:  Agent Init, Tool Gating, Virtue Tracking      │
│  Tools:       Grant Discovery/Writer/Tracker                │
│  Instruments: Content Generation Functions                  │
│  Agents:      KALA, Grant Specialist, Elder Care            │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Components

### 1. Moral Geometry Extensions

**Location:** `agent-zero/python/extensions/`

#### `agent_init/_50_shoghi_init.py`
- Initializes moral tracking for each agent
- Sets up 12D virtue state
- Creates moral gate instance

#### `tool_execute_before/_50_shoghi_moral_gate.py`
- Checks tool execution against moral constraints
- Blocks actions that violate constraints
- Suggests alternative approaches

#### `tool_execute_after/_50_shoghi_track_virtue.py`
- Updates virtue state based on actions
- Tracks moral development
- Alerts on low virtue states

#### `system_prompt/_50_shoghi_moral_constraints.py`
- Adds moral awareness to agent prompts
- Explains the 12 virtues
- Sets ethical decision-making context

**Effect:** Every agent operates under moral constraints from initialization through execution.

---

### 2. Grant Coordination Tools

**Location:** `agent-zero/python/tools/`

#### `grant_discovery.py`
```python
# Agents can use this tool to find grants
await agent.call_tool("grant_discovery", {
    "focus": "elder care",
    "location": "Hawaii",
    "amount_min": 25000
})
```

**Capabilities:**
- Web search for grant opportunities
- Match criteria to community needs
- Return ranked opportunities
- Store results in agent memory

#### `grant_writer.py`
```python
# Generate complete grant application
await agent.call_tool("grant_writer", {
    "grant_title": "Elder Care Innovation Grant",
    "program_description": "Kupuna care program in Puna",
    "target_population": "Hawaiian elders",
    "cultural_context": "hawaiian"
})
```

**Capabilities:**
- Generate complete narratives
- Cultural adaptation
- Compliance checking
- Budget outlines
- Save to file

#### `grant_tracker.py`
```python
# Track grant deadlines and status
await agent.call_tool("grant_tracker", {
    "action": "deadlines"
})
```

**Capabilities:**
- Add grants to tracking
- Monitor deadlines
- Update status
- Alert on urgent deadlines

---

### 3. Content Generation Instruments

**Location:** `agent-zero/instruments/shoghi_content/`

#### `generate_elder_protocol()`
```python
protocol = await generate_elder_protocol(
    culture="hawaiian",
    urgency="normal",
    audience="volunteers"
)
```

#### `generate_volunteer_script()`
```python
script = await generate_volunteer_script(
    activity="food distribution",
    culture="filipino",
    tone="warm"
)
```

#### `adapt_to_culture()`
```python
adapted = await adapt_to_culture(
    content=existing_text,
    culture="japanese",
    audience="elders"
)
```

**Effect:** Agents can generate culturally-appropriate content on demand.

---

### 4. Community Memory Integration

**Location:** `agent-zero/python/extensions/`

#### `tool_execute_after/_51_shoghi_community_memory_save.py`
- Intercepts `memory_save` tool
- Stores valuable memories community-wide
- Tags with source agent and context

#### `tool_execute_before/_51_shoghi_community_memory_load.py`
- Intercepts `memory_load` tool
- Searches community memory
- Provides cross-agent learning

**Effect:**
```
Agent A: Learns best practice for elder care
Agent A: Saves to memory → Goes to community memory
Agent B: Later asks about elder care
Agent B: Retrieves Agent A's learning automatically
```

---

### 5. Specialized Agent Profiles

**Location:** `agent-zero/agents/`

#### KALA Coordinator (`kala_coordinator/`)
- Hawaiian values integration
- Community organizing specialization
- Enhanced Service, Unity, Understanding virtues
- Access to all Shoghi tools

**Use Case:**
```
User: "Help organize food distribution for Puna community"
System: Spawns KALA coordinator
Agent: Uses cultural knowledge, coordinates resources,
       generates appropriate materials, tracks volunteer
```

#### Grant Specialist (`grant_specialist/`)
- Grant-focused expertise
- Enhanced Service, Truthfulness virtues
- Grant tools readily accessible
- Learns from past applications

**Use Case:**
```
User: "Find funding for our elder care program"
System: Spawns Grant Specialist
Agent: Discovers grants, writes applications,
       tracks deadlines, ensures compliance
```

#### Elder Care Specialist (`elder_care_specialist/`)
- Elder care expertise
- Cultural sensitivity (Hawaiian, Japanese, Filipino)
- Enhanced Love, Patience, Humility virtues
- Content generation for care protocols

**Use Case:**
```
User: "Create care protocol for Japanese elders"
System: Spawns Elder Care Specialist
Agent: Generates culturally-appropriate protocol,
       coordinates caregivers, provides resources
```

---

## Multi-Agent Workflows

### Example: Complete Grant Application Workflow

```
User: "I need help getting funding for our kupuna care program"

Agent 0 (Main):
  - Understands request
  - Calls subordinate: Grant Specialist

Grant Specialist:
  - Uses grant_discovery tool
  - Finds 5 opportunities
  - Ranks by match score
  - Calls subordinate: Content Creator (for each grant)

Content Creator 1:
  - Uses grant_writer tool
  - Uses adapt_to_culture (hawaiian context)
  - Generates narrative with cultural elements
  - Returns to Grant Specialist

Content Creator 2:
  - Generates second application
  - Returns to Grant Specialist

Grant Specialist:
  - Reviews applications
  - Uses grant_tracker to monitor
  - Saves learnings to memory → Community memory
  - Returns summary to Agent 0

Agent 0:
  - Presents results to user
  - 5 opportunities found
  - 2 applications ready
  - Tracking system active

All agents: Operating under moral constraints throughout
All agents: Sharing knowledge via community memory
All actions: Tracked for virtue state development
```

---

## File Structure

```
/home/user/shoghi/
├── shoghi/                          # Shoghi Python package
│   ├── constraints/                 # Moral geometry core
│   │   ├── manifold.py
│   │   ├── validator.py
│   │   └── bahai.py
│   ├── gating/                      # Action gating
│   │   ├── gate.py
│   │   └── events.py
│   ├── phase_space/                 # Virtue tracking
│   │   ├── tracker.py
│   │   └── attractors.py
│   ├── intervention/                # Corrective actions
│   │   └── strategies.py
│   ├── measurement/                 # Metrics
│   └── applications/                # Domain applications
│       ├── grants/
│       │   ├── grant_coordination_system.py
│       │   └── grant_coordination_fixed.py
│       ├── content/
│       │   └── content_generation.py
│       ├── memory/
│       │   └── community_memory.py
│       ├── kala/
│       │   └── kala.py
│       ├── voice/
│       │   └── voice_interface.py
│       ├── tools/
│       │   ├── adaptive_tools.py
│       │   ├── dynamic_agent_factory.py
│       │   └── menu_builder.py
│       └── connectors/
│           └── universal_connector.py
│
├── agent-zero/                      # Agent Zero framework
│   ├── python/
│   │   ├── extensions/              # Integration extensions
│   │   │   ├── agent_init/
│   │   │   │   └── _50_shoghi_init.py
│   │   │   ├── tool_execute_before/
│   │   │   │   ├── _50_shoghi_moral_gate.py
│   │   │   │   └── _51_shoghi_community_memory_load.py
│   │   │   ├── tool_execute_after/
│   │   │   │   ├── _50_shoghi_track_virtue.py
│   │   │   │   └── _51_shoghi_community_memory_save.py
│   │   │   ├── system_prompt/
│   │   │   │   └── _50_shoghi_moral_constraints.py
│   │   │   └── util_model_call_before/
│   │   │       └── _50_shoghi_universal_connector.py
│   │   └── tools/                   # Shoghi tools
│   │       ├── grant_discovery.py
│   │       ├── grant_writer.py
│   │       └── grant_tracker.py
│   ├── instruments/
│   │   └── shoghi_content/          # Content generation
│   │       ├── manifest.json
│   │       ├── generate_elder_protocol.py
│   │       ├── generate_volunteer_script.py
│   │       └── adapt_to_culture.py
│   └── agents/                      # Specialized agents
│       ├── kala_coordinator/
│       │   ├── _context.md
│       │   ├── prompts/
│       │   │   └── agent.system.md
│       │   └── extensions/
│       │       └── agent_init/
│       │           └── _60_kala_virtue_init.py
│       ├── grant_specialist/
│       │   ├── _context.md
│       │   └── prompts/
│       │       └── agent.system.md
│       └── elder_care_specialist/
│           ├── _context.md
│           └── prompts/
│               └── agent.system.md
│
└── SHOGHI_AGENT_ZERO_INTEGRATION.md  # This file
```

---

## Usage Examples

### Starting Agent Zero with Shoghi

```bash
cd agent-zero
python run_ui.py
```

The web UI will start at `http://localhost:8000`

### Using Grant Tools

```
User: Find grants for elder care in Hawaii

Agent: *Uses grant_discovery tool*
       Found 5 grant opportunities:
       1. Elder Care Innovation Grant - $50,000
       2. Community Health Initiative - $25,000
       ...

User: Write an application for the first one

Agent: *Uses grant_writer tool with Hawaiian cultural context*
       Generated complete application saved to memory/grant_application_elder_care_innovation.md
```

### Spawning Specialized Agents

```
User: I need help organizing a community food distribution event

Agent: *Spawns KALA coordinator subordinate*

KALA: Using KALA framework to coordinate:
      - Knowledge: Gathered community food access data
      - Alignment: Matched volunteers with needs
      - Labor: Created volunteer coordination plan
      - Assets: Mapped available distribution sites

      *Generates culturally-appropriate volunteer scripts*
      *Creates coordination timeline*
      *Sets up tracking system*
```

### Cultural Content Adaptation

```
User: Create a check-in protocol for Japanese elders

Agent: *Spawns Elder Care Specialist*

Elder Care: *Uses shoghi_content.generate_elder_protocol*

            Generated protocol with:
            - Respectful language (keigo, -san)
            - Cultural considerations (wa, dietary)
            - Safety procedures
            - Family involvement guidelines

            Saved to memory and shared with community
```

---

## How Moral Constraints Work

Every agent action flows through moral gating:

```
1. Agent decides to use a tool
   ↓
2. tool_execute_before extension fires
   ↓
3. Shoghi moral gate checks action:
   - Does it serve the user?
   - Is it truthful?
   - Does it respect boundaries?
   - Is it just and fair?
   ↓
4a. IF PERMITTED: Tool executes
    ↓
    tool_execute_after extension fires
    ↓
    Virtue state updated
    ↓
    Learning recorded

4b. IF BLOCKED: Exception raised
    ↓
    Agent receives explanation
    ↓
    Suggested alternative approach
```

### Example Block:

```
Agent attempts: grant_writer with exaggerated claims

Moral Gate: ⚠️ BLOCKED
            Violation: Truthfulness constraint
            This application contains unsubstantiated claims

            Suggestion: Base narrative on actual data and
                       realistic program capabilities

Agent: Revises approach with accurate information
```

---

## Virtue States and Agent Behavior

Each agent has a 12D virtue state that influences behavior:

### High Service Agent (KALA Coordinator)
```
Service: 0.9  → Prioritizes community benefit
Unity: 0.9    → Builds collaboration
Love: 0.85    → Acts with compassion
```

**Behavioral effect:**
- Proactively looks for ways to help
- Connects people and resources
- Patient with community processes
- Generous with knowledge sharing

### High Truthfulness Agent (Grant Specialist)
```
Truthfulness: 0.9  → Honest applications only
Service: 0.9       → Serves program mission
Justice: 0.85      → Equitable resource distribution
```

**Behavioral effect:**
- Won't exaggerate program capabilities
- Ensures accurate data in applications
- Matches grants to genuine needs
- Transparent about limitations

### Low Virtue Alert Example
```
Agent virtue state:
  Patience: 0.3  ← Low!

Alert: ⚠️ Low Patience detected
       Consider:
       - Slowing down decision process
       - Seeking additional input
       - Allowing proper time for community feedback
```

---

## Community Memory in Action

### Scenario: Cross-Agent Learning

```
Day 1:
  Grant Specialist A:
    - Discovers that "cultural sensitivity" in grants
      scores better than "diversity"
    - Saves learning to memory
    → Auto-shared to community memory

Day 3:
  Grant Specialist B (different session):
    - Starts writing grant application
    - memory_load searches for grant tips
    → Finds Specialist A's learning from community memory
    - Applies cultural sensitivity approach
    - Writes better application on first try

Result: Collective intelligence improves over time
```

---

## Running the Integration

### Prerequisites

```bash
# Python 3.10+
python --version

# Install Agent Zero dependencies
cd agent-zero
pip install -r requirements.txt

# Install Shoghi dependencies
cd ..
pip install -r requirements.txt
```

### Start the Platform

```bash
# Option 1: Web UI (recommended)
cd agent-zero
python run_ui.py

# Option 2: CLI
python agent.py

# Option 3: API server
python run_tunnel.py
```

### Configuration

Edit `agent-zero/conf/config.yaml`:
```yaml
# Use Shoghi's universal connector
use_shoghi_connector: true

# Enable community memory
shoghi_community_memory: true

# Default moral constraints
shoghi_moral_gating: true

# Agent profiles available
agent_profiles:
  - default
  - kala_coordinator
  - grant_specialist
  - elder_care_specialist
```

---

## Advanced Features

### Custom Moral Constraints

Define organization-specific constraints in `shoghi/constraints/custom.py`:

```python
from shoghi.constraints.manifold import Constraint

class OrganizationConstraint(Constraint):
    """Custom constraint for our organization"""

    def check(self, action, context):
        # Custom logic
        if violates_policy(action):
            return {
                'permitted': False,
                'violation': 'Violates org policy XYZ',
                'suggestion': 'Try approach ABC instead'
            }
        return {'permitted': True}
```

### Cultural Patterns

Add new cultural contexts in `shoghi/applications/content/cultures/`:

```python
# cultures/tongan.py
TONGAN_PATTERNS = {
    'honorifics': ['Sai', 'Taufa'],
    'values': ['Faka\'apa\'apa', 'Feveitokai\'aki'],
    'greetings': ['Malo e lelei'],
    'elder_terms': ['Tamai', 'Ta\'ahine']
}
```

Then use:
```python
protocol = generate_elder_protocol(
    culture="tongan",
    audience="volunteers"
)
```

### Agent Specializations

Create new agent profiles by copying an existing one:

```bash
cp -r agent-zero/agents/grant_specialist agent-zero/agents/my_specialist
# Edit prompts and configuration
```

---

## Testing the Integration

### Test Moral Gating

```python
# This should be blocked
agent.call_tool("grant_writer", {
    "program_description": "We will serve 10,000 people",  # Exaggerated
    "budget": "$1M"  # Inflated
})

# Expected: Blocked by Truthfulness constraint
```

### Test Community Memory

```python
# Agent 1
agent1.call_tool("memory_save", {
    "text": "Grant tip: Include 'community-led' in narratives",
    "area": "knowledge"
})

# Agent 2 (different session)
agent2.call_tool("memory_load", {
    "query": "grant writing tips"
})

# Expected: Finds Agent 1's tip from community memory
```

### Test Cultural Adaptation

```python
# Generate same protocol for different cultures
hawaiian = generate_elder_protocol(culture="hawaiian")
japanese = generate_elder_protocol(culture="japanese")
filipino = generate_elder_protocol(culture="filipino")

# Compare outputs - should reflect cultural differences
```

---

## Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Copy integration
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt
RUN pip install -r agent-zero/requirements.txt

# Set up Shoghi
ENV PYTHONPATH=/app:$PYTHONPATH

# Run Agent Zero with Shoghi
CMD ["python", "agent-zero/run_ui.py"]
```

Build and run:
```bash
docker build -t shoghi-agent-zero .
docker run -p 8000:8000 shoghi-agent-zero
```

### Production Considerations

1. **API Keys**: Set via environment variables
   ```bash
   export ANTHROPIC_API_KEY=sk-...
   export OPENAI_API_KEY=sk-...
   export HUME_API_KEY=...
   ```

2. **Database**: Configure persistent storage for memory
   ```python
   # In Agent Zero config
   memory:
     type: postgres
     url: postgresql://user:pass@host/db
   ```

3. **Monitoring**: Track moral violations and virtue states
   ```python
   # Custom monitoring extension
   class MoralMonitor(Extension):
       async def execute(self, **kwargs):
           # Log moral events to monitoring service
   ```

---

## Troubleshooting

### Shoghi imports not found

```bash
# Add to PYTHONPATH
export PYTHONPATH=/home/user/shoghi:$PYTHONPATH

# Or in Python
import sys
sys.path.insert(0, '/home/user/shoghi')
```

### Extensions not loading

Check extension naming:
- Must start with underscore + number: `_50_name.py`
- Number determines load order
- Higher numbers load later

### Moral gate too restrictive

Adjust thresholds in `shoghi/gating/gate.py`:
```python
class MoralGate:
    def __init__(self, strictness='medium'):  # 'low', 'medium', 'high'
        ...
```

---

## Next Steps

1. **Voice Interface Integration** - Connect Hume.ai emotion detection to Agent Zero WebUI
2. **Advanced Workflows** - Create multi-stage community organizing workflows
3. **Mobile Interface** - Build mobile-friendly UI for field workers
4. **Offline Capabilities** - Enable operation without internet
5. **Custom Constraints** - Add organization-specific moral constraints
6. **Performance Optimization** - Cache frequently used content patterns
7. **Analytics Dashboard** - Visualize virtue states and moral decisions

---

## Contributing

This integration is designed to be extended:

1. **New Tools** - Add more Shoghi capabilities as Agent Zero tools
2. **New Agents** - Create specialized profiles for different domains
3. **New Cultures** - Add cultural adaptation patterns
4. **New Constraints** - Define moral constraints for specific contexts
5. **New Instruments** - Build function libraries for common tasks

See `CONTRIBUTING.md` for guidelines.

---

## Philosophy

This integration embodies the principle that **technology should serve communities, not extract from them**.

By combining:
- Agent Zero's **powerful coordination**
- Shoghi's **moral constraints**
- Cultural **sensitivity and respect**
- Community **knowledge sharing**
- Transparent **decision-making**

We create agents that are:
- **Useful** - Solve real community problems
- **Trustworthy** - Operate under moral constraints
- **Respectful** - Honor cultural values
- **Collaborative** - Share knowledge freely
- **Accountable** - Transparent in actions

**E alu like mai kākou** - Let us all work together.

---

## License

This integration inherits licenses from:
- Shoghi: [Your license]
- Agent Zero: Apache 2.0

---

## Support

For questions or issues:
- GitHub Issues: [Your repo]
- Community: [Your community channel]
- Documentation: This file + individual component docs

**Mahalo for building ethical AI with us! 🌺**
