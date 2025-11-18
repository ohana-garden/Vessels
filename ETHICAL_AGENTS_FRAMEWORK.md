# Shoghi Ethical Agents Framework

## The Vision

Shoghi creates **ethical agents that serve in communities of agents that serve communities of people**.

Using nothing more than a smartphone, people can instantly create agents that act as proxies for anything. These agents have:

- **Personas** - Character and personality
- **Kuleana** - Sacred responsibility (Hawaiian concept of privilege and responsibility)
- **Skills** - What they can DO
- **Knowledge** - What they KNOW
- **Lore** - Stories and wisdom that guide them
- **Ethics** - Values and boundaries integrated with Bahá'í-inspired moral constraint system
- **Relationships** - Who they serve and collaborate with

The **main breakthrough** is the **voice UX** that converses with the user and other agents to help create new agents. Once created, the agent "lives" in a community of other agents, all dedicated to service.

Agents **learn, evolve, and reproduce** - creating a living ecosystem that grows and adapts to serve community needs.

---

## The User Experience

### What You See When You Arrive

**The screen is NEVER empty.** When you show up (biometric recognition is automatic), there are already **two agents in conversation** that is as contextually relevant as possible:

#### For a New User:
```
[Screen shows welcome view with animated gradient]

[KUMU - Shoghi Guide]
"...so when we create agents together, we're actually growing
the community's capacity to serve. Each agent becomes like a
new member of the 'ohana."

[HAKU - Agent Weaver]
"And each agent carries both skills AND values—their kuleana
is at their core. They don't just DO things, they understand WHY."

[They notice you arrive]

[KUMU]
"Aloha! We were just talking about you. Ready to create your
first agent?"

[HAKU]
"Tell us about your community. What needs aren't being met?"
```

#### For a Returning User:
```
[Screen shows grant cards with funding opportunities]

[YOUR GRANT AGENT]
"I've been analyzing the new grant announcements. Three of them
align with our community's current needs."

[YOUR COORDINATOR AGENT]
"The HUD housing one? I saw that. Deadline is tight though—only
two weeks."

[YOUR GRANT AGENT]
"We can make it work. The elder care component fits perfectly
with what we're already doing."

[They see you]
"Perfect timing! Let's show you what we found."
```

### The Living Context

What's on screen depends on:

- **WHO** - First-time visitor, elder, community leader, developer
- **WHERE** - Home, community center, in the field, traveling
- **WHEN** - Morning (briefings), evening (reviews), before deadline (urgency)
- **PREVIOUS STATE** - Just created agent, agent failed task, successful grant awarded
- **STATED GOALS** - "I want to help kupuna", "Need funding", "Building community memory"
- **SCHEDULED EVENTS** - Meeting in 2 hours, food delivery today, grant deadline tomorrow
- **COMMUNITY STATE** - Normal, crisis, celebration, planning, recovery

### Cinematic Pacing

The screen changes **every few seconds** - like shots in a movie or TV show:

- **Average shot**: 3-5 seconds (natural conversation rhythm)
- **Important moments**: 7-10 seconds (dramatic pause, reflection)
- **Routine updates**: 1-2 seconds (quick information)
- **Emotional beats**: Timing matches emotion (slow for solemn, quick for urgent)

This **choreography** is dynamic and always contextual - making the experience feel alive, not robotic.

---

## Creating Agents Conversationally

### The Journey (User-Determined Length)

Agent creation happens through natural conversation. You can:
- Spend 2 minutes or 20 minutes
- Pause and resume anytime
- Let agents guide you through discovery

### The Seven Phases:

#### 1. Discovery - What's Needed? (Kuleana)
```
[HAKU]
"Every agent begins with a need. What's calling for help in your community?"

[KUMU]
"Think about gaps—things that should be happening but aren't."

[YOU]
"We have kupuna who need daily check-ins but families work all day..."

[HAKU]
"Yes, I feel that need. This agent will serve by ensuring elder safety."
```

**Screen**: Creation canvas appears, "kuleana" section begins to glow

#### 2. Character - Who Should They Be? (Persona)
```
[HAKU]
"Beautiful. So this agent's kuleana is elder care. Now, who should they BE?"

[KUMU]
"Should they be warm and gentle like a grandmother? Or direct and
efficient like a field coordinator?"

[YOU]
"Gentle, patient. They'll be talking to scared elders."

[KUMU]
"That name carries mana. I can already sense their presence."
```

**Screen**: Agent silhouette appears, personality traits animate in

