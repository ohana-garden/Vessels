-- Migration: Add missing indexes for performance
-- Version: 1
-- Created: 2025-01-23

-- Memory table indexes (critical for O(n) -> O(log n) search)
CREATE INDEX IF NOT EXISTS idx_memories_agent ON memories(agent_id);
CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_agent_timestamp ON memories(agent_id, timestamp DESC);

-- Vessel registry indexes
CREATE INDEX IF NOT EXISTS idx_vessels_name ON vessels(name);
CREATE INDEX IF NOT EXISTS idx_vessels_privacy ON vessels(privacy_level);
CREATE INDEX IF NOT EXISTS idx_vessels_community ON vessels(community_id);
