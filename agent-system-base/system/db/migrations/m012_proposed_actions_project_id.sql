PRAGMA foreign_keys = ON;

ALTER TABLE proposed_actions ADD COLUMN project_id INTEGER REFERENCES projects(id);
CREATE INDEX idx_proposed_actions_project_id ON proposed_actions(project_id);
