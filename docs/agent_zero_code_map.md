# Agent Zero Hierarchy - Code Map

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HUMAN USER                                      │
│                           (Ultimate Superior)                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ intervene()
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AgentZeroCore                                      │
│                      agent_zero_core.py:146                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  agents: Dict[str, AgentInstance]                                    │   │
│  │  llm_call: Callable                                                  │   │
│  │  ssf_integration: A0SSFIntegration                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Hierarchy Methods:                                                         │
│  ├── call_subordinate()      → Create/communicate with child agent          │
│  ├── _create_subordinate()   → Instantiate subordinate with deep-copy       │
│  ├── _execute_monologue()    → Run agent's reasoning loop                   │
│  ├── _handle_intervention()  → Process human interruption                   │
│  ├── intervene()             → Queue intervention for agent                 │
│  ├── get_agent_hierarchy()   → Visualize hierarchy tree                     │
│  └── process_chain_response()→ Propagate results up chain                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  Agent 0  │   │  Agent 0  │   │  Agent 0  │
            │ (level 0) │   │ (level 0) │   │ (level 0) │
            └─────┬─────┘   └───────────┘   └───────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  ┌───────────┐       ┌───────────┐
  │   Sub 1   │       │   Sub 2   │
  │ (level 1) │       │ (level 1) │
  └─────┬─────┘       └───────────┘
        │
        ▼
  ┌───────────┐
  │  Sub 1.1  │
  │ (level 2) │
  └───────────┘
```

---

## File Structure

```
/home/user/Vessels/
├── agent_zero_core.py              # Core hierarchy implementation
├── prompts/
│   └── system.md                   # System prompt with hierarchy docs
├── vessels/
│   └── ssf/
│       └── builtins/
│           └── coordination/
│               └── __init__.py     # SSF definitions for hierarchy
└── docs/
    ├── agent_zero_subagent_hierarchy.md  # Learning documentation
    └── agent_zero_code_map.md            # This file
```

---

## Core Data Structures

### agent_zero_core.py

#### InterventionException (line 65)
```python
class InterventionException(Exception):
    """Raised when human intervention interrupts agent execution."""
    def __init__(self, message: Any):
        self.intervention_message = message
```
**Purpose**: Allows human to interrupt any agent's reasoning loop.

---

#### LoopData (line 72)
```python
@dataclass
class LoopData:
    user_message: Optional[str] = None
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    reasoning: str = ""
    response: str = ""
```
**Purpose**: Tracks state during a single monologue iteration.

---

#### AgentConfig (line 81)
```python
@dataclass
class AgentConfig:
    prompt_profile: str = "default"
    tools_enabled: List[str] = field(default_factory=list)
    max_iterations: int = 50
    context_window_size: int = 8000
    compression_enabled: bool = True
    custom_instructions: str = ""
    temperature: float = 0.7
```
**Purpose**: Configuration that gets **deep-copied** for subordinates.
**Critical**: Prevents shared state bug (A0 issue #674).

---

#### AgentInstance (line 98)
```python
@dataclass
class AgentInstance:
    # Identity
    id: str
    specification: AgentSpecification
    status: AgentStatus

    # Vessel integration
    vessel_id: Optional[str] = None
    memory_backend: Optional[Any] = None
    action_gate: Optional[Any] = None
    tools: List[str] = field(default_factory=list)

    # === A0 HIERARCHY FIELDS ===
    hierarchy_number: int = 0           # 0 = Agent Zero, 1+ = subordinates
    superior_id: Optional[str] = None   # Parent agent ID (None = human)
    subordinate_ids: List[str] = []     # Child agent IDs
    config: AgentConfig                 # Deep-copied per agent
    history: List[Dict[str, Any]] = []  # Conversation context

    # Intervention support
    intervention: Optional[Any] = None  # Pending human message
    paused: bool = False                # Pause state

    # Monologue state
    loop_data: Optional[LoopData] = None
    last_user_message: Optional[str] = None
```

---

## Hierarchy Methods

### call_subordinate (line 1054)
```
┌─────────────────────────────────────────────────────────────────┐
│ call_subordinate(agent_id, message, reset, profile)             │
├─────────────────────────────────────────────────────────────────┤
│ 1. Get parent agent from self.agents[agent_id]                  │
│ 2. Check for existing subordinate (parent.subordinate_ids[-1])  │
│ 3. If reset=True or no subordinate: _create_subordinate()       │
│ 4. Add message to subordinate history                           │
│ 5. Execute subordinate's monologue                              │
│ 6. Return response to parent                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Flow**:
```
Parent Agent                     Subordinate Agent
     │                                  │
     │─── call_subordinate(msg) ───────▶│
     │                                  │
     │                          _create_subordinate()
     │                          - hierarchy_number + 1
     │                          - copy.deepcopy(config)
     │                          - Set superior_id
     │                          - Add to parent.subordinate_ids
     │                                  │
     │                          _add_user_message(msg)
     │                                  │
     │                          _execute_monologue()
     │                          ┌───────────────────┐
     │                          │ while iterations: │
     │                          │   prepare_prompt  │
     │                          │   llm_call        │
     │                          │   process_tools   │
     │                          └───────────────────┘
     │                                  │
     │◀──────── response ──────────────│
     │                                  │
     │ (response added to parent's     │
     │  history as tool_result)        │
```

