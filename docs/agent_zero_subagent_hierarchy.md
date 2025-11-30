# Agent Zero Subagent & Hierarchy Architecture

## Executive Summary

Agent Zero implements a **hierarchical multi-agent architecture** where agents organize in superior-subordinate relationships. This document captures key learnings from studying the official Agent Zero framework to inform Vessels' agent coordination design.

---

## Core Hierarchy Model

### The Superior-Subordinate Chain

```
Human User (Ultimate Superior)
    │
    ▼
Agent 0 (sees user as superior)
    │
    ├─► Subordinate Agent 1 (number = 1)
    │       │
    │       └─► Sub-subordinate (number = 2)
    │
    └─► Subordinate Agent 2 (number = 1)
```

**Key Principle**: "Every agent has a superior agent giving it tasks and instructions. Every agent then reports back to its superior."

The first agent (Agent 0) treats the human user as its superior - **there is no structural difference** in how agents perceive their superiors, whether human or agent.

---

## The `call_subordinate` Tool

### Purpose
Agents use this tool to create and delegate to child agents, decomposing complex tasks.

### Implementation Pattern

```python
# Subordinate creation (from Agent Zero source)
sub = Agent(
    self.agent.number + 1,  # Increment hierarchy level
    copy.deepcopy(self.agent.config),  # IMPORTANT: deepcopy to prevent config sharing
    self.agent.context
)

# Establish bidirectional references
sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)
```

### Tool Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `message` | string | Detailed task instructions for subordinate |
| `reset` | boolean | `true` = new subordinate, `false` = continue existing |

### Example Usage

```json
{
  "thoughts": ["Task requires specialized code generation, delegating to subordinate"],
  "tool_name": "call_subordinate",
  "tool_args": {
    "message": "You are a Python developer. Write a function that validates email addresses using regex. Include comprehensive test cases.",
    "reset": "true"
  }
}
```

---

## Communication Patterns

### Bidirectional Message Flow

```
Superior ──[instructions]──► Subordinate
    │                            │
    │◄──[results/questions]──────┘
```

Agents can:
1. **Ask questions** upward to superiors
2. **Give instructions** downward to subordinates
3. **Provide guidance** in either direction
4. **Report results** back up the chain

### Chain Processing (`_process_chain`)

When a subordinate completes, results propagate back:

```python
async def _process_chain(self, agent, msg, user=True):
    if user:
        agent.hist_add_user_message(msg)
    else:
        # Subordinate result added as tool result
        agent.hist_add_tool_result(
            tool_name="call_subordinate",
            tool_result=msg
        )

    response = await agent.monologue()

    # Callback to superior if exists
    superior = agent.data.get(Agent.DATA_NAME_SUPERIOR, None)
    if superior:
        response = await self._process_chain(superior, response, False)

    return response
```

---

## The Monologue Loop

Each agent runs an independent `monologue()` loop:

```python
async def monologue(self):
    while True:
        # 1. Initialize loop data
        self.loop_data = LoopData(user_message=self.last_user_message)

        # 2. Call extensions (hooks for customization)
        await self.call_extensions("monologue_start", loop_data=self.loop_data)

        # 3. Inner loop - continue until task complete
        while True:
            # Prepare prompt with context
            prompt = await self.prepare_prompt(loop_data=self.loop_data)

            # Call LLM
            agent_response, reasoning = await self.call_chat_model(
                messages=prompt,
                response_callback=stream_callback,
                reasoning_callback=reasoning_callback
            )

            # Process tool calls
            tools_result = await self.process_tools(agent_response)
            if tools_result:
                return tools_result  # Task complete
```

---

## Context Management

### Why Subordinates Help Context

> "Every agent can create its subordinate agent to help break down and solve subtasks. **This helps all agents keep their context clean and focused.**"

Each agent maintains its own:
- Conversation history
- Message context
- Tool execution state

By delegating, the parent agent offloads complexity while maintaining a clean context window.

### Memory Compression Strategy

Agent Zero uses a hybrid memory model:
- **Recent messages**: Uncompressed, full detail
- **Older messages**: Progressively summarized
- **Result**: "Near-infinite short-term memory"

---

## Customizing Subordinate Agents

