-- Stable keys for push_claude_artifacts file mirrors (upsert by project + source_key).

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS source_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_decisions_project_source_key
  ON decisions (project_id, source_key)
  WHERE source_key IS NOT NULL;

ALTER TABLE session_logs ADD COLUMN IF NOT EXISTS source_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_logs_project_source_key
  ON session_logs (project_id, source_key)
  WHERE source_key IS NOT NULL
