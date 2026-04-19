-- AI action proposal staging: all AI-proposed task operations land here
-- before a human approves via the dashboard.
-- proposed_action_service.py is the only allowed writer.

CREATE TABLE proposed_actions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE INDEX idx_proposed_actions_status ON proposed_actions (status);
