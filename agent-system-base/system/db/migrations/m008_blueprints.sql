PRAGMA foreign_keys = ON;

CREATE TABLE blueprints (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_blueprints_project_id ON blueprints(project_id);
CREATE INDEX idx_blueprints_project_type ON blueprints(project_id, type);