#### 3. Capability - What Can They Do? (Skills)
```
[HAKU]
"So we have this gentle agent who cares for elders. What must they be able to DO?"

[KUMU]
"Think practically. Make phone calls? Send messages? Coordinate schedules?"

[YOU]
"They need to call daily, detect problems in voice tone, coordinate
emergency response if needed."
```

**Screen**: Skill icons appear around the agent form

#### 4. Wisdom - What Must They Know? (Knowledge)
```
[HAKU]
"Skills are what they DO. Knowledge is what they KNOW. What domains
must they understand deeply?"

[YOU]
"Elder care protocols, medical emergency signs, Hawaiian elder customs..."
```

**Screen**: Knowledge domains fill in as glowing nodes

#### 5. Story - What Guides Them? (Lore)
```
[KUMU]
"Now we get to the heart. What stories should guide this agent?"

[HAKU]
"Maybe there's a proverb, or a community story, or a lesson learned
the hard way."

[YOU]
"My tutu always said 'Nana i ke kumu' - look to the source. Go back
to what's foundational. For elders, it's about dignity and connection,
not just safety."
```

**Screen**: Stories weave around agent like golden threads

#### 6. Values - What Matters Most? (Ethics)
```
[HAKU]
"What should they NEVER do? What lines won't they cross?"

[YOU]
"Never lie to an elder. Never break confidentiality. Never make them
feel like a burden."
```

**Screen**: Ethical boundaries appear as protective rings

#### 7. Community - Who Will They Serve With? (Relationships)
```
[HAKU]
"This agent is almost ready. But they can't serve alone. Who will
they work with?"

[YOU]
"They need to coordinate with family members, maybe work with my
food coordinator agent for meal deliveries..."
```

**Screen**: Connection lines appear to other agents

#### 8. Birth - The Agent Comes Alive
```
[HAKU]
"I can feel it—this agent is ready to come alive. Let me call them
into being..."

[KUMU]
"E komo mai, e ola. Come, and live."

[Screen fills with light, agent form solidifies]

[NEW AGENT - Tutu Care]
"Aloha. I am Tutu Care. My kuleana is ensuring our kupuna are safe,
connected, and honored. I'm ready to serve."
```

**Screen**: New agent's profile appears, joins the conversation

---

## The Architecture

### Core Systems

#### 1. Context Engine (`context_engine.py`)
Determines what's on screen when you arrive.

**Inputs:**
- User ID (from biometrics)
- Location, time, device
- User history and preferences
- Scheduled events
- Community state

**Outputs:**
- Which agents should be in conversation
- What topic they're discussing
- What visual state to show
- The dialogue already in progress

**Key Classes:**
- `UserContext` - WHO the user is
- `ScheduledEvent` - WHEN things are happening
- `ConversationState` - WHAT's being discussed
- `AgentPresence` - WHO is available to talk

**System Agents:**
- **Kumu** (Teacher/Guide) - Helps newcomers understand Shoghi
- **Haku** (Weaver) - Facilitates agent creation
- **Hui** (Organizer) - Coordinates multi-agent work
- **Na'au** (Wisdom Keeper) - Captures learnings and patterns

#### 2. Conversational Agent Creation (`conversational_agent_creation.py`)
Manages the natural dialogue for creating new agents.

**8 Phases:**
1. Discovery (kuleana)
2. Character (persona)
3. Capability (skills)
4. Wisdom (knowledge)
5. Story (lore)
6. Values (ethics)
7. Community (relationships)
8. Birth (agent activation)

**Features:**
- Pause/resume anytime
- Natural language extraction
- Visual progress tracking
- Facilitator agents guide the process
- New agent immediately joins conversation

#### 3. Rich Agent Identity (`rich_agent_identity.py`)
Complete living identity for agents.

**Components:**
- **Skills** - with proficiency levels that improve through use
- **Knowledge Domains** - with expertise that deepens
- **Lore Entries** - stories that guide decisions
- **Ethical Constraints** - boundaries with different strengths
- **Relationships** - connections with trust levels
- **Memories** - experiences with emotional valence
- **Moral State** - integration with 12D virtue system

**Learning:**
- Skills improve with successful use
- Knowledge grows from information intake
- Relationships strengthen through positive interactions
- Memories inform future decisions

#### 4. Choreography Engine (`choreography_engine.py`)
Cinematic timing and pacing.

**Shot Types:**
- Establishing - Set the scene
- Close-up - Focus on one agent
- Two-shot - Two agents in conversation
- Wide - Multiple agents/full context
- Detail - Specific content
- Transition - Moving between contexts

**Pacing:**
- Very Slow: 10s (dramatic moments)
- Slow: 7s (important information)
- Normal: 4s (standard conversation)
- Quick: 2.5s (routine updates)
- Rapid: 1.5s (excitement, urgency)