---

### _create_subordinate (line 1110)
```python
def _create_subordinate(self, parent, profile=None):
    # CRITICAL: Deep copy config
    sub_config = copy.deepcopy(parent.config)

    subordinate = AgentInstance(
        id=uuid4(),
        hierarchy_number=parent.hierarchy_number + 1,  # Increment level
        superior_id=parent.id,                         # Link to parent
        config=sub_config,                             # Isolated config
        # Inherit: vessel_id, memory_backend, action_gate, tools
    )

    # Bidirectional reference
    parent.subordinate_ids.append(subordinate.id)

    return subordinate
```

---

### _execute_monologue (line 1197)
```
┌─────────────────────────────────────────────────────────────────┐
│                     MONOLOGUE LOOP                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ while iterations < max_iterations:                        │  │
│  │                                                           │  │
│  │   1. _handle_intervention()                               │  │
│  │      └─▶ Check if human interrupted                       │  │
│  │      └─▶ Raise InterventionException if pending           │  │
│  │                                                           │  │
│  │   2. _prepare_prompt()                                    │  │
│  │      └─▶ Build context from history                       │  │
│  │      └─▶ Include hierarchy info                           │  │
│  │      └─▶ List available tools                             │  │
│  │                                                           │  │
│  │   3. llm_call(prompt)                                     │  │
│  │      └─▶ Get LLM response                                 │  │
│  │                                                           │  │
│  │   4. _extract_tool_calls(response)                        │  │
│  │      └─▶ Parse JSON tool calls from response              │  │
│  │                                                           │  │
│  │   5. If tool_calls:                                       │  │
│  │      └─▶ _process_tool_call() for each                    │  │
│  │      └─▶ If "response" tool → return final answer         │  │
│  │      └─▶ If "call_subordinate" → delegate & continue      │  │
│  │      └─▶ Add tool results to history                      │  │
│  │   Else:                                                   │  │
│  │      └─▶ No tools = final response                        │  │
│  │      └─▶ Return response                                  │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Exception handling:                                            │
│  - InterventionException → Re-run with new instructions         │
│  - Other errors → Return error message                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### _process_tool_call (line 1344)
```python
def _process_tool_call(self, agent, tool_call):
    tool_name = tool_call.get("tool_name")
    tool_args = tool_call.get("tool_args", {})

    # Special handling for hierarchy tools
    if tool_name == "call_subordinate":
        return self.call_subordinate(
            agent_id=agent.id,
            message=tool_args.get("message"),
            reset=tool_args.get("reset", "false") == "true",
        )

    if tool_name == "response":
        return tool_args.get("message")  # Final answer

    # Try SSF integration
    if self.ssf_integration:
        return self.ssf_integration.execute_tool(tool_name, tool_args)

    # Fallback to vessel tools
    if agent.vessel_id and self.vessel_registry:
        vessel = self.vessel_registry.get_vessel(agent.vessel_id)
        if vessel:
            tool_impl = vessel.get_tool(tool_name)
            if tool_impl:
                return tool_impl(**tool_args)
```

---

### intervene (line 1401)
```
Human                     AgentZeroCore                    Agent
  │                            │                             │
  │── intervene(agent_id, ────▶│                             │
  │    "stop and do X")        │                             │
  │                            │── agent.intervention = msg ─▶│
  │                            │                             │
  │                            │   (Agent is in monologue)   │
  │                            │                             │
  │                            │   _handle_intervention()    │
  │                            │   ┌─────────────────────┐   │
  │                            │   │ if intervention:    │   │
  │                            │   │   raise Exception   │   │
  │                            │   └─────────────────────┘   │
  │                            │                             │
  │                            │   InterventionException     │
  │                            │   caught in monologue       │
  │                            │                             │
  │                            │   Add msg to history        │
  │                            │   Re-run monologue          │
  │                            │◀────────────────────────────│
```

---

### get_agent_hierarchy (line 1439)
```python
def get_agent_hierarchy(self, agent_id):
    """Returns hierarchy visualization"""

    # Build superior chain (up to human)
    superior_chain = []
    current = agent.superior_id
    while current:
        sup = self.agents[current]
        superior_chain.append({id, name, level})
        current = sup.superior_id

    # Build subordinate tree (recursive)
    def get_subordinate_tree(agent):
        return [{
            id, name, level,
            subordinates: get_subordinate_tree(sub)
        } for sub_id in agent.subordinate_ids]

    return {
        agent_id, agent_name, hierarchy_level,
        superior_chain: reversed(superior_chain),
        subordinates: get_subordinate_tree(agent)
    }
