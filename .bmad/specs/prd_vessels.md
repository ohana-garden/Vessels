---
id: PRD-001
title: Vessels Voice-First Assistant Platform
author: Stephen
date: 2025-11-11
---

## Executive Summary

Vessels is a voice-first, context-aware assistant platform designed to support community members in Puna, Hawaiʻī. It combines specialized AI agents, dynamic agent orchestration, a persistent community memory and universal connectors to deliver grant discovery, elder-care programs, resource coordination and general assistance.

## Goals

- Provide accessible, intuitive voice- and chat-driven interaction.
- Offer grant discovery, preparation and submission assistance for individuals and organizations.
- Generate standardized protocols, checklists and narratives for elder care and disaster response.
- Manage volunteer and resource coordination across the community.
- Capture and re-use knowledge through a community memory system.
- Integrate seamlessly with third-party systems via connectors (e.g., Google Calendar, Gmail, etc.).
- Uphold user privacy, data security and cultural sensitivity.

## User Personas

- Elders seeking care protocols and information.
- Caregivers seeking support and resources.
- Community organizers coordinating volunteers and resources.
- Grant applicants searching for and applying to funding opportunities.
- Developers and administrators extending Vessels’s capabilities.

## Functional Requirements

1. **Voice Interface** – Accept voice input and deliver voice responses through a web interface and local device microphone/speaker.
2. **Natural Language Understanding** – Identify user intents (grant discovery, elder care, community coordination, etc.) using regex patterns and optional ML models.
3. **Dynamic Agent Orchestration** – Instantiate specialized agents based on user intents using the BMAD-defined agent specifications and load them from `.bmad/agents`.
4. **Story-Based Task Execution** – Use story files from `.bmad/stories` to guide the agent workflow, ensuring each story’s context, requirements and acceptance criteria are satisfied.
5. **Grant Management** – Search external grant databases, scrape websites with respect to robots.txt, deduplicate results, store grants in a local SQLite database and generate narrative sections for applications.
6. **Community Memory** – Persist knowledge shards and user feedback to support recall and continuous improvement.
7. **User Feedback Loop** – Provide feedback mechanisms (ratings, corrections) and store them for effectiveness metrics.
8. **Deployment and Scaling** – Run locally via CLI, host via Flask web server and optionally deploy in Docker using `deploy_vessels.sh`.

## Non-Functional Requirements

- **Reliability:** 99% uptime for web UI and API when hosted.
- **Performance:** Latency under 2 seconds for typical interactive requests.
- **Scalability:** Modular design allows horizontal scaling via containerization.
- **Privacy & Security:** Redact personally identifiable information and require explicit consent for voice recordings. Securely store API keys.
- **Compliance:** Follow industry standards (SOC 2, HIPAA) in data handling where applicable.
- **Accessibility:** Provide clear fonts, accessible color schemes and support for screen readers.

## Constraints and Assumptions

- The platform will run primarily in a Linux environment; Windows support via Docker.
- Internet connectivity is assumed for grant searches and connector usage.
- Some tasks rely on external APIs (e.g. Google, Hume) and may require valid API keys.
- The system is currently English-centric but should incorporate Hawaiian diacritics and multicultural terminology where possible.
