-- Extend runs table for manual-first execution model.
-- Adds: mode, input_prompt, output. Extends status CHECK. Copies agent -> output.

ALTER TABLE runs ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'ai';
ALTER TABLE runs ADD COLUMN IF NOT EXISTS input_prompt TEXT;
ALTER TABLE runs ADD COLUMN IF NOT EXISTS output TEXT;

ALTER TABLE runs DROP CONSTRAINT IF EXISTS runs_status_check;
ALTER TABLE runs ADD CONSTRAINT runs_status_check
  CHECK (status IN ('pending', 'pending_input', 'running', 'success', 'failed', 'cancelled'));

ALTER TABLE runs ADD CONSTRAINT runs_mode_check
  CHECK (mode IN ('manual', 'ai'));

UPDATE runs SET output = agent WHERE output IS NULL AND agent IS NOT NULL
