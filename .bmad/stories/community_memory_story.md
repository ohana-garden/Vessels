# Story: Community Memory for Knowledge Retention

## metadata
id: STORY-004
author: Stephen
date: 2025-11-11
tags: [community_memory, knowledge, retention]

## context
The Vessels platform benefits from remembering important interactions and learnings, such as summaries of past grant searches or feedback from elders. A community memory component allows the system to store and retrieve such information to improve responses over time.

## requirements
1. Persist key user interactions and outputs (e.g., requests, grant search results, elder-care protocols) in a memory store.
2. Provide a retrieval function that allows agents to query the memory based on keywords or tags.
3. Implement privacy safeguards, including redaction of personally identifiable information before storage.
4. Offer a summarization or pruning mechanism to keep the memory manageable and relevant.

## tools
community_memory

## acceptance_criteria
* At least three past interactions can be stored and retrieved with relevant details.
* Memory entries persist across sessions and restarts of the Vessels platform.
* Memory retrieval returns entries sorted by relevance to the query or tag.
* Privacy-sensitive data (like names, phone numbers) are redacted before storage.

## test_cases
* Store a sample grant search result and retrieve it later using a keyword from the original query.
* Store an elder care protocol summary and verify that sensitive personal identifiers are redacted.
* Add more than five entries and ensure that the summarization mechanism removes or compresses less relevant entries.
