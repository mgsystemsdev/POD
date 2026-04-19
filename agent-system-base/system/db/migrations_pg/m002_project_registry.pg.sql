-- Add root_path column to projects table.

ALTER TABLE projects ADD COLUMN IF NOT EXISTS root_path TEXT
