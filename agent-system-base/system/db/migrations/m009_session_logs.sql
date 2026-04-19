PRAGMA foreign_keys = ON;

CREATE TABLE session_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
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

CREATE INDEX idx_session_logs_project_id ON session_logs(project_id);
CREATE INDEX idx_session_logs_session_date ON session_logs(session_date);
