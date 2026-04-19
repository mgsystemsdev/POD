PRAGMA foreign_keys = ON;

ALTER TABLE decisions ADD COLUMN project_id INTEGER REFERENCES projects(id);
CREATE INDEX idx_decisions_project_id ON decisions(project_id);