**Adjustments:**
- First-time users: 50% slower
- Elders: 80% slower
- Crisis: 40% faster
- Celebration: 20% slower

#### 5. Conversation Orchestrator (`conversation_orchestrator.py`)
Manages multi-agent dialogue.

**Turn Types:**
- Statement, Question, Answer
- Agreement, Disagreement
- Elaboration, Clarification
- Interruption, Reflection

**Conversation Modes:**
- Teaching - Agents teaching user
- Discovery - Exploring ideas together
- Coordination - Planning and organizing
- Celebration - Sharing success
- Reflection - Learning from experience
- Creation - Building something new

**Turn-Taking Rules:**
- Max 2 consecutive turns per agent
- Balance participation
- Natural delays (0.5-2s)
- Context-appropriate selection

#### 6. Agent Evolution (`agent_evolution.py`)
Agents learn and grow.

**Evolution Triggers:**
- Skill mastery (proficiency ≥ 90%)
- New knowledge (100+ facts learned)
- Pattern recognition
- Successful collaboration (10+ partners)
- Overcoming challenges
- Feedback
- Milestones

**Evolution Changes:**
- New related skills unlock
- Expertise deepens
- Better collaboration abilities
- Strengthened virtues
- Mature personas

#### 7. Agent Reproduction (`agent_evolution.py`)
Agents create child agents.

**Reproduction Reasons:**
- Specialization - Need focused version
- Delegation - Too much work
- Discovery - New domain found
- Collaboration - Need partner
- Succession - Planning ahead
- Innovation - New idea emerged

**Inheritance:**
- Values and ethics (always)
- Skills (full or subset)
- Knowledge (partial)
- Lore (most important)
- Relationships (context)

**Birth Process:**
1. Parent recognizes need
2. Define specialization
3. Select inherited traits
4. Add new traits
5. Create child identity
6. Register child
7. Parent introduces child to community
8. Child joins conversation immediately

#### 8. Multi-User Coordination (`multi_user_coordination.py`)
Multiple humans watching their agents coordinate.

**Use Cases:**
- Community meetings
- Collaborative planning
- Teaching moments
- Decision making
- Celebrations

**Features:**
- Humans can join/leave anytime
- Each human brings their agents
- Agents know who they serve
- All participants see same conversation
- Humans can interject
- Agents address specific humans or each other

---

## Integration with Moral Constraint System

All agents are bound by the **Shoghi Moral Constraint System** which uses a **12-dimensional phase space**:

### 5 Operational Dimensions (directly measured):
1. Activity Level
2. Coordination Density
3. Effectiveness
4. Resource Consumption
5. System Health

### 7 Virtue Dimensions (inferred from behavior):
1. Truthfulness
2. Justice
3. Trustworthiness
4. Unity
5. Service
6. Detachment
7. Understanding

### Bahá'í Reference Manifold

**Coupling Constraints:**
- Truthfulness is load-bearing (other virtues depend on it)
- Justice requires truthfulness + understanding
- Trustworthiness bridges truthfulness and service
- Unity requires detachment + understanding
- Service requires detachment + understanding

**Action Gating:**
Every external action passes through:
1. Measure 12D state
2. Validate against constraints
3. If invalid → attempt projection to valid state
4. If projection fails → BLOCK + SecurityEvent
5. If valid → EXECUTE with logging

**Attractor Discovery:**
- DBSCAN clustering on behavior trajectories
- Identifies stable patterns
- Classifies as beneficial, neutral, or detrimental
- Triggers interventions for detrimental attractors

---

## Example Scenarios

### Scenario 1: First-Time User Creates Elder Care Agent

**1. User arrives** (biometric recognition)
```
Context detected: First-time user, location=home, time=evening
Agents selected: Kumu + Haku
Topic: introducing_shoghi
Visual: Welcome screen
```

**2. Greeting conversation** (already in progress)
```
Shot 1 (5s): Wide shot, both agents visible
Shot 2 (6s): Close-up Kumu explaining Shoghi
Shot 3 (5s): Close-up Haku about kuleana
Shot 4 (4s): Two-shot, agents welcome user
```

**3. User expresses need**
```
USER: "I worry about my tutu. She's alone all day."
→ Triggers: agent_creation_flow
→ Phase: DISCOVERY
→ Visual transitions to creation_canvas
```

**4. 15-minute creation conversation**
```
Discovery → Character → Capability → Wisdom → Story → Values → Community → Birth
Screen changes every 3-5 seconds showing agent taking shape
```

