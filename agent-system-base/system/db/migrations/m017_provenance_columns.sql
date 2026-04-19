-- Migration: Add provenance columns to core tables
PRAGMA foreign_keys = ON;

-- Adding columns to existing tables for Baton Pipeline traceability
ALTER TABLE blueprints ADD COLUMN created_by TEXT;
ALTER TABLE blueprints ADD COLUMN correlation_id TEXT;
ALTER TABLE blueprints ADD COLUMN write_reason TEXT;
ALTER TABLE blueprints ADD COLUMN source_proposal_ref TEXT;

ALTER TABLE tasks ADD COLUMN created_by TEXT;
ALTER TABLE tasks ADD COLUMN correlation_id TEXT;

ALTER TABLE decisions ADD COLUMN created_by TEXT;
ALTER TABLE decisions ADD COLUMN correlation_id TEXT;
ALTER TABLE decisions ADD COLUMN source_proposal_id INTEGER REFERENCES auxiliary_agent_outputs(id);

ALTER TABLE memory ADD COLUMN created_by TEXT;
ALTER TABLE memory ADD COLUMN write_reason TEXT;
