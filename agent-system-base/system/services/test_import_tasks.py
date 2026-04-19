"""Tests for import_tasks: temp DB + JSON file, idempotent import."""

from __future__ import annotations

import json
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
import import_tasks  # noqa: E402
import task_service  # noqa: E402

_real_connect = db_mod.connect


class TestImportTasks(unittest.TestCase):
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

        self._patcher = unittest.mock.patch.object(task_service.db, "connect", _patched_connect)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)

        self._project_id = self._insert_project()

        jfd, jpath = tempfile.mkstemp(suffix=".json")
        os.close(jfd)
        self._json_path = Path(jpath)
        self.addCleanup(lambda: self._json_path.exists() and self._json_path.unlink())

        payload = [
            {
                "title": "Alpha",
                "description": "d1",
                "status": "complete",
                "priority": 3,
                "created_at": "2026-03-10T10:00:00+00:00",
                "updated_at": "2026-03-10T11:00:00Z",
            },
            {
                "title": "Beta",
                "status": "open",
                "priority": 2,
                "created_at": "2026-03-11T12:00:00Z",
            },
        ]
        self._json_path.write_text(json.dumps(payload), encoding="utf-8")

    def _insert_project(self) -> int:
        now = "2026-01-01T00:00:00Z"
        slug = f"i_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, slug, created_at, updated_at) VALUES (?,?,?,?)",
                ("Import Test", slug, now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def test_dry_run_no_writes(self) -> None:
        rc = import_tasks.main(
            ["--project-id", str(self._project_id), "--tasks-json", str(self._json_path), "--dry-run"],
        )
        self.assertEqual(rc, 0)
        self.assertEqual(len(task_service.list_tasks(project_id=self._project_id)), 0)

    def test_missing_project_id_fails_fast(self) -> None:
        rc = import_tasks.main(
            ["--project-id", "999999", "--tasks-json", str(self._json_path), "--dry-run"],
        )
        self.assertEqual(rc, 1)

    def test_import_twice_idempotent(self) -> None:
        rc1 = import_tasks.main(
            ["--project-id", str(self._project_id), "--tasks-json", str(self._json_path)],
        )
        self.assertEqual(rc1, 0)
        tasks = task_service.list_tasks(project_id=self._project_id)
        self.assertEqual(len(tasks), 2)
        titles = {t["title"] for t in tasks}
        self.assertEqual(titles, {"Alpha", "Beta"})
        for t in tasks:
            self.assertEqual(t["source"], "import")
        alpha = next(t for t in tasks if t["title"] == "Alpha")
        self.assertEqual(alpha["status"], "done")
        self.assertEqual(alpha["priority"], "high")
        self.assertEqual(alpha["created_at"], "2026-03-10T10:00:00Z")

        rc2 = import_tasks.main(
            ["--project-id", str(self._project_id), "--tasks-json", str(self._json_path)],
        )
        self.assertEqual(rc2, 0)
        tasks2 = task_service.list_tasks(project_id=self._project_id)
        self.assertEqual(len(tasks2), 2)

    def test_duplicate_within_file_second_skipped(self) -> None:
        dup = [
            {
                "title": "Same",
                "created_at": "2026-01-01T00:00:00Z",
                "priority": 1,
            },
            {
                "title": "Same",
                "created_at": "2026-01-01T00:00:00Z",
                "priority": 2,
            },
        ]
        dfd, dpath = tempfile.mkstemp(suffix=".json")
        os.close(dfd)
        p = Path(dpath)
        self.addCleanup(lambda: p.exists() and p.unlink())
        p.write_text(json.dumps(dup), encoding="utf-8")

        import_tasks.main(["--project-id", str(self._project_id), "--tasks-json", str(p)])
        self.assertEqual(len(task_service.list_tasks(project_id=self._project_id)), 1)


if __name__ == "__main__":
    unittest.main()
