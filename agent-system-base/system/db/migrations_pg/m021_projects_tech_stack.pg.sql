-- Per-project tech stack selections (JSON document, overwritten on save).

ALTER TABLE projects ADD COLUMN IF NOT EXISTS tech_stack TEXT;
