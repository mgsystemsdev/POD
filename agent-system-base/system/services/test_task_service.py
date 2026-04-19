"""Tests for task_service using real SQLite with m001 applied via db.connect().

Uses a temp file (not :memory:) so multi-connection threading tests avoid shared-cache
holder quirks and concurrent BEGIN IMMEDIATE lock errors.
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
import unittest.mock
import uuid
from contextlib import contextmanager
from pathlib import Path

_SERVICES_DIR = Path(__file__).resolve().parent
if str(_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(_SERVICES_DIR))

import db as db_mod  # noqa: E402
import task_service  # noqa: E402

_real_connect = db_mod.connect


class TestTaskService(unittest.TestCase):
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

        self._patcher = unittest.mock.patch.object(
            task_service.db,
            "connect",
            _patched_connect,
        )
        self._patcher.start()
        self._project_id = self._insert_project()

    def tearDown(self) -> None:
        self._patcher.stop()

    def _insert_project(self) -> int:
        now = "2026-01-01T00:00:00Z"
        slug = f"t_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._db_path) as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, slug, created_at, updated_at) VALUES (?,?,?,?)",
                ("Test Project", slug, now, now),
            )
            conn.commit()
            return int(cur.lastrowid)

    def test_create_get_list(self) -> None:
        t = task_service.create_task(
            self._project_id,
            "Hello",
            description="d",
            task_type="feature",
            source="manual",
        )
        self.assertEqual(t["title"], "Hello")
        self.assertEqual(t["status"], "pending")
        got = task_service.get_task(t["id"])
        assert got is not None
        self.assertEqual(got["title"], "Hello")
        listed = task_service.list_tasks(project_id=self._project_id)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], t["id"])

    def test_list_tasks_status_filter(self) -> None:
        task_service.create_task(self._project_id, "a")
        t2 = task_service.create_task(self._project_id, "b")
        task_service.update_status(t2["id"], "done")
        pending = task_service.list_tasks(project_id=self._project_id, status="pending")
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["title"], "a")

    def test_update_status_invalid_raises(self) -> None:
        t = task_service.create_task(self._project_id, "x")
        with self.assertRaises(ValueError):
            task_service.update_status(t["id"], "not_a_status")

    def test_create_task_invalid_enum(self) -> None:
        with self.assertRaises(ValueError):
            task_service.create_task(self._project_id, "x", priority="mega")

    def test_create_task_preserves_timestamps(self) -> None:
        c = "2026-02-01T12:30:00Z"
        u = "2026-02-02T15:00:00+00:00"
        t = task_service.create_task(
            self._project_id,
            "ts",
            created_at=c,
            updated_at=u,
            source="import",
        )
        self.assertEqual(t["created_at"], "2026-02-01T12:30:00Z")
        self.assertEqual(t["updated_at"], "2026-02-02T15:00:00Z")

    def test_claim_priority_order(self) -> None:
        with _real_connect(database=self._db_path) as conn:
            conn.executemany(
                """
                INSERT INTO tasks (project_id, title, status, priority, type, source, created_at, updated_at)
                VALUES (?, ?, 'pending', ?, 'chore', 'manual', ?, ?)
                """,
                [
                    (self._project_id, "low", "low", "2026-01-01T00:00:01Z", "2026-01-01T00:00:01Z"),
                    (self._project_id, "urgent", "urgent", "2026-01-01T00:00:00Z", "2026-01-01T00:00:00Z"),
                    (self._project_id, "low2", "low", "2026-01-01T00:00:02Z", "2026-01-01T00:00:02Z"),
                ],
            )
            conn.commit()
        claimed = task_service.claim_next_pending(project_id=self._project_id)
        assert claimed is not None
        self.assertEqual(claimed["title"], "urgent")
        self.assertEqual(claimed["status"], "in_progress")

    def test_claim_sequential_single_pending_second_none(self) -> None:
        task_service.create_task(self._project_id, "solo")
        first = task_service.claim_next_pending()
        second = task_service.claim_next_pending()
        assert first is not None
        self.assertIsNone(second)
        self.assertEqual(first["status"], "in_progress")

    def test_concurrent_claim_no_duplicate(self) -> None:
        task_service.create_task(self._project_id, "t1", priority="urgent")
        task_service.create_task(self._project_id, "t2", priority="low")
        results: list[dict | None] = []
        lock = threading.Lock()

        def claim() -> None:
            r = task_service.claim_next_pending()
            with lock:
                results.append(r)

        threads = [threading.Thread(target=claim) for _ in range(2)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        ids = {r["id"] for r in results if r is not None}
        self.assertEqual(len(ids), 2, msg="each claim must return a distinct task")

    def test_concurrent_claim_one_task_only_one_wins(self) -> None:
        task_service.create_task(self._project_id, "only")
        results: list[dict | None] = []
        barrier = threading.Barrier(2)

        def claim() -> None:
            barrier.wait()
            results.append(task_service.claim_next_pending())

        threads = [threading.Thread(target=claim) for _ in range(2)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        winners = [r for r in results if r is not None]
        self.assertEqual(len(winners), 1)


class TestTaskServiceInMemory(unittest.TestCase):
    """Single-threaded :memory: check (m001 via connect); holder keeps the DB alive."""

    def setUp(self) -> None:
        self._uri = f"file:mem_{uuid.uuid4().hex}?mode=memory&cache=shared"
        self._holder_cm = _real_connect(database=self._uri, uri=True)
        self._holder_cm.__enter__()

        @contextmanager
        def _patched(*, database: str | None = None, uri: bool = False):
            if database is None:
                with _real_connect(database=self._uri, uri=True) as conn:
                    yield conn
            else:
                with _real_connect(database=database, uri=uri) as conn:
                    yield conn

        self._patcher = unittest.mock.patch.object(task_service.db, "connect", _patched)
        self._patcher.start()
        now = "2026-01-01T00:00:00Z"
        slug = f"im_{uuid.uuid4().hex[:12]}"
        with _real_connect(database=self._uri, uri=True) as conn:
            cur = conn.execute(
                "INSERT INTO projects (name, slug, created_at, updated_at) VALUES (?,?,?,?)",
                ("IM", slug, now, now),
            )
            conn.commit()
            self._project_id = int(cur.lastrowid)

    def tearDown(self) -> None:
        self._patcher.stop()
        self._holder_cm.__exit__(None, None, None)

    def test_create_and_get_in_memory(self) -> None:
        t = task_service.create_task(self._project_id, "mem")
        got = task_service.get_task(t["id"])
        assert got is not None
        self.assertEqual(got["title"], "mem")


if __name__ == "__main__":
    unittest.main()
