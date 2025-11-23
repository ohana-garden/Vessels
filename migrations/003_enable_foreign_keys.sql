-- Migration: Enable foreign key constraints
-- Version: 3
-- Created: 2025-01-23

-- Enable foreign key enforcement (CRITICAL FIX)
PRAGMA foreign_keys=ON;

-- Verify foreign keys are enabled
PRAGMA foreign_keys;

-- Note: This migration ensures foreign key constraints are enforced.
-- Existing tables with foreign key definitions will now have those enforced.
