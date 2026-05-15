-- Migration: Add specialized auxiliary agent tables
PRAGMA foreign_keys = ON;

-- Specialist: Security Reviewer
CREATE TABLE IF NOT EXISTS security_findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  aux_output_id INTEGER NOT NULL REFERENCES auxiliary_agent_outputs(id),
  cve_id TEXT,
  severity TEXT NOT NULL CHECK(severity IN ('low', 'medium', 'high', 'critical')),
  component TEXT,
  vulnerability_desc TEXT NOT NULL,
  remediation_steps TEXT,
  created_at TEXT NOT NULL
);

-- Specialist: Database Specialist
CREATE TABLE IF NOT EXISTS db_recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  aux_output_id INTEGER NOT NULL REFERENCES auxiliary_agent_outputs(id),
  table_name TEXT,
  recommendation_type TEXT NOT NULL, -- 'schema', 'index', 'query_opt', 'migration'
  content TEXT NOT NULL,
  performance_impact TEXT,
  created_at TEXT NOT NULL
);

-- Specialist: Devil's Advocate
CREATE TABLE IF NOT EXISTS adversarial_critiques (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  aux_output_id INTEGER NOT NULL REFERENCES auxiliary_agent_outputs(id),
  counter_argument TEXT NOT NULL,
  failure_mode TEXT NOT NULL,
  confidence_score TEXT CHECK(confidence_score IN ('low', 'medium', 'high')),
  suggested_fix TEXT,
  created_at TEXT NOT NULL
);

-- Link auxiliary_agent_outputs to its specialist table via registry fields
ALTER TABLE auxiliary_agent_outputs ADD COLUMN specialist_table TEXT;
ALTER TABLE auxiliary_agent_outputs ADD COLUMN specialist_id INTEGER;

CREATE INDEX idx_sec_findings_proj ON security_findings(project_id);
CREATE INDEX idx_db_rec_proj ON db_recommendations(project_id);
CREATE INDEX idx_adv_crit_proj ON adversarial_critiques(project_id);
