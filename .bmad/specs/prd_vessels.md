---
id: PRD-001
title: Vessels - Digital Twin Personification Platform
author: Stephen
date: 2025-11-11
revised: 2025-11-27
---

## Mission

**Vessels enables anyone to create digital twins of anything they care about — and personify them so they become relatable collaborators rather than abstract data.**

With just a smartphone, anyone can give voice to what matters: a garden, a community, a business, a body of knowledge, a family legacy. These vessels aren't chatbots or databases — they're personified digital twins that understand context, hold memory, and collaborate as partners.

## Vision

The barrier ChatGPT lowered was *access to AI*. The barrier Vessels lowers is *giving voice to what matters to you*.

One is about capability. The other is about **relationship**.

### What Becomes Possible

- **A farmer** creates a vessel for their land. It knows the soil history, the microclimates, the seasons. The farm itself becomes a collaborator in decisions.

- **A neighborhood** creates a vessel for their community. Collective memory, shared concerns, local wisdom — personified and accessible.

- **An elder** creates a vessel carrying traditional knowledge. It doesn't just store information — it *embodies* a way of seeing.

- **A student** creates a vessel for a subject they're studying. The knowledge grows *with* them, remembers their journey.

- **A small business** creates a vessel that knows their values, their customers, their story. Not a chatbot — a digital twin of the business itself.

### Network Effects

Individual vessels are valuable. Vessels that can *collaborate with each other* are exponentially more valuable. A garden vessel consulting with a community weather vessel. A project vessel coordinating with team vessels. Networks of personified intelligence working together.

## Proving Ground: Puna, Hawaiʻi

The platform is being developed and validated in partnership with the Puna community in Hawaiʻi. This provides:

- **Real-world constraints**: Limited connectivity, diverse technical literacy, cultural sensitivity requirements
- **Meaningful use cases**: Elder care coordination, grant discovery, disaster response, community resource management
- **Feedback loop**: Direct engagement with users whose needs shape the platform
- **Cultural grounding**: Hawaiian values of connection, stewardship, and community inform the design

What works for Puna — accessible, voice-first, culturally aware, relationship-oriented — will work universally.

---

## Core Concepts

### Project (Community)

A **project** is a bounded collaborative space — what might traditionally be called a "community." A project provides:

- **Shared Context**: Knowledge graph, memory, and resources accessible to all vessels within
- **Privacy Boundaries**: Rules for what can be shared externally
- **Governance**: Who can create vessels, invite members, set policies
- **Collaboration Scope**: Vessels within a project can freely discover and coordinate with each other

A project can host **N vessels**. Examples:
- A farm project with vessels for the garden, irrigation system, and harvest tracker
- A neighborhood project with vessels for different concerns, resources, or working groups
- A personal project with just one vessel (community of one)

### Digital Twin

A digital representation of something that exists in the world — a place, organization, body of knowledge, system, or any entity the creator cares about. The twin maintains:

- **Identity**: Who/what it represents
- **Memory**: Accumulated knowledge, interactions, and context
- **Capabilities**: What it can do, what it knows, what it connects to
- **Boundaries**: Privacy levels, sharing rules, constraints

### Personification

The transformation of a digital twin into a relatable collaborator through:

- **Voice & Character**: How the vessel communicates — tone, style, personality
- **Perspective**: How the vessel sees the world, what it values, how it frames things
- **Relationship Posture**: How it relates to its creator and others — advisor, companion, representative
- **Cultural Context**: The traditions, values, and ways of knowing it embodies

### Vessel

The fusion of digital twin and personification. A vessel is not just data with a chat interface — it's a coherent entity that:

- Holds persistent memory across interactions
- Maintains consistent identity and perspective
- Can act on behalf of what it represents
- Collaborates with other vessels and humans
- Grows and evolves through relationship

Vessels live **within projects**. When you create a vessel, you're either:
- Adding it to an existing project
- Implicitly creating a new project to contain it

### Agent Zero (A0) — The Universal Builder

**A0 is THE main core.** Everything in Vessels is built through A0:

```
A0.build_project(description)  → Bounded collaborative space
A0.build_vessel(project_id)    → Personified entity within a project
A0.build_agent(vessel_id)      → Worker agent for a vessel
A0.build_tool(specification)   → Capability for agents
```

