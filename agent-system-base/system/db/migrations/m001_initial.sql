-- Initial schema: migration ledger, projects, tasks, agent runs.
PRAGMA foreign_keys = ON;

CREATE TABLE schema_version (
  migration_name TEXT PRIMARY KEY NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE projects (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE tasks (
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
  CHECK (source IN ('manual', 'cron', 'api', 'import', 'orchestrator', 'other'))
);

CREATE TABLE runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER NOT NULL,
  status TEXT NOT NULL,
  agent TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  error_message TEXT,
  FOREIGN KEY (task_id) REFERENCES tasks (id),
  CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled'))
);

CREATE INDEX idx_tasks_project_id ON tasks (project_id);
CREATE INDEX idx_runs_task_id ON runs (task_id);
