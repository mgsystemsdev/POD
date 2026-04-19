PRAGMA foreign_keys = ON;

ALTER TABLE tasks ADD COLUMN requirement_ref TEXT;
ALTER TABLE tasks ADD COLUMN decision_id INTEGER REFERENCES decisions(id);
CREATE INDEX idx_tasks_requirement_ref ON tasks(project_id, requirement_ref);
