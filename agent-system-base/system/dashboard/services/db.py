"""
Shared database connection helper.

Supports both PostgreSQL (via DATABASE_URL) and SQLite (fallback for local dev).
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

_DATABASE_URL = os.environ.get("DATABASE_URL", "")

# ── SQLite fallback ────────────────────────────────────────────────────────────
_SQLITE_PATH = Path(os.environ.get("SQLITE_PATH", "/app/data/dashboard.db"))
_sqlite_local: threading.local = threading.local()


def _get_sqlite() -> sqlite3.Connection:
    conn = getattr(_sqlite_local, "conn", None)
    if conn is None:
        _SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(_SQLITE_PATH), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        _sqlite_local.conn = conn
    return conn


# ── PostgreSQL ─────────────────────────────────────────────────────────────────
_pg_pool = None
_pg_lock = threading.Lock()


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        with _pg_lock:
            if _pg_pool is None:
                import psycopg2
                from psycopg2 import pool as pg_pool

                _pg_pool = pg_pool.ThreadedConnectionPool(1, 10, _DATABASE_URL)
    return _pg_pool


# ── Public API ─────────────────────────────────────────────────────────────────

USE_PG = bool(_DATABASE_URL)


@contextmanager
def get_conn() -> Generator:
    if USE_PG:
        pool = _get_pg_pool()
        conn = pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)
    else:
        conn = _get_sqlite()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def fetchall(cursor) -> list[dict]:
    """Return all rows as plain dicts regardless of backend."""
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def fetchone(cursor) -> dict | None:
    """Return one row as a plain dict, or None."""
    row = cursor.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def init_schema() -> None:
    """Create all tables if they don't exist yet."""
    ddl = """
    CREATE TABLE IF NOT EXISTS projects (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        name       TEXT NOT NULL,
        slug       TEXT NOT NULL UNIQUE,
        root_path  TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id       INTEGER NOT NULL REFERENCES projects(id),
        title            TEXT NOT NULL,
        description      TEXT,
        notes            TEXT,
        status           TEXT NOT NULL DEFAULT 'pending',
        priority         TEXT NOT NULL DEFAULT 'normal',
        correlation_id   TEXT,
        requirement_ref  TEXT,
        decision_id      INTEGER,
        created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
        updated_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS runs (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id    INTEGER NOT NULL REFERENCES tasks(id),
        mode       TEXT NOT NULL DEFAULT 'auto',
        status     TEXT NOT NULL DEFAULT 'pending',
        output     TEXT,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS blueprints (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id     INTEGER NOT NULL REFERENCES projects(id),
        blueprint_type TEXT NOT NULL DEFAULT 'prd',
        title          TEXT NOT NULL,
        content        TEXT NOT NULL DEFAULT '',
        version        INTEGER NOT NULL DEFAULT 1,
        created_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
        updated_at     TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS decisions (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER REFERENCES projects(id),
        title      TEXT NOT NULL,
        content    TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS memory (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id),
        key        TEXT NOT NULL,
        value      TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
        UNIQUE(project_id, key)
    );

    CREATE TABLE IF NOT EXISTS session_logs (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id       INTEGER NOT NULL REFERENCES projects(id),
        session_date     TEXT NOT NULL,
        agent            TEXT,
        scope_active     TEXT,
        tasks_completed  TEXT,
        next_task        TEXT,
        git_state        TEXT,
        open_issues      TEXT,
        notes            TEXT,
        created_at       TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS proposed_actions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id  INTEGER REFERENCES projects(id),
        title       TEXT NOT NULL,
        description TEXT,
        status      TEXT NOT NULL DEFAULT 'pending',
        note        TEXT,
        created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now')),
        updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );

    CREATE TABLE IF NOT EXISTS auxiliary_agent_outputs (
        id                      INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id              INTEGER NOT NULL REFERENCES projects(id),
        agent_role              TEXT NOT NULL,
        content                 TEXT NOT NULL,
        target_core_agent       TEXT,
        related_requirement_ref TEXT,
        related_decision_id     INTEGER,
        created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ','now'))
    );
    """
    if USE_PG:
        # PostgreSQL: adapt AUTOINCREMENT → SERIAL, strftime → NOW()
        pg_ddl = ddl.replace(
            "INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY"
        ).replace(
            "strftime('%Y-%m-%dT%H:%M:%SZ','now')", "NOW()"
        )
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(pg_ddl)
    else:
        with get_conn() as conn:
            conn.executescript(ddl)


# Initialise schema on import
init_schema()
