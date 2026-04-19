-- Add project_id FK to proposed_actions table.

ALTER TABLE proposed_actions ADD COLUMN IF NOT EXISTS project_id BIGINT REFERENCES projects(id);
CREATE INDEX IF NOT EXISTS idx_proposed_actions_project_id ON proposed_actions(project_id)