### Profile System

Subordinates can have dedicated configurations:

```
/agents/{agent_profile}/
    ├── extensions/     # Custom extensions
    ├── tools/         # Custom tools
    ├── prompts/       # Custom prompts
    └── settings.json  # Agent settings
```

### Loading Priority

1. Check agent-specific directory first
2. Fall back to defaults if not found
3. Override by filename matching

---

## Communication Governance Patterns

Users can instruct agents to implement governance:

1. **Regular Reporting**: "Report back to superior before proceeding"
2. **Point-Scoring**: "Use point system to decide when to delegate"
3. **Verification**: "Superior must verify subordinate results"
4. **Dispute Resolution**: "Superior can reject and re-request"

---

## Intervention Handling

Real-time human oversight:

```python
async def handle_intervention(self, progress: str = ""):
    while self.context.paused:
        await asyncio.sleep(0.1)

    if self.intervention:
        msg = self.intervention
        self.intervention = None
        self.hist_add_user_message(msg, intervention=True)
        raise InterventionException(msg)
```

> "You can stop and intervene at any point. If you see your agent heading in the wrong direction, just stop and tell it right away."

---

## Key Implementation Insights

### 1. Config Isolation Bug

A critical bug was discovered: sharing config by reference between agents caused corruption.

**Bad**:
```python
sub = Agent(number + 1, self.agent.config, context)  # Shared reference!
```

**Good**:
```python
sub = Agent(number + 1, copy.deepcopy(self.agent.config), context)
```

### 2. Data Keys for Hierarchy

```python
DATA_NAME_SUPERIOR = "_superior"      # Reference to parent
DATA_NAME_SUBORDINATE = "_subordinate"  # Reference to child
```

### 3. Tool Results Flow Upward

When subordinate completes, parent receives result as a tool response:
```python
agent.hist_add_tool_result(
    tool_name="call_subordinate",
    tool_result=subordinate_response
)
```

---

## Comparison: Agent Zero vs Current Vessels Implementation

| Feature | Agent Zero | Vessels (Current) |
|---------|-----------|-------------------|
| Hierarchy | True parent-child with context inheritance | Flat spawning, no hierarchy tracking |
| Delegation | `call_subordinate` tool with reset option | SSFs for delegation (stub implementation) |
| Communication | Bidirectional through chain | No inter-agent messaging |
| Context | Each agent maintains own context | Shared memory backends |
| Intervention | Real-time interruption support | No intervention mechanism |
| Config | Deep-copied per agent | Shared references |

---

## Recommendations for Vessels

### 1. Implement True Hierarchy Tracking

```python
@dataclass
class AgentInstance:
    # ... existing fields ...
    superior_id: Optional[str] = None
    subordinate_ids: List[str] = field(default_factory=list)
    hierarchy_level: int = 0  # 0 = top-level
```

### 2. Add `call_subordinate` Tool

Implement the delegation pattern:
- Create child agent with incremented level
- Deep-copy configuration
- Establish bidirectional references
- Add subordinate result to parent's history

### 3. Implement Monologue Loop

Each agent should have an independent reasoning loop that:
- Processes instructions
- Executes tools
- Returns results to superior

### 4. Context Isolation

Ensure subordinates get isolated context to:
- Keep parent context clean
- Allow focused task execution
- Prevent context window overflow

### 5. Support Real-Time Intervention

Allow humans to interrupt any agent in the hierarchy and redirect its behavior.

---

## Sources

- [Agent Zero GitHub Repository](https://github.com/agent0ai/agent-zero)
- [Agent Zero Documentation](https://github.com/agent0ai/agent-zero/tree/main/docs)
- [Architecture Documentation](https://github.com/agent0ai/agent-zero/blob/main/docs/architecture.md)
- [Usage Guide](https://github.com/frdel/agent-zero/blob/main/docs/usage.md)
- [DeepWiki Agent Zero Analysis](https://deepwiki.com/agent0ai/agent-zero)
- [GitHub Issue #674 - Config Bug](https://github.com/agent0ai/agent-zero/issues/674)

---

*Document created: 2025-11-30*
*Based on Agent Zero framework analysis for Vessels integration*
