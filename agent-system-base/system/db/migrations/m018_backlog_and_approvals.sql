-- Migration: Add backlog, approvals, and validations tables
PRAGMA foreign_keys = ON;

-- The "waiting room" for ideas
CREATE TABLE IF NOT EXISTS backlog (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  title TEXT NOT NULL,
  description TEXT,
  submitted_by TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'backlog' CHECK(status IN ('backlog', 'promoted', 'rejected')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- The authoritative audit log for Human-in-the-Loop gates
CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  entity_type TEXT NOT NULL, -- 'proposal', 'task', 'blueprint', 'backlog'
  entity_id INTEGER NOT NULL,
  approver_role TEXT DEFAULT 'human_operator',
  decision TEXT NOT NULL CHECK(decision IN ('approved', 'rejected')),
  reason TEXT,
  created_at TEXT NOT NULL
);

-- Spec Gate Validation Log
CREATE TABLE IF NOT EXISTS validations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  blueprint_id INTEGER NOT NULL REFERENCES blueprints(id),
  status TEXT NOT NULL CHECK(status IN ('passed', 'blocked')),
  findings TEXT, -- JSON string of missing contract elements or gaps
  created_at TEXT NOT NULL
);

-- High-fidelity log of agent tool use
CREATE TABLE IF NOT EXISTS execution_trace (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER REFERENCES tasks(id),
  run_id INTEGER REFERENCES runs(id),
  agent_role TEXT NOT NULL,
  action TEXT NOT NULL,
  result TEXT,
  error_message TEXT,
  timestamp TEXT NOT NULL
);

CREATE INDEX idx_backlog_project ON backlog(project_id);
CREATE INDEX idx_approvals_entity ON approvals(entity_type, entity_id);
CREATE INDEX idx_validations_blueprint ON validations(blueprint_id);
