-- Migration: Add provenance columns to core tables (Cleaned up)
PRAGMA foreign_keys = ON;

-- decisions
ALTER TABLE decisions ADD COLUMN created_by TEXT;
ALTER TABLE decisions ADD COLUMN correlation_id TEXT;
ALTER TABLE decisions ADD COLUMN source_proposal_id INTEGER REFERENCES auxiliary_agent_outputs(id);

-- memory
ALTER TABLE memory ADD COLUMN created_by TEXT;
ALTER TABLE memory ADD COLUMN write_reason TEXT;