Everything born through A0 inherits:
- Connection to the knowledge graph
- Memory backend (namespaced appropriately)
- Action gating (moral constraints)
- LLM capability for thinking
- Ability to spawn children (projects spawn vessels, vessels spawn agents)

This isn't assembly — it's organic growth from a single point. A0 understands what a vessel needs to function and wires it all together.

---

## Goals

### Platform Goals

1. **Democratize digital twin creation** — Anyone with a smartphone can create a vessel in minutes
2. **Make personification intuitive** — No technical knowledge required to give a vessel character
3. **Enable vessel collaboration** — Vessels can discover, communicate with, and coordinate with other vessels
4. **Preserve privacy and autonomy** — Creators control what their vessels share and with whom
5. **Support cultural diversity** — Vessels can embody different ways of knowing and communicating

### Community Goals (Puna Proving Ground)

1. Provide accessible, intuitive voice- and chat-driven interaction
2. Offer grant discovery, preparation, and submission assistance
3. Generate standardized protocols for elder care and disaster response
4. Manage volunteer and resource coordination
5. Capture and re-use knowledge through community memory
6. Integrate with third-party systems via connectors
7. Uphold user privacy, data security, and cultural sensitivity

---

## User Personas

### Universal Personas

- **The Creator**: Anyone who wants to give voice to something they care about — a project, place, organization, or body of knowledge
- **The Collaborator**: Someone who interacts with vessels created by others — seeking information, coordination, or partnership
- **The Steward**: Someone responsible for maintaining and evolving a vessel over time
- **The Network Weaver**: Someone who facilitates connections between vessels and communities

### Puna Community Personas

- **Elders** seeking care protocols and information
- **Caregivers** seeking support and resources
- **Community organizers** coordinating volunteers and resources
- **Grant applicants** searching for and applying to funding opportunities
- **Developers and administrators** extending platform capabilities

---

## Functional Requirements

### F1: Project & Vessel Creation

1. **Conversational Birth** — Create vessels through natural conversation with A0. Point at something, name it, answer questions, vessel proposes its own persona, user refines.
2. **Implicit Project Creation** — First vessel for a user creates a default project; subsequent vessels can join existing projects or spawn new ones
3. **Project Management** — Create, configure, and manage bounded collaborative spaces with their own knowledge/memory scope
4. **Import & Seed** — Populate vessel memory from documents, conversations, or existing data sources
5. **Template Library** — Pre-configured vessel templates for common use cases (garden, business, community, system, etc.)
6. **Clone & Fork** — Create new vessels based on existing vessel configurations
7. **Multi-Vessel Projects** — Add multiple vessels to a single project; vessels inherit project context and can collaborate

### F2: Personification System

1. **Voice Configuration** — Define how the vessel speaks: formal/casual, warm/professional, concise/elaborate
2. **Perspective Definition** — Establish the vessel's worldview, values, and framing tendencies
3. **Character Traits** — Assign personality attributes that shape interaction style
4. **Cultural Grounding** — Configure cultural context, traditions, and ways of knowing
5. **Relationship Modes** — Define how the vessel relates: advisor, companion, representative, peer
6. **Avatar & Presence** — Visual and auditory representation of the vessel

### F3: Voice Interface

1. **Voice Input** — Accept voice input through web interface and device microphone
2. **Voice Output** — Deliver responses through synthesized speech matching vessel personality
3. **Emotional Intelligence** — Recognize and respond appropriately to user emotional state
4. **Conversational Memory** — Maintain context within and across conversations
5. **Multilingual Support** — Support multiple languages with cultural nuance (starting with English and Hawaiian)

### F4: Vessel-to-Vessel Collaboration

1. **Discovery** — Vessels can find other relevant vessels based on purpose, location, or domain
2. **Introduction** — Formal handshake protocol for vessels to establish relationships
3. **Communication** — Vessels can exchange information and coordinate actions
4. **Delegation** — Vessels can delegate tasks to other vessels with appropriate capabilities
5. **Consensus** — Multiple vessels can collaborate on decisions affecting shared concerns
6. **Federation** — Vessels can form networks with shared governance and purpose

