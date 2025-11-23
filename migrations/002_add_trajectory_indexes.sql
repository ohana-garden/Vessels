-- Migration: Add trajectory and state indexes
-- Version: 2
-- Created: 2025-01-23

-- State tracking indexes
CREATE INDEX IF NOT EXISTS idx_states_agent_timestamp ON states(agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_security_events_blocked ON security_events(blocked, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transitions_agent ON transitions(agent_id);
CREATE INDEX IF NOT EXISTS idx_transitions_timestamp ON transitions(timestamp DESC);

-- Attractor indexes
CREATE INDEX IF NOT EXISTS idx_attractors_agent ON attractors(agent_id);
CREATE INDEX IF NOT EXISTS idx_attractors_strength ON attractors(strength DESC);