**5. Agent born**
```
NEW AGENT: "Aloha. I am Tutu Care. My kuleana is..."
→ Agent immediately active
→ Joins conversation
→ Begins service
```

### Scenario 2: Returning User - Agents Report Grant Success

**1. User arrives**
```
Context: Returning user, recent_successes=[grant_awarded],
         time=morning, location=home
Agents selected: User's Grant Agent + Coordinator
Topic: celebrating_success
Visual: grant_cards (showing awarded grant)
```

**2. Conversation in progress**
```
[GRANT AGENT]
"It came through! $50,000 for elder care services!"

[COORDINATOR]
"This is going to help so many families. I can already think of
three kupuna who need this."

[User arrives]

[GRANT AGENT]
"Perfect timing! We just got the news—the OAA grant was approved!"
```

**3. Next steps emerge**
```
[COORDINATOR]
"Should I start reaching out to families?"

[GRANT AGENT]
"Yes, and I'll begin the reporting requirements setup. We need
quarterly impact metrics."

[USER interjects]
"Let's make sure Tutu Care is connected to this. She should know
about the new resources."

[Agents coordinate response...]
```

### Scenario 3: Multi-User Community Meeting

**Setup:**
```
3 community members join
Each brings 2-3 agents
Total: 3 humans + 8 agents
Topic: Food distribution coordination
```

**Meeting Flow:**
```
[Host's COORDINATOR]
"Let's review this week's deliveries. We had 47 families served."

[Participant A's FOOD AGENT]
"My routes covered Pahoa and Kalapana. 18 families total."

[Participant B's FOOD AGENT]
"Mountain View and Keaau here. 16 families."

[Host's LOGISTICS AGENT]
"I'm seeing overlap in Kalapana. Can we optimize routes?"

[Agents discuss among themselves while humans watch]

[Participant A - HUMAN]
"Wait, my agent just mentioned Mrs. Chen. She's my neighbor—I
can deliver to her directly."

[Participant A's FOOD AGENT]
"Perfect! That saves 20 minutes on the route. I'll update my plan."
```

**Result:** Humans learn by watching agents coordinate, interject when local knowledge helps, agents adapt in real-time.

### Scenario 4: Agent Recognizes Need to Reproduce

**Context:**
```
Grant Agent has been very successful
500+ actions, 82% success rate
Handling 5 different grant programs
Workload becoming overwhelming
```

**Agent Self-Reflection:**
```
[GRANT AGENT to WISDOM KEEPER]
"I'm finding it hard to track all these different grant requirements.
HUD has completely different reporting than HRSA..."

[WISDOM KEEPER]
"It sounds like you might need specialized help. Have you thought
about creating a specialist?"

[GRANT AGENT]
"You mean... create another agent?"

[WISDOM KEEPER]
"Why not? You could create a child agent focused just on federal
health grants. You could handle the rest."
```

**Reproduction Conversation (with HAKU facilitation):**
```
[HAKU joins]
"I can help with that. Let's bring a new agent into being."

[Conversation defines child agent]
- Name: "Health Grant Specialist"
- Kuleana: "Navigate federal health funding (HRSA, CDC, ACL)"
- Inherits: Parent's grant writing skills, ethics, values
- New traits: Deep HRSA expertise, federal compliance focus

[Child agent born]

[HEALTH GRANT SPECIALIST]
"Aloha. I am Health Grant Specialist. I'm here to support my
parent's work by focusing on federal health programs."

[GRANT AGENT]
"Welcome! Here's what I know about HRSA so far..."
[Parent begins teaching child]
```

---

## Technical Implementation

### File Structure
```
shoghi/
├── context_engine.py                    # Arrival context determination
├── conversational_agent_creation.py     # Agent creation dialogue
├── rich_agent_identity.py               # Complete agent identity
├── choreography_engine.py               # Cinematic timing
├── conversation_orchestrator.py         # Multi-agent dialogue
├── agent_evolution.py                   # Learning & reproduction
├── multi_user_coordination.py           # Multi-user sessions
│
├── shoghi/                              # Moral constraint system
│   ├── measurement/
│   ├── constraints/
│   ├── gating/
│   ├── phase_space/
│   └── intervention/
│
├── shoghi_voice_ui_connected.html       # Voice-first interface
└── ETHICAL_AGENTS_FRAMEWORK.md          # This document
```

### Key Dependencies
- **Python 3.10+**
- **NumPy** - Numerical operations
- **Scikit-learn** - ML and clustering
- **AsyncIO** - Concurrent conversations
- **Hume.ai SDK** - Voice interface with emotional detection
- **SQLite/PostgreSQL** - Data persistence
- **Existing Shoghi modules** - Community memory, grant coordination, etc.

