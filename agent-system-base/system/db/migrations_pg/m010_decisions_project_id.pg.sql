-- Add project_id FK to decisions table.

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
CREATE INDEX IF NOT EXISTS idx_decisions_project_id ON decisions(project_id)
