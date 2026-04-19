from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

DATABASE_PATH = str(Path.home() / "agents" / "agent-system-base" / "system" / "db" / "database.sqlite")
_BUSY_TIMEOUT_MS = 10_000
_SYSTEM_ROOT = Path(__file__).resolve().parent.parent
_MIGRATIONS_DIR = _SYSTEM_ROOT / "db" / "migrations"
_MIGRATIONS_PG_DIR = _SYSTEM_ROOT / "db" / "migrations_pg"


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_postgres() -> bool:
    url = os.environ.get("DATABASE_URL", "")
    return url.startswith(("postgres://", "postgresql://"))


# ── SQLite path (unchanged) ───────────────────────────────────────────────────

def _migration_files() -> list[Path]:
    if not _MIGRATIONS_DIR.is_dir():
        return []
    return sorted(p for p in _MIGRATIONS_DIR.glob("*.sql") if p.is_file())


def _applied_migrations(conn: sqlite3.Connection) -> set[str]:
    try:
        cur = conn.execute("SELECT migration_name FROM schema_version")
    except sqlite3.OperationalError:
        return set()
    return {row[0] for row in cur.fetchall()}


def _run_pending_migrations(conn: sqlite3.Connection) -> None:
    applied = _applied_migrations(conn)
    for path in _migration_files():
        name = path.name
        if name in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_version (migration_name, applied_at) VALUES (?, ?)",
                (name, _iso_now()),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise


def _configure_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA foreign_keys = ON")


@contextmanager
def _sqlite_connect(
    *,
    database: str | None = None,
    uri: bool = False,
) -> Generator[sqlite3.Connection, None, None]:
    path = DATABASE_PATH if database is None else database
    if database is None:
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, uri=uri)
    conn.row_factory = sqlite3.Row
    try:
        _configure_connection(conn)
        _run_pending_migrations(conn)
        yield conn
    finally:
        conn.close()


# ── Postgres path ─────────────────────────────────────────────────────────────

class _PgCursor:
    """Wraps a psycopg2 RealDictCursor to expose the same surface as sqlite3.Cursor."""

    def __init__(self, raw_cursor):
        self._cur = raw_cursor
        self.lastrowid = None
        self.rowcount = 0

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()


class _PgConnection:
    """Wraps a psycopg2 connection to present the same execute() API as sqlite3.Connection."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql: str, params=()):
        import psycopg2.extras
        pg_sql = sql.replace("?", "%s")
        raw = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        raw.execute(pg_sql, params)
        cur = _PgCursor(raw)
        cur.rowcount = raw.rowcount
        if "RETURNING id" in sql.upper():
            row = raw.fetchone()
            cur.lastrowid = row["id"] if row else None
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def _pg_migration_files() -> list[Path]:
    if not _MIGRATIONS_PG_DIR.is_dir():
        return []
    return sorted(p for p in _MIGRATIONS_PG_DIR.glob("*.pg.sql") if p.is_file())


def _applied_pg_migrations(raw_conn) -> set[str]:
    import psycopg2.extras
    try:
        cur = raw_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT migration_name FROM schema_version")
        return {row["migration_name"] for row in cur.fetchall()}
    except Exception:
        raw_conn.rollback()
        return set()


def _run_pg_migrations(raw_conn) -> None:
    applied = _applied_pg_migrations(raw_conn)
    for path in _pg_migration_files():
        name = path.name
        if name in applied:
            continue
        sql = path.read_text(encoding="utf-8")
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        try:
            cur = raw_conn.cursor()
            for stmt in statements:
                cur.execute(stmt)
            cur.execute(
                "INSERT INTO schema_version (migration_name, applied_at) VALUES (%s, %s)",
                (name, _iso_now()),
            )
            raw_conn.commit()
        except Exception:
            raw_conn.rollback()
            raise


@contextmanager
def _pg_connect() -> Generator[_PgConnection, None, None]:
    import psycopg2
    url = os.environ["DATABASE_URL"]
    raw = psycopg2.connect(url)
    try:
        _run_pg_migrations(raw)
        yield _PgConnection(raw)
    finally:
        raw.close()


# ── Public API ────────────────────────────────────────────────────────────────

@contextmanager
def connect(
    *,
    database: str | None = None,
    uri: bool = False,
):
    """Open the DB. Uses Postgres when DATABASE_URL is set, SQLite otherwise."""
    if _is_postgres():
        with _pg_connect() as conn:
            yield conn
    else:
        with _sqlite_connect(database=database, uri=uri) as conn:
            yield conn
