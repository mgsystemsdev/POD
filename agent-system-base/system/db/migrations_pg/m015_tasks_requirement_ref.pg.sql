-- Add requirement_ref and decision_id columns to tasks.

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS requirement_ref TEXT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS decision_id BIGINT REFERENCES decisions(id);
CREATE INDEX IF NOT EXISTS idx_tasks_requirement_ref ON tasks(project_id, requirement_ref)