```

**Example Output**:
```json
{
  "agent_id": "abc-123",
  "agent_name": "GrantWriter",
  "hierarchy_level": 1,
  "superior_chain": [
    {"id": "root-001", "name": "AgentZero", "level": 0}
  ],
  "subordinates": [
    {
      "id": "sub-456",
      "name": "GrantWriter_sub_2",
      "level": 2,
      "subordinates": []
    }
  ]
}
```

---

## SSF Integration

### vessels/ssf/builtins/coordination/__init__.py

```
┌─────────────────────────────────────────────────────────────────┐
│                    SSF DEFINITIONS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  _agent_zero_core = None  (set via set_agent_zero_core)         │
│                                                                 │
│  Handlers:                                                      │
│  ├── handle_call_subordinate()  → Calls core.call_subordinate() │
│  ├── handle_intervene()         → Calls core.intervene()        │
│  ├── handle_spawn_sub_agent()   → Uses call_subordinate(reset=T)│
│  ├── handle_delegate_to_agent() → A2A protocol delegation       │
│  ├── handle_broadcast_to_community()                            │
│  └── handle_request_human_input()                               │
│                                                                 │
│  SSF Definitions:                                               │
│  ├── call_subordinate  (A0 hierarchy core)                      │
│  ├── intervene         (A0 human oversight)                     │
│  ├── spawn_sub_agent                                            │
│  ├── delegate_to_agent                                          │
│  ├── broadcast_to_community                                     │
│  └── request_human_input                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### call_subordinate SSF (line 410)
```yaml
name: call_subordinate
category: AGENT_COORDINATION
tags: [subordinate, hierarchy, delegation, a0, agent-zero]

input_schema:
  agent_id: string      # Parent agent ID
  message: string       # Task instructions
  reset: boolean        # true=new, false=continue
  profile: string       # Optional prompt profile

output_schema:
  success: boolean
  subordinate_id: string
  hierarchy_level: integer
  response: string
  parent_id: string

timeout: 300 seconds
risk_level: MEDIUM
```

---

## Message Flow Example

```
Human: "Write a grant proposal for elder care"
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│ AgentZeroCore._execute_monologue(Agent 0)                       │
│                                                                 │
│ Agent 0 thinks: "I'll delegate research to a subordinate"       │
│                                                                 │
│ Agent 0 outputs:                                                │
│ {"tool_name": "call_subordinate",                               │
│  "tool_args": {                                                 │
│    "message": "You are a researcher. Find elder care grants...",│
│    "reset": "true"                                              │
│  }}                                                             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ _process_tool_call() → call_subordinate()                       │
│                                                                 │
│ Creates Sub-1 (hierarchy_number=1, superior_id=Agent0)          │
│ Runs _execute_monologue(Sub-1)                                  │
│                                                                 │
│ Sub-1 thinks: "I'll search for grants..."                       │
│ Sub-1 executes web_search tool                                  │
│ Sub-1 returns: "Found 5 grants: [list]"                         │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│ Result added to Agent 0's history as tool_result                │
│                                                                 │
│ Agent 0 continues monologue with Sub-1's findings               │
│ Agent 0 thinks: "Now I'll draft the proposal..."                │
│ Agent 0 outputs final response                                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
                         Human receives
                       "Here is your grant
                        proposal draft..."
```

---

## History Management

Each agent maintains its own `history` list:

```python
# User message
agent.history.append({
    "role": "user",
    "content": "Find grants for elder care",
    "timestamp": "2025-11-30T10:00:00"
})

# Tool result (including subordinate responses)
agent.history.append({
    "role": "tool",
    "tool_name": "call_subordinate",
    "content": "Found 5 grants: ...",
    "timestamp": "2025-11-30T10:01:00"
})

# Assistant response
agent.history.append({
    "role": "assistant",
    "content": "Based on the research, here is the proposal...",
    "timestamp": "2025-11-30T10:02:00"
})
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Deep-copy config | Prevents subordinate changes from affecting parent (A0 bug #674) |
| Bidirectional refs | `superior_id` + `subordinate_ids` allows traversal both ways |
| Separate history per agent | Context isolation - each agent has focused context |
| InterventionException | Clean way to interrupt monologue and re-route |
| Tool extraction via regex | Flexible - works with any LLM output format |
| SSF integration | All tools route through SSF constraint validation |

---

## Testing the Hierarchy

```python
# Create core
core = AgentZeroCore(llm_call=my_llm)
core.initialize()

# Spawn root agent
spec = AgentSpecification(name="TestAgent", ...)
agent_ids = core.spawn_agents([spec])
root_id = agent_ids[0]

# Call subordinate
result = core.call_subordinate(
    agent_id=root_id,
    message="You are a researcher. Find X...",
    reset=True
)
print(f"Subordinate ID: {result['subordinate_id']}")
print(f"Level: {result['hierarchy_level']}")  # Should be 1
print(f"Response: {result['response']}")

# View hierarchy
hierarchy = core.get_agent_hierarchy(root_id)
print(hierarchy['subordinates'])  # Shows sub-agent tree

# Intervene
core.intervene(result['subordinate_id'], "Stop and focus on Y instead")
```

---

## References

- Agent Zero GitHub: https://github.com/agent0ai/agent-zero
- A0 Architecture Docs: https://github.com/agent0ai/agent-zero/blob/main/docs/architecture.md
- Config Bug Fix: https://github.com/agent0ai/agent-zero/issues/674
- Vessels Documentation: docs/agent_zero_subagent_hierarchy.md
