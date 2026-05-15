-- Migration: Add provenance columns to core tables (Postgres Safe)

ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS write_reason TEXT;
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS source_proposal_ref TEXT;

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_by TEXT;

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS source_proposal_id INTEGER REFERENCES auxiliary_agent_outputs(id);

ALTER TABLE memory ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE memory ADD COLUMN IF NOT EXISTS write_reason TEXT;
