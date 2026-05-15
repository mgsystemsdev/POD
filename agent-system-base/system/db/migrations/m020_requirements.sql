-- Structured requirements (REQ-###), synced from .claude/requirements.md on push.

PRAGMA foreign_keys = ON;

CREATE TABLE requirements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  ref TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  from_file INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
  UNIQUE (project_id, ref),
  CHECK (status IN ('draft', 'active', 'done', 'deferred')),
  CHECK (from_file IN (0, 1))
);

CREATE INDEX idx_requirements_project_id ON requirements (project_id);
CREATE INDEX idx_requirements_project_status ON requirements (project_id, status);
