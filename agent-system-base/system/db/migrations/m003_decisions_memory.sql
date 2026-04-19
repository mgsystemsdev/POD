-- Persistent decisions (append-only at service layer) and key-value memory (upsert by key).
PRAGMA foreign_keys = ON;

CREATE TABLE decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE memory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT NOT NULL UNIQUE,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX idx_decisions_created_at ON decisions (created_at);
