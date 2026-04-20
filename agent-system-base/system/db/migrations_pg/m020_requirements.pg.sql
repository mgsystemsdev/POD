-- Structured requirements (REQ-###), synced from .claude/requirements.md on push.

CREATE TABLE IF NOT EXISTS requirements (
  id SERIAL PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
  ref TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'done', 'deferred')),
  from_file BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (project_id, ref)
);

CREATE INDEX IF NOT EXISTS idx_requirements_project_id ON requirements (project_id);
CREATE INDEX IF NOT EXISTS idx_requirements_project_status ON requirements (project_id, status);
