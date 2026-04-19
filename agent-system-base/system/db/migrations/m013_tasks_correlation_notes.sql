PRAGMA foreign_keys = ON;

ALTER TABLE tasks ADD COLUMN correlation_id TEXT;
ALTER TABLE tasks ADD COLUMN notes TEXT;
CREATE INDEX idx_tasks_correlation_id ON tasks(correlation_id);
