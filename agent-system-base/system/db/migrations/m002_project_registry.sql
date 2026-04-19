-- Project registry: optional on-disk root for context loading (T10 project registry + context loader).
PRAGMA foreign_keys = ON;

ALTER TABLE projects ADD COLUMN root_path TEXT;
