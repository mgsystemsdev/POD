-- Add correlation_id and notes columns to tasks.

ALTER TABLE tasks ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS notes TEXT;
CREATE INDEX IF NOT EXISTS idx_tasks_correlation_id ON tasks(correlation_id)
