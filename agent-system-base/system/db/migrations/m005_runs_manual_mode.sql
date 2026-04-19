-- m005: Extend runs table for manual-first execution model.
-- Adds: mode (manual|ai), input_prompt, output columns.
-- Adds: pending_input to status CHECK.
-- agent column is retained as legacy read-only; existing data copied to output.
-- All new code writes to output only; agent is never written post-migration.
PRAGMA foreign_keys = OFF;

CREATE TABLE runs_new (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id       INTEGER NOT NULL,
  mode          TEXT NOT NULL DEFAULT 'ai'
                  CHECK (mode IN ('manual', 'ai')),
  status        TEXT NOT NULL
                  CHECK (status IN ('pending', 'pending_input', 'running', 'success', 'failed', 'cancelled')),
  input_prompt  TEXT,
  output        TEXT,
  agent         TEXT,
  started_at    TEXT NOT NULL,
  completed_at  TEXT,
  error_message TEXT,
  FOREIGN KEY (task_id) REFERENCES tasks (id)
);

INSERT INTO runs_new (
  id, task_id, mode, status, input_prompt, output, agent, started_at, completed_at, error_message
)
SELECT
  id,
  task_id,
  'ai',
  status,
  NULL,
  agent,
  agent,
  started_at,
  completed_at,
  error_message
FROM runs;

DROP TABLE runs;
ALTER TABLE runs_new RENAME TO runs;

CREATE INDEX idx_runs_task_id ON runs (task_id);

PRAGMA foreign_keys = ON;
