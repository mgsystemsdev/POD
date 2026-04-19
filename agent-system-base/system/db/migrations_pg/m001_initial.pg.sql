-- Initial schema: migration ledger, projects, tasks, agent runs.

CREATE TABLE IF NOT EXISTS schema_version (
  migration_name TEXT PRIMARY KEY NOT NULL,
  applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id BIGSERIAL PRIMARY KEY,
  project_id BIGINT NOT NULL,
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

CREATE TABLE IF NOT EXISTS runs (
  id BIGSERIAL PRIMARY KEY,
  task_id BIGINT NOT NULL,
  status TEXT NOT NULL,
  agent TEXT,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  error_message TEXT,
  FOREIGN KEY (task_id) REFERENCES tasks (id),
  CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks (project_id);
CREATE INDEX IF NOT EXISTS idx_runs_task_id ON runs (task_id)
