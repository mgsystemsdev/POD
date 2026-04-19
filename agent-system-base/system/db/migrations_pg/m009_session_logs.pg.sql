-- Session logs table for session summaries and notes.

CREATE TABLE IF NOT EXISTS session_logs (
  id BIGSERIAL PRIMARY KEY,
  project_id BIGINT NOT NULL REFERENCES projects(id),
  agent TEXT,
  scope_active TEXT,
  tasks_completed TEXT,
  next_task TEXT,
  git_state TEXT,
  open_issues TEXT,
  notes TEXT,
  session_date TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_session_logs_project_id ON session_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_session_logs_session_date ON session_logs(session_date)
