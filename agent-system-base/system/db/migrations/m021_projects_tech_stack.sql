-- Per-project tech stack selections (JSON document, overwritten on save).
PRAGMA foreign_keys = ON;

ALTER TABLE projects ADD COLUMN tech_stack TEXT;
