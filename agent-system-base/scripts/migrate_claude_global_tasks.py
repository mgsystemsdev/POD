#!/usr/bin/env python3
"""
One-off: clean claude-global SQLite tasks — remove duplicates of dmrb titles,
move Agent System Base work to agent-system-base.

Safe to re-run: duplicate DELETE is idempotent; UPDATE only touches remaining rows.

Usage:
  python3 migrate_claude_global_tasks.py          # dry-run
  python3 migrate_claude_global_tasks.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_SERVICES = Path(__file__).resolve().parent.parent / "system" / "services"
sys.path.insert(0, str(_SERVICES))

import db  # noqa: E402


def _project_ids(conn) -> dict[str, int]:
    rows = conn.execute("SELECT slug, id FROM projects").fetchall()
    return {r["slug"]: int(r["id"]) for r in rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    args = parser.parse_args()

    with db.connect() as conn:
        pids = _project_ids(conn)
        need = ("claude-global", "dmrb", "agent-system-base")
        for s in need:
            if s not in pids:
                raise SystemExit(f"missing project slug in DB: {s!r}")

        cg = pids["claude-global"]
        dmrb = pids["dmrb"]
        asb = pids["agent-system-base"]

        # 1) Delete global rows whose title already exists on dmrb (import source)
        dup_sql = """
        SELECT t.id, t.title FROM tasks t
        WHERE t.project_id = ?
          AND t.title IN (
            SELECT t2.title FROM tasks t2
            WHERE t2.project_id = ? AND t2.source = 'import'
          )
        """
        dups = conn.execute(dup_sql, (cg, dmrb)).fetchall()
        print(f"Duplicate titles (global rows to delete): {len(dups)}")
        for r in dups:
            print(f"  DELETE id={r['id']} title={r['title']!r}")

        # 2) Move remaining ASB work: Execution loop + Claude worker stack titles
        asb_titles_exact = (
            "Add Claude API execution module (no DB)",
            "Prompt builder: task row + project context",
            "Wire task_worker: replace mock with real execution + run_service",
            "Timeout + retry policy for Claude calls",
            "Update test_task_worker: mock Claude, assert runs + task status",
            "Document env vars and operator runbook",
        )
        placeholders = ",".join("?" * len(asb_titles_exact))
        q_asb = f"""
        SELECT id, title FROM tasks
        WHERE project_id = ? AND (
          title LIKE 'Execution Loop%'
          OR title IN ({placeholders})
        )
        """
        asb_rows = conn.execute(q_asb, (cg, *asb_titles_exact)).fetchall()
        print(f"Rows to move to agent-system-base: {len(asb_rows)}")
        for r in asb_rows:
            print(f"  UPDATE id={r['id']} -> asb title={r['title']!r}")

        if not args.apply:
            print("\nDry-run only. Pass --apply to execute.")
            return

        if dups:
            ids = tuple(r["id"] for r in dups)
            conn.execute(f"DELETE FROM tasks WHERE id IN ({','.join('?' * len(ids))})", ids)
            print(f"Deleted {len(ids)} duplicate global task(s).")

        if asb_rows:
            ids = [r["id"] for r in asb_rows]
            conn.execute(
                f"""
                UPDATE tasks SET project_id = ?, updated_at = datetime('now')
                WHERE id IN ({",".join("?" * len(ids))})
                """,
                (asb, *ids),
            )
            print(f"Moved {len(ids)} task(s) to agent-system-base.")

        conn.commit()
        print("Done.")


if __name__ == "__main__":
    main()