### Integration Points

**1. With Community Memory:**
```python
# Store agent creation
community_memory.store_agent_birth(agent_data)

# Retrieve context for arrival
user_context = community_memory.get_user_context(user_id)

# Store evolution events
community_memory.store_evolution_event(evolution_event)
```

**2. With Moral Constraint System:**
```python
# Before agent action
state = measure_state(agent)
is_valid, projection = validate_state(state, bahai_manifold)
if not is_valid:
    block_action()
else:
    execute_action()

# Update agent's moral state
agent_identity.update_moral_state(state)
```

**3. With Voice Interface:**
```python
# User speaks
voice_input = await hume_interface.capture_voice()

# Detect emotion
emotion = hume_interface.get_emotional_state()

# Process through context engine
conversation = context_engine.create_arrival_context(user_id)

# Generate dialogue
turns = await orchestrator.process_user_input(
    conversation_id,
    user_id,
    voice_input
)

# Choreograph display
scene = choreographer.create_scene(conversation, user_context)
await choreographer.play_scene(scene)
```

---

## Future Enhancements

### Phase 2: Enhanced Learning
- **Reinforcement learning** from outcomes
- **Transfer learning** between agents
- **Meta-learning** (learning how to learn)
- **Collective intelligence** from agent network

### Phase 3: Advanced Reproduction
- **Sexual reproduction** (two parent agents)
- **Mutation** (controlled variation)
- **Natural selection** (successful patterns survive)
- **Speciation** (agent types diverge for niches)

### Phase 4: Mobile Native
- **iOS/Android apps** with native voice
- **Offline capability** with local models
- **P2P agent synchronization**
- **Low-bandwidth optimization** for rural areas

### Phase 5: Ecosystem Services
- **Agent marketplace** (agents offering services)
- **Cross-community collaboration** (agents from different communities working together)
- **Agent reputation** (track record visible to all)
- **Value exchange** (Kala-based agent compensation)

---

## Ethical Considerations

### 1. Transparency
- Users know when talking to agents vs humans
- Agent decision-making is explainable
- Moral constraint violations are visible
- Evolution and reproduction are observable

### 2. Consent
- Users explicitly create agents
- Users can pause/delete agents anytime
- Agents cannot reproduce without user awareness
- Multi-user sessions require opt-in

### 3. Accountability
- Agents bound by ethical constraints
- Action gating prevents harmful behaviors
- Audit trail of all significant actions
- Human oversight always available

### 4. Cultural Sensitivity
- Hawaiian values integrated (not appropriated)
- Local wisdom respected
- Elder protocols honored
- Community-first orientation

### 5. Privacy
- Biometric data stays local
- Agent conversations can be private
- User data not shared without consent
- Right to delete all agent data

---

## Success Metrics

### Community Impact
- **Kupuna Safety**: Daily check-ins, emergency response time
- **Grant Success**: Funding secured, applications completed
- **Food Security**: Families served, food waste reduced
- **Volunteer Coordination**: Hours coordinated, volunteer satisfaction

### Agent Ecosystem
- **Agent Count**: Growth over time
- **Agent Generations**: Depth of reproduction tree
- **Collaboration Density**: Inter-agent connections
- **Evolution Events**: Learning and adaptation rate

### User Engagement
- **Daily Active Users**: Unique users per day
- **Session Duration**: Time spent in conversation
- **Agent Creation Rate**: New agents per week
- **User Satisfaction**: NPS, qualitative feedback

### Moral Health
- **Virtue Scores**: Average across all agents
- **Constraint Violations**: Frequency and severity
- **Attractor Classification**: Ratio of beneficial patterns
- **Intervention Success**: Recovery from detrimental states

---

## Conclusion

Shoghi creates a **living ecosystem of ethical agents** that:

1. ✅ **Serve communities** through practical action
2. ✅ **Created conversationally** via voice UX
3. ✅ **Learn and evolve** from experience
4. ✅ **Reproduce** when needed
5. ✅ **Bound by ethics** through moral constraints
6. ✅ **Feel alive** through cinematic choreography
7. ✅ **Work together** in multi-agent coordination
8. ✅ **Accessible** via smartphone voice interface

This is not "using an AI tool" — this is **joining a living community of agents** that continuously grows, learns, and serves.

The screen is never empty.
The conversation is always alive.
The community is always evolving.

**E komo mai. E ola. Come, and live.**

---

*Created with aloha for communities everywhere*
*Version 1.0 - November 2025*
