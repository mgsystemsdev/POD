PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE memory_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  project_id INTEGER NOT NULL REFERENCES projects(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(project_id, key)
);

DROP TABLE memory;
ALTER TABLE memory_new RENAME TO memory;
CREATE INDEX idx_memory_project_id ON memory(project_id);

COMMIT;
PRAGMA foreign_keys = ON;
