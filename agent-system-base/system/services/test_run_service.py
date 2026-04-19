"""Tests for run_service using temp SQLite + patched db.connect (same pattern as test_task_service)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import unittest.mock
import uuid
from contextlib import contextmanager
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import db as db_mod  # noqa: E402
import run_service  # noqa: E402

_real_connect = db_mod.connect


class TestRunService(unittest.TestCase):
    def setUp(self) -> None:
        fd, self._db_path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self._db_path) and os.unlink(self._db_path))

        @contextmanager
        def _patched_connect(*, database: str | None = None, uri: bool = False):
            if database is None:
                with _real_connect(database=self._db_path) as conn:
                    yield conn
            else:
                with _real_connect(database=database, uri=uri) as conn:
                    yield conn

        self._patcher = unittest.mock.patch.object(run_service.db, "connect", _patched_connect)
        self._patcher.start()
        self._project_id = self._insert_project()
        self._task_id = self._insert_task(self._project_id)

    def tearDown(self) -> None:
        self._patcher.stop()

    def _insert_project(self) -> int:
        now = "2026-01-01T00:00:00Z"
        slug = f"r_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, slug, created_at, updated_at) VALUES (?,?,?,?)",
                ("Run Test Project", slug, now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def _insert_task(self, project_id: int) -> int:
        now = "2026-01-01T00:00:00Z"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO tasks (
                  project_id, title, description, status, priority, type, source, created_at, updated_at
                ) VALUES (?, ?, NULL, 'pending', 'normal', 'chore', 'manual', ?, ?)
                """,
                (project_id, "task for runs", now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def test_create_run_pending_timestamps(self) -> None:
        r = run_service.create_run(self._task_id)
        self.assertEqual(r["status"], "pending")
        self.assertIsNotNone(r["started_at"])
        self.assertIsNone(r["completed_at"])
        self.assertIsNone(r["error_message"])
        self.assertIsNone(r["output"])  # agent is legacy; output is the active field

    def test_lifecycle_success_sets_completed_at(self) -> None:
        r = run_service.create_run(self._task_id)
        r1 = run_service.update_run(r["id"], "running")
        assert r1 is not None
        self.assertEqual(r1["status"], "running")
        self.assertIsNone(r1["completed_at"])
        r2 = run_service.update_run(r["id"], "success", output={"ok": True})
        assert r2 is not None
        self.assertEqual(r2["status"], "success")
        self.assertIsNotNone(r2["started_at"])
        self.assertIsNotNone(r2["completed_at"])
        self.assertIsNone(r2["error_message"])

    def test_failed_requires_error(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        with self.assertRaises(ValueError) as ctx:
            run_service.update_run(r["id"], "failed", error=None)
        self.assertEqual(str(ctx.exception), "failed runs require error")

    def test_failed_sets_error_message(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        r2 = run_service.update_run(r["id"], "failed", error={"code": 500})
        assert r2 is not None
        self.assertEqual(r2["status"], "failed")
        self.assertIn("500", r2["error_message"] or "")
        self.assertIsNotNone(r2["completed_at"])

    def test_success_rejects_error_kwarg(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "success", error="nope")

    def test_invalid_status_raises(self) -> None:
        r = run_service.create_run(self._task_id)
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "boom")

    def test_illegal_pending_to_success(self) -> None:
        r = run_service.create_run(self._task_id)
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "success")

    def test_illegal_running_to_pending(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "pending")

    def test_terminal_immutable(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        run_service.update_run(r["id"], "success", output="done")
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "failed", error="x")

    def test_get_runs_for_task_reverse_chronological(self) -> None:
        a = run_service.create_run(self._task_id)
        b = run_service.create_run(self._task_id)
        listed = run_service.get_runs_for_task(self._task_id)
        self.assertEqual([x["id"] for x in listed], [b["id"], a["id"]])

    def test_get_runs_for_task_empty(self) -> None:
        t_other = self._insert_task(self._project_id)
        self.assertEqual(run_service.get_runs_for_task(t_other), [])

    def test_update_missing_returns_none(self) -> None:
        self.assertIsNone(run_service.update_run(999_999, "running"))

    def test_cancelled_optional_error(self) -> None:
        r = run_service.create_run(self._task_id)
        run_service.update_run(r["id"], "running")
        c = run_service.update_run(r["id"], "cancelled")
        assert c is not None
        self.assertEqual(c["status"], "cancelled")
        self.assertIsNone(c["error_message"])
        self.assertIsNotNone(c["completed_at"])

    def test_agent_not_in_row_dict(self) -> None:
        """agent is legacy read-only — must not appear in returned dict."""
        r = run_service.create_run(self._task_id)
        self.assertNotIn("agent", r)

    # ── pending_input lifecycle ───────────────────────────────────────────────

    def test_pending_to_pending_input_legal(self) -> None:
        r = run_service.create_run(self._task_id, mode="manual")
        p = run_service.update_run(r["id"], "pending_input", input_prompt="hello")
        assert p is not None
        self.assertEqual(p["status"], "pending_input")
        self.assertEqual(p["input_prompt"], "hello")
        self.assertIsNone(p["completed_at"])

    def test_pending_input_to_running_legal(self) -> None:
        r = run_service.create_run(self._task_id, mode="manual")
        run_service.update_run(r["id"], "pending_input", input_prompt="p")
        rr = run_service.update_run(r["id"], "running")
        assert rr is not None
        self.assertEqual(rr["status"], "running")

    def test_pending_to_success_still_illegal(self) -> None:
        r = run_service.create_run(self._task_id)
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "success")

    def test_pending_input_to_success_illegal(self) -> None:
        """pending_input must go through running before reaching terminal."""
        r = run_service.create_run(self._task_id, mode="manual")
        run_service.update_run(r["id"], "pending_input", input_prompt="p")
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "success")

    def test_input_prompt_only_on_pending_input_transition(self) -> None:
        r = run_service.create_run(self._task_id)
        with self.assertRaises(ValueError):
            run_service.update_run(r["id"], "running", input_prompt="bad")

    def test_mode_manual_stored(self) -> None:
        r = run_service.create_run(self._task_id, mode="manual")
        self.assertEqual(r["mode"], "manual")

    def test_mode_ai_default(self) -> None:
        r = run_service.create_run(self._task_id)
        self.assertEqual(r["mode"], "ai")

    def test_mode_invalid_raises(self) -> None:
        with self.assertRaises(ValueError):
            run_service.create_run(self._task_id, mode="robot")

    # ── complete_manual_run ───────────────────────────────────────────────────

    def test_complete_manual_run_ordering(self) -> None:
        """task → done timestamp must come before run.completed_at."""

        r = run_service.create_run(self._task_id, mode="manual")
        run_service.update_run(r["id"], "pending_input", input_prompt="prompt")

        task, run = run_service.complete_manual_run(r["id"], "my output")

        self.assertEqual(task["status"], "done")
        self.assertEqual(run["status"], "success")
        self.assertEqual(run["output"], "my output")

        # task.updated_at <= run.completed_at
        self.assertLessEqual(task["updated_at"], run["completed_at"])

    def test_complete_manual_run_requires_pending_input(self) -> None:
        r = run_service.create_run(self._task_id, mode="manual")
        with self.assertRaises(ValueError, msg="run must be pending_input"):
            run_service.complete_manual_run(r["id"], "output")

    def test_complete_manual_run_missing_run_raises(self) -> None:
        with self.assertRaises(ValueError):
            run_service.complete_manual_run(999_999, "output")


if __name__ == "__main__":
    unittest.main()
