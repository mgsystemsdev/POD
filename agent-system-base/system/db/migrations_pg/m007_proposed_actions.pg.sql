-- AI action proposal staging table.

CREATE TABLE IF NOT EXISTS proposed_actions (
  id          BIGSERIAL PRIMARY KEY,
  type        TEXT    NOT NULL,
  payload     TEXT    NOT NULL,
  status      TEXT    NOT NULL DEFAULT 'pending',
  created_by  TEXT,
  created_at  TEXT    NOT NULL,
  reviewed_at TEXT,
  review_note TEXT,
  CHECK (type   IN ('create_task', 'update_task', 'other')),
  CHECK (status IN ('pending', 'approved', 'rejected'))
);

CREATE INDEX IF NOT EXISTS idx_proposed_actions_status ON proposed_actions (status)