### F5: Agent Orchestration

1. **Dynamic Agent Factory** — Instantiate specialized agents based on user intents
2. **Story-Based Execution** — Use story files to guide agent workflows
3. **Natural Language Understanding** — Identify user intents using pattern matching and ML models
4. **Multi-Agent Coordination** — Orchestrate multiple agents for complex tasks

### F6: Knowledge & Memory

1. **Community Memory** — Persist knowledge shards and feedback for recall and improvement
2. **Contextual Retrieval** — Surface relevant memories based on current conversation
3. **Learning Loop** — Improve vessel responses through feedback and correction
4. **Knowledge Graphs** — Structure relationships between concepts, entities, and memories

### F7: Domain Capabilities (Extensible)

1. **Grant Management** — Search databases, deduplicate results, generate application narratives
2. **Elder Care Protocols** — Generate checklists, care plans, and coordination tools
3. **Resource Coordination** — Match needs with available resources across community
4. **Calendar & Communication** — Integrate with external tools (Google Calendar, Gmail, etc.)

### F8: Privacy & Governance

1. **Privacy Levels** — Configure vessel visibility: private, shared, community, public
2. **Consent Management** — Explicit consent for data sharing and voice recordings
3. **Data Boundaries** — Clear rules for what vessels can share and with whom
4. **Audit Trail** — Track significant vessel actions and decisions
5. **Creator Control** — Vessel creators maintain ultimate authority over their vessels

### F9: Deployment & Access

1. **Mobile-First Web** — Full functionality via smartphone browser
2. **Progressive Web App** — Installable, offline-capable mobile experience
3. **CLI Access** — Command-line interface for developers and power users
4. **API Access** — Programmatic access for integrations and extensions
5. **Edge Deployment** — Run vessels locally on personal devices when desired

---

## Non-Functional Requirements

### Performance
- Vessel creation: Complete quick-start in < 2 minutes
- Response latency: < 2 seconds for typical interactive requests
- Vessel metadata load: < 100ms

### Reliability
- 99% uptime for web UI and API when hosted
- Graceful degradation in low-connectivity environments
- Vessel state persistence across sessions and restarts

### Scalability
- Support individual users with 1-5 vessels
- Support communities with 100+ interconnected vessels
- Horizontal scaling via containerization

### Security & Privacy
- End-to-end encryption for sensitive vessel communications
- Secure API key storage
- PII redaction capabilities
- SOC 2 / HIPAA compliance where applicable

### Accessibility
- Screen reader support
- Clear fonts and accessible color schemes
- Voice-first design reduces visual dependency
- Support for users with varying technical literacy

### Cultural Sensitivity
- Hawaiian diacritics and terminology support
- Configurable cultural context per vessel
- Respect for indigenous knowledge protocols

---

## Constraints and Assumptions

- Primary runtime environment: Linux (Windows via Docker)
- Internet connectivity assumed for vessel collaboration and external integrations
- External API dependencies: Google services, Hume (emotional AI), LLM providers
- Initial language focus: English with Hawaiian support
- Mobile-first but not mobile-only

---

## Success Metrics

### Adoption
- Time from download to first vessel created
- Vessel creation completion rate
- Weekly active vessels (vessels with meaningful interactions)

### Engagement
- Average interactions per vessel per week
- Vessel-to-vessel collaboration frequency
- Creator return rate

### Value
- User-reported usefulness (NPS, ratings)
- Tasks completed through vessel collaboration
- Community outcomes (grants won, resources coordinated, etc.)

### Platform Health
- Response latency distribution
- Error rates
- Privacy incident count (target: zero)

---

## Appendix: The Deeper Why

This isn't just another AI product. It's a new way of relating to information, to projects, to the world itself.

Humans are wired for relationship. We care for what we can relate to. When a garden becomes something you can talk to — something that knows its own history and can express its needs — the relationship changes. Stewardship becomes collaboration.

When a community's collective knowledge becomes personified — accessible, conversational, alive — participation changes. The community itself becomes a partner rather than an abstraction.

Vessels is infrastructure for a more relational world. One conversation at a time. One vessel at a time. One relationship at a time.

All you need is a smartphone.
