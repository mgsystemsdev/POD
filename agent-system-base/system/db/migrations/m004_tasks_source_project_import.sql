-- T12.1: Extend tasks.source CHECK to allow 'project_import' (SQLite table rebuild).
-- Preserves row ids and runs.task_id foreign keys.
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE tasks_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL,
  priority TEXT NOT NULL,
  type TEXT NOT NULL,
  source TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  FOREIGN KEY (project_id) REFERENCES projects (id),
  CHECK (status IN ('pending', 'queued', 'in_progress', 'blocked', 'done', 'cancelled', 'failed')),
  CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
  CHECK (type IN ('feature', 'bug', 'chore', 'research', 'maintenance', 'other')),
  CHECK (source IN ('manual', 'cron', 'api', 'import', 'orchestrator', 'other', 'project_import'))
);

INSERT INTO tasks_new SELECT * FROM tasks;

DROP TABLE tasks;

ALTER TABLE tasks_new RENAME TO tasks;

CREATE INDEX idx_tasks_project_id ON tasks (project_id);

COMMIT;

PRAGMA foreign_keys = ON;
