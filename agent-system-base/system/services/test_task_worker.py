"""Tests for task_worker: manual mode, AI mode, recovery, idempotency."""

from __future__ import annotations

import io
import os
import shutil
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
import task_service  # noqa: E402
import task_worker  # noqa: E402

_real_connect = db_mod.connect


class TestTaskWorker(unittest.TestCase):
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

        self._patch_db = unittest.mock.patch.object(db_mod, "connect", _patched_connect)
        self._patch_db.start()

        self._root = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(self._root, ignore_errors=True))

        self._project_id = self._insert_project()
        self.addCleanup(self._patch_db.stop)

    def _insert_project(self) -> int:
        now = "2026-01-01T00:00:00Z"
        slug = f"w_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                """
                INSERT INTO projects (name, slug, root_path, created_at, updated_at)
                VALUES (?,?,?,?,?)
                """,
                ("Worker Test", slug, self._root, now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    # ── Manual mode tests ─────────────────────────────────────────────────────

    @unittest.mock.patch("task_worker.claude_prompts.build_prompts", return_value=("sys", "usr"))
    @unittest.mock.patch("task_worker.context_loader.load_project_context", return_value={})
    def test_manual_mode_stores_prompt_and_stops(
        self,
        _mock_ctx: unittest.mock.MagicMock,
        _mock_prompts: unittest.mock.MagicMock,
    ) -> None:
        """Manual mode: run reaches pending_input with prompt stored; no Claude call."""
        t = task_service.create_task(self._project_id, "manual", task_type="chore", source="manual")

        buf = io.StringIO()
        with unittest.mock.patch("sys.stdout", buf):
            rc = task_worker.main(["--mode", "manual", "--project-id", str(self._project_id)])

        self.assertEqual(rc, 0)

        # Task stays in_progress (not yet completed by human).
        after = task_service.get_task(t["id"])
        assert after is not None
        self.assertEqual(after["status"], "in_progress")

        # Run is at pending_input with prompt stored.
        runs = run_service.get_runs_for_task(t["id"])
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "pending_input")
        self.assertEqual(runs[0]["mode"], "manual")
        self.assertIsNotNone(runs[0]["input_prompt"])
        self.assertIn("sys", runs[0]["input_prompt"])

    @unittest.mock.patch("task_worker.claude_prompts.build_prompts", return_value=("sys", "usr"))
    @unittest.mock.patch("task_worker.context_loader.load_project_context", return_value={})
    def test_manual_mode_prompt_not_in_stdout(
        self,
        _mock_ctx: unittest.mock.MagicMock,
        _mock_prompts: unittest.mock.MagicMock,
    ) -> None:
        """Prompt text must not appear in stdout — only READY line."""
        task_service.create_task(self._project_id, "quiet", task_type="chore", source="manual")

        buf = io.StringIO()
        with unittest.mock.patch("sys.stdout", buf):
            task_worker.main(["--mode", "manual", "--project-id", str(self._project_id)])

        stdout = buf.getvalue()
        self.assertIn("READY", stdout)
        self.assertNotIn("SYSTEM:", stdout)
        self.assertNotIn("USER:", stdout)

    @unittest.mock.patch("task_worker.claude_prompts.build_prompts", return_value=("sys", "usr"))
    @unittest.mock.patch("task_worker.context_loader.load_project_context", return_value={})
    def test_manual_mode_single_task_only(
        self,
        _mock_ctx: unittest.mock.MagicMock,
        _mock_prompts: unittest.mock.MagicMock,
    ) -> None:
        """With 2 pending tasks, worker claims exactly one per invocation."""
        task_service.create_task(self._project_id, "first", task_type="chore", source="manual")
        task_service.create_task(self._project_id, "second", task_type="chore", source="manual")

        task_worker.main(["--mode", "manual", "--project-id", str(self._project_id)])

        pending = task_service.list_tasks(project_id=self._project_id, status="pending")
        in_progress = task_service.list_tasks(project_id=self._project_id, status="in_progress")
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(in_progress), 1)

    # ── AI mode tests ─────────────────────────────────────────────────────────

    def test_ai_mode_without_api_key_exits_before_claim(self) -> None:
        t = task_service.create_task(self._project_id, "no-key", task_type="chore", source="manual")
        err = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            with unittest.mock.patch("sys.stderr", err):
                rc = task_worker.main(["--mode", "ai", "--project-id", str(self._project_id)])
        self.assertEqual(rc, 2)
        self.assertIn("ANTHROPIC_API_KEY", err.getvalue())
        after = task_service.get_task(t["id"])
        assert after is not None
        self.assertEqual(after["status"], "pending")
        self.assertEqual(len(run_service.get_runs_for_task(t["id"])), 0)

    @unittest.mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
    @unittest.mock.patch(
        "task_worker.claude_execution.run_messages_with_retry",
        return_value="assistant output",
    )
    def test_ai_mode_one_task_then_idempotent(
        self, _mock_claude: unittest.mock.MagicMock
    ) -> None:
        t = task_service.create_task(self._project_id, "one", task_type="chore", source="manual")
        self.assertEqual(t["status"], "pending")

        rc = task_worker.main(["--mode", "ai", "--project-id", str(self._project_id)])
        self.assertEqual(rc, 0)

        after = task_service.get_task(t["id"])
        assert after is not None
        self.assertEqual(after["status"], "done")

        runs = run_service.get_runs_for_task(t["id"])
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "success")
        self.assertIsNotNone(runs[0]["output"])
        self.assertIn("assistant output", runs[0]["output"])

        # Second invocation: no more pending tasks.
        rc2 = task_worker.main(["--mode", "ai", "--project-id", str(self._project_id)])
        self.assertEqual(rc2, 0)
        runs2 = run_service.get_runs_for_task(t["id"])
        self.assertEqual(len(runs2), 1)

    @unittest.mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}, clear=False)
    @unittest.mock.patch(
        "task_worker.claude_execution.run_messages_with_retry",
        side_effect=RuntimeError("claude unavailable"),
    )
    def test_ai_mode_claude_failure_marks_run_failed_and_task_blocked(
        self, _mock: unittest.mock.MagicMock
    ) -> None:
        t = task_service.create_task(self._project_id, "fail", task_type="chore", source="manual")
        rc = task_worker.main(["--mode", "ai", "--project-id", str(self._project_id)])
        self.assertEqual(rc, 1)
        after = task_service.get_task(t["id"])
        assert after is not None
        self.assertEqual(after["status"], "blocked")
        runs = run_service.get_runs_for_task(t["id"])
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["status"], "failed")
        self.assertIn("claude unavailable", runs[0]["error_message"] or "")

    # ── No pending tasks ──────────────────────────────────────────────────────

    def test_no_pending_prints_and_exits_zero(self) -> None:
        buf = io.StringIO()
        with unittest.mock.patch("sys.stdout", buf):
            rc = task_worker.main(["--project-id", str(self._project_id)])
        self.assertEqual(rc, 0)
        self.assertIn("No pending tasks", buf.getvalue())

    # ── Recovery tests ────────────────────────────────────────────────────────

    def test_recover_stuck_runs(self) -> None:
        """Startup recovery: running run whose task is done → success."""
        t = task_service.create_task(self._project_id, "stuck", task_type="chore", source="manual")
        run = run_service.create_run(t["id"], mode="ai")
        run_service.update_run(run["id"], "running")
        # Simulate crash after task→done but before run→success.
        task_service.update_status(t["id"], "done")
        # Run is still 'running' — stuck state.
        self.assertEqual(run_service.get_runs_for_task(t["id"])[0]["status"], "running")

        # Next worker startup recovers it.
        buf = io.StringIO()
        with unittest.mock.patch("sys.stdout", buf):
            task_worker.main(["--project-id", str(self._project_id)])

        self.assertIn("Recovered", buf.getvalue())
        recovered_run = run_service.get_runs_for_task(t["id"])[0]
        self.assertEqual(recovered_run["status"], "success")
        self.assertEqual(recovered_run["output"], "recovered")


if __name__ == "__main__":
    unittest.main()
